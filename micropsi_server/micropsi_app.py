#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
MicroPsi server application.

This version of MicroPsi is meant to be deployed as a web server, and accessed through a browser.
For local use, simply start this server and point your browser to "http://localhost:6543".
The latter parameter is the default port and can be changed as needed.
"""

__author__ = 'joscha'
__date__ = '15.05.12'

VERSION = "0.1"

import micropsi_core.runtime
import micropsi_core.tools
import user
import config
import bottle
from bottle import route, post, run, request, response, template, static_file, redirect
import argparse
import os

DEFAULT_PORT = 6543
DEFAULT_HOST = "localhost"

APP_PATH = os.path.dirname(__file__)
RESOURCE_PATH = os.path.join(os.path.dirname(__file__),"..","resources")

bottle.debug( True ) #devV
bottle.TEMPLATE_PATH.insert( 0, os.path.join(APP_PATH, 'view', ''))


@route('/static/<filepath:path>')
def server_static(filepath):
    return static_file(filepath, root=os.path.join(APP_PATH, 'static'))

@route("/")
def index():
    if not request.get_cookie("token"):
        token = None
    else:
        token = request.get_cookie("token")

    return template("nodenet",
        version = VERSION,
        user = usermanager.get_user_id_for_session_token(token),
        permissions = usermanager.get_permissions_for_session_token(token))

@route("/about")
def about():
    return template("about", version = VERSION)

@route("/docs")
def documentation():
    return template("documentation", version = VERSION)

@route("/contact")
def contact():
    return template("contact", version = VERSION)

@route("/logout")
def logout():
    if request.get_cookie("token"):
        token = request.get_cookie("token")
        usermanager.end_session(token)
    token = None
    response.delete_cookie("token")
    redirect('/')

@route("/login")
def login():
    if not usermanager.users:  # create first user
        return template("signup", version = VERSION, first_user = True, userid="admin")

    return template("login",
        version = VERSION,
        user = usermanager.get_user_id_for_session_token(None),
        permissions = usermanager.get_permissions_for_session_token(None))

@post("/login_submit")
def login_submit():
    user_id = request.forms.userid
    password = request.forms.password

    # log in new user
    token = usermanager.start_session(user_id, password, request.forms.get("keep_logged_in"))
    if token:
        response.set_cookie("token", token)
        # redirect to start page
        redirect("/")
    else:
        # login failed, retry
        if user_id in usermanager.users:
            return template("login", version = VERSION, userid=user_id, password=password,
                password_error="Re-enter the password",
                login_error="User name and password do not match",
                cookie_warning = (token is None),
                permissions = usermanager.get_permissions_for_session_token(token))
        else:
            return template("login", version = VERSION, userid=user_id, password=password,
                userid_error="Re-enter the user name",
                login_error="User unknown",
                cookie_warning = (token is None),
                permissions = usermanager.get_permissions_for_session_token(token))

@route("/signup")
def signup():
    if request.get_cookie("token"):
        token = request.get_cookie("token")
    else:
        token = None

    if not usermanager.users:  # create first user
        return template("signup", version = VERSION, first_user = True, cookie_warning = (token is None))

    return template("signup", version = VERSION,
        permissions = usermanager.get_permissions_for_session_token(token),
        cookie_warning = (token is None))

@post("/signup_submit")
def signup_submit():
    if request.get_cookie("token"):
        token = request.get_cookie("token")
    else:
        token = None
    user_id = request.forms.userid
    password = request.forms.password
    role = request.forms.get('permissions')
    (success, result) = micropsi_core.tools.check_for_url_proof_id(user_id, existing_ids = usermanager.users.keys())
    permissions = usermanager.get_permissions_for_session_token(token)

    if success:
        # check if permissions in form are consistent with internal permissions
        if ((role == "Administrator" and ("create admin" in permissions or not usermanager.users)) or
            (role == "Full" and "create full" in permissions) or
            (role == "Restricted" and "create restricted" in permissions)):
            if usermanager.create_user(user_id, password, role, uid = micropsi_core.tools.generate_uid()):
                # log in new user
                token = usermanager.start_session(user_id, password, request.forms.get("keep_logged_in"))
                response.set_cookie("token", token)
                # redirect to start page
                redirect('/')
            else:
                return template("error", msg = "User creation failed for an obscure internal reason.")
        else:
            return template("error", msg = "Permission inconsistency during user creation.")
    else:
        # something wrong with the user id, retry
        return template("signup", version = VERSION, userid=user_id, password=password, userid_error=result,
            permissions = permissions, cookie_warning = (token is None))

@route("/change_password")
def change_password():
    if request.get_cookie("token"):
        token = request.get_cookie("token")
        return template("change_password", version = VERSION,
            userid = usermanager.get_user_id_for_session_token(token),
            permissions = usermanager.get_permissions_for_session_token(token))
    else:
        return template("error", msg = "Cannot change password outside of a session")

@post("/change_password_submit")
def change_password_submit():
    if request.get_cookie("token"):
        token = request.get_cookie("token")

        old_password = request.forms.old_password
        new_password = request.forms.new_password
        user_id = usermanager.get_user_id_for_session_token(token)
        permissions = usermanager.get_permissions_for_session_token(token)

        if usermanager.test_password(user_id, old_password):
            usermanager.set_user_password(user_id, new_password)
            redirect('/')

        else:
            return template("change_password", version = VERSION, userid=user_id, old_password=old_password,
                permissions = permissions, new_password=new_password,
                old_password_error="Wrong password, please try again")
    else:
        return template("error", msg = "Cannot change password outside of a session")

@route("/user_mgt")
def user_mgt():
    if request.get_cookie("token"):
        token = request.get_cookie("token")
        permissions = usermanager.get_permissions_for_session_token(token)
        if "manage users" in permissions:
            return template("user_mgt", version = VERSION, permissions = permissions,
                user = usermanager.get_user_id_for_session_token(token),
                userlist = usermanager.list_users())
    return template("error", msg = "Insufficient rights to access user console")

@route("/set_permissions/<user_id>/<role>")
def set_permissions(user_id, role):
    if request.get_cookie("token"):
        token = request.get_cookie("token")
        permissions = usermanager.get_permissions_for_session_token(token)
        if "manage users" in permissions:
            if user_id in usermanager.users.keys() and role in user.USER_ROLES.keys():
                usermanager.set_user_role(user_id, role)
            redirect('/user_mgt')
    return template("error", msg = "Insufficient rights to access user console")

@route("/create_user")
def create_user():
    if request.get_cookie("token"):
        token = request.get_cookie("token")
        permissions = usermanager.get_permissions_for_session_token(token)
        if "manage users" in permissions:
            return template("create_user", version = VERSION, user = usermanager.get_user_id_for_session_token(token),
                permissions = permissions)

    return template("error", msg = "Insufficient rights to access user console")


@post("/create_user_submit")
def create_user_submit():
    if request.get_cookie("token"):
        token = request.get_cookie("token")
        permissions = usermanager.get_permissions_for_session_token(token)

        user_id = request.forms.userid
        password = request.forms.password
        role = request.forms.get('permissions')
        (success, result) = micropsi_core.tools.check_for_url_proof_id(user_id, existing_ids = usermanager.users.keys())

        if success:
            # check if permissions in form are consistent with internal permissions
            if ((role == "Administrator" and ("create admin" in permissions or not usermanager.users)) or
                (role == "Full" and "create full" in permissions) or
                (role == "Restricted" and "create restricted" in permissions)):
                if usermanager.create_user(user_id, password, role, uid = micropsi_core.tools.generate_uid()):
                    redirect('/user_mgt')
                else:
                    return template("error", msg = "User creation failed for an obscure internal reason.")
            else:
                return template("error", msg = "Permission inconsistency during user creation.")
        else:
            # something wrong with the user id, retry
            return template("create_user", version = VERSION, user = usermanager.get_user_id_for_session_token(token),
                permissions = permissions, userid_error = result)
    return template("error", msg = "Insufficient rights to access user console")

@route("/set_password/<user_id>")
def set_password(user_id):
    if request.get_cookie("token"):
        token = request.get_cookie("token")
        permissions = usermanager.get_permissions_for_session_token(token)
        if "manage users" in permissions:
            return template("set_password", version = VERSION, permissions = permissions,
                user = usermanager.get_user_id_for_session_token(token),
                user_id=user_id)
    return template("error", msg = "Insufficient rights to access user console")

@post("/set_password_submit")
def set_password_submit():
    if request.get_cookie("token"):
        token = request.get_cookie("token")
        permissions = usermanager.get_permissions_for_session_token(token)
        if "manage users" in permissions:
            user_id = request.forms.userid
            password = request.forms.password
            if user_id in usermanager.users.keys():
                usermanager.set_user_password(user_id, password)
            redirect('/user_mgt')
    return template("error", msg = "Insufficient rights to access user console")

@route("/delete_user/<user_id>")
def delete_user(user_id):
    if request.get_cookie("token"):
        token = request.get_cookie("token")
        permissions = usermanager.get_permissions_for_session_token(token)
        if "manage users" in permissions:
            if user_id in usermanager.users.keys():
                usermanager.delete_user(user_id)
            redirect("/user_mgt")
    return template("error", msg = "Insufficient rights to access user console")


@route("/agent/import")
def import_agent():
    if('file' in request.forms):
        # do stuff
        pass
    token = request.get_cookie("token")
    return template("upload.tpl", title='Import agent', message='Select a file to upload and use for importing', action='/agent/import',
        version = VERSION,
        userid = usermanager.get_user_id_for_session_token(token),
        permissions = usermanager.get_permissions_for_session_token(token))


@route("/agent/merge")
def merge_agent():
    if('file' in request.forms):
        # do stuff
        pass
    token = request.get_cookie("token")
    return template("upload.tpl", title='Merge agent', message='Select a file to upload and use for merging', action='/agent/merge',
        version = VERSION,
        userid = usermanager.get_user_id_for_session_token(token),
        permissions = usermanager.get_permissions_for_session_token(token))


@route("/agent/export")
def export_agent():
    response.set_header('Content-type', 'application/json')
    response.set_header('Content-Disposition', 'attachment; filename="world.json"')
    return "{}"


@route("/agent/edit")
def edit_agent():
    token = request.get_cookie("token")
    id = request.params.get('id', None)
    title = 'Edit Blueprint' if id is not None else 'New Blueprint'
    return template("agent_form.tpl", title=title, agent={}, templates=[], worlds=[], worldadapters=[],
        version = VERSION,
        userid = usermanager.get_user_id_for_session_token(token),
        permissions = usermanager.get_permissions_for_session_token(token))


@route("/world/import")
def import_world():
    if('file' in request.forms):
        # do stuff
        pass
    token = request.get_cookie("token")
    return template("upload.tpl", title='World import', message='Select a file to upload and use for importing', action='/world/import',
        version = VERSION,
        userid = usermanager.get_user_id_for_session_token(token),
        permissions = usermanager.get_permissions_for_session_token(token))


@route("/world/export")
def export_world():
    response.set_header('Content-type', 'application/json')
    response.set_header('Content-Disposition', 'attachment; filename="world.json"')
    return "{}"


@route("/world/edit")
def edit_world():
    token = request.get_cookie("token")
    id = request.params.get('id', None)
    title = 'Edit World' if id is not None else 'New World'
    return template("world_form.tpl", title=title, world={}, worldtypes=[],
        version = VERSION,
        userid = usermanager.get_user_id_for_session_token(token),
        permissions = usermanager.get_permissions_for_session_token(token))



def main(host=DEFAULT_HOST, port=DEFAULT_PORT):
    global micropsi
    global usermanager
    global configs
    configs = config.ConfigurationManager(os.path.join(RESOURCE_PATH, "config.json"))
    micropsi = micropsi_core.runtime.MicroPsiRuntime(RESOURCE_PATH)
    usermanager = user.UserManager(os.path.join(RESOURCE_PATH, "user-db.json"))


    run(host=host, port=port) #devV

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Start the MicroPsi server.")
    parser.add_argument('-d', '--host', type=str, default=DEFAULT_HOST)
    parser.add_argument('-p', '--port', type=int, default=DEFAULT_PORT)
    args = parser.parse_args()
    main(host = args.host, port = args.port)




