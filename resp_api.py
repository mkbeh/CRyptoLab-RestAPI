#!/usr/bin/python
# -*- coding: utf-8 -*-

import BaseHTTPServer
import functools
import json
import unicodedata
import ssl

import utils

from pymongodb import pymongodb


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
        'confirm_password': (basestring, lambda x: 5 < len(x) < 40),
        'id': (basestring, lambda x: x)
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

    schema = UserSchema()
    mongo = pymongodb.MongoDB()
    json_encoder = pymongodb.JSONEncoder()

    def registration(self, data):
        """Create new user."""
        self.schema.validate(data)

        # Encode data.
        email = unicodedata.normalize('NFKD', data['email']).encode('utf-8', 'ignore')
        password = unicodedata.normalize('NFKD', data['password']).encode('utf-8', 'ignore')
        confirm_password = unicodedata.normalize('NFKD', data['confirm_password']).encode('utf-8', 'ignore')

        # Validate data.
        result = utils.validate_values(email, password, confirm_password)

        if result is True:
            # Check on current email is already registered.
            document = self.mongo.find_one({'email': email}, 'users')

            if document is None:
                # Hashing password.
                passwd_hash = utils.passwd_hashing(password)

                # Try to get email from db.
                document = self.mongo.insert_one({'email': email, 'password': passwd_hash}, 'users')

                return {'id': self.json_encoder.encode(document.inserted_id)}

            elif document is not None:
                return {'status': {'error': 'User with current email is already registered.'}}

        else:
            # Return error.
            return {'status': {'error': 'Incorrect data.'}}

    def login(self, data):
        """User's authentication."""
        self.schema.validate(data)

        # Validate user's data.
        result = utils.validate_values(data['email'], data['password'])

        # Check result.
        if result is True:
            # Try to get email from db.
            if data['id'] == 'None':
                document = self.mongo.find_one({'email': data['email']}, 'users')
            else:
                document = self.mongo.find_one_by_id(data['id'], 'users')

            if document:
                email_s = document['email'].encode()
                password_s = document['password'].encode()
                email_c = data['email'].encode()
                password_c = data['password'].encode()

                if email_s == email_c and utils.passwd_checker(password_s, password_c):
                    return {'status': 'success'}

                else:
                    return {'status': {'error': 'Incorrect data.'}}

            else:
                return {'status': {'error': 'Incorrect data.'}}

        else:
            return {'status': {'error': 'Incorrect data.'}}


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
    server_address = ('127.0.0.1', 4443)

    server = BaseHTTPServer.HTTPServer(server_address, HTTPHandler)
    server.socket = ssl.wrap_socket(server.socket, keyfile=utils.get_path('cert', 'key.pem'),
                                    certfile=utils.get_path('cert', 'cert.pem'), server_side=True)
    server.serve_forever()


if __name__ == '__main__':
    main()