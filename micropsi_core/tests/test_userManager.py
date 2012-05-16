"""
Test case for user creation
"""
import hashlib
from unittest import TestCase
import src.micropsi_core.user

__author__ = 'joscha'
__date__ = '13.05.12'

class TestUserManager(TestCase):

    um = src.micropsi_core.user.UserManager()

    def test_create_user(self):
        self.um.create_user("test user without password and role")
        self.um.create_user("test user 2", "pwd", "World Creator")
        self.assertIn("admin", self.um.users)
        self.assertIn("test user without password and role", self.um.users)
        self.assertIn("test user 2", self.um.users)
        self.assertEqual(self.um.users["admin"]["role"], "Administrator")
        self.assertEqual(self.um.users["test user without password and role"]["hashed_password"], hashlib.md5("").hexdigest())
        self.assertEqual(self.um.users["test user without password and role"]["role"], src.micropsi_core.user.DEFAULT_ROLE)
        self.assertEqual(self.um.users["test user 2"]["hashed_password"], hashlib.md5("pwd").hexdigest())
        self.assertEqual(self.um.users["test user 2"]["role"], "World Creator")

    def test_set_user_id(self):
        self.assertNotIn("test user 1", self.um.users)
        self.assertIn("test user without password and role", self.um.users)
        success = self.um.set_user_id("test user without password and role", "admin")
        self.assertIn("test user without password and role", self.um.users)
        self.assertEqual(success, "test user without password and role")
        success = self.um.set_user_id("test user without password and role", "test user 1")
        self.assertNotIn("test user without password and role", self.um.users)
        self.assertEqual(success, "test user 1")
        self.assertEqual(self.um.users["test user 1"]["hashed_password"], hashlib.md5("").hexdigest())

    def test_list_users(self):
        userlist = self.um.list_users()
        self.assertIn()
        self.fail()


    def test_set_user_role(self):
        self.fail()

    def test_set_user_password(self):
        self.fail()

    def test_delete_user(self):
        self.fail()

    def test_start_session(self):
        self.fail()

    def test_end_session(self):
        self.fail()

    def test_end_all_sessions(self):
        self.fail()

    def test_refresh_session(self):
        self.fail()

    def test_check_for_expired_user_sessions(self):
        self.fail()

    def test_get_permissions_for_session_token(self):
        self.fail()
