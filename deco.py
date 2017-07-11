#!/usr/bin/env python
# -*- coding: utf-8 -*-

from functools import update_wrapper


def disable():
    '''
    Disable a decorator by re-assigning the decorator's name
    to this function. For example, to turn off memoization:
    >>> memo = disable
    '''

    return


def decorator(original_func):
    '''
    Decorate a decorator so that it inherits the docstrings
    and stuff from the function it's decorating.
    '''

    def deco_factory(called_func):
        def decorator_wrapper(*args, **kwargs):
            # print "original func name: %s" % original_func.func_name
            # print "called   func name: %s" % called_func.func_name
            return called_func(*args, **kwargs)

        return update_wrapper(decorator_wrapper, original_func)

    return deco_factory


def countcalls(fn):
    '''Decorator that counts calls made to the function decorated.'''

    def countcalls_wrapper(*args, **kwargs):
        # print "in  countcalls() -> wrapper()"
        # print "\tfunc_name=%s()" % fn.func_name

        f = globals()[fn.func_name]
        f.calls += 1

        return fn(*args, **kwargs)

    fn.calls = 0
    return update_wrapper(countcalls_wrapper, fn)


def memo(fn):
    '''
    Memoize a function so that it caches all return values for
    faster future lookups.
    '''

    def memo_wrapper(*args, **kwargs):
        args_res = args + tuple(kwargs.viewitems())

        if not memo_wrapper.cache.get(args_res):
            func_res = fn(*args, **kwargs)
            memo_wrapper.cache[args_res] = func_res

        return memo_wrapper.cache[args_res]

    memo_wrapper.cache = dict()
    return update_wrapper(memo_wrapper, fn)


def n_ary():
    '''
    Given binary function f(x, y), return an n_ary function such
    that f(x, y, z) = f(x, f(y,z)), etc. Also allow f(x) = x.
    '''
    return


def trace():
    '''Trace calls made to function decorated.

    @trace("____")
    def fib(n):
        ....

    >>> fib(3)
     --> fib(3)
    ____ --> fib(2)
    ________ --> fib(1)
    ________ <-- fib(1) == 1
    ________ --> fib(0)
    ________ <-- fib(0) == 1
    ____ <-- fib(2) == 2
    ____ --> fib(1)
    ____ <-- fib(1) == 1
     <-- fib(3) == 3

    '''
    return


@memo
@countcalls
@n_ary
def foo(a, b):
    return a + b


@countcalls
@memo
@n_ary
def bar(a, b):
    return a * b


@countcalls
@trace("####")
@memo
def fib(n):
    return 1 if n <= 1 else fib(n - 1) + fib(n - 2)


def main():
    print foo(4, 3)
    print foo(4, 3, 2)
    print foo(4, 3)
    print "foo was called", foo.calls, "times"

    print bar(4, 3)
    print bar(4, 3, 2)
    print bar(4, 3, 2, 1)
    print "bar was called", bar.calls, "times"

    print fib.__doc__
    fib(3)
    print fib.calls, 'calls made'


if __name__ == '__main__':
    main()
