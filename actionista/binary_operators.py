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


def to_lower(obj):
    """ Produces a lower-cased representation of obj.
    If obj is a list or set, returns a list or set where `to_lower()`
    has been applied to all elements.

    If obj is a dict, returns a list or set where `to_lower()`
    has been applied to all keys and values.

    Else, return `str(obj).lower()`
    """
    if isinstance(obj, (set, list)):
        return type(obj)([to_lower(val) for val in obj])
    elif isinstance(obj, dict):
        return type(obj)([(to_lower(key), to_lower(val)) for key, val in obj.items()])
    else:
        return str(obj).lower()


def startswith(a, b):
    a = str(a)
    b = str(b)
    return a.startswith(b)


def istartswith(a, b):
    """ Case insensitive startswith. """
    a, b = to_lower(a), to_lower(b)
    return a.startswith(b)


def endswith(a, b):
    a = str(a)
    b = str(b)
    return a.endswith(b)


def iendswith(a, b):
    """ Case insensitive startswith. """
    a, b = to_lower(a), to_lower(b)
    return a.endswith(b)


def icontains(a, b):
    """ Case insensitive contains.
    Note that the order of operands is reversed between `contains` and `in_`:

        contains(a, b)  <=>   b in a

    """
    a, b = to_lower(a), to_lower(b)
    return contains(a, b)


def in_(a, b):
    """ Returns True if `a` contains `b`, i.e. `contains` but with args in reversed order.

    Note that the order of operands is reversed between `contains` and `in_`:

        contains(a, b)  <=>   b in a    <=> in_(b, a)

    OBS: Please make sure this is really what you mean to use!
    The general format of the `-filter` action is:
        `-filter <key> <op> <value>`,
    e.g.
        `-filter content in "task1_content task2_content".
    """
    return a in b


def iin(a, b):
    """ Returns True if `a.lower()` contains `b.lower()`, i.e. `contains` but with args in reversed order."""
    a, b = to_lower(a), to_lower(b)
    return a in b


def ieq(a, b):
    """ Case insensitive equality. """
    a, b = to_lower(a), to_lower(b)
    return a == b


def ine(a, b):
    """ Case insensitive in-equality. """
    a, b = to_lower(a), to_lower(b)
    return a != b


def ilt(a, b):
    """ Case insensitive less-than. """
    a, b = to_lower(a), to_lower(b)
    return a < b


def igt(a, b):
    """ Case insensitive greater-than. """
    a, b = to_lower(a), to_lower(b)
    return a > b


def ige(a, b):
    """ Case insensitive greater-than-or-equal-to. """
    a, b = to_lower(a), to_lower(b)
    return a > b


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
    a, b = to_lower(a), to_lower(b)
    return _match(b, a)


def ifnmatch(a, b):
    """ Case insensitive glob-style matching. """
    a, b = to_lower(a), to_lower(b)
    return fnmatchcase(a, b)


iglob = ifnmatch
