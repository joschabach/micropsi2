#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Shared tool code
"""

__author__ = 'joscha'
__date__ = '29.06.12'

import uuid
import errno
import os
import sys
try:
    import ipdb as pdb
except ImportError:
    import pdb


def post_mortem():
    """ if desired, point a debugger to the origin of the last exception """
    from micropsi_core.runtime import runtime_config
    if runtime_config['micropsi2'].get('on_exception') == 'debug':
        exception_type, exception, tb = sys.exc_info()
        print('\033[01m\033[31m%s: \033[32m%s\033[0m' % (exception_type.__name__, exception))
        pdb.post_mortem(tb)


def pid_exists(pid):
    """Check whether pid exists in the current process table.
    UNIX only. obtained from http://stackoverflow.com/a/6940314/5952582
    """
    if pid < 0:
        return False
    if pid == 0:
        # According to "man 2 kill" PID 0 refers to every process
        # in the process group of the calling process.
        # On certain systems 0 is a valid PID but we have no way
        # to know that in a portable fashion.
        raise ValueError('invalid PID 0')
    try:
        os.kill(pid, 0)
    except OSError as err:
        if err.errno == errno.ESRCH:
            # ESRCH == No such process
            return False
        elif err.errno == errno.EPERM:
            # EPERM clearly means there's a process to deny access to
            return True
        else:
            # According to "man 2 kill" possible error values are
            # (EINVAL, EPERM, ESRCH)
            raise
    else:
        return True


def generate_uid():
    """produce a unique identifier, restricted to an ASCII string"""
    return uuid.uuid1().hex


def check_for_url_proof_id(id, existing_ids=None, min_id_length=1, max_id_length=21):
    """Returns (True, id) if id is permissible, and (False, error message) otherwise. Since
    we strip the id, you should use the returned one, not the original one"""

    id = id.strip()

    # maybe this is too restrictive, but I want to use the id directly in urls
    for c in id:
        if not c.lower() in "0123456789abcdefghijklmnopqrstuvwxyz@._-":
            return False, "The character '%s' is not allowed" % c

    if existing_ids and id.lower() in existing_ids:
        return False, "ID already exists"
    if len(id) < min_id_length:
        return False, "Must at least have %s characters" % min_id_length
    if len(id) > max_id_length:
        return False, "Must have less than %s characters" % max_id_length

    return True, id


# Global parameters for all created functions

# symbols that are included by default in the generated function's environment
SAFE_SYMBOLS = ["list", "dict", "tuple", "set", "long", "float", "object", "bool", "callable", "True", "False", "dir",
                "frozenset", "getattr", "hasattr", "abs", "cmp", "complex", "divmod", "id", "pow", "round", "slice",
                "vars", "hash", "hex", "int", "isinstance", "issubclass", "len", "filter", "max", "min", "oct",
                "chr", "ord", "range", "repr", "str", "type", "zip", "xrange", "None",
                "Exception", "KeyboardInterrupt"]

# add standard exceptions
__bi = __builtins__
if type(__bi) is not dict:
    __bi = __bi.__dict__
for k in __bi:
    if k.endswith("Error") or k.endswith("Warning"):
        SAFE_SYMBOLS.append(k)
del __bi


def create_function(source_string, parameters="", additional_symbols=None):
    """Create a python function from the given source code.

    Arguments:
        source_string: A python string containing the source code of the function.
        parameters: A string with arguments that are passed to the function by the caller, ("a, b", or "a=12, b").
        additional_symbols: A dictionary of name : variable/function/object that are passed into the function

    If the users can edit the string, then creating functions on the fly is potentially harmful. To mitigate the risk
    somewhat, only a set of safe builtins is allowed (for instance, no file operations). Using additional_symbols,
    other modules, objects or functions can be imported into the function's namespace.

    To make the function stateful, you can pass mutable parameters or mutable additional symbols.
    In CPython, the created function should execute just as fast as a normal function.

    Example use:
        my_function_source = '''return usermanager.users[index]'''
        get_user = create_function(my_function_source, parameters="index = 0",
                                   additional_symbols = {'usermanager': usermanager})
        print get_user("klaus")

    (This function is inspired by a recipe by David Decotigny.)
    """

    # Include the sourcecode as the code of a function __my_function__:
    s = "def __my_function__(%s):\n" % parameters
    s += "\t" + "\n\t".join(source_string.split('\n')) + "\n"

    # Byte-compilation (optional)
    bytecode = compile(s, "<string>", 'exec')

    # Setup the local and global dictionaries of the execution
    # environment for __my_function__
    bis = dict()  # builtins
    globs = dict()
    locs = dict()

    # Setup a standard-compatible python environment
    bis["locals"] = lambda: locs
    bis["globals"] = lambda: globs
    globs["__builtins__"] = bis
    globs["__name__"] = "SUBENV"
    globs["__doc__"] = source_string

    # Determine how the __builtins__ dictionary should be accessed
    if type(__builtins__) is dict:
        bi_dict = __builtins__
    else:
        bi_dict = __builtins__.__dict__

    # Include the safe symbols
    for k in SAFE_SYMBOLS:
        # try from current locals
        try:
            locs[k] = locals()[k]
            continue
        except KeyError:
            pass
            # Try from globals
        try:
            globs[k] = globals()[k]
            continue
        except KeyError:
            pass
            # Try from builtins
        try:
            bis[k] = bi_dict[k]
        except KeyError:
            # Symbol not available anywhere: silently ignored
            pass

    # Include the symbols added by the caller, in the globals dictionary
    globs.update(additional_symbols or {})

    # Finally execute the def __my_function__ statement:
    eval(bytecode, globs, locs)
    # As a result, the function is defined as the item __my_function__
    # in the locals dictionary
    fct = locs["__my_function__"]
    # Attach the function to the globals so that it can be recursive
    del locs["__my_function__"]
    globs["__my_function__"] = fct
    # Attach the actual source code to the docstring
    fct.__doc__ = source_string
    return fct


class Bunch(dict):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
        for i in kwargs:
            self[i] = kwargs[i]


import collections


class OrderedSet(collections.OrderedDict, collections.MutableSet):

    def update(self, *args, **kwargs):
        if kwargs:
            raise TypeError("update() takes no keyword arguments")

        for s in args:
            for e in s:
                self.add(e)

    def add(self, elem):
        self[elem] = None

    def discard(self, elem):
        self.pop(elem, None)

    def __le__(self, other):
        return all(e in other for e in self)

    def __lt__(self, other):
        return self <= other and self != other

    def __ge__(self, other):
        return all(e in self for e in other)

    def __gt__(self, other):
        return self >= other and self != other

    def __repr__(self):
        return 'OrderedSet([%s])' % (', '.join(map(repr, self.keys())))

    def __str__(self):
        return '{%s}' % (', '.join(map(repr, self.keys())))

    difference = property(lambda self: self.__sub__)
    difference_update = property(lambda self: self.__isub__)
    intersection = property(lambda self: self.__and__)
    intersection_update = property(lambda self: self.__iand__)
    issubset = property(lambda self: self.__le__)
    issuperset = property(lambda self: self.__ge__)
    symmetric_difference = property(lambda self: self.__xor__)
    symmetric_difference_update = property(lambda self: self.__ixor__)
    union = property(lambda self: self.__or__)


def itersubclasses(cls, folder=None, _seen=None):
    """
    Generator over all subclasses of a given class, in depth first order.

    Example usage:
        for cls in itersubclasses(A):
            print(cls.__name__)
    """

    if not isinstance(cls, type):
        raise TypeError('itersubclasses must be called with new-style classes, not %.100r' % cls)
    if _seen is None:
        _seen = set()
    try:
        subs = cls.__subclasses__()
    except TypeError:  # fails only when cls is type
        subs = cls.__subclasses__(cls)
    for sub in subs:
        if sub not in _seen:
            if folder is None or sub.__module__.startswith(folder):
                _seen.add(sub)
                yield sub
            for sub in itersubclasses(sub, folder=folder, _seen=_seen):
                yield sub
