import logging
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib import parse
import json
import threading
from Utils.settings import Settings


class ThreadedServer:

    def __init__(self, processor):  # TODO processor is hier spin in web; beter lijkt om daarvoor een app_info_distributor toe te passen
        self.processor = processor
        self.runServer()

    def runServer(self):
        # Start the server in a new thread
        daemon = threading.Thread(name='daemon_server',
                                  target=self.start_server,
                                  args=(self.processor, Settings().webServerPort()))
        daemon.setDaemon(True)  # Set as a daemon so it will be killed once the main thread is dead.
        daemon.start()

    @staticmethod
    def start_server(processor, port=80):
        """Start a simple webserver serving path on port"""
        httpd = ThreadingHTTPServer(('', port), MakeHandlerClass(processor))
        httpd.serve_forever()


def MakeHandlerClass(init_args):

    class Handler(BaseHTTPRequestHandler):

        URL_BROWSER_VIEWS = {
            "/raw": "getRaw",
            "/dumpdata": "getRealtimeDatadump",
            "/": "getStr",
        }

        URL_DATA_VIEWS = {
            "/get_data": "get_data",
        }

        def __init__(self, *args, **kwargs):
            super(Handler, self).__init__(*args, **kwargs)

        def do_HEAD(self):
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()

        def do_GET(self):
            """Respond to a GET request."""
            logging.debug(f"GET request: {self.path}")
            parsed = parse.urlsplit(self.path)
            self.send_response(200)
            if parsed.path in self.URL_DATA_VIEWS:
                logging.debug(f"GET request is in URL_DATA_VIEWS")
                self.send_header("Accept", "application/json")
                self.end_headers()
                view = getattr(self.init_args, self.URL_DATA_VIEWS[parsed.path])
                result = view(parsed.query)
                logging.debug(f"result from do_GET: {result}")
                self.wfile.write(bytes(json.dumps(result), 'utf-8'))
            elif parsed.path in self.URL_BROWSER_VIEWS:
                logging.debug(f"GET request is in URL_BROWSER_VIEWS")
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(b"<html><head><title>Power logger</title></head>")
                self.wfile.write(b"<body><p>Erik Kouwenhoven, 2023</p>")
                self.wfile.write(b"<p>You accessed path: %b</p>" % self.path.encode())
                view = getattr(self.init_args, self.URL_BROWSER_VIEWS[parsed.path])
                result = view()
                for line in result:
                    self.wfile.write(f"{line}<br>".encode('utf-8'))
                self.wfile.write(b"</body></html>")
            else:
                logging.error(f"Invalid request {self.path}")
            logging.debug(f"GET request completed")

    Handler.init_args = init_args
    return Handler

