# ESSENZA — Perfume Comparison

## Overview
A static single-page web application for comparing perfumes. The app loads a large catalog of perfume data from JSON files and provides filtering, sorting, and comparison features.

## Project Architecture
- **Frontend**: Single `index.html` file with embedded CSS and JavaScript
- **Data**: `catalog/catalog.json` (31MB perfume catalog) and `catalog/images.json` (image URL mappings)
- **Server**: `server.py` — Python HTTP server with gzip compression for large JSON files
- **Utility**: `scrape_images.py` — Python script for scraping perfume images

## Key Technical Details
- The catalog JSON is ~31MB uncompressed, pre-compressed to ~3MB with gzip
- Server serves pre-compressed `.gz` files for `.json` requests when client accepts gzip
- No build system or package manager needed — pure static site
- Python 3.12 used for the static file server

## Running
- Workflow: `python server.py` on port 5000
- The app takes a few seconds to load due to the large catalog file

## Recent Changes
- 2026-02-06: Initial Replit setup with gzip-compressed static file server
