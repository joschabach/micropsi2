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
from micropsi_core.runtime import AVAILABLE_WORLD_TYPES
import micropsi_core.tools
import usermanagement
import bottle
from bottle import route, post, run, request, response, template, static_file, redirect, error
import argparse
import os
import json
import inspect


DEFAULT_PORT = 6543
DEFAULT_HOST = "localhost"

APP_PATH = os.path.dirname(__file__)
RESOURCE_PATH = os.path.join(os.path.dirname(__file__), "..", "resources")

bottle.debug(True)  # devV
bottle.TEMPLATE_PATH.insert(0, os.path.join(APP_PATH, 'view', ''))

micropsi = micropsi_core.runtime.MicroPsiRuntime(RESOURCE_PATH)
usermanager = usermanagement.UserManager(os.path.join(RESOURCE_PATH, "user-db.json"))


def rpc(command, route_prefix="/rpc/", method="GET", permission_required=None):
    """Defines a decorator for accessing API calls. Use it by specifying the
    API method, followed by the permissions necessary to execute the method.
    Within the calling web page, use http://<url>/rpc/<method>(arg1="val1", arg2="val2", ...)
    Import these arguments into your decorated function:
        @rpc("my_method")
        def this_is_my_method(arg1, arg2):
            pass

    This will either return a JSON object with the result, or {"Error": <error message>}
    The decorated function can optionally import the following parameters (by specifying them in its signature):
        argument: the original argument string
        token: the current session token
        user_id: the id of the user associated with the current session token
        permissions: the set of permissions associated with the current session token

    Arguments:
        command: the command against which we want to match
        method (optional): the request method
        permission_required (optional): the type of permission necessary to execute the method;
            if omitted, permissions won't be tested by the decorator
    """
    def _decorator(func):
        @route(route_prefix + command, "POST")
        @route(route_prefix + command + "()", method)
        @route(route_prefix + command + "(<argument>)", method)
        def _wrapper(argument=None):
            response.content_type = 'application/json; charset=utf8'
            kwargs = {}
            if argument:
                try:
                    # split at commas and correct illegaly split lists:
                    arglist = argument.split(",")
                    kwargs = []
                    for index, val in enumerate(arglist):
                        if '=' not in val:
                            kwargs[len(kwargs) - 1] = kwargs[-1:][0] + ',' + val  # ugly.
                        else:
                            kwargs.append(val)
                    kwargs = dict((n.strip(), json.loads(v)) for n, v in (item.split('=') for item in kwargs))
                except ValueError, err:
                    response.status = 400
                    return {"Error": "Invalid arguments for remote procedure call: " + err.message}
            elif len(request.params) > 0:
                kwargs = dict((key.strip(), json.loads(val)) for key, val in request.params.iteritems())
            user_id, permissions, token = get_request_data()
            if permission_required and permission_required not in permissions:
                response.status = 401
                return {"Error": "Insufficient permissions for remote procedure call"}
            else:
                #kwargs.update({"argument": argument, "permissions": permissions, "user_id": user_id, "token": token})
                arguments = dict((name, kwargs[name]) for name in inspect.getargspec(func).args if name in kwargs)
                arguments.update(kwargs)
                try:
                    return json.dumps(func(**arguments))
                except TypeError, err:
                    response.status = 400
                    return {"Error": "Bad parameters in remote procedure call: %s" % err}
        return _wrapper
    return _decorator


def get_request_data():
    """Helper function to determine the current user, permissions and token"""
    if request.get_cookie("token"):
        token = request.get_cookie("token")
    else:
        token = None
    permissions = usermanager.get_permissions_for_session_token(token)
    user_id = usermanager.get_user_id_for_session_token(token)
    return user_id, permissions, token


# ----------------------------------------------------------------------------------

@route('/static/<filepath:path>')
def server_static(filepath):
    return static_file(filepath, root=os.path.join(APP_PATH, 'static'))


