#!/usr/local/bin/python
# coding: utf-8
import argparse
import mimetypes
import os
import select
import socket
import urllib
from datetime import datetime
from email.utils import formatdate
from time import mktime

from functools32 import lru_cache


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
    statuses = {
        'OK': '200 OK',
        'NotFound': '404 Not Found',
    }

    allowed_extensions = (
        '.html', '.css', '.js', '.jpg', '.jpeg', '.png', '.gif', '.swf'
    )

    def __init__(self, request, init_params):
        self.req = request.splitlines()
        self.params = init_params

    def build_header(self, status, **kwargs):
        response_header = (
            'HTTP/1.1 %s' % status,
            'Date: %s' % formatdate(timeval=mktime(datetime.now().timetuple()), localtime=False, usegmt=True),
            'Server: test server',
            'Content-Length: %d' % content_length,
            'Content-Type: %s' % "%s" % content_type,
            'Connection: Close'
        )

        return response_header

    def response(self):
        allowed_methods = {
            'GET': self.get_response,
            'HEAD': self.head_response,
        }
        try:
            method, path, version = self.req[0].split()
            return allowed_methods[method](path)
        except KeyError:
            # method not allowed
            return 'HTTP/1.1 405 Method Not Allowed\nDate: {date}\n' \
                   'Server: test server\nAllow: {allowed_methods}\nConnection: Close'.format(
                date=formatdate(timeval=mktime(datetime.now().timetuple()), localtime=False, usegmt=True),
                allowed_methods=','.join(allowed_methods.keys())
            )

    @lru_cache(20)
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

            response_header = self.build_header(self.statuses['OK'], len(content), content_type)
        else:
            error404 = 'Not Found'
            content_type = 'text/html; charset=utf-8'
            response_header = self.build_header(self.statuses['NotFound'], len(error404), content_type)

        response = "\n".join(response_header) + "\n\n" + content

        return response

    @lru_cache(20)
    def head_response(self, path):
        new_path = self.translate_url(path)
        file_ext = os.path.splitext(new_path)[1]

        if os.path.isfile(new_path) and file_ext in self.allowed_extensions:
            new_path = urllib.pathname2url(new_path)
            mime = mimetypes.guess_type(new_path)[0]

            response_header = self.build_header(self.statuses['OK'], os.path.getsize(new_path), mime)
        else:
            error404 = 'Not Found'
            content_type = 'text/html; charset=utf-8'
            response_header = self.build_header(self.statuses['NotFound'], len(error404), content_type)

        response = "\n".join(response_header)
        return response

    def translate_url(self, url, index_file='index.html'):
        url = urllib.unquote(url).decode('utf8')

        url = url.lstrip('/')

        if url.endswith('/'):
            url += index_file

        return os.path.join(self.params['DOCUMENT_ROOT'], url[1:])


def main(arguments):
    request_params = {
        'DOCUMENT_ROOT': arguments.root
    }

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Разрешаем выполнять bind() даже в случае, если другая программа недавно слушала тот же порт
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    server_socket.bind(('', arguments.port))
    server_socket.setblocking(0)
    server_socket.listen(1)

    print 'Server started...'

    inputs = {server_socket}
    output_query = {}
    excepts = []

    while True:
        input_ready, output_ready, except_ready = select.select(list(inputs), output_query.keys(), excepts, 0.5)

        for s in input_ready:
            if s == server_socket:
                client_socket, remote_address = server_socket.accept()
                client_socket.setblocking(0)
                inputs.add(client_socket)
            else:
                request = s.recv(1024)
                print '{} : {}'.format(s.getpeername(), request)
                output_query[s] = HTTPRequest(request, request_params).response()
                inputs.remove(s)

        for s in output_ready:
            if s in output_query:
                s.send(output_query[s])
                del output_query[s]
                s.close()


if __name__ == '__main__':
    args = parse_args()
    main(args)
