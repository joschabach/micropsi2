#!/usr/local/bin/python
# -*- coding: utf-8 -*-

"""
MicroPsi runtime component;
maintains a set of users, worlds (up to one per user), and agents, and provides an interface to external clients
"""

__author__ = 'joscha'
__date__ = '10.05.12'

# import nodenet
import world
import user

class MicroPsiRuntime(object):
    """The central component of the MicroPsi installation.

    The runtime instantiates a user manager, an agent manager and a world manager and coordinates the interaction
    between them. It must be a singleton, otherwise competing instances might conflict over the resource files.
    """

    # Borg pattern: runtime should be a singleton
    _shared_resources = {}

    def __new__(cls, *args, **kwargs):
        self = object.__new__(cls, *args, **kwargs)
        self.__dict__ = cls._shared_resources
        return self

    def __init__(self):
        self.usermanager = user.UserManager()

        # temporary test code
        print "user manager started"
        um = self.usermanager
        print um.list_users()
        um.create_user("tom", "test")
        print um.list_users()
        um.create_user("britta", "pwd", "World Creator")
        print um.list_users()
        stom = um.start_session("tom")
        print stom
        stom1 = um.start_session("tom", "task")
        print stom1
        print um.list_users()
        stom = um.start_session("tom", "test")
        #um.delete_user("tom")
        print um.list_users()
        print stom
        print um.list_users()
        print um.get_permissions_for_session_token(stom1)
        print um.get_permissions_for_session_token(stom)
        um.end_session(stom)
        print um.list_users()
        print um.get_permissions_for_session_token(stom)
        #um.delete_user("tom")
        print um.list_users()






def main():
    run = MicroPsiRuntime()

if __name__ == '__main__':
    main()