@route("/")
def index():
    user_id, permissions, token = get_request_data()
    print "received request with cookie token ", token, " from user ", user_id
    return template("all", version=VERSION, user_id=user_id, permissions=permissions)

@route("/nodenet")
def index():
    user_id, permissions, token = get_request_data()
    print "received request with cookie token ", token, " from user ", user_id
    return template("nodenet", version=VERSION, user_id=user_id, permissions=permissions)

@route("/world")
def index():
    user_id, permissions, token = get_request_data()
    print "received request with cookie token ", token, " from user ", user_id
    return template("world", version=VERSION, user_id=user_id, permissions=permissions)



@error(404)
def error_page(error):
    return template("error.tpl", error=error, msg="Page not found.", img="/static/img/brazil.gif")


@error(405)
def error_page_405(error):
    return template("error.tpl", error=error, msg="Method not allowed.", img="/static/img/strangelove.gif")


@error(500)
def error_page_500(error):
    return template("error.tpl", error=error, msg="Internal server error.", img="/static/img/brainstorm.gif")


@route("/about")
def about():
    user_id, permissions, token = get_request_data()
    return template("about", version=VERSION, user_id=user_id, permissions=permissions)


@route("/docs")
def documentation():
    return template("documentation", version=VERSION)


@route("/contact")
def contact():
    return template("contact", version=VERSION)


@route("/logout")
def logout():
    user_id, permissions, token = get_request_data()
    usermanager.end_session(token)
    response.delete_cookie("token")
    redirect("/")


@route("/login")
def login():
    if not usermanager.users:  # create first user
        return template("signup", version=VERSION, first_user=True, userid="admin",
            title="Create the administrator for the MicroPsi server")

    return template("login",
        title="Log in to the MicroPsi server",
        version=VERSION,
        user_id=usermanager.get_user_id_for_session_token(None),
        permissions=usermanager.get_permissions_for_session_token(None))


@post("/login_submit")
def login_submit():
    user_id = request.forms.userid
    password = request.forms.password

    # log in new user
    token = usermanager.start_session(user_id, password, request.forms.get("keep_logged_in"))
    if token:
        response.set_cookie("token", token)
        # redirect to start page
        return dict(redirect="/")
    else:
        # login failed, retry
        if user_id in usermanager.users:
            return template("login", version=VERSION, userid=user_id, password=password,
                title="Log in to the MicroPsi server",
                password_error="Re-enter the password",
                login_error="User name and password do not match",
                cookie_warning=(token is None),
                permissions=usermanager.get_permissions_for_session_token(token))
        else:
            return template("login", version=VERSION, userid=user_id, password=password,
                title="Log in to the MicroPsi server",
                userid_error="Re-enter the user name",
                login_error="User unknown",
                cookie_warning=(token is None),
                permissions=usermanager.get_permissions_for_session_token(token))


@route("/signup")
def signup():
    if request.get_cookie("token"):
        token = request.get_cookie("token")
    else:
        token = None

    if not usermanager.users:  # create first user
        return template("signup", version=VERSION,
            title="Create the administrator for the MicroPsi server",
            first_user=True, cookie_warning=(token is None))

    return template("signup", version=VERSION,
        title="Create a new user for the MicroPsi server",
        permissions=usermanager.get_permissions_for_session_token(token),
        cookie_warning=(token is None))


@post("/signup_submit")
def signup_submit():
    user_id, permissions, token = get_request_data()
    userid = request.forms.userid
    password = request.forms.password
    role = request.forms.get('permissions')
    (success, result) = micropsi_core.tools.check_for_url_proof_id(userid, existing_ids=usermanager.users.keys())
    if success:
        # check if permissions in form are consistent with internal permissions
        if ((role == "Administrator" and ("create admin" in permissions or not usermanager.users)) or
            (role == "Full" and "create full" in permissions) or
            (role == "Restricted" and "create restricted" in permissions)):
            if usermanager.create_user(userid, password, role, uid=micropsi_core.tools.generate_uid()):
                # log in new user
                token = usermanager.start_session(userid, password, request.forms.get("keep_logged_in"))
                response.set_cookie("token", token)
                # redirect to start page
                return dict(redirect='/')
            else:
                return dict(status="error", msg="User creation failed for an obscure internal reason.")
        else:
            return dict(status="error", msg="Permission inconsistency during user creation.")
    else:
        # something wrong with the user id, retry
        return template("signup", version=VERSION, userid=userid, password=password, userid_error=result,
            title="Create a new user for the MicroPsi server",
            user_id=user_id, permissions=permissions, cookie_warning=(token is None))


