#!/usr/bin/env python3
"""
Scrape perfume bottle images from Parfumo pages.
Saves a mapping of canonical_url -> image_url to catalog/images.json
Uses session cookies, rotating user agents, and careful rate limiting.
"""

import json
import re
import time
import os
import random
import http.cookiejar
from urllib.request import Request, urlopen, build_opener, HTTPCookieProcessor
from urllib.error import HTTPError, URLError

CATALOG_PATH = "catalog/catalog.json"
OUTPUT_PATH = "catalog/images.json"
BATCH_SAVE_EVERY = 20
BASE_DELAY = 2.0
MAX_RETRIES = 2

USER_AGENTS = [
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_3) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:122.0) Gecko/20100101 Firefox/122.0',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
]

# Create a session with cookies
cj = http.cookiejar.CookieJar()
opener = build_opener(HTTPCookieProcessor(cj))

def extract_image_url(html):
    """Extract the main perfume image from Parfumo HTML."""
    og_match = re.search(r'<meta\s+property=["\']og:image["\']\s+content=["\']([^"\']+)["\']', html)
    if og_match:
        url = og_match.group(1)
        if '404' not in url and 'parfumo' in url:
            return url
    for pattern in [
        r'(https://media\.parfumo\.com/perfume_social/[^"\'\s]+\.(?:jpg|png|webp)[^"\'\s]*)',
        r'(https://media\.parfumo\.com/perfumes/[^"\'\s]+\.(?:jpg|png|webp)[^"\'\s]*)',
        r'(https://images\.parfumo\.de/perfume_bottle/[^"\'\s]+\.(?:jpg|png|webp))',
    ]:
        match = re.search(pattern, html)
        if match:
            return match.group(1)
    return None

def fetch_image_url(canonical_url, attempt=0):
    """Fetch a Parfumo page and extract the image URL."""
    try:
        ua = random.choice(USER_AGENTS)
        req = Request(canonical_url, headers={
            'User-Agent': ua,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9,de;q=0.8',
            'Accept-Encoding': 'identity',
            'Referer': 'https://www.parfumo.com/',
            'DNT': '1',
            'Upgrade-Insecure-Requests': '1',
        })
        resp = opener.open(req, timeout=20)
        html = resp.read().decode('utf-8', errors='ignore')
        resp.close()
        return extract_image_url(html)
    except HTTPError as e:
        if (e.code == 429 or e.code == 403) and attempt < MAX_RETRIES:
            wait = (2 ** attempt) * 10 + random.uniform(2, 8)
            print(f"\n  [{e.code}] Backing off {wait:.0f}s (attempt {attempt+1})...", flush=True)
            time.sleep(wait)
            return fetch_image_url(canonical_url, attempt + 1)
        return None
    except Exception:
        return None

def main():
    print("Loading catalog...")
    with open(CATALOG_PATH) as f:
        data = json.load(f)

    urls = set()
    for item in data:
        if item.get('canonical_url'):
            urls.add(item['canonical_url'])
    print(f"Found {len(urls)} unique perfumes")

    existing = {}
    if os.path.exists(OUTPUT_PATH):
        with open(OUTPUT_PATH) as f:
            raw = json.load(f)
        existing = {k: v for k, v in raw.items() if v is not None}
        print(f"Loaded {len(existing)} existing images, will retry failed ones")

    to_scrape = [u for u in urls if u not in existing]
    random.shuffle(to_scrape)  # Randomize order to avoid pattern detection
    print(f"Need to scrape {len(to_scrape)} URLs")

    if not to_scrape:
        print("All done!")
        return

    # First, warm up with the homepage to get cookies
    try:
        warmup = Request('https://www.parfumo.com/', headers={
            'User-Agent': random.choice(USER_AGENTS),
            'Accept': 'text/html',
        })
        resp = opener.open(warmup, timeout=15)
        resp.read()
        resp.close()
        print("Session established, starting scrape...")
        time.sleep(3)
    except:
        print("Could not establish session, proceeding anyway...")

    results = dict(existing)
    completed = 0
    found = len(existing)
    consecutive_fails = 0

    for url in to_scrape:
        delay = BASE_DELAY + random.uniform(0.5, 2.5)
        time.sleep(delay)

        img = fetch_image_url(url)
        results[url] = img
        completed += 1

        if img:
            found += 1
            consecutive_fails = 0
        else:
            consecutive_fails += 1
            if consecutive_fails >= 5:
                wait = 60 + random.uniform(0, 30)
                print(f"\n  {consecutive_fails} consecutive fails — pausing {wait:.0f}s...", flush=True)
                time.sleep(wait)
                consecutive_fails = 0

        if completed % 5 == 0 or completed == len(to_scrape):
            pct = completed / len(to_scrape) * 100
            print(f"\r[{pct:5.1f}%] {completed}/{len(to_scrape)} | Images: {found}/{found + completed - (found - len(existing))}", end="", flush=True)

        if completed % BATCH_SAVE_EVERY == 0:
            with open(OUTPUT_PATH, 'w') as f:
                json.dump(results, f)

    with open(OUTPUT_PATH, 'w') as f:
        json.dump(results, f)

    print(f"\n\nDone! {found} images found out of {len(urls)} perfumes.")
    print(f"Saved to {OUTPUT_PATH}")

if __name__ == "__main__":
    main()
