#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Нужно реализовать простое HTTP API сервиса скоринга. Шаблон уже есть в api.py, тесты в test.py.
# API необычно тем, что пользователи дергают методы POST запросами. Чтобы получить результат
# пользователь отправляет в POST запросе валидный JSON определенного формата на локейшн /method

# Структура json-запроса:

# {"account": "<имя компании партнера>", "login": "<имя пользователя>", "method": "<имя метода>",
#  "token": "<аутентификационный токен>", "arguments": {<словарь с аргументами вызываемого метода>}}

# account - строка, опционально, может быть пустым
# login - строка, обязательно, может быть пустым
# method - строка, обязательно, может быть пустым
# token - строка, обязательно, может быть пустым
# arguments - словарь (объект в терминах json), обязательно, может быть пустым

# Валидация:
# запрос валиден, если валидны все поля по отдельности

# Структура ответа:
# {"code": <числовой код>, "response": {<ответ вызываемого метода>}}
# {"code": <числовой код>, "error": {<сообщение об ошибке>}}

# Аутентификация:
# смотри check_auth в шаблоне. В случае если не пройдена, нужно возвращать
# {"code": 403, "error": "Forbidden"}

# Метод online_score.
# Аргументы:
# phone - строка или число, длиной 11, начинается с 7, опционально, может быть пустым
# email - строка, в которой есть @, опционально, может быть пустым
# first_name - строка, опционально, может быть пустым
# last_name - строка, опционально, может быть пустым
# birthday - дата в формате DD.MM.YYYY, с которой прошло не больше 70 лет, опционально, может быть пустым
# gender - число 0, 1 или 2, опционально, может быть пустым

# Валидация аругементов:
# аргументы валидны, если валидны все поля по отдельности и если присутсвует хоть одна пара
# phone-email, first name-last name, gender-birthday с непустыми значениями.

# Ответ:
# в ответ выдается произвольное число, которое больше или равно 0
# {"score": <число>}
# или если запрос пришел от валидного пользователя admin
# {"score": 42}
# или если произошла ошибка валидации
# {"code": 422, "error": "<сообщение о том какое поле невалидно>"}

# $ curl -X POST  -H "Content-Type: application/json" -d '{"account": "horns&hoofs", "login": "h&f", "method": "online_score", "token": "55cc9ce545bcd144300fe9efc28e65d415b923ebb6be1e19d2750a2c03e80dd209a27954dca045e5bb12418e7d89b6d718a9e35af34e14e1d5bcd5a08f21fc95", "arguments": {"phone": "79175002040", "email": "stupnikov@otus.ru", "first_name": "Стансилав", "last_name": "Ступников", "birthday": "01.01.1990", "gender": 1}}' http://127.0.0.1:8080/method/
# -> {"code": 200, "response": {"score": 5.0}}

# Метод clients_interests.
# Аргументы:
# client_ids - массив чисел, обязательно, не пустое
# date - дата в формате DD.MM.YYYY, опционально, может быть пустым

# Валидация аругементов:
# аргументы валидны, если валидны все поля по отдельности.

# Ответ:
# в ответ выдается словарь <id клиента>:<список интересов>. Список генерировать произвольно.
# {"client_id1": ["interest1", "interest2" ...], "client2": [...] ...}
# или если произошла ошибка валидации
# {"code": 422, "error": "<сообщение о том какое поле невалидно>"}

# $ curl -X POST  -H "Content-Type: application/json" -d '{"account": "horns&hoofs", "login": "admin", "method": "clients_interests", "token": "d3573aff1555cd67dccf21b95fe8c4dc8732f33fd4e32461b7fe6a71d83c947688515e36774c00fb630b039fe2223c991f045f13f24091386050205c324687a0", "arguments": {"client_ids": [1,2,3,4], "date": "20.07.2017"}}' http://127.0.0.1:8080/method/
# -> {"code": 200, "response": {"1": ["books", "hi-tech"], "2": ["pets", "tv"], "3": ["travel", "music"], "4": ["cinema", "geek"]}}

# Требование: в результате в git должно быть только два(2!) файлика: api.py, test.py.
# Deadline: следующее занятие

import datetime
import hashlib
import json
import logging
import uuid
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
from optparse import OptionParser
from pprint import pprint

SALT = "Otus"
ADMIN_LOGIN = "admin"
ADMIN_SALT = "42"
OK = 200
BAD_REQUEST = 400
FORBIDDEN = 403
NOT_FOUND = 404
INVALID_REQUEST = 422
INTERNAL_ERROR = 500
ERRORS = {
    BAD_REQUEST: "Bad Request",
    FORBIDDEN: "Forbidden",
    NOT_FOUND: "Not Found",
    INVALID_REQUEST: "Invalid Request",
    INTERNAL_ERROR: "Internal Server Error",
}
UNKNOWN = 0
MALE = 1
FEMALE = 2
GENDERS = {
    UNKNOWN: "unknown",
    MALE: "male",
    FEMALE: "female",
}


class Field(object):
    def __init__(self, requried, nullable):
        self.required = requried
        self.nullable = nullable
        self._value = None

    def is_valid(self):
        pass


class CharField(Field):
    def __init__(self, requried=True, nullable=True):
        super(CharField, self).__init__(requried, nullable)


class ArgumentsField(Field):
    def __init__(self, requried=True, nullable=True):
        super(ArgumentsField, self).__init__(requried, nullable)


