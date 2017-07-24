#!/usr/bin/env python
# -*- coding: utf-8 -*-
import bz2
import datetime
import gzip
import json
import os
import re
import sys
from collections import defaultdict

# log_format ui_short '$remote_addr $remote_user $http_x_real_ip [$time_local] "$request" '
#                     '$status $body_bytes_sent "$http_referer" '
#                     '"$http_user_agent" "$http_x_forwarded_for" "$http_X_REQUEST_ID" "$http_X_RB_USER" '
#                     '$request_time';


config = {
    "REPORT_SIZE": 1000,
    "REPORT_DIR": "./reports",
    "LOG_DIR": "./log"
}

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

log_format = 'remote_addr remote_user http_x_real_ip time_local request status body_bytes_sent http_referer ' \
             'http_user_agent http_x_forwarded_for http_X_REQUEST_ID http_X_RB_USER request_time'.split()


class LogAnalyzerException(Exception):
    pass


def html_report(report_data, report_template, report_result):
    with open(report_template) as rt:
        t_data = rt.read()
        t_data = t_data.replace('$table_json', report_data)

    with open(report_result, 'w') as rr:
        rr.write(t_data)


def get_last_log(path):
    file_regexp = re.compile('(?P<year>\d{4})(?P<month>\d{2})(?P<day>\d{2})')
    log_files = {fname: file_regexp.search(fname).groups()
                 for fname in os.listdir(path)}

    sorted_list = sorted(log_files,
                         key=lambda fname: datetime.date(*map(int, log_files[fname])).timetuple(),
                         reverse=True)

    return (
        os.path.join(config['LOG_DIR'], sorted_list[0]),
        log_files[sorted_list[0]]
    )


def get_log_opener(file_path):
    _, ext = os.path.splitext(file_path)
    ext_map = {
        '.gz': gzip.open,
        '.bz2': bz2.BZ2File
    }

    return ext_map.get(ext, open)


def get_results(report_data, req_count, req_time):
    results_list = []

    for url, time_list in report_data:
        l = len(time_list)
        s = sum(time_list)
        stl = sorted(time_list)
        mediana = stl[l / 2] if l % 2 else (stl[l / 2] + stl[l / 2 - 1]) / 2.0

        results_list.append(dict(
            url=url,
            count=l,
            count_perc=round((l / float(req_count)) * 100, 3),
            time_avg=round(s / l, 3),
            time_max=round(max(time_list), 3),
            time_med=round(mediana, 3),
            time_perc=round(s / req_time * 100, 3),
            time_sum=round(s, 3)
        ))

    return results_list


def main():
    last_log, log_date = get_last_log(config['LOG_DIR'])
    report_filename = os.path.join(config['REPORT_DIR'], "report-{}.{}.{}.html".format(*log_date))

    if os.path.isfile(report_filename):
        print "report {} already generated".format(report_filename)
        sys.exit(0)

    log_opener = get_log_opener(last_log)

    try:
        with log_opener(last_log) as f:
            regexp_str = r"^" + r"\s+".join([regexp_dict[rx] for rx in log_format]) + r"$"
            regexp_c = re.compile(regexp_str)

            all_results_dict = defaultdict(list)
            requests_count, requests_time = 0, 0

            for line in f:
                parse_result = regexp_c.search(line).groupdict()

                if parse_result['request'].count(" ") > 1:
                    _, url, _ = parse_result['request'].split()
                else:
                    url = parse_result['request']

                all_results_dict[url].append(float(parse_result['request_time']))

                requests_count += 1
                requests_time += float(parse_result['request_time'])
    except IOError:
        raise LogAnalyzerException("Not supported file format!")

    sorted_list = sorted(all_results_dict.iteritems(), key=lambda (k, v): sum(v), reverse=True)
    del all_results_dict

    results_list = get_results(
        sorted_list[:config['REPORT_SIZE']],
        requests_count,
        requests_time
    )

    json_data = json.dumps(results_list)
    html_report(json_data, "report.html", report_filename)
    print "report {} generated".format(report_filename)


if __name__ == "__main__":
    main()
