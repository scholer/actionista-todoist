# Copyright 2018 Rasmus Scholer Sorensen

"""

This is a module to create generic query/filter operators.

It is pretty basic, a query consists of expressions (currenly joined by AND).

Each expressions is of the form "value1 OPERATOR value2", e.g.
    string1 equals string2
    'abcdefg' startswith 'abc'  # True
    'abcdefg' contains 'cde' # True
    etc.


"""

from re import match as _match  # Wrong signature: re.match(pattern, string), I want "string re pattern"
from fnmatch import fnmatch, fnmatchcase

from operator import eq, ne, lt, le, gt, ge, mod, countOf, contains, indexOf, and_, or_, is_, is_not
# unary operators: not_, truth, is_not

# Aliases:
equals = equal = eq
neq = nequal = ne
less = lessthan = lt
greater = greaterthan = gt
modulus = mod
glob = fnmatchcase


def startswith(a, b):
    a = str(a)
    b = str(b)
    return a.startswith(b)


def istartswith(a, b):
    """ Case insensitive startswith. """
    a = str(a).lower()
    b = str(b).lower()
    return a.startswith(b)


def endswith(a, b):
    a = str(a)
    b = str(b)
    return a.endswith(b)


def iendswith(a, b):
    """ Case insensitive startswith. """
    a = str(a).lower()
    b = str(b).lower()
    return a.endswith(b)


def icontains(a, b):
    """ Case insensitive contains. """
    a = str(a).lower()
    b = str(b).lower()
    return contains(a, b)


def in_(a, b):
    """ Returns True if `a` contains `b`, i.e. `contains` but with args in reversed order."""
    return a in b


def iin(a, b):
    """ Returns True if `a.lower()` contains `b.lower()`, i.e. `contains` but with args in reversed order."""
    return str(a).lower() in str(b).lower()


def ieq(a, b):
    """ Case insensitive equality. """
    return a.lower() == b.lower()


def ine(a, b):
    """ Case insensitive in-equality. """
    return a.lower() != b.lower()


def ilt(a, b):
    """ Case insensitive less-than. """
    return a.lower() < b.lower()


def igt(a, b):
    """ Case insensitive greater-than. """
    return a.lower() > b.lower()


def ige(a, b):
    """ Case insensitive greater-than-or-equal-to. """
    return a.lower() > b.lower()


# def is_(a, b):
#     return a is b


def re(a, b):
    """ Returns True if `a` matches the regular expression given by `b`.
    Unfortunately, the call signature of re.match(pat, name) is different from the other binary operators,
    which are usually `a lt b  ==> lt(a, b) ==>  a < b`,
    Note that `fnmatchcase(name, pat)` follows the "correct" order.
    """
    return _match(b, a)


def ire(a, b):
    """ Returns True if `a.lower()` matches the regular expression given by `b.lower()`."""
    return _match(b.lower(), a.lower())


def ifnmatch(a, b):
    """ Case insensitive glob-style matching. """
    return fnmatchcase(a.lower(), b.lower())


iglob = ifnmatch


