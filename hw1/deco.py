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
            return called_func(*args, **kwargs)

        return update_wrapper(decorator_wrapper, original_func)

    return deco_factory


def countcalls(fn):
    '''Decorator that counts calls made to the function decorated.'''

    def countcalls_wrapper(*args, **kwargs):
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
        args_res = args, tuple(kwargs.viewitems())

        if args_res not in cache:
            cache[args_res] = fn(*args, **kwargs)

        return cache[args_res]

    cache = dict()
    return update_wrapper(memo_wrapper, fn)


def n_ary(fn):
    '''
    Given binary function f(x, y), return an n_ary function such
    that f(x, y, z) = f(x, f(y,z)), etc. Also allow f(x) = x.
    '''

    def n_ary_wrapper(*args, **kwargs):
        largs = len(args)
        if largs == 2:
            return fn(*args, **kwargs)
        elif largs == 1:
            return fn(*(args[0], 0), **kwargs)
        elif largs > 2:
            first, other = args[0], args[1:]
            other_result = n_ary_wrapper(*other, **kwargs)
            return fn(*(first, other_result), **kwargs)

    return update_wrapper(n_ary_wrapper, fn)


def trace(pre_str):
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

    def pre_str_decorator(fn):
        pre_str_decorator.level = 0

        def wrapper(*args, **kwargs):
            prefix = pre_str * pre_str_decorator.level
            pre_str_decorator.level += 1
            print "%s --> %s(%d)" % (prefix, fn.func_name, args[0])

            result = fn(*args, **kwargs)
            pre_str_decorator.level -= 1
            prefix = pre_str * pre_str_decorator.level

            print "%s <-- %s(%d) == %d" % (prefix, fn.func_name, args[0], result)

            return result

        return update_wrapper(wrapper, fn)

    return pre_str_decorator


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