@route("/change_password")
def change_password():
    user_id, permissions, token = get_request_data()
    if token:
        return template("change_password", title="Change password", version=VERSION, user_id=user_id, permissions=permissions)
    else:
        return dict(status="error", msg="Cannot change password outside of a session")


@post("/change_password_submit")
def change_password_submit():
    user_id, permissions, token = get_request_data()
    if token:
        old_password = request.forms.old_password
        new_password = request.forms.new_password
        if usermanager.test_password(user_id, old_password):
            usermanager.set_user_password(user_id, new_password)
            return dict(msg='New password saved', status="success")
        else:
            return template("change_password", title="Change password", version=VERSION, user_id=user_id, old_password=old_password,
                permissions=permissions, new_password=new_password,
                old_password_error="Wrong password, please try again")
    else:
        return dict(status="error", msg="Cannot change password outside of a session")


@route("/user_mgt")
def user_mgt():
    user_id, permissions, token = get_request_data()
    if "manage users" in permissions:
        return template("user_mgt", version=VERSION, permissions=permissions,
            user_id=user_id,
            userlist=usermanager.list_users())
    return template("error", msg="Insufficient rights to access user console")


@route("/set_permissions/<user_key>/<role>")
def set_permissions(user_key, role):
    user_id, permissions, token = get_request_data()
    if "manage users" in permissions:
        if user_key in usermanager.users.keys() and role in usermanagement.USER_ROLES.keys():
            usermanager.set_user_role(user_key, role)
        redirect('/user_mgt')
    return template("error", msg="Insufficient rights to access user console")


@route("/create_user")
def create_user():
    user_id, permissions, token = get_request_data()
    if "manage users" in permissions:
        return template("create_user", version=VERSION, user_id=user_id,
            title="Create a user for the MicroPsi server", permissions=permissions)
    return template("error", msg="Insufficient rights to access user console")


@post("/create_user_submit")
def create_user_submit():
    user_id, permissions, token = get_request_data()
    userid = request.forms.userid
    password = request.forms.password
    role = request.forms.get('permissions')
    (success, result) = micropsi_core.tools.check_for_url_proof_id(userid, existing_ids=usermanager.users.keys())

    if success:
        # check if permissions in form are consistent with internal permissions
        if ((role == "Administrator" and ("create admin" in permissions or not usermanager.users)) or
            (role == "Full" and "create full" in permissions) or
            (role == "Restricted" and "create restricted" in permissions)):
            if usermanager.create_user(userid, password, role, uid=micropsi_core.tools.generate_uid()):
                if request.is_xhr:
                    return dict(status="OK", redirect='/user_mgt')
                else:
                    redirect('/user_mgt')
            else:
                return dict(status="error", msg="User creation failed for an obscure internal reason.")
        else:
            return dict(status="error", msg="Permission inconsistency during user creation.")
    else:
        # something wrong with the user id, retry
        return template("create_user", version=VERSION, user_id=user_id,
            title="Create a user for the MicroPsi server",
            permissions=permissions, userid_error=result)
    return dict(status="error", msg="Insufficient rights to access user console")


@route("/set_password/<userid>")
def set_password(userid):
    user_id, permissions, token = get_request_data()
    if "manage users" in permissions:
        return template("set_password", version=VERSION, permissions=permissions,
            title="Change Password",
            user_id=user_id,
            userid=userid)
    return template("error", msg="Insufficient rights to access user console")


