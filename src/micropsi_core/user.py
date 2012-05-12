"""
Very simple user management for the MicroPsi service

Agents are created and deleted by individual users. The agents of multiple users may share a common world.
Users have different roles that determine whether they may manage worlds and create/edit agents.

The user 'admin' may administer other users
"""
import shelve

__author__ = 'joscha'
__date__ = '11.05.12'

from hashlib import md5
from uuid import UUID
from os import urandom
from datetime import datetime, timedelta
from threading import Timer

ADMIN_USER = "admin"  # name of the admin user
USER_FILE = "user-data"  # resource files for all normal users
DEFAULT_ROLE = "Agent Creator"  # new users can create and edit agents, but not create worlds
IDLE_TIME_BEFORE_SESSION_EXPIRES = 360000  # after 100h idle time, expire the user session (but not the simulation)
TIME_INTERVAL_BETWEEN_EXPIRATION_CHECKS = 3600  # check every hour if we should log out users

USER_ROLES = {
    "Administrator": {
        "manage users": True,
        "manage worlds": True,
        "manage agents": True
    },
    "World Creator": {
        "manage users": False,
        "manage worlds": True,
        "manage agents": True
    },
    "Agent Creator": {
        "manage users": False,
        "manage worlds": False,
        "manage agents": True
    },
    "Guest": {
        "manage users": False,
        "manage worlds": False,
        "manage agents": False
    }
}

class UserManager(object):
    """The user manager creates, deletes and authenticates users.

    It must be a singleton, because all user managers would use the same resources for maintaining persistence.

    Attributes:
    """

    _shared_state = {}
    users = None
    sessions = {}
    timer = None

    # Borg pattern
    def __new__(cls):
        """share the state of this object with all objects of the same class"""
        self = object.__new__(cls)
        self.__dict__ = cls._shared_state
        return self

    def __init__(self):
        """initialize user management.

        If no user data are found, a new resource file is created.
        If you loose your admin password, you may delete the admin data from the resource file, so a new admin without
        password is created.
        """
        # set up persistence
        if not self.users:
            self.users = shelve.open(USER_FILE)

        # create admin user
        if not ADMIN_USER in self.users:
            self.users[ADMIN_USER] = {
                "hashed_password": None,
                "role": "Administrator",
                "session_token": "1"
            }

        # set up sessions
        for i in self.users:
            active_session = self.users[i]["session_token"]
            if active_session: self.sessions[active_session] = i

        self.timed_check_for_expired_user_sessions()

    def __del__(self):
        """shut down user management"""
        self.users.close()
        if self.timer: self.timer.cancel()

    def create_user(self, user_id, password, role = DEFAULT_ROLE):
        """create a new user.

        Returns False if the creation was not successful.

        Arguments:
            user_id: a non-empty string which must be unique
            password: an arbitrary string
            role: a string corresponding to a user role (such as "Administrator", or "Agent Creator")
        """
        if user_id and not user_id in self.users:
            self.users[user_id] = {
                "hashed_password": md5(password),
                "role": role,
                "session_token": None
            }
            return True
        else: return False

    def list_users(self):
        """returns a dictionary with all users currently known to the user manager"""
        return { self.users[self.user_index[i]]: {
            "role":self.users[self.user_index[i]]["role"],
            "index":i} for i in self.user_index }

    def set_user_id(self, user_id_old, user_id_new):
        """returns the new username if the user has been renamed successfully, the old username if the new one was
        already in use, and None if the old username did not exist"""
        if user_id_old in self.users:
            if not user_id_new in self.users:
                self.users[user_id_new] = self.users[user_id_old]
                del self.users[user_id_old]
                return user_id_new
            else:
                return user_id_old
        return None

    def set_user_role(self, user_id, role):
        """sets the role, and thereby the permissions of a user, returns False if user does not exist"""
        if user_id in self.users:
            self.users[user_id]["role"] = role
            return True
        return False

    def set_user_password(self, user_id, password):
        """sets the password of a user, returns False if user does not exist"""
        if user_id in self.users:
            self.users[user_id]["hashed_password"] = md5(password)
            return True
        return False

    def delete_user(self, user_id):
        """deletes the specified user, returns True if successful"""
        if user_id in self.users:
            self.end_session(user_id)
            del self.users[user_id]
            return True
        return False

    def start_session(self, user_id, password=None, keep_logged_in_forever=True):
        """authenticates the specified user, returns session token if successful, or None if not.

        Arguments:
            user_id: a string that must be the id of an existing user
            password (optional): checked against the stored password; ignored if no password is stored
            keep_logged_in_forever (optional): if True, the session will not expire unless manually logging off
        """

        if self.users[user_id]:
            if not self.users["hashed_password"] or self.users["hashed_password"] == md5(password):
                session_token = UUID(urandom(16))
                self.users[user_id]["session_token"] = session_token
                self.sessions[session_token] = user_id
                if keep_logged_in_forever:
                    self.users[user_id]["session_expires"] = False
                else:
                    self.refresh_session(session_token)
                return session_token
        return None

    def end_session(self, session_token):
        """ends the session associated with the given token"""
        if self.sessions[session_token]:
            user_id = self.sessions[session_token]
            del self.sessions[session_token]
            if self.users[user_id]:
                self.users[user_id]["session_token"] = None

    def end_all_sessions(self):
        """useful during a reset of the runtime, because all open user sessions will persist during shutdown"""
        for session_token in self.sessions: self.end_session(session_token)

    def refresh_session(self, session_token):
        """resets the idle time until a currently active session expires to some point in the future"""
        if self.sessions[session_token]:
            user_id = self.sessions[session_token]
            if self.users[user_id]["session_expires"]:
                self.users[user_id]["session_expires"] = datetime.now() + timedelta(
                    seconds=IDLE_TIME_BEFORE_SESSION_EXPIRES)

    def check_for_expired_user_sessions(self):
        """removes all user sessions that have been idle for too long"""

        for session_token in self.sessions:
            user_id = self.sessions[session_token]
            if self.users[user_id]["session_expires"]:
                if self.users[user_id]["session_expires"] < datetime.now():
                    self.end_session(session_token)

    def timed_check_for_expired_user_sessions(self):
        """callback for a timer function that checks if idling users should be logged off"""
        self.check_for_expired_user_sessions()
        self.timer = Timer(TIME_INTERVAL_BETWEEN_EXPIRATION_CHECKS, self.timed_check_for_expired_user_sessions())
        self.timer.start()

    def get_permissions(self, session_token):
        """returns a permission object corresponding to the role of the user associated with the session;
        if no session with that token exists, the Guest role permissions are returned"""

        if session_token in self.sessions:
            user_id = self.sessions[session_token]
            if user_id in self.users:
                role = self.users[user_id]["role"]
                if role in USER_ROLES:
                    return USER_ROLES[role]

        return USER_ROLES["Guest"]