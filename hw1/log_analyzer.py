#!/usr/bin/env python
# -*- coding: utf-8 -*-
import gzip
import json
import re
from argparse import ArgumentParser

# log_format ui_short '$remote_addr $remote_user $http_x_real_ip [$time_local] "$request" '
#                     '$status $body_bytes_sent "$http_referer" '
#                     '"$http_user_agent" "$http_x_forwarded_for" "$http_X_REQUEST_ID" "$http_X_RB_USER" '
#                     '$request_time';


regexp_dict = {
    'remote_addr': r"(?P<remote_addr>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})",
    'remote_user': r'(?P<remote_user>[\S]+)',
    'http_x_real_ip': r'(?P<http_x_real_ip>[\S]+)',
    'time_local': r'\[(?P<time_local>.+)\]',
    'request': r'"(?P<request>.+)"',
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


def html_report(report_template, report_result):
    def factory(fn):
        def wrapper(*args, **kwargs):
            func_result = fn(*args, **kwargs)
            with open(report_template) as rt:
                t_data = rt.read()
                t_data = t_data.replace('$table_json', json.dumps(func_result))
                with open(report_result, 'w') as rr:
                    rr.write(t_data)

            return func_result

        return wrapper

    return factory


@html_report("report.html", "report-2017.06.30.html")
def main():
    arguments = parse_args()
    regexp_str = r"^" + r"\s+".join([regexp_dict[rx] for rx in log_format]) + r"$"
    regexp_c = re.compile(regexp_str)
    all_results_dict = dict()
    requests_count, requests_time = 0, 0

    with gzip.open(arguments.file, 'rb') as f:
        for line in f:
            parse_result = regexp_c.search(line).groupdict()

            if parse_result['request'].count(" ") > 1:
                _, url, _ = parse_result['request'].split()
            else:
                url = parse_result['request']

            url_rec = all_results_dict.get(url, [])
            url_rec.append(float(parse_result['request_time']))
            all_results_dict[url] = url_rec

            requests_count += 1
            requests_time += float(parse_result['request_time'])

    sorted_list = sorted(all_results_dict.iteritems(), key=lambda (k, v): len(v), reverse=True)

    results_list = []

    for url, time_list in sorted_list[:config['REPORT_SIZE']]:
        l = len(time_list)
        s = sum(time_list)
        stl = sorted(time_list)
        mediana = stl[l / 2] if l % 2 else (stl[l / 2] + stl[l / 2 - 1]) / 2.0

        results_list.append(dict(
            url=url,
            count=l,
            count_perc=round((l / float(requests_count)) * 100, 3),
            time_avg=round(s / l, 3),
            time_max=round(max(time_list), 3),
            time_med=round(mediana, 3),
            time_perc=round(s / requests_time * 100, 3),
            time_sum=round(s, 3)
        ))

    return results_list


if __name__ == "__main__":
    main()