@post("/set_password_submit")
def set_password_submit():
    user_id, permissions, token = get_request_data()
    if "manage users" in permissions:
        userid = request.forms.userid
        password = request.forms.password
        if userid in usermanager.users.keys():
            usermanager.set_user_password(userid, password)
        return dict(status='success', msg="New password saved")
    return dict(status="error", msg="Insufficient rights to access user console")


@route("/delete_user/<userid>")
def delete_user(userid):
    user_id, permissions, token = get_request_data()
    if "manage users" in permissions:
        if userid in usermanager.users.keys():
            usermanager.delete_user(userid)
        redirect("/user_mgt")
    return template("error", msg="Insufficient rights to access user console")


@route("/login_as/<userid>")
def login_as_user(userid):
    user_id, permissions, token = get_request_data()
    if "manage users" in permissions:
        if userid in usermanager.users:
            if usermanager.switch_user_for_session_token(userid, token):
                # redirect to start page
                redirect("/")
            return template("error", msg="Could not log in as new user")
        return template("error", msg="User does not exist")
    return template("error", msg="Insufficient rights to access user console")


@route("/nodenet/import")
def import_nodenet_form():
    token = request.get_cookie("token")
    return template("upload.tpl", title='Import Nodenet', message='Select a file to upload and use for importing', action='/nodenet/import',
        version=VERSION,
        userid=usermanager.get_user_id_for_session_token(token),
        permissions=usermanager.get_permissions_for_session_token(token))


@route("/nodenet/import", method="POST")
def import_nodenet():
    user_id, p, t = get_request_data()
    data = request.files['file_upload'].file.read()
    nodenet_uid = micropsi.import_nodenet(data, owner=user_id)
    return dict(status='success', msg="Nodenet imported", nodenet_uid=nodenet_uid)


@route("/nodenet/merge/<nodenet_uid>")
def merge_nodenet_form(nodenet_uid):
    token = request.get_cookie("token")
    return template("upload.tpl", title='Merge Nodenet', message='Select a file to upload and use for merging', action='/nodenet/merge/%s' % nodenet_uid,
        version=VERSION,
        userid=usermanager.get_user_id_for_session_token(token),
        permissions=usermanager.get_permissions_for_session_token(token))


@route("/nodenet/merge/<nodenet_uid>", method="POST")
def merge_nodenet(nodenet_uid):
    micropsi.merge_nodenet(nodenet_uid, request.files['file_upload'].file.read())
    return dict(status='success', msg="Nodenet merged")


@route("/nodenet/export/<nodenet_uid>")
def export_nodenet(nodenet_uid):
    response.set_header('Content-type', 'application/json')
    response.set_header('Content-Disposition', 'attachment; filename="nodenet.json"')
    return micropsi.export_nodenet(nodenet_uid)


@route("/nodenet/edit")
def edit_nodenet():
    user_id, permissions, token = get_request_data()
    id = request.params.get('id', None)
    title = 'Edit Nodenet' if id is not None else 'New Nodenet'
    return template("nodenet_form.tpl", title=title,
        nodenets=micropsi.get_available_nodenets(),
        templates=micropsi.get_available_nodenets(),
        worlds=micropsi.get_available_worlds(),
        version=VERSION, user_id=user_id, permissions=permissions)


@route("/nodenet/edit", method="POST")
def write_nodenet():
    user_id, permissions, token = get_request_data()
    if "manage nodenets" in permissions:
        result, nodenet_uid = micropsi.new_nodenet(request.params['nn_name'], request.params['nn_worldadapter'], template=request.params.get('nn_template'), owner=user_id, world_uid=request.params.get('nn_world'))
        if result:
            return dict(status="success", msg="Nodenet created", nodenet_uid=nodenet_uid)
        else:
            return dict(status="error", msg="Error saving nodenet: %s" % nodenet_uid)
    return dict(status="error", msg="Insufficient rights to write nodenet")


