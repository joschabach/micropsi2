"""
Very simple user management for the MicroPsi service

The user manager takes care of users, sessions and user roles.
Users without a password set can login with an arbitrary password, so make sure that users do not set empty passwords
if this concerns you.

When new users are created, they are given a role and stored along with their hashed password. Because we do not store
the password itself, it cannot be retrieved if it is lost. Instead, set a new password.

Users, including the admin user, must be logged in to receive a valid session token. The session token is valid until
the user logs off, or until it expires. To prevent expiration, it may be refreshed during each user interaction.

To check the permissions of a given user, you may use get_permissions_for_session_token. In return, the user manager
will return the rights matrix of the associated user, if the user is logged in, or the rights of a guest it the session
token does not correspond to an open session.

At the moment, persistence is achieved with a simple file, into which user and session data is dumped in json format.

Example usage:

>>> um = UserManager()
>>> um.create_user("eliza", "qwerty", "World Creator")  # new user "eliza" with password "querty" as "World Creator"
>>> print um.list_users["eliza"]
{'is_active': False, 'role': 'World Creator'}
>>> elizas_token = um.start_session("eliza", "querty")  # log in eliza (give this token to her)
>>> print um.list_users["eliza"]
{'is_active': True, 'role': 'World Creator'}
>>> print um.get_permissions(elizas_token)
set(['manage worlds', 'manage nodenets'])
>>> um.set_user_role('eliza', 'Administrator')
>>> print um.get_permissions(elizas_token)
Set(['manage users', 'manage worlds', 'manage nodenets'])
>>> um.end_session(elizas_token)  # log off eliza
>>> print um.get_permissions(elizas_token)
{}
"""

__author__ = 'joscha'
__date__ = '11.05.12'

import json
import hashlib
import os
import datetime
import threading
import time
import uuid
import logging
import micropsi_core.tools
from configuration import config as cfg

ADMIN_USER = "admin"  # default name of the admin user
DEFAULT_ROLE = "Restricted"  # new users can create and edit nodenets, but not create worlds
IDLE_TIME_BEFORE_SESSION_EXPIRES = 360000  # after 100h idle time, expire the user session (but not the calculation)
TIME_INTERVAL_BETWEEN_EXPIRATION_CHECKS = 3600  # check every hour if we should log out users

USER_ROLES = {  # sets of strings; each represents a permission.
    "Administrator": {"manage users","manage worlds","manage nodenets", "manage server",
                      "create admin", "create restricted", "create full"},
    "Full": {"manage worlds","manage nodenets", "manage server", "create full", "create restricted"},
    "Restricted": {"manage nodenets", "create restricted"},
    "Guest": {"create restricted"}
}


