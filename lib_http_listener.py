#!/usr/bin/env python3

__date__ = "20200406"
__author__ = "pjn2work@gmail.com"


import sys
import threading
import json
import re

from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import unquote
from time import sleep


HOST = '127.0.0.1'      # Hostname to bind
_listeners = list()     # list with all listeners passed on start()
_servers_list = list()  # list with all http servers (for later .close())
_verbose = None


def print_message(message):
    if _verbose:
        print(message, file=sys.stderr)


def _notify_listeners(message_dict):
    global _listeners
    for lst in _listeners:
        lst(message_dict)


def prettify(json_obj) -> str:
    try:
        if isinstance(json_obj, dict):
            return json.dumps(json_obj, indent=3)
        return json.dumps(json.loads(json_obj), indent=3)
    except:
        return str(json_obj)


def _demo_listener(message_dict):
    print(prettify(message_dict))


class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        if _verbose:
            super().log_message(format, args)

    def _send_formated_response(self, message):
        self.send_response(200)

        if isinstance(message, dict):
            self.send_header('Content-type', "application/json")
            message = json.dumps(message).encode("utf-8")
        else:
            self.send_header('Content-type', 'text/html')
            message = str(message).encode("utf-8")
        self.end_headers()

        self.wfile.write(message)

    # return a dict with all received headers
    def _parse_headers(self):
        return {k: v for k, v in self.headers.items()}

    # return a string with path (omitting http://address:port and ?querystring=stuff)
    def _parse_path(self):
        if "?" in self.path:
            return self.path[:self.path.index("?")]
        return self.path

    # return a dict with all parameters on the querystring
    def _parse_querystring(self):
        res = dict()
        if "?" in self.path:
            for kv in self.path[self.path.index("?")+1:].split("&"):
                k, v = kv.split("=")
                res[k] = unquote(v)
        return res

    # used on posts
    def _parse_post_body(self):
        resp = dict()

        if 'Content-Length' in self.headers:
            body = self.rfile.read(int(self.headers['Content-Length'])).decode("utf8")

            ct = "multipart/form-data; boundary="
            if self.headers["Content-Type"].startswith(ct):
                boundary = self.headers["Content-Type"][len(ct):]

                for row in body.split(boundary):
                    if row and row != "--" and row != "--\r\n":
                        re_groups = re.search('Content-Disposition: form-data; name=\"(.+)\"\r\n\r\n(.+)\r\n--', row)
                        if re_groups:
                            field_name = re_groups.group(1)
                            field_value = re_groups.group(2)
                            resp[field_name] = field_value
            elif self.headers["Content-Type"].startswith("application/x-www-form-urlencoded"):
                for kv in body.split("&"):
                    k, v = kv.split("=")
                    resp[k] = unquote(v)
            else:
                resp["raw"] = body

        return resp

    # dictionary with all http info
    def _get_response_dict(self):
        return dict(method=self.command,
                    headers=self._parse_headers(),
                    address=self.address_string(),
                    fullpath=self.path,
                    path=self._parse_path(),
                    querystring=self._parse_querystring(),
                    body=self._parse_post_body())

    def do_GET(self):
        if self.path != "/favicon.ico":
            message = self._get_response_dict()
            self._send_formated_response(message)
            _notify_listeners(message)

    def do_POST(self):
        message = self._get_response_dict()
        self._send_formated_response(message)
        _notify_listeners(message)


def close_all_http():
    global _servers_list
    for http_server in list(_servers_list):
        try:
            http_server.server_close()
            _servers_list.remove(http_server)
            print_message(f"Closed HTTP Server {http_server.server_port}")
            sleep(3)    # unbind takes time for the OS to react
        except:
            print_message(f"Error closing HTTP Server {http_server.server_port}")


def open_tcp_port(host, port):
    httpd = HTTPServer((host, port), SimpleHTTPRequestHandler)
    print_message(f"Running Server http://{host}:{port}")

    # append to list for later closure
    _servers_list.append(httpd)

    httpd.serve_forever()
    httpd.server_close()


def start(tcp_ports_list=[8080], listeners_list=[_demo_listener], blocking=False, verbose=False):
    global _listeners, _verbose
    _listeners = listeners_list
    _verbose = verbose

    # start threads
    list_of_threads = list()
    for port in tcp_ports_list:
        x = threading.Thread(target=open_tcp_port, args=(HOST,int(port)), daemon=True)
        list_of_threads.append(x)
        x.start()

    if blocking:
        try:
            for x in list_of_threads:
                x.join()
        except KeyboardInterrupt:
            close_all_http()


if __name__ == "__main__":
    start(tcp_ports_list=[8080, 8081], blocking=True)
