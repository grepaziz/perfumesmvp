import http.server
import socketserver
import os

PORT = 5000
HOST = "0.0.0.0"

class ReuseAddrServer(socketserver.TCPServer):
    allow_reuse_address = True

class GzipHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()

    def do_GET(self):
        if self.path.endswith('.json'):
            accept_encoding = self.headers.get('Accept-Encoding', '')
            gz_path = self.translate_path(self.path) + '.gz'
            if 'gzip' in accept_encoding and os.path.isfile(gz_path):
                try:
                    with open(gz_path, 'rb') as f:
                        compressed = f.read()
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.send_header('Content-Encoding', 'gzip')
                    self.send_header('Content-Length', str(len(compressed)))
                    self.end_headers()
                    self.wfile.write(compressed)
                except (ConnectionResetError, BrokenPipeError):
                    pass
                return
        try:
            super().do_GET()
        except (ConnectionResetError, BrokenPipeError):
            pass

    def log_message(self, format, *args):
        if args and '404' in str(args) and 'favicon' in str(args):
            return
        super().log_message(format, *args)

with ReuseAddrServer((HOST, PORT), GzipHandler) as httpd:
    print(f"Serving on http://{HOST}:{PORT}")
    httpd.serve_forever()
