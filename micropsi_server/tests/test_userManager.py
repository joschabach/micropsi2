#!/usr/local/bin/python
# -*- coding: utf-8 -*-

"""

"""
import datetime

__author__ = 'joscha'
__date__ = '29.10.12'

import os
import tempfile
import pytest
from micropsi_server import usermanagement

@pytest.fixture(scope="session")
def path():
    return os.path.join(tempfile.gettempdir(), "users.json")

@pytest.fixture(scope="session")
def user_mgr():
    return usermanagement.UserManager(path())

# user_mgr = usermanagement.UserManager()

def test_create_user(user_mgr):
    user_mgr.delete_user("eliza")
    assert "eliza" not in user_mgr.users
    user_mgr.create_user("eliza", "qwerty", "Full")
    assert "eliza" in user_mgr.users

def test_save_users(user_mgr):
    os.remove(path())
    assert not os.path.exists(path())
    user_mgr.save_users()
    assert os.path.exists(path())

def test_list_users(user_mgr):
    l = user_mgr.list_users()
    assert "eliza" in l
    assert l["eliza"]["is_active"] == False
    assert l["eliza"]["role"] == "Full"
    assert len(l) == len(user_mgr.users)

def test_set_user_id(user_mgr):
    assert "eliza" in user_mgr.users
    user_mgr.delete_user("tom")
    t = user_mgr.set_user_id("eliza", "tom")
    assert t == "tom"
    assert "eliza" not in user_mgr.users
    assert "tom" in user_mgr.users
    e = user_mgr.set_user_id("tom", "eliza")
    assert e == "eliza"
    assert "tom" not in user_mgr.users
    assert "grxxtrxx" not in user_mgr.users
    assert not user_mgr.set_user_id("grxxtrxx", "tom")
    assert "tom" not in user_mgr.users

def test_set_user_role(user_mgr):
    assert user_mgr.users["eliza"]["role"] == "Full"
    user_mgr.set_user_role("eliza", "Restricted")
    assert user_mgr.users["eliza"]["role"] == "Restricted"
    user_mgr.set_user_role("eliza", "Full")
    assert user_mgr.users["eliza"]["role"] == "Full"
    assert not user_mgr.set_user_role("grxxtrxx", "Full")

def test_set_user_password(user_mgr):
    pwd = user_mgr.users["eliza"]["hashed_password"]
    user_mgr.set_user_password("eliza", "abcd")
    assert not pwd == user_mgr.users["eliza"]["hashed_password"]
    user_mgr.set_user_password("eliza", "qwerty")
    assert pwd == user_mgr.users["eliza"]["hashed_password"]

def test_start_session(user_mgr):
    assert user_mgr.users["eliza"]["session_token"] is None
    assert user_mgr.start_session("eliza", password="wrong") is None
    assert user_mgr.users["eliza"]["session_token"] is None
    token = user_mgr.start_session("eliza", password="qwerty")
    assert token is not None
    assert token == user_mgr.users["eliza"]["session_token"]

def test_get_user_id_for_session_token(user_mgr):
    token = user_mgr.start_session("eliza")
    assert user_mgr.get_user_id_for_session_token(token) == "eliza"
    assert user_mgr.get_user_id_for_session_token("notoken") == "Guest"

def test_get_permissions_for_session_token(user_mgr):
    token = user_mgr.users["eliza"]["session_token"]
    perms = user_mgr.get_permissions_for_session_token(token)
    assert "manage server" in perms
    assert "manage users" not in perms
    user_mgr.set_user_role("eliza", "Guest")
    perms = user_mgr.get_permissions_for_session_token(token)
    assert "manage server" not in perms

def test_switch_user_for_session_token(user_mgr):
    token = user_mgr.users["eliza"]["session_token"]
    user_mgr.create_user("norbert", "abcd", "Full")
    user_mgr.switch_user_for_session_token("norbert", token)
    token1 = user_mgr.users["eliza"]["session_token"]
    token2 = user_mgr.users["norbert"]["session_token"]
    assert token1 is None
    assert token2 == token

def test_end_session(user_mgr):
    token = user_mgr.users["norbert"]["session_token"]
    assert token is not None
    user_mgr.end_session(token)
    assert user_mgr.users["norbert"]["session_token"] is None

def test_test_password(user_mgr):
    assert user_mgr.test_password("eliza", "qwerty")
    assert not user_mgr.test_password("eliza", "qwertz")

def test_end_all_sessions(user_mgr):
    user_mgr.start_session("eliza")
    user_mgr.start_session("norbert")
    assert user_mgr.users["eliza"]["session_token"] is not None
    assert user_mgr.users["norbert"]["session_token"] is not None
    user_mgr.end_all_sessions()
    assert user_mgr.users["eliza"]["session_token"] is None
    assert user_mgr.users["norbert"]["session_token"] is None

def test_delete_user(user_mgr):
    assert "norbert" in user_mgr.users
    user_mgr.delete_user("norbert")
    assert "norbert" not in user_mgr.users


def test_check_for_expired_user_sessions(user_mgr):
    t = datetime.datetime.now().time().isoformat()
    user_mgr.create_user("norbert", "abcd", "Full")
    user_mgr.start_session("norbert", keep_logged_in_forever=False)
    user_mgr.users["norbert"]["session_expires"] = repr(t)
    user_mgr.start_session("eliza", keep_logged_in_forever=True)
    assert user_mgr.users["eliza"]["session_expires"] is False
    user_mgr.check_for_expired_user_sessions()
    assert user_mgr.users["norbert"]["session_token"] is None
    assert user_mgr.users["eliza"]["session_token"] is not None


def test_refresh_session(user_mgr):
    t = datetime.datetime.now().isoformat()
    token = user_mgr.start_session("norbert", keep_logged_in_forever=False)
    user_mgr.users["norbert"]["session_expires"] = t
    user_mgr.refresh_session(token)
    user_mgr.check_for_expired_user_sessions()
    assert user_mgr.users["norbert"]["session_token"] is token