class UserManager(object):
    """The user manager creates, deletes and authenticates users.

    It should be a singleton, because all user managers would use the same resources for maintaining persistence.

    Attributes:
        users: a dictionary of user_ids to user objects (containing session tokens, access role and hashed passwords)
        sessions: a dictionary of active sessions for faster reference
        user_file: the handle for the user data file
    """

    def __init__(self, userfile_path=None):
        """initialize user management.

        If no user data are found, a new resource file is created.

        Parameters:
            resource_path (optional): a path to store user data permanently.
        """
        self.users = None
        self.sessions = {}

        # set up persistence
        if userfile_path is None:
            userfile_path = cfg['paths']['usermanager_path']

        dirpath = os.path.dirname(userfile_path)
        if not os.path.isdir(dirpath):
            os.makedirs(dirpath, exist_ok=True)

        self.user_file_name = userfile_path  # todo: make this work without a file system
        try:
            with open(self.user_file_name, encoding="utf-8") as file:
                self.users = json.load(file)
        except ValueError:
            logging.getLogger('system').warning("Invalid user data")
        except IOError:
            logging.getLogger('system').info("No readable userdata file, attempting to create one.")

        if not self.users:
            self.users = {}
            self.create_user('admin', role="Administrator")

        # set up sessions
        for name in self.users:

            # compatibility for files before multi-session-feature
            if "session_token" in self.users[name] and "sessions" not in self.users[name]:
                self.users[name]["sessions"] = {
                    self.users[name]["session_token"]: {"expires": self.users[name]["session_expires"]}
                }

            for token in self.users[name]["sessions"]:
                self.sessions[token] = name

        # set up session cleanup
        def _session_expiration():
            while True:
                self.check_for_expired_user_sessions()
                time.sleep(TIME_INTERVAL_BETWEEN_EXPIRATION_CHECKS)

        session_expiration_daemon = threading.Thread(target=_session_expiration)
        session_expiration_daemon.daemon = True
        session_expiration_daemon.start()

    def __del__(self):
        """shut down user management"""
        self.save_users()

    def create_user(self, user_id, password="", role = DEFAULT_ROLE, uid = None):
        """create a new user.

        Returns False if the creation was not successful.

        Arguments:
            user_id: a non-empty string which must be unique, used for display and urls
            password: an arbitrary string
            role: a string corresponding to a user role (such as "Administrator", or "Restricted")
            uid: a string that acts as a unique, immutable handle (so we can store resources for this user)
        """
        if user_id and user_id not in self.users:
            self.users[user_id] = {
                "uid": uid or user_id,
                "hashed_password": hashlib.md5(password.encode('utf-8')).hexdigest(),
                "role": role,
                "sessions": {}
            }
            self.save_users()
            return True
        else:
            return False

    def save_users(self):
        """stores the user data to a file"""
        with open(self.user_file_name, mode='w+', encoding="utf-8") as file:
            json.dump(self.users, file, indent=4)

    def list_users(self):
        """returns a dictionary with all users currently known to the user manager for display purposes"""
        return dict((name, {
            "role": self.users[name]["role"],
            "is_active": True if self.users[name]["sessions"] else False})
            for name in self.users)

    def set_user_id(self, user_id_old, user_id_new):
        """returns the new username if the user has been renamed successfully, the old username if the new one was
        already in use, and None if the old username did not exist"""
        if user_id_old in self.users:
            if user_id_new not in self.users:
                self.users[user_id_new] = self.users[user_id_old]
                del self.users[user_id_old]
                self.save_users()
                return user_id_new
            else:
                return user_id_old
        return None

    def set_user_role(self, user_id, role):
        """sets the role, and thereby the permissions of a user, returns False if user does not exist"""
        if user_id in self.users:
            self.users[user_id]["role"] = role
            self.save_users()
            return True
        return False

    def set_user_password(self, user_id, password):
        """sets the password of a user, returns False if user does not exist"""
        if user_id in self.users:
            self.users[user_id]["hashed_password"] = hashlib.md5(password.encode('utf-8')).hexdigest()
            self.save_users()
            return True
        return False

    def delete_user(self, user_id):
        """deletes the specified user, returns True if successful"""
        if user_id in self.users:
            # if the user is still active, kill the session
            for token in list(self.users[user_id]["sessions"].keys()):
                self.end_session(token)
            del self.users[user_id]
            self.save_users()
            return True
        return False

    def start_session(self, user_id, password=None, keep_logged_in_forever=True):
        """authenticates the specified user, returns session token if successful, or None if not.

        Arguments:
            user_id: a string that must be the id of an existing user
            password (optional): checked against the stored password
            keep_logged_in_forever (optional): if True, the session will not expire unless manually logging off
        """
        if password is None or self.test_password(user_id, password):
            session_token = str(uuid.UUID(bytes=os.urandom(16)))
            self.users[user_id]["sessions"][session_token] = {
                "expires": not keep_logged_in_forever
            }
            self.sessions[session_token] = user_id
            if keep_logged_in_forever:
                self.save_users()
            else:
                self.refresh_session(session_token)
            return session_token
        return None

    def switch_user_for_session_token(self, user_id, session_token):
        """Ends the current session associated with the token, starts a new session for the supplied user,
        and associates the same token to it. Used for allowing admins to take on the identity of a user, so they
        can edit resources with the user credentials.
        Returns True if successful, False if not.

        Arguments:
            user_id: a string that must be the id of an existing user
            token: a valid session token
        """
        if session_token in self.sessions and user_id in self.users:
            current_user = self.sessions[session_token]
            if current_user in self.users:
                session = self.users[current_user]["sessions"][session_token]
                del self.users[current_user]["sessions"][session_token]
                self.users[user_id]["sessions"].update({
                    session_token: session
                })
                self.sessions[session_token] = user_id
                self.refresh_session(session_token)
                self.save_users()
            return True
        return False

    def test_password(self, user_id, password):
        """returns True if the user is known and the password matches, False otherwise"""
        if user_id in self.users:
            if self.users[user_id]["hashed_password"] == hashlib.md5(password.encode('utf-8')).hexdigest():
                return True
        return False

    def end_session(self, session_token):
        """ends the session associated with the given token"""
        if session_token in self.sessions:
            user_id = self.sessions[session_token]
            del self.sessions[session_token]
            if user_id in self.users:
                del self.users[user_id]["sessions"][session_token]

    def end_all_sessions(self):
        """useful during a reset of the runtime, because all open user sessions will persist during shutdown"""
        sessions = self.sessions.copy()
        for session_token in sessions:
            self.end_session(session_token)

    def refresh_session(self, session_token):
        """resets the idle time until a currently active session expires to some point in the future"""
        if session_token in self.sessions:
            user_id = self.sessions[session_token]
            if self.users[user_id]["sessions"][session_token]["expires"]:
                self.users[user_id]["sessions"][session_token]["expires"] = (datetime.datetime.now() + datetime.timedelta(
                    seconds=IDLE_TIME_BEFORE_SESSION_EXPIRES)).isoformat()

    def check_for_expired_user_sessions(self):
        """removes all user sessions that have been idle for too long"""
        change_flag = False
        now = datetime.datetime.now().isoformat()
        sessions = self.sessions.copy()
        for session_token in sessions:
            user_id = self.sessions[session_token]
            expires = self.users[user_id]["sessions"][session_token]["expires"]
            if expires and expires < now:
                self.end_session(session_token)
                change_flag = True
        if change_flag:
            self.save_users()

    def get_permissions_for_session_token(self, session_token):
        """returns a set of permissions corresponding to the role of the user associated with the session;
        if no session with that token exists, the Guest role permissions are returned.

        Example usage:
            if "create nodenets" in usermanager.get_permissions(my_session): ...
        """
        if session_token in self.sessions:
            user_id = self.sessions[session_token]
            if user_id in self.users:
                role = self.users[user_id]["role"]
                if role in USER_ROLES:
                    return USER_ROLES[role]

        return USER_ROLES["Guest"]

    def get_user_id_for_session_token(self, session_token):
        """returns the id of the user associated with the session token, or 'Guest', if the token is invalid"""

        if session_token in self.sessions:
            return self.sessions[session_token]
        else:
            return "Guest"
