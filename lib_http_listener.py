#!/usr/bin/env python3

__date__ = "20200406"
__author__ = "pjn2work@gmail.com"


import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import json
import re
from urllib.parse import unquote


HOST = '127.0.0.1'      # address to bind
_listeners = list()     # list with all listeners passed on start()
_servers_list = list()  # list with all http servers (for later .close())


def _notify_listeners(message_dict):
    global _listeners
    for lst in _listeners:
        lst(message_dict)


def _demo_listener(message_dict):
    print(message_dict)


class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):

    def _send_formated_response(self, message):
        self.send_response(200)

        if isinstance(message, dict):
            self.send_header('Content-type', "application/json")
            message = json.dumps(message).encode("utf8")
        else:
            self.send_header('Content-type', 'text/html')
            message = str(message).encode("utf8")
        self.end_headers()

        self.wfile.write(message)

    # return a dict with all received headers
    def _parse_headers(self):
        res = dict()
        for k, v in self.headers.items():
            res[k] = v
        return res

    # return a string with path (omitting http://address:port and ?querystring=stuff)
    def _parse_path(self):
        if "?" in self.path:
            return self.path[:self.path.index("?")]
        return self.path

    # return a dict with all parameters on the querystring
    def _parse_querystring(self):
        res = dict()
        if "?" in self.path:
            i = self.path.index("?")
            for kv in self.path[i+1:].split("&"):
                k, v = kv.split("=")
                res[k] = unquote(v)
        return res

    # dictionary with all http info
    def _get_dict(self):
        return dict(method=self.command,
                    headers=self._parse_headers(),
                    address=self.address_string(),
                    fullpath=self.path,
                    path=self._parse_path(),
                    querystring=self._parse_querystring())

    # used on posts
    def _parse_post_body(self):
        resp = dict()
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

    def do_GET(self):
        if self.path != "/favicon.ico":
            message = self._get_dict()
            self._send_formated_response(message)
            _notify_listeners(message)

    def do_POST(self):
        message = self._get_dict()
        message["body"] = self._parse_post_body()
        self._send_formated_response(message)
        _notify_listeners(message)


def close_all_http():
    global _servers_list
    print("Closing HTTP Servers", _servers_list, file=sys.stderr)
    for http_server in _servers_list:
        try:
            http_server.server_close()
        except:
            pass


def open_tcp_port(host, port):
    httpd = HTTPServer((host, port), SimpleHTTPRequestHandler)
    print(f"Running Server http://{host}:{port}", file=sys.stderr)

    # append to list for later closure
    _servers_list.append(httpd)

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass

    httpd.server_close()


def start(tcp_ports_list=[8080], listeners_list=[_demo_listener], blocking=False):
    global _listeners
    _listeners = listeners_list

    # start threads
    list_of_threads = list()
    for port in tcp_ports_list:
        x = threading.Thread(target=open_tcp_port, args=(HOST,int(port)), daemon=True)
        list_of_threads.append(x)
        x.start()

    if blocking:
        for x in list_of_threads:
            x.join()


if __name__ == "__main__":
    start(tcp_ports_list=[8080, 8081], blocking=True)