@route("/world/import")
def import_world_form():
    token = request.get_cookie("token")
    return template("upload.tpl", title='World import', message='Select a file to upload and use for importing',
        action='/world/import',
        version=VERSION,
        user_id=usermanager.get_user_id_for_session_token(token),
        permissions=usermanager.get_permissions_for_session_token(token))


@route("/world/import", method="POST")
def import_world():
    user_id, p, t = get_request_data()
    data = request.files['file_upload'].file.read()
    world_uid = micropsi.import_world(data, owner=user_id)
    return dict(status='success', msg="World imported", world_uid=world_uid)


@route("/world/export/<world_uid>")
def export_world(world_uid):
    response.set_header('Content-type', 'application/json')
    response.set_header('Content-Disposition', 'attachment; filename="world.json"')
    return micropsi.export_world(world_uid)


@route("/world/edit")
def edit_world_form():
    token = request.get_cookie("token")
    id = request.params.get('id', None)
    title = 'Edit World' if id is not None else 'New World'
    return template("world_form.tpl", title=title, worldtypes=AVAILABLE_WORLD_TYPES,
        version=VERSION,
        user_id=usermanager.get_user_id_for_session_token(token),
        permissions=usermanager.get_permissions_for_session_token(token))


@route("/world/edit", method="POST")
def edit_world():
    user_id, permissions, token = get_request_data()
    if "manage worlds" in permissions:
        result, uid = micropsi.new_world(request.params['world_name'], request.params['world_type'], user_id)
        if result:
            return dict(status="success", msg="World created", world_uid=uid)
        else:
            return dict(status="error", msg=": %s" % result)
    return dict(status="error", msg="Insufficient rights to create world")


@route("/nodenet_list/")
@route("/nodenet_list/<current_nodenet>")
def nodenet_list(current_nodenet=None):
    user_id, permissions, token = get_request_data()
    nodenets = micropsi.get_available_nodenets()
    return template("nodenet_list", type="nodenet", user_id=user_id,
        current=current_nodenet,
        mine=dict((uid, nodenets[uid]) for uid in nodenets if nodenets[uid].owner == user_id),
        others=dict((uid, nodenets[uid]) for uid in nodenets if nodenets[uid].owner != user_id))


@route("/world_list/")
@route("/world_list/<current_world>")
def world_list(current_world=None):
    user_id, permissions, token = get_request_data()
    worlds = micropsi.get_available_worlds()
    return template("nodenet_list", type="world", user_id=user_id,
        current=current_world,
        mine=dict((uid, worlds[uid]) for uid in worlds if worlds[uid].owner == user_id),
        others=dict((uid, worlds[uid]) for uid in worlds if worlds[uid].owner != user_id))


@rpc("select_nodenet")
def select_nodenet(nodenet_uid):
    result, msg = micropsi.load_nodenet(nodenet_uid)
    if result:
        return dict(Status="OK")
    else:
        return dict(Error=msg)


@rpc("load_nodenet_into_ui")
def load_nodenet_into_ui(nodenet_uid, **coordinates):
    result, uid = micropsi.load_nodenet(nodenet_uid)
    if not result:
        return dict(Error=uid)
    return micropsi.get_nodenet_area(nodenet_uid, **coordinates)


@rpc("generate_uid")
def generate_uid():
    return micropsi_core.tools.generate_uid()


@rpc("get_available_nodenets")
def get_available_nodenets(user_id):
    return micropsi.get_available_nodenets(user_id)


@route("/create_new_nodenet_form")
def create_new_nodenet_form():
    user_id, permissions, token = get_request_data()
    nodenets = micropsi.get_available_nodenets()
    worlds = micropsi.get_available_worlds()
    return template("nodenet_form", user_id=user_id, template="None",
        nodenets=nodenets, worlds=worlds)


@route("/create_worldadapter_selector/<world_uid>")
def create_worldadapter_selector(world_uid):
    nodenets = micropsi.get_available_nodenets()
    worlds = micropsi.get_available_worlds()
    return template("worldadapter_selector", world_uid=world_uid,
        nodenets=nodenets, worlds=worlds)


