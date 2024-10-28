import logging
from enum import Enum, auto
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib import parse
import json
import threading
from Utils.settings import Settings
from WebServer.request_executor import RequestExecutor
from Application.inquirer import Inquirer


class ThreadedServer:

    def __init__(self, inquirer: Inquirer):
        self.request_executor = RequestExecutor(inquirer)
        self.run_server()

    def run_server(self):
        # Start the server in a new thread
        daemon = threading.Thread(name='daemon_server',
                                  target=self.start_server,
                                  args=(self.request_executor, Settings().web_server_port()),
                                  daemon=True)  # Set as a daemon, so it will be killed once the main thread is dead.
        daemon.start()

    @staticmethod
    def start_server(request_executor: RequestExecutor, port=80):
        """Start a simple webserver serving path on port"""
        httpd = ThreadingHTTPServer(('', port), make_handler_class(request_executor))
        httpd.serve_forever()


def make_handler_class(request_executor: RequestExecutor):

    class Handler(BaseHTTPRequestHandler):

        class ResponseReturn(Enum):
            DATA = auto()
            TEXT = auto()

        URL_VIEWS = {
            "/home": (ResponseReturn.TEXT, "home"),
            "/data_stores": (ResponseReturn.DATA, "get_data_stores"),
            "/data_store_info": (ResponseReturn.DATA, "get_data_store_info"),
            "/get_data": (ResponseReturn.DATA, "get_compact_data"),
            "/show_data": (ResponseReturn.DATA, "get_readable_data"),
            "/shift_info": (ResponseReturn.DATA, "get_shift_info"),
            "/system_info": (ResponseReturn.DATA, "get_system_info"),
            "/raw": (ResponseReturn.TEXT, "getRaw"),
            "/dumpdata": (ResponseReturn.TEXT, "getRealtimeDatadump"),
        }

        def __init__(self, *args, **kwargs):
            super(Handler, self).__init__(*args, **kwargs)
            self.request_executor = None

        def do_HEAD(self):
            logging.debug(f"HEAD request")
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()

        def do_GET(self):
            """Respond to a GET request."""
            logging.debug(f"GET request: {self.path}")
            parsed = parse.urlparse(self.path)

            try:
                view = getattr(self.request_executor, self.URL_VIEWS[parsed.path][1])
            except KeyError:
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"<p>Unknown request; path: %b</p>" % self.path.encode())
                self.wfile.write(b"<p>Usage: %b</p>" % self.help())
                return
            except AttributeError:
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"<p>Not implemented; path: %b</p>" % self.path.encode())
                self.wfile.write(b"<p>Usage: %b</p>" % self.help())
                return
            try:
                result = view(parsed.query)
            except AttributeError:
                self.send_response(200)  # Bad request
                self.end_headers()
                self.wfile.write(b"<p>Unknown error path: %b</p>" % self.path.encode())
                self.wfile.write(b"<p>Usage: %b</p>" % self.help())
                return

            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.send_header("Accept", "application/json")
            self.end_headers()

            if self.URL_VIEWS[parsed.path][0] == self.ResponseReturn.DATA:
                self.wfile.write(json.dumps(result).encode('utf-8'))
            else:
                for line in result:
                    self.wfile.write(f"{line}\n".encode('utf-8'))
            # logging.debug(f"result from do_GET {parsed.query}: {result}")
            logging.debug(f"GET request completed")

        def help(self):
            return f"Usage: {[key for key in self.URL_VIEWS]}".encode('utf-8')

    Handler.request_executor = request_executor
    return Handler
