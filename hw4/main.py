#!/usr/local/bin/python
# coding: utf-8
import mimetypes
import socket
import select
import argparse
import urllib
from collections import namedtuple
from email.utils import formatdate

import os

from datetime import datetime
from time import mktime


def parse_args():
    args = argparse.ArgumentParser()
    # порт задается аргументом -p
    args.add_argument('-p', '--port', default=8080)
    # Числов worker'ов задается аргументом командной строки -w
    args.add_argument('-w', '--workers', default=4)
    # DOCUMENT_ROOT задается аргументом командной строки -r
    args.add_argument('-r', '--root', default=os.getcwd())
    return args.parse_args()


class HTTPRequest(object):
    http_status = namedtuple("http_status", ['code', 'message'])
    statuses = {
        'OK': http_status(200, 'OK'),
        'NotFound': http_status(404, 'Not Found'),
        'Error': http_status(405, 'Method Not Allowed')
    }
    allowed_extensions = (
        '.html', '.css', '.js', '.jpg', '.jpeg', '.png', '.gif', '.swf'
    )

    def __init__(self, request, init_params):
        self.req = request.splitlines()
        self.params = init_params
        # print request

    def response(self):
        methods_map = {
            'GET': self.get_response,
            'HEAD': self.head_response,
        }
        try:
            method, path, version = self.req[0].split()
            return methods_map[method](path)
        except Exception:
            pass

    def get_response(self, path):
        new_path = self.translate_url(path)
        file_ext = os.path.splitext(new_path)[1]

        content = ''

        if os.path.isfile(new_path) and file_ext in self.allowed_extensions:
            new_path = urllib.pathname2url(new_path)
            mime = mimetypes.guess_type(new_path)[0]

            mode = 'r' if mime.split('/')[0] == 'text' else 'rb'
            content_type = mime if mode == 'rb' else mime + '; charset=utf-8'

            with open(new_path, mode=mode) as f:
                content = f.read()

        response_header = (
            'HTTP/1.1 %d %s' % self.statuses['OK'],
            'Date: %s' % formatdate(timeval=mktime(datetime.now().timetuple()), localtime=False, usegmt=True),
            'Server: test server',
            'Content-Length: %d' % len(content),
            'Content-Type: %s' % "%s" % content_type,
            'Connection: Close'
        )
        response = "\n".join(response_header) + "\n\n" + content
        # print response
        return response

    def translate_url(self, url, index_file='index.html'):
        url = urllib.unquote(url).decode('utf8')

        if url.endswith('/'):
            url += index_file

        return os.path.join(self.params['DOCUMENT_ROOT'], url[1:])


def main(arguments):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    request_params = {
        'DOCUMENT_ROOT': arguments.root
    }

    server_socket.bind(('', arguments.port))
    server_socket.setblocking(0)
    server_socket.listen(10)

    print 'Server started...'

    inputs = {server_socket}
    outputs = {}
    excepts = []

    while True:
        input_ready, output_ready, except_ready = select.select(list(inputs), outputs.keys(), excepts, 0.5)

        for s in input_ready:
            if s == server_socket:
                client_socket, remote_address = server_socket.accept()
                client_socket.setblocking(0)
                inputs.add(client_socket)
            else:
                request = s.recv(1024)
                print '{} : {}'.format(s.getpeername(), request)
                outputs[s] = HTTPRequest(request, request_params).response()
                inputs.remove(s)

        for s in output_ready:
            if s in outputs:
                s.send(outputs[s])
                del outputs[s]
                s.close()


if __name__ == '__main__':
    args = parse_args()
    main(args)
