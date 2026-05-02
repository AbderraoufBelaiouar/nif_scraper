#!/usr/bin/env python3
"""
NIF Checker API - REST API for checking Algerian Tax Identification Number
Uses Python's built-in http.server (no external dependencies required)
Usage: python api.py
"""

import json
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from nif_checker import check_nif


class NIFHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'healthy'}).encode())
            return

        if self.path.startswith('/api/check-nif/'):
            nif = self.path.split('/api/check-nif/')[1]
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            result = check_nif(nif)
            self.wfile.write(json.dumps(result).encode())
            return

        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        if self.path == '/api/check-nif':
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')

            try:
                data = json.loads(body) if body else {}
            except json.JSONDecodeError:
                data = {}

            nif = data.get('nif')

            if not nif:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'status': 'error', 'message': 'NIF parameter is required'}).encode())
                return

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            result = check_nif(nif)
            self.wfile.write(json.dumps(result).encode())
            return

        self.send_response(404)
        self.end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def log_message(self, format, *args):
        print(f"[{self.log_date_time_string()}] {format % args}")


def run_server(port=5000):
    server_address = ('', port)
    httpd = HTTPServer(server_address, NIFHandler)
    print(f"NIF Checker API running on http://0.0.0.0:{port}")
    print(f"Endpoints:")
    print(f"  GET  /health                    - Health check")
    print(f"  GET  /api/check-nif/<nif>       - Check NIF via URL")
    print(f"  POST /api/check-nif             - Check NIF via JSON body")
    print(f"\nExample:")
    print(f"  curl http://localhost:{port}/api/check-nif/123456789012345")
    httpd.serve_forever()


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    run_server(port)