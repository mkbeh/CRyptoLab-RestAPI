#!/usr/bin/python
# -*- coding: utf-8 -*-

import BaseHTTPServer
import json
import functools


class HTTPError(Exception):
    def __init__(self, code, reason):
        super(Exception, self).__init__(reason)
        self.code = code


class JsonSerializable(object):
    """Implements method toDict to convert class to dict.
    Inherited class should use __slots__"""

    def to_dict(self):
        return {
            k: getattr(self, k) for k in self.__slots__
        }


class JSONEncoder(json.JSONEncoder):
    """The custom json encoder, which allows to serialize JsonSerializable objects"""
    def default(self, o):
        if isinstance(o, JsonSerializable):
            return o.to_dict()
        return super(JSONEncoder, self).default(o)


class User(JsonSerializable):
    __slots__ = ('email', 'password')

    def __init__(self, email, password):
        self.email = email
        self.password = password


class UserController(object):
    def __init__(self):
        self.user = {}

    def create(self, data):
        """Create new user."""

        # Need add user into db.
        print 'Creating user'

        return {'ok': 'True'}

    def check_auth(self, username):
        """User's authentication."""

        # Request to db to check: user in db or not.
        print 'Checking auth'

        return {'ok': 'True'}


class HTTPHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    controller = UserController()

    def do_GET(self):
        if self.path.startswith('/user/'):
            parts = self.path.split('/', 4)

            if 3 == len(parts):
                username = parts[2]

                return self.process_request(200, functools.partial(self.controller.check_auth, username))

            self.not_found()

    def do_POST(self):
        if self.path == '/users/':
            self.process_request(201, functools.partial(self.call_with_body, self.controller.create))

        self.not_found()

    def get_data(self):
        """Get request params from body."""
        if not self.headers['Content-Type'].startswith('application/json'):
            raise HTTPError(415, 'expected application/json')

        number_of_bits = int(self.headers['Content-Length'])
        body = self.rfile.read(number_of_bits)

        return json.loads(body, encoding='utf-8')

    def call_with_body(self, handler):
        """Call handler with request body."""

        try:
            data = self.get_data()
        except Exception as e:
            raise HTTPError(400, str(e))

        return handler(data)

    def process_request(self, status, handler):
        """Process requests and handle exceptions."""
        try:
            data = handler()

        except HTTPError as e:
            data = {'error': str(e)}
            status = e.code

        except Exception as e:
            data = {'error': str(e)}
            status = 500

        self.write_response(status, data)

    def write_response(self, status, data):
        """Formats response as json and writes."""
        if data is not None:
            body = json.dumps(data, sort_keys=True, indent=4, cls=JSONEncoder).encode('utf-8')
            self.send_response(status)
            self.send_header('Content-Type', 'application/json; charset=utf=8')
            self.send_header('Content-Length', len(body))
            self.end_headers()
            self.wfile.write(body)
            self.wfile.flush()
        else:
            self.send_response(204)

    def not_found(self):
        self.write_response(404, {'error': 'Not found.'})


def main():
    server_address = ('127.0.0.1', 8080)
    server = BaseHTTPServer.HTTPServer(server_address, HTTPHandler)
    server.serve_forever()


if __name__ == '__main__':
    main()
