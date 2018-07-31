#!/usr/bin/python
# -*- coding: utf-8 -*-

import BaseHTTPServer
import functools
import json


class HTTPError(Exception):
    def __init__(self, code, reason):
        super(HTTPError, self).__init__(reason)
        self.code = code


class JsonSerializable(object):
    """Implements method toDict to convert class to dict.

    Inherited class should use __slots__
    """

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


class UserSchema(object):
    """The class to validate correctness of input data for User methods"""

    schema = {
        'email': (basestring, lambda x: x),
        'password': (basestring, lambda x: 5 < len(x) < 40),
        'confirm_password': (basestring, lambda x: 5 < len(x) < 40)
    }

    @classmethod
    def check_value(cls, name, value):
        try:
            traits = cls.schema[name]
        except KeyError:
            raise HTTPError(400, 'unknown value {}'.format(name))

        if not isinstance(value, traits[0]):
            raise HTTPError(400, '{} does has wrong type, expected {}'.format(name, traits[0]))
        if not traits[1](value):
            raise HTTPError(400, '{} does has wrong value'.format(name))

    @classmethod
    def validate(cls, d):
        for k, v in d.items():
            cls.check_value(k, v)


class UserController(object):
    """Manages Users collection."""

    schema = UserSchema

    def registration(self, data):
        """Create new user."""
        self.schema.validate(data)

        # Need add user into db.
        print 'Creating user'
        print(data)

        return {'ok': 'True'}

    def login(self, data):
        """User's authentication."""
        self.schema.validate(data)

        # Request to db to check: user in db or not.
        print 'Checking auth'
        print(data)

        return {'ok': 'True'}


class HTTPHandler(BaseHTTPServer.BaseHTTPRequestHandler):

    """The main http handler, routes requests by path and calls appropriate controller methods."""

    controller = UserController()

    def do_POST(self):
        """Process POST requests."""
        if self.path == '/user/login':
            return self.process_request(201, functools.partial(self.call_with_body, self.controller.login))

        elif self.path == '/user/registration':
            return self.process_request(201, functools.partial(self.call_with_body, self.controller.registration))

        self.not_found()

    def get_data(self):
        """Get request params from body"""
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
        """Process requests and handle exceptions"""
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
        """Formats response as json and writes"""
        if data is not None:
            body = json.dumps(data, sort_keys=True, indent=4, cls=JSONEncoder).encode('utf-8')
            self.send_response(status)
            self.send_header('Content-Type', 'application/json; charset=utf=8')
            self.send_header('Content-Length',  len(body))
            self.end_headers()
            self.wfile.write(body)
            self.wfile.flush()
        else:
            self.send_response(204)

    def not_found(self):
        self.write_response(404, {'error': 'not found'})


def main():
    server_address = ('127.0.0.1', 8080)
    server = BaseHTTPServer.HTTPServer(server_address, HTTPHandler)
    server.serve_forever()


if __name__ == '__main__':
    main()
