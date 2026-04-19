#!/usr/bin/env python3
"""
Tiny server for LALR(1) Parser GUI
Run: python3 server.py
Then open: http://localhost:8765
"""
import os
import subprocess, json, os, sys
from http.server import HTTPServer, BaseHTTPRequestHandler

BINARY = os.path.join(os.path.dirname(__file__), "lalr_parser")

# Compile if binary missing
if not os.path.exists(BINARY):
    src = os.path.join(os.path.dirname(__file__), "lalr_parser.c")
    result = subprocess.run(["gcc", src, "-o", BINARY], capture_output=True, text=True)
    if result.returncode != 0:
        print("Compilation failed:\n" + result.stderr)
        sys.exit(1)
    print("Compiled successfully.")

HTML_FILE = os.path.join(os.path.dirname(__file__), "index.html")

class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass  # suppress default logs

    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            with open(HTML_FILE, "rb") as f:
                data = f.read()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == "/parse":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            try:
                payload = json.loads(body)
                expr = payload.get("expr", "").strip()
                if not expr:
                    raise ValueError("empty")
            except Exception:
                self._json({"error": "Invalid request"}, 400)
                return

            try:
                proc = subprocess.run(
                    [BINARY],
                    input=expr + "\nquit\n",
                    capture_output=True, text=True, timeout=5
                )
                self._json({"output": proc.stdout, "expr": expr})
            except subprocess.TimeoutExpired:
                self._json({"error": "Parser timed out"}, 500)
            except FileNotFoundError:
                self._json({"error": "Parser binary not found. Compile lalr_parser.c first."}, 500)
        else:
            self.send_response(404)
            self.end_headers()

    def _json(self, data, code=200):
        body = json.dumps(data).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8765)) 
    server = HTTPServer(("0.0.0.0", port), Handler)
    print(f"LALR(1) Parser GUI running at http://localhost:{port}")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