@rpc("delete_nodenet", permission_required="manage nodenets")
def delete_nodenet(nodenet_uid):
    return micropsi.delete_nodenet(nodenet_uid)


@rpc("set_nodenet_properties", permission_required="manage nodenets")
def set_nodenet_properties(nodenet_uid, nodenet_name=None, worldadapter=None, world_uid=None, owner=None):
    return micropsi.set_nodenet_properties(nodenet_uid, nodenet_name, worldadapter, world_uid, owner)


@rpc("set_node_state")
def set_node_state(nodenet_uid, node_uid, state):
    if state == "":
        state = None
    return micropsi.set_node_state(nodenet_uid, node_uid, state)


@rpc("set_node_activation")
def set_node_activation(nodenet_uid, node_uid, activation):
    return micropsi.set_node_activation(nodenet_uid, node_uid, activation)


@rpc("start_nodenetrunner", permission_required="manage nodenets")
def start_nodenetrunner(nodenet_uid):
    return micropsi.start_nodenetrunner(nodenet_uid)


@rpc("set_nodenetrunner_timestep", permission_required="manage nodenets")
def set_nodenetrunner_timestep(timestep):
    return micropsi.set_nodenetrunner_timestep(timestep)


@rpc("get_nodenetrunner_timestep", permission_required="manage server")
def get_nodenetrunner_timestep():
    return micropsi.get_nodenetrunner_timestep()


@rpc("get_is_nodenet_running")
def get_is_nodenet_running(nodenet_uid):
    return micropsi.get_is_nodenet_running(nodenet_uid)


@rpc("stop_nodenetrunner", permission_required="manage nodenets")
def stop_nodenetrunner(nodenet_uid):
    return micropsi.stop_nodenetrunner(nodenet_uid)


@rpc("step_nodenet", permission_required="manage nodenets")
def step_nodenet(nodenet_uid, nodespace=None):
    return micropsi.step_nodenet(nodenet_uid, nodespace)


@rpc("revert_nodenet", permission_required="manage nodenets")
def revert_nodenet(nodenet_uid):
    return micropsi.revert_nodenet(nodenet_uid)


@rpc("save_nodenet", permission_required="manage nodenets")
def save_nodenet(nodenet_uid):
    return micropsi.save_nodenet(nodenet_uid)


@rpc("export_nodenet")
def export_nodenet_rpc(nodenet_uid):
    return micropsi.export_nodenet(nodenet_uid)


@rpc("import_nodenet", permission_required="manage nodenets")
def import_nodenet(nodenet_uid, nodenet): return micropsi.import_nodenet


@rpc("merge_nodenet", permission_required="manage nodenets")
def merge_nodenet(nodenet_uid, nodenet): return micropsi.merge_nodenet


# World
@rpc("get_available_worlds")
def get_available_worlds():
    user_id, p, t = get_request_data()
    return micropsi.get_available_worlds(user_id)


@rpc("get_world_properties")
def get_world_properties(world_uid):
    return micropsi.get_world_properties(world_uid)


@rpc("get_worldadapters")
def get_worldadapters(world_uid):
    return micropsi.get_worldadapters(world_uid)


@rpc("get_world_objects")
def get_world_objects(world_uid):
    return micropsi.get_world_objects(world_uid)


@rpc("new_world", permission_required="manage worlds")
def new_world(world_name, world_type, owner=""):
    return micropsi.new_world(world_name, world_type, owner)


@rpc("get_available_world_types")
def get_available_world_types():
    return AVAILABLE_WORLD_TYPES


@rpc("delete_world", permission_required="manage worlds")
def delete_world(world_uid):
    return micropsi.delete_world(world_uid)


@rpc("get_world_view")
def get_world_view(world_uid, step):
    return micropsi.get_world_view(world_uid, step)


