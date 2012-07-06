#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Shared tool code
"""

__author__ = 'joscha'
__date__ = '29.06.12'

import uuid
import os

def generate_uid():
    """produce a unique identifier, restricted to an ASCII string"""
    return uuid.uuid1().hex

def mkdir(new_directory_name):
    """if the directory does not exist, create it; otherwise, exit quietly"""

    if os.path.isdir(new_directory_name):
        pass
    elif os.path.isfile(new_directory_name):
        raise OSError("a file with the same name as the desired directory, '%s', already exists." % new_directory_name)
    else:
        head, tail = os.path.split(new_directory_name)
        if head and not os.path.isdir(head):
            mkdir(head)
        if tail:
            os.mkdir(new_directory_name)

def check_for_url_proof_id(id, existing_ids = None, min_id_length = 1, max_id_length = 21):
    """Returns (True, id) if id is permissible, and (False, error message) otherwise. Since
    we strip the id, you should use the returned one, not the original one"""

    id = id.strip()

    # maybe this is too restrictive, but I want to use the id directly in urls
    for c in id:
        if not c.lower() in "0123456789abcdefghijklmnopqrstuvwxyz@._-":
            return False, "The character '%s' is not allowed" %c

    if existing_ids and id.lower() in existing_ids: return False, "ID already exists"
    if len(id) < min_id_length:
        return False, "Must at least have %s characters" % min_id_length
    if len(id) > max_id_length:
        return False, "Must have less than %s characters" % max_id_length

    return True, id