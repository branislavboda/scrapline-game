import http.server, socketserver, functools, os

PORT = 4180
ROOT = os.path.dirname(os.path.abspath(__file__))
Handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=ROOT)
with socketserver.TCPServer(("127.0.0.1", PORT), Handler) as httpd:
    httpd.serve_forever()
