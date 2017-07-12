#!/usr/bin/env python
# -*- coding: utf-8 -*-
import gzip
import re
from argparse import ArgumentParser

# log_format ui_short '$remote_addr $remote_user $http_x_real_ip [$time_local] "$request" '
#                     '$status $body_bytes_sent "$http_referer" '
#                     '"$http_user_agent" "$http_x_forwarded_for" "$http_X_REQUEST_ID" "$http_X_RB_USER" '
#                     '$request_time';


# ^(?P<remote_addr>\d+\.\d+\.\d+\.\d+)\s+(?P<remote_user>[\S]+)\s+(?P<http_x_real_ip>[\S]+)\s+(?P<time_local>\[.+\])\s+"(?P<request>\w+\s+\S+\sHTTP/1.[0|1])"\s+(?P<status>\d{3})\s+(?P<body_bytes_sent>\d+)\s+"(?P<http_referer>\S+)"\s+"(?P<http_user_agent>[^"]+)"\s+"(?P<http_x_forwarded_for>[^"]+)"\s+"(?P<http_X_REQUEST_ID>[^"]+)"\s+"(?P<http_X_RB_USER>[^"]+)"\s+(?P<request_time>[\.\d]+)$

regexp_dict = {
    'remote_addr': r"(?P<remote_addr>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})",
    'remote_user': r'(?P<remote_user>[\S]+)',
    'http_x_real_ip': r'(?P<http_x_real_ip>[\S]+)',
    'time_local': r'\[(?P<time_local>.+)\]',
    'request': r'"(?P<request>.+)"',
    # 'request': r'"(?P<request>\w+\s+\S+\sHTTP/1.[0|1])"',
    'status': r'(?P<status>\d{3})',
    'body_bytes_sent': r'(?P<body_bytes_sent>\d+)',
    'http_referer': r'"(?P<http_referer>\S+)"',
    'http_user_agent': r'"(?P<http_user_agent>[^"]+)"',
    'http_x_forwarded_for': r'"(?P<http_x_forwarded_for>[^"]+)"',
    'http_X_REQUEST_ID': r'"(?P<http_X_REQUEST_ID>[^"]+)"',
    'http_X_RB_USER': r'"(?P<http_X_RB_USER>[^"]+)"',
    'request_time': r'(?P<request_time>[\.\d]+)'
}

config = {
    "REPORT_SIZE": 1000,
    "REPORT_DIR": "./reports",
    "LOG_DIR": "./log"
}

log_format = 'remote_addr remote_user http_x_real_ip time_local request status body_bytes_sent http_referer ' \
             'http_user_agent http_x_forwarded_for http_X_REQUEST_ID http_X_RB_USER request_time'.split()


def parse_args():
    p = ArgumentParser()
    p.description = "log file parser"
    p.add_argument("file", help="path to logfile")
    return p.parse_args()


def main():
    arguments = parse_args()
    regexp_str = r"^" + r"\s+".join([regexp_dict[rx] for rx in log_format]) + r"$"
    regexp_c = re.compile(regexp_str)
    result_dict = dict()
    requests_count, requests_time = 0, 0

    with gzip.open(arguments.file, 'rb') as f:
        for line in f:
            try:
                parse_result = regexp_c.search(line).groupdict()

                if parse_result['request'].count(" ") > 1:
                    _, url, _ = parse_result['request'].split()
                else:
                    url = parse_result['request']

                cur_time = float(parse_result['request_time'])

                url_rec = result_dict.get(url, [])
                url_rec.append(cur_time)
                result_dict[url] = url_rec
            except Exception as e:
                print e
                print line

            requests_count += 1
            requests_time += cur_time

    sorted_list = sorted(result_dict.iteritems(), key=lambda (k, v): len(v), reverse=True)

    for url, time_list in sorted_list[:config['REPORT_SIZE']]:
        l = len(time_list)
        s = sum(time_list)
        stl = sorted(time_list)
        mediana = stl[l / 2] if l % 2 else (stl[l / 2] + stl[l / 2 - 1]) / 2.0
        print "%s count=%d, time_sum=%s, time_max=%s, time_min=%s, time_avg=%s, time_med=%s" % (
            url, l, s, max(time_list), min(time_list), round(s / l, 3), mediana)

        # result_dict = {rec: result_dict[rec] for rec in s[:config['REPORT_SIZE']]}

        # pprint(result_dict)
    print requests_count, requests_time


if __name__ == "__main__":
    main()