@rpc("set_world_properties", permission_required="manage worlds")
def set_world_data(world_uid, world_name=None, world_type=None, owner=None): return micropsi.set_world_properties


@rpc("start_worldrunner", permission_required="manage worlds")
def start_worldrunner(world_uid):
    return micropsi.start_worldrunner(world_uid)


@rpc("get_worldrunner_timestep")
def get_worldrunner_timestep():
    return micropsi.get_worldrunner_timestep()


@rpc("get_is_world_running")
def get_is_world_running(world_uid):
    return micropsi.get_is_world_running(world_uid)


@rpc("set_worldrunner_timestep", permission_required="manage server")
def set_worldrunner_timestep():
    return micropsi.set_worldrunner_timestep()


@rpc("stop_worldrunner", permission_required="manage worlds")
def stop_worldrunner(world_uid):
    return micropsi.stop_worldrunner(world_uid)


@rpc("step_world", permission_required="manage worlds")
def step_world(world_uid, return_world_view=False):
    return micropsi.step_world(world_uid, return_world_view)


@rpc("revert_world", permission_required="manage worlds")
def revert_world(world_uid):
    return micropsi.revert_world(world_uid)


@rpc("save_world", permission_required="manage worlds")
def save_world(world_uid):
    return micropsi.save_world(world_uid)


@rpc("export_world")
def export_world_rpc(world_uid):
    return micropsi.export_world(world_uid)


@rpc("import_world", permission_required="manage worlds")
def import_world_rpc(world_uid, worlddata):
    return micropsi.import_world(world_uid, worlddata)

# Monitor

@rpc("add_gate_monitor")
def add_gate_monitor(nodenet_uid, node_uid, gate_index): return micropsi.add_gate_monitor

@rpc("add_slot_monitor")
def add_slot_monitor(nodenet_uid, node_uid, slot_index): return micropsi.add_slot_monitor

@rpc("remove_monitor")
def remove_monitor(monitor_uid): return micropsi.remove_monitor

@rpc("clear_monitor")
def clear_monitor(monitor_uid): return micropsi.clear_monitor

@rpc("export_monitor_data")
def export_monitor_data(nodenet_uid): return micropsi.export_monitor_data

@rpc("get_monitor_data")
def get_monitor_data(nodenet_uid, step): return micropsi.get_monitor_data

# Nodenet


@rpc("get_nodespace")
def get_nodespace(nodenet_uid, nodespace, step):
    return micropsi.get_nodespace(nodenet_uid, nodespace, step)


@rpc("get_node")
def get_node(nodenet_uid, node_uid):
    return micropsi.get_node(nodenet_uid, node_uid)


@rpc("add_node", permission_required="manage nodenets")
def add_node(nodenet_uid, type, pos, nodespace, state=None, uid=None, name="", parameters={}):
    result, uid = micropsi.add_node(nodenet_uid, type, pos, nodespace, state=state, uid=uid, name=name, parameters=parameters)
    if result:
        return dict(Status="OK", uid=uid)
    else:
        return dict(Error=uid)


@rpc("set_node_position", permission_required="manage nodenets")
def set_node_position(nodenet_uid, node_uid, pos):
    return micropsi.set_node_position(nodenet_uid, node_uid, pos)


@rpc("set_node_name", permission_required="manage nodenets")
def set_node_name(nodenet_uid, node_uid, name):
    return micropsi.set_node_name(nodenet_uid, node_uid, name)


@rpc("delete_node", permission_required="manage nodenets")
def delete_node(nodenet_uid, node_uid):
    return micropsi.delete_node(nodenet_uid, node_uid)


@rpc("get_available_node_types")
def get_available_node_types(nodenet_uid=None):
    return micropsi.get_available_node_types(nodenet_uid)


@rpc("get_available_native_module_types")
def get_available_native_module_types(nodenet_uid):
    return micropsi.get_available_native_module_types(nodenet_uid)


@rpc("get_nodefunction")
def get_nodefunction(nodenet_uid, node_type):
    return micropsi.get_nodefunction(nodenet_uid, node_type)


