#!/usr/bin/env python
# -*- coding: utf-8 -*-
import gzip
from argparse import ArgumentParser

# log_format ui_short '$remote_addr $remote_user $http_x_real_ip [$time_local] "$request" '
#                     '$status $body_bytes_sent "$http_referer" '
#                     '"$http_user_agent" "$http_x_forwarded_for" "$http_X_REQUEST_ID" "$http_X_RB_USER" '
#                     '$request_time';


# ^(?P<remote_addr>\d+\.\d+\.\d+\.\d+)\s+(?P<remote_user>[\S]+)\s+(?P<http_x_real_ip>[\S]+)\s+(?P<time_local>\[.+\])
# 1.196.116.32 -  - [29/Jun/2017:03:50:22 +0300] "GET /api/v2/banner/25019354 HTTP/1.1" 200 927 "-" "Lynx/2.8.8dev.9 libwww-FM/2.14 SSL-MM/1.4.1 GNUTLS/2.10.5" "-" "1498697422-2190034393-4708-9752759" "dc7161be3" 0.390
regexp_dict = {
    'remote_addr': r"(?P<remote_addr>\d+\.\d+\.\d+\.\d+)",
    'remote_user': r'(?P<remote_user>[\S]+)',
    'http_x_real_ip': r'(?P<http_x_real_ip>[\S]+)',
    'time_local': r'(?P<time_local>\[.+\])',
    'request': r'',
    'status': r'',
    'body_bytes_sent': r'',
    'http_referer': r'',
    'http_user_agent': r'',
    'http_x_forwarded_for': r'',
    'http_X_REQUEST_ID': r'',
    'http_X_RB_USER': r'',
    'request_time': r''
}

config = {
    "REPORT_SIZE": 1000,
    "REPORT_DIR": "./reports",
    "LOG_DIR": "./log"
}


def parse_args():
    p = ArgumentParser()
    p.description = "log file parser"
    p.add_argument("file", help="path to logfile")
    return p.parse_args()


def main():
    arguments = parse_args()

    with gzip.open(arguments.file, 'rb') as f:
        for line in f:
            print line


if __name__ == "__main__":
    main()
