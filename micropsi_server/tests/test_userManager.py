#!/usr/local/bin/python
# -*- coding: utf-8 -*-

"""
Overly verbose and clumsy attempt at testing with py.test
"""

__author__ = 'joscha'
__date__ = '29.10.12'

import os
import datetime


def test_create_user(user_mgr, eliza):
    user_mgr.delete_user("eliza")
    assert "eliza" not in user_mgr.users
    user_mgr.create_user("eliza", "qwerty", "Full")
    assert "eliza" in user_mgr.users


def test_save_users(user_mgr, user_def):
    try:
        os.remove(user_def)
    except:
        pass
    assert not os.path.exists(user_def)
    user_mgr.save_users()
    assert os.path.exists(user_def)


def test_list_users(user_mgr, eliza):
    l = user_mgr.list_users()
    assert "eliza" in l
    assert l["eliza"]["is_active"] is True
    assert l["eliza"]["role"] == "Full"
    assert len(l) == len(user_mgr.users)


def test_set_user_id(user_mgr, eliza):
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


def test_set_user_role(user_mgr, eliza):
    assert user_mgr.users["eliza"]["role"] == "Full"
    user_mgr.set_user_role("eliza", "Restricted")
    assert user_mgr.users["eliza"]["role"] == "Restricted"
    user_mgr.set_user_role("eliza", "Full")
    assert user_mgr.users["eliza"]["role"] == "Full"
    assert not user_mgr.set_user_role("grxxtrxx", "Full")


def test_set_user_password(user_mgr, eliza):
    pwd = user_mgr.users["eliza"]["hashed_password"]
    user_mgr.set_user_password("eliza", "abcd")
    assert not pwd == user_mgr.users["eliza"]["hashed_password"]
    user_mgr.set_user_password("eliza", "qwerty")
    assert pwd == user_mgr.users["eliza"]["hashed_password"]


def test_start_session(user_mgr, eliza):
    user_mgr.end_session(eliza)
    assert user_mgr.users["eliza"]["sessions"] == {}
    assert user_mgr.start_session("eliza", password="wrong") is None
    assert user_mgr.users["eliza"]["sessions"] == {}
    token = user_mgr.start_session("eliza", password="qwerty")
    assert token is not None
    assert token in user_mgr.users["eliza"]["sessions"]


def test_get_user_id_for_session_token(user_mgr, eliza):
    assert user_mgr.get_user_id_for_session_token(eliza) == "eliza"
    assert user_mgr.get_user_id_for_session_token("notoken") == "Guest"


def test_get_permissions_for_session_token(user_mgr, eliza):
    perms = user_mgr.get_permissions_for_session_token(eliza)
    assert "manage server" in perms
    assert "manage users" not in perms
    user_mgr.set_user_role("eliza", "Guest")
    perms = user_mgr.get_permissions_for_session_token(eliza)
    assert "manage server" not in perms


def test_switch_user_for_session_token(user_mgr, eliza):
    user_mgr.create_user("norbert", "abcd", "Full")
    token = user_mgr.start_session("norbert")
    user_mgr.switch_user_for_session_token("eliza", token)
    assert user_mgr.users["norbert"]["sessions"] == {}
    assert token in user_mgr.users["eliza"]["sessions"]
    # assert eliza's own session is still valid
    assert eliza in user_mgr.users["eliza"]["sessions"]


def test_end_session(user_mgr, eliza):
    user_mgr.end_session(eliza)
    assert user_mgr.users["eliza"]["sessions"] == {}


def test_test_password(user_mgr, eliza):
    assert user_mgr.test_password("eliza", "qwerty")
    assert not user_mgr.test_password("eliza", "qwertz")


def test_end_all_sessions(user_mgr, eliza):
    user_mgr.create_user("norbert", "abcd", "Full")
    norbert = user_mgr.start_session("norbert")
    assert eliza in user_mgr.users["eliza"]["sessions"]
    assert norbert in user_mgr.users["norbert"]["sessions"]
    user_mgr.end_all_sessions()
    assert user_mgr.users["eliza"]["sessions"] == {}
    assert user_mgr.users["norbert"]["sessions"] == {}
    assert user_mgr.sessions == {}


def test_delete_user(user_mgr):
    user_mgr.create_user("norbert", "abcd", "Full")
    assert "norbert" in user_mgr.users
    user_mgr.delete_user("norbert")
    assert "norbert" not in user_mgr.users


def test_check_for_expired_user_sessions(user_mgr, eliza):
    t = datetime.datetime.now().time().isoformat()
    user_mgr.create_user("norbert", "abcd", "Full")
    norbert = user_mgr.start_session("norbert", keep_logged_in_forever=False)
    user_mgr.users["norbert"]["sessions"][norbert]['expires'] = repr(t)
    assert user_mgr.users["eliza"]["sessions"][eliza]["expires"] is False
    user_mgr.check_for_expired_user_sessions()
    assert user_mgr.users["norbert"]["sessions"] == {}
    assert user_mgr.users["eliza"]["sessions"] != {}


def test_refresh_session(user_mgr):
    user_mgr.create_user("norbert", "abcd", "Full")
    norbert = user_mgr.start_session("norbert", keep_logged_in_forever=False)
    t = datetime.datetime.now().isoformat()
    user_mgr.users["norbert"]["sessions"][norbert]["expires"] = t
    user_mgr.refresh_session(norbert)
    user_mgr.check_for_expired_user_sessions()
    assert norbert in user_mgr.users["norbert"]["sessions"]


def test_multiple_sessions_for_user(user_mgr, eliza):
    eliza2 = user_mgr.start_session("eliza", keep_logged_in_forever=False)
    assert user_mgr.get_user_id_for_session_token(eliza) == "eliza"
    assert user_mgr.get_user_id_for_session_token(eliza2) == "eliza"
    assert not user_mgr.users["eliza"]["sessions"][eliza]['expires']
    assert user_mgr.users["eliza"]["sessions"][eliza2]['expires']