@rpc("set_nodefunction", permission_required="manage nodenets")
def set_nodefunction(nodenet_uid, node_type, nodefunction=None):
    return micropsi.set_nodefunction(nodenet_uid, node_type, nodefunction)


@rpc("set_node_parameters", permission_required="manage nodenets")
def set_node_parameters(nodenet_uid, node_uid, parameters):
    return micropsi.set_node_parameters(nodenet_uid, node_uid, parameters)


@rpc("add_node_type", permission_required="manage nodenets")
def add_node_type(nodenet_uid, node_type, slots=[], gates=[], node_function=None, parameters=[]):
    return micropsi.add_node_type(nodenet_uid, node_type, slots, gates, node_function, parameters)


@rpc("delete_node_type", permission_required="manage nodenets")
def delete_node_type(nodenet_uid, node_type):
    return micropsi.delete_node_type(nodenet_uid, node_type)


@rpc("get_slot_types")
def get_slot_types(nodenet_uid, node_type):
    return micropsi.get_slot_types(nodenet_uid, node_type)


@rpc("get_gate_types")
def get_gate_types(nodenet_uid, node_type):
    return micropsi.get_gate_types(nodenet_uid, node_type)


@rpc("get_gate_function")
def get_gate_function(nodenet_uid, nodespace, node_type, gate_type): return micropsi.get_gate_function

@rpc("set_gate_function", permission_required="manage nodenets")
def set_gate_function(nodenet_uid, nodespace, node_type, gate_type, gate_function=None, parameters=None): return micropsi.set_gate_function

@rpc("set_gate_parameters", permission_required="manage nodenets")
def set_gate_parameters(nodenet_uid, node_uid, gate_type, parameters=None): return micropsi.set_gate_parameters


@rpc("get_available_datasources")
def get_available_datasources(nodenet_uid):
    return micropsi.get_available_datasources(nodenet_uid)


@rpc("get_available_datatargets")
def get_available_datatargets(nodenet_uid):
    return micropsi.get_available_datatargets(nodenet_uid)


@rpc("bind_datasource_to_sensor", permission_required="manage nodenets")
def bind_datasource_to_sensor(nodenet_uid, sensor_uid, datasource):
    return micropsi.bind_datasource_to_sensor(nodenet_uid, sensor_uid, datasource)


@rpc("bind_datatarget_to_actor", permission_required="manage nodenets")
def bind_datatarget_to_actor(nodenet_uid, actor_uid, datatarget):
    return micropsi.bind_datatarget_to_actor(nodenet_uid, actor_uid, datatarget)


@rpc("add_link", permission_required="manage nodenets")
def add_link(nodenet_uid, source_node_uid, gate_type, target_node_uid, slot_type, weight, uid):
    return micropsi.add_link(nodenet_uid, source_node_uid, gate_type, target_node_uid, slot_type, weight=weight, uid=uid)


@rpc("set_link_weight", permission_required="manage nodenets")
def set_link_weight(nodenet_uid, link_uid, weight, certainty=1):
    return micropsi.set_link_weight(nodenet_uid, link_uid, weight, certainty)


@rpc("get_link")
def get_link(nodenet_uid, link_uid):
    return micropsi.get_link(nodenet_uid, link_uid)


@rpc("delete_link", permission_required="manage nodenets")
def delete_link(nodenet_uid, link_uid):
    return micropsi.delete_link(nodenet_uid, link_uid)


@rpc("get_example_nodenet")
def return_dummy_nodenet():
    return {

    }


# -----------------------------------------------------------------------------------------------

def main(host=DEFAULT_HOST, port=DEFAULT_PORT):
    run(host=host, port=port)  # devV

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Start the MicroPsi server.")
    parser.add_argument('-d', '--host', type=str, default=DEFAULT_HOST)
    parser.add_argument('-p', '--port', type=int, default=DEFAULT_PORT)
    args = parser.parse_args()
    main(host=args.host, port=args.port)