class EmailField(CharField):
    """
    email - строка, в которой есть @, опционально, может быть пустым
    """

    def is_valid(self):
        return '@' in self._value


class PhoneField(Field):
    def __init__(self, requried=True, nullable=True):
        super(PhoneField, self).__init__(requried, nullable)

    @property
    def number(self):
        return self._value

    @number.setter
    def number(self, value):
        self._value = value

    def is_valid(self):
        """
         phone - строка или число, длиной 11, начинается с 7, опционально, может быть пустым
        """
        return len(self._value) and str(self._value).startswith('7')


class ApiDateException(Exception):
    pass


class DateField(Field):
    def __init__(self, requried=True, nullable=True):
        super(DateField, self).__init__(requried, nullable)

    @property
    def date(self):
        return self._value

    @date.setter
    def date(self, value):
        try:
            day, month, year = map(int, str(value).split('.'))
            self._value = datetime.datetime(year=year, month=month, day=day)
        except ValueError as e:
            raise ApiDateException('Wrong DateField value: %s' % e.args)


class BirthDayField(DateField):
    def is_valid(self):
        """
        birthday - дата в формате DD.MM.YYYY, с которой прошло не больше 70 лет, опционально, может быть пустым
        """
        return (datetime.datetime.now() - self.date) < datetime.datetime(year=70)


class GenderField(Field):
    def __init__(self, requried=True, nullable=True):
        super(GenderField, self).__init__(requried, nullable)

    def is_valid(self):
        """
        gender - число 0, 1 или 2, опционально, может быть пустым
        """
        return str(self._value).isdigit() and int(self._value) in xrange(0, 3)


class ClientIDsField(Field):
    def __init__(self, requried=True, nullable=True):
        super(ClientIDsField, self).__init__(requried, nullable)


class Request(object):
    def __init__(self, req_data):
        for name, value in req_data['body']['arguments'].iteritems():
            attr = getattr(self, name)
            attr._value = value
        self.login = req_data['body']['login']
        self.token = req_data['body']['token']
        self.token = req_data['body']['account']


class ClientsInterestsRequest(Request):
    client_ids = ClientIDsField(requried=True)
    date = DateField(requried=False, nullable=True)


class OnlineScoreRequest(Request):
    first_name = CharField(requried=False, nullable=True)
    last_name = CharField(requried=False, nullable=True)
    email = EmailField(requried=False, nullable=True)
    phone = PhoneField(requried=False, nullable=True)
    birthday = BirthDayField(requried=False, nullable=True)
    gender = GenderField(requried=False, nullable=True)


class MethodRequest(Request):
    account = CharField(requried=False, nullable=True)
    login = CharField(requried=True, nullable=True)
    token = CharField(requried=True, nullable=True)
    arguments = ArgumentsField(requried=True, nullable=True)
    method = CharField(requried=True, nullable=True)

    @property
    def is_admin(self):
        return self.login == ADMIN_LOGIN


def check_auth(request):
    if request.login == ADMIN_LOGIN:
        digest = hashlib.sha512(datetime.datetime.now().strftime("%Y%m%d%H") + ADMIN_SALT).hexdigest()
    else:
        digest = hashlib.sha512(request.account + request.login + SALT).hexdigest()
    if digest == request.token:
        return True
    return False


def method_handler(request, ctx):
    response, code = None, None
    pprint(request)

    req_types = {
        'online_score': OnlineScoreRequest,
    }

    try:
        method_name = request['body']['method']
        req_object = req_types[method_name](request)
        auth = check_auth(req_object)
    except Exception as e:
        # print e, e.args
        pass

    return response, code


class MainHTTPHandler(BaseHTTPRequestHandler):
    router = {
        "method": method_handler,
    }

    def get_request_id(self, headers):
        return headers.get('HTTP_X_REQUEST_ID', uuid.uuid4().hex)

    def do_POST(self):
        response, code = {}, OK
        context = {"request_id": self.get_request_id(self.headers)}
        request = None
        try:
            data_string = self.rfile.read(int(self.headers['Content-Length']))
            request = json.loads(data_string)
        except:
            code = BAD_REQUEST

        if request:
            path = self.path.strip("/")
            logging.info("%s: %s %s" % (self.path, data_string, context["request_id"]))
            if path in self.router:
                try:
                    response, code = self.router[path]({"body": request, "headers": self.headers}, context)
                except Exception as e:
                    logging.exception("Unexpected error: %s" % e)
                    code = INTERNAL_ERROR
            else:
                code = NOT_FOUND

        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        if code not in ERRORS:
            r = {"response": response, "code": code}
        else:
            r = {"error": response or ERRORS.get(code, "Unknown Error"), "code": code}
        context.update(r)
        logging.info(context)
        self.wfile.write(json.dumps(r))
        return


if __name__ == "__main__":
    op = OptionParser()
    op.add_option("-p", "--port", action="store", type=int, default=8080)
    op.add_option("-l", "--log", action="store", default=None)
    (opts, args) = op.parse_args()
    logging.basicConfig(filename=opts.log, level=logging.INFO,
                        format='[%(asctime)s] %(levelname).1s %(message)s', datefmt='%Y.%m.%d %H:%M:%S')
    server = HTTPServer(("localhost", opts.port), MainHTTPHandler)
    logging.info("Starting server at %s" % opts.port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    server.server_close()
