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


from micropsi_core import runtime

import micropsi_core.tools
from micropsi_server import micropsi_logging
from micropsi_server import usermanagement
from micropsi_server import bottle
from micropsi_server.bottle import route, post, run, request, response, template, static_file, redirect, error
import argparse
import os
import json
import inspect
from micropsi_server import minidoc
from configuration import DEFAULT_HOST, DEFAULT_PORT, VERSION, APPTITLE

APP_PATH = os.path.dirname(__file__)

bottle.debug(False)  # devV

bottle.TEMPLATE_PATH.insert(0, os.path.join(APP_PATH, 'view', ''))
bottle.TEMPLATE_PATH.insert(1, os.path.join(APP_PATH, 'static', ''))

# runtime = micropsi_core.runtime.MicroPsiRuntime()
usermanager = usermanagement.UserManager()


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
        @route(route_prefix + command + "(:argument#.+#)", method)
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
                except ValueError as err:
                    response.status = 400
                    return {"Error": "Invalid arguments for remote procedure call: " + str(err)}
            else:
                try:
                    kwargs = request.json
                except ValueError:
                    if len(request.params) > 0:
                        kwargs = dict((key.strip('[]'), json.loads(val)) for key, val in request.params.iteritems())
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
                except Exception as err:
                    response.status = 500
                    response.content_type = 'application/json'
                    import traceback
                    return json.dumps({"Error": str(err), "Traceback": traceback.format_exc()})
                
                # except TypeError as err:
                #     response.status = 400
                #     return {"Error": "Bad parameters in remote procedure call: %s" % err}
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


def _add_world_list(template_name, **params):
    worlds = runtime.get_available_worlds()
    if request.query.get('select_world') and request.query.get('select_world') in worlds:
        current_world = request.query.get('select_world')
        response.set_cookie('selected_world', current_world)
    else:
        current_world = request.get_cookie('selected_world')
    if current_world in worlds and hasattr(worlds[current_world], 'assets'):
        world_assets = worlds[current_world].assets
    else:
        world_assets = {}
    return template(template_name, current=current_world,
        mine=dict((uid, worlds[uid]) for uid in worlds if worlds[uid].owner == params['user_id']),
        others=dict((uid, worlds[uid]) for uid in worlds if worlds[uid].owner != params['user_id']),
        world_assets=world_assets, **params)

@route('/static/<filepath:path>')
def server_static(filepath):
    return static_file(filepath, root=os.path.join(APP_PATH, 'static'))


@route("/")
def index():
    user_id, permissions, token = get_request_data()
    return _add_world_list("viewer", mode="all", version=VERSION, user_id=user_id, permissions=permissions)


@route("/nodenet")
def nodenet():
    user_id, permissions, token = get_request_data()
    return template("viewer", mode="nodenet", version=VERSION, user_id=user_id, permissions=permissions)


@route('/minidoc/<filepath:path>')
def document(filepath):
    return template("minidoc",
        navi=minidoc.get_navigation(),
        content=minidoc.get_documentation_body(filepath), title="Minidoc: " + filepath)

@route("/world")
def world():
    user_id, permissions, token = get_request_data()
    return _add_world_list("viewer", mode="world", version=VERSION, user_id=user_id, permissions=permissions)


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
            title="Create the administrator for the %s server" % APPTITLE)

    return template("login",
        title="Log in to the %s server" % APPTITLE,
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
                title="Log in to the %s server" % APPTITLE,
                password_error="Re-enter the password",
                login_error="User name and password do not match",
                cookie_warning=(token is None),
                permissions=usermanager.get_permissions_for_session_token(token))
        else:
            return template("login", version=VERSION, userid=user_id, password=password,
                title="Log in to the %s server" % APPTITLE,
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
            title="Create the administrator for the %s server" % APPTITLE,
            first_user=True, cookie_warning=(token is None))

    return template("signup", version=VERSION,
        title="Create a new user for the %s server" % APPTITLE,
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
            title="Create a new user for the %s server" % APPTITLE,
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
            title="Create a user for the %s server" % APP_PATH, permissions=permissions)
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
            title="Create a user for the %s server" % APPTITLE,
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


@route("/nodenet_mgt")
def nodenet_mgt():
    user_id, permissions, token = get_request_data()
    if "manage nodenets" in permissions:
        notification = None
        if request.get_cookie('notification'):
            notification = json.loads(request.get_cookie('notification'))
            response.set_cookie('notification', '', path='/')
        return template("nodenet_mgt", version=VERSION, permissions=permissions,
            user_id=user_id,
            nodenet_list=runtime.get_available_nodenets(), notification=notification)
    return template("error", msg="Insufficient rights to access nodenet console")


@route("/select_nodenet_from_console/<nodenet_uid>")
def select_nodenet_from_console(nodenet_uid):
    user_id, permissions, token = get_request_data()
    result, uid = runtime.load_nodenet(nodenet_uid)
    if not result:
        return template("error", msg="Could not select nodenet")
    response.set_cookie("selected_nodenet", nodenet_uid, path="/")
    redirect("/")


@route("/delete_nodenet_from_console/<nodenet_uid>")
def delete_nodenet_from_console(nodenet_uid):
    user_id, permissions, token = get_request_data()
    if "manage nodenets" in permissions:
        runtime.delete_nodenet(nodenet_uid)
        response.set_cookie('notification', '{"msg":"Nodenet deleted", "status":"success"}', path='/')
        redirect('/nodenet_mgt')
    return template("error", msg="Insufficient rights to access nodenet console")


@route("/save_all_nodenets")
def save_all_nodenets():
    user_id, permissions, token = get_request_data()
    if "manage nodenets" in permissions:
        for uid in runtime.nodenets:
            runtime.save_nodenet(uid)
        response.set_cookie('notification', '{"msg":"All nodenets saved", "status":"success"}', path='/')
        redirect('/nodenet_mgt')
    return template("error", msg="Insufficient rights to access nodenet console")


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
    data = data.decode('utf-8')
    nodenet_uid = runtime.import_nodenet(data, owner=user_id)
    return dict(status='success', msg="Nodenet imported", nodenet_uid=nodenet_uid)


@route("/nodenet/merge/<nodenet_uid>")
def merge_nodenet_form(nodenet_uid):
    token = request.get_cookie("token")
    return template("upload.tpl", title='Merge Nodenet', message='Select a file to upload and use for merging',
        action='/nodenet/merge/%s' % nodenet_uid,
        version=VERSION,
        userid=usermanager.get_user_id_for_session_token(token),
        permissions=usermanager.get_permissions_for_session_token(token))


@route("/nodenet/merge/<nodenet_uid>", method="POST")
def merge_nodenet(nodenet_uid):
    runtime.merge_nodenet(nodenet_uid, request.files['file_upload'].file.read())
    return dict(status='success', msg="Nodenet merged")


@route("/nodenet/export/<nodenet_uid>")
def export_nodenet(nodenet_uid):
    response.set_header('Content-type', 'application/json')
    response.set_header('Content-Disposition', 'attachment; filename="nodenet.json"')
    return runtime.export_nodenet(nodenet_uid)


@route("/nodenet/edit")
def edit_nodenet():
    user_id, permissions, token = get_request_data()
    # nodenet_id = request.params.get('id', None)
    title = 'Edit Nodenet' if id is not None else 'New Nodenet'
    return template("nodenet_form.tpl", title=title,
        # nodenet_uid=nodenet_uid,
        nodenets=runtime.get_available_nodenets(),
        templates=runtime.get_available_nodenets(),
        worlds=runtime.get_available_worlds(),
        version=VERSION, user_id=user_id, permissions=permissions)


@route("/nodenet/edit", method="POST")
def write_nodenet():
    user_id, permissions, token = get_request_data()
    if "manage nodenets" in permissions:
        result, nodenet_uid = runtime.new_nodenet(request.params['nn_name'], request.params['nn_worldadapter'], template=request.params.get('nn_template'), owner=user_id, world_uid=request.params.get('nn_world'))
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
    data = data.decode('utf-8')
    world_uid = runtime.import_world(data, owner=user_id)
    return dict(status='success', msg="World imported", world_uid=world_uid)


@route("/world/export/<world_uid>")
def export_world(world_uid):
    response.set_header('Content-type', 'application/json')
    response.set_header('Content-Disposition', 'attachment; filename="world.json"')
    return runtime.export_world(world_uid)


@route("/world/edit")
def edit_world_form():
    token = request.get_cookie("token")
    id = request.params.get('id', None)
    title = 'Edit World' if id is not None else 'New World'
    return template("world_form.tpl", title=title, worldtypes=runtime.get_available_world_types(),
        version=VERSION,
        user_id=usermanager.get_user_id_for_session_token(token),
        permissions=usermanager.get_permissions_for_session_token(token))


@route("/world/edit", method="POST")
def edit_world():
    user_id, permissions, token = get_request_data()
    if "manage worlds" in permissions:
        result, uid = runtime.new_world(request.params['world_name'], request.params['world_type'], user_id)
        if result:
            return dict(status="success", msg="World created", world_uid=uid)
        else:
            return dict(status="error", msg=": %s" % result)
    return dict(status="error", msg="Insufficient rights to create world")


@route("/nodenet_list/")
@route("/nodenet_list/<current_nodenet>")
def nodenet_list(current_nodenet=None):
    user_id, permissions, token = get_request_data()
    nodenets = runtime.get_available_nodenets()
    return template("nodenet_list", type="nodenet", user_id=user_id,
        current=current_nodenet,
        mine=dict((uid, nodenets[uid]) for uid in nodenets if nodenets[uid].owner == user_id),
        others=dict((uid, nodenets[uid]) for uid in nodenets if nodenets[uid].owner != user_id))


@route("/world_list/")
@route("/world_list/<current_world>")
def world_list(current_world=None):
    user_id, permissions, token = get_request_data()
    worlds = runtime.get_available_worlds()
    return template("nodenet_list", type="world", user_id=user_id,
        current=current_world,
        mine=dict((uid, worlds[uid]) for uid in worlds if worlds[uid].owner == user_id),
        others=dict((uid, worlds[uid]) for uid in worlds if worlds[uid].owner != user_id))


@route("/config/nodenet/runner")
@route("/config/nodenet/runner", method="POST")
def edit_nodenetrunner():
    user_id, permissions, token = get_request_data()
    if len(request.params) > 0:
        runtime.set_nodenetrunner_timestep(int(request.params['runner_timestep']))
        return dict(status="success", msg="Timestep saved")
    else:
        return template("runner_form", mode="nodenet", action="/config/nodenet/runner", value=runtime.get_nodenetrunner_timestep())


@route("/config/world/runner")
@route("/config/world/runner", method="POST")
def edit_worldrunner():
    user_id, permissions, token = get_request_data()
    if len(request.params) > 0:
        runtime.set_worldrunner_timestep(int(request.params['runner_timestep']))
        return dict(status="success", msg="Timestep saved")
    else:
        return template("runner_form", mode="world", action="/config/world/runner", value=runtime.get_worldrunner_timestep())


@rpc("select_nodenet")
def select_nodenet(nodenet_uid):
    result, msg = runtime.load_nodenet(nodenet_uid)
    if result:
        return dict(Status="OK")
    else:
        return dict(Error=msg)


@rpc("load_nodenet")
def load_nodenet(nodenet_uid, **coordinates):
    result, uid = runtime.load_nodenet(nodenet_uid)
    if not result:
        return dict(Error=uid)
    data = runtime.get_nodenet_data(nodenet_uid, **coordinates)
    data['nodetypes'] = runtime.get_available_node_types(nodenet_uid)
    return data


@rpc("generate_uid")
def generate_uid():
    return micropsi_core.tools.generate_uid()


@rpc("get_available_nodenets")
def get_available_nodenets(user_id):
    return runtime.get_available_nodenets(user_id)


@route("/create_new_nodenet_form")
def create_new_nodenet_form():
    user_id, permissions, token = get_request_data()
    nodenets = runtime.get_available_nodenets()
    worlds = runtime.get_available_worlds()
    return template("nodenet_form", user_id=user_id, template="None",
        nodenets=nodenets, worlds=worlds)


@route("/create_worldadapter_selector/<world_uid>")
def create_worldadapter_selector(world_uid):
    nodenets = runtime.get_available_nodenets()
    worlds = runtime.get_available_worlds()
    return template("worldadapter_selector", world_uid=world_uid,
        nodenets=nodenets, worlds=worlds)


@rpc("delete_nodenet", permission_required="manage nodenets")
def delete_nodenet(nodenet_uid):
    return runtime.delete_nodenet(nodenet_uid)


@rpc("set_nodenet_properties", permission_required="manage nodenets")
def set_nodenet_properties(nodenet_uid, nodenet_name=None, worldadapter=None, world_uid=None, owner=None):
    return runtime.set_nodenet_properties(nodenet_uid, nodenet_name=nodenet_name, worldadapter=worldadapter, world_uid=world_uid, owner=owner)


@rpc("set_node_state")
def set_node_state(nodenet_uid, node_uid, state):
    if state == "":
        state = None
    return runtime.set_node_state(nodenet_uid, node_uid, state)


@rpc("set_node_activation")
def set_node_activation(nodenet_uid, node_uid, activation):
    return runtime.set_node_activation(nodenet_uid, node_uid, activation)


@rpc("start_nodenetrunner", permission_required="manage nodenets")
def start_nodenetrunner(nodenet_uid):
    return runtime.start_nodenetrunner(nodenet_uid)


@rpc("set_nodenetrunner_timestep", permission_required="manage nodenets")
def set_nodenetrunner_timestep(timestep):
    return runtime.set_nodenetrunner_timestep(timestep)


@rpc("get_nodenetrunner_timestep", permission_required="manage server")
def get_nodenetrunner_timestep():
    return runtime.get_nodenetrunner_timestep()


@rpc("get_is_nodenet_running")
def get_is_nodenet_running(nodenet_uid):
    return runtime.get_is_nodenet_running(nodenet_uid)


@rpc("stop_nodenetrunner", permission_required="manage nodenets")
def stop_nodenetrunner(nodenet_uid):
    return runtime.stop_nodenetrunner(nodenet_uid)


@rpc("step_nodenet", permission_required="manage nodenets")
def step_nodenet(nodenet_uid, nodespace=None):
    return runtime.step_nodenet(nodenet_uid, nodespace)


@rpc("revert_nodenet", permission_required="manage nodenets")
def revert_nodenet(nodenet_uid):
    return runtime.revert_nodenet(nodenet_uid)


@rpc("save_nodenet", permission_required="manage nodenets")
def save_nodenet(nodenet_uid):
    return runtime.save_nodenet(nodenet_uid)


@rpc("export_nodenet")
def export_nodenet_rpc(nodenet_uid):
    return runtime.export_nodenet(nodenet_uid)


@rpc("import_nodenet", permission_required="manage nodenets")
def import_nodenet(nodenet_uid, nodenet): return runtime.import_nodenet


@rpc("merge_nodenet", permission_required="manage nodenets")
def merge_nodenet(nodenet_uid, nodenet): return runtime.merge_nodenet


# World
@rpc("get_available_worlds")
def get_available_worlds(user_id=None):
    data = {}
    for uid, world in runtime.get_available_worlds(user_id).items():
        data[uid] = {'name': world.name}  # fixme
    return data


@rpc("get_world_properties")
def get_world_properties(world_uid):
    try:
        return runtime.get_world_properties(world_uid)
    except KeyError:
        return {'Error': 'World %s not found' % world_uid}


@rpc("get_worldadapters")
def get_worldadapters(world_uid):
    return runtime.get_worldadapters(world_uid)


@rpc("get_world_objects")
def get_world_objects(world_uid, type=None):
    try:
        return runtime.get_world_objects(world_uid, type)
    except KeyError:
        return {'Error': 'World %s not found' % world_uid}


@rpc("add_worldobject")
def add_worldobject(world_uid, type, position, orientation=0.0, name="", parameters=None, uid=None):
    result, uid = runtime.add_worldobject(world_uid, type, position, orientation=orientation, name=name, parameters=parameters, uid=uid)
    if result:
        return dict(status="success", uid=uid)
    else:
        return dict(status="error", msg=uid)


@rpc("delete_worldobject")
def delete_worldobject(world_uid, object_uid):
    result = runtime.delete_worldobject(world_uid, object_uid)
    if result:
        return dict(status="success")
    else:
        return dict(status="error")


@rpc("set_worldobject_properties")
def set_worldobject_properties(world_uid, uid, type=None, position=None, orientation=None, name=None, parameters=None):
    if runtime.set_worldobject_properties(world_uid, uid, type, position, orientation, name, parameters):
        return dict(status="success")
    else:
        return dict(status="error", msg="unknown world or world object")


@rpc("set_worldagent_properties")
def set_worldagent_properties(world_uid, uid, position=None, orientation=None, name=None, parameters=None):
    if runtime.set_worldagent_properties(world_uid, uid, position, orientation, name, parameters):
        return dict(status="success")
    else:
        return dict(status="error", msg="unknown world or world object")


@rpc("new_world", permission_required="manage worlds")
def new_world(world_name, world_type, owner=""):
    return runtime.new_world(world_name, world_type, owner)


@rpc("get_available_world_types")
def get_available_world_types():
    return runtime.get_available_worldtypes()


@rpc("delete_world", permission_required="manage worlds")
def delete_world(world_uid):
    return runtime.delete_world(world_uid)


@rpc("get_world_view")
def get_world_view(world_uid, step):
    try:
        return runtime.get_world_view(world_uid, step)
    except KeyError:
        return {'Error': 'World %s not found' % world_uid}


@rpc("set_world_properties", permission_required="manage worlds")
def set_world_data(world_uid, world_name=None, world_type=None, owner=None): return runtime.set_world_properties


@rpc("start_worldrunner", permission_required="manage worlds")
def start_worldrunner(world_uid):
    return runtime.start_worldrunner(world_uid)


@rpc("get_worldrunner_timestep")
def get_worldrunner_timestep():
    return runtime.get_worldrunner_timestep()


@rpc("get_is_world_running")
def get_is_world_running(world_uid):
    return runtime.get_is_world_running(world_uid)


@rpc("set_worldrunner_timestep", permission_required="manage server")
def set_worldrunner_timestep():
    return runtime.set_worldrunner_timestep()


@rpc("stop_worldrunner", permission_required="manage worlds")
def stop_worldrunner(world_uid):
    return runtime.stop_worldrunner(world_uid)


@rpc("step_world", permission_required="manage worlds")
def step_world(world_uid, return_world_view=False):
    return runtime.step_world(world_uid, return_world_view)


@rpc("revert_world", permission_required="manage worlds")
def revert_world(world_uid):
    return runtime.revert_world(world_uid)


@rpc("save_world", permission_required="manage worlds")
def save_world(world_uid):
    return runtime.save_world(world_uid)


@rpc("export_world")
def export_world_rpc(world_uid):
    return runtime.export_world(world_uid)


@rpc("import_world", permission_required="manage worlds")
def import_world_rpc(world_uid, worlddata):
    return runtime.import_world(world_uid, worlddata)


# Logging
#@rpc("get_logs")
@route("/get_logs")
@route("/get_logs/<logger>")
@route("/get_logs/<logger>/<after>")
def get_logs(logger="*", after=0):
    return micropsi_logging.get_logs(logger, int(after))


# Monitor

@rpc("add_gate_monitor")
def add_gate_monitor(nodenet_uid, node_uid, gate):
    return runtime.add_gate_monitor(nodenet_uid, node_uid, gate)


@rpc("add_slot_monitor")
def add_slot_monitor(nodenet_uid, node_uid, slot):
    return runtime.add_slot_monitor(nodenet_uid, node_uid, slot)


@rpc("remove_monitor")
def remove_monitor(nodenet_uid, monitor_uid):
    try:
        runtime.remove_monitor(nodenet_uid, monitor_uid)
        return dict(status='success')
    except KeyError:
        return dict(status='error', msg='unknown nodenet or monitor')


@rpc("clear_monitor")
def clear_monitor(nodenet_uid, monitor_uid):
    try:
        runtime.clear_monitor(nodenet_uid, monitor_uid)
        return dict(status='success')
    except KeyError:
        return dict(status='error', msg='unknown nodenet or monitor')


@rpc("export_monitor_data")
def export_monitor_data(nodenet_uid, monitor_uid=None):
    return runtime.export_monitor_data(nodenet_uid, monitor_uid)


@rpc("get_monitor_data")
def get_monitor_data(nodenet_uid, step):
    return runtime.get_monitor_data(nodenet_uid, step)

# Nodenet

@rpc("get_nodespace_list")
def get_nodespace_list(nodenet_uid):
    """ returns a list of nodespaces in the given nodenet."""
    return runtime.get_nodespace_list(nodenet_uid)


@rpc("get_nodespace")
def get_nodespace(nodenet_uid, nodespace, step, **coordinates):
    return runtime.get_nodespace(nodenet_uid, nodespace, step, **coordinates)


@rpc("get_node")
def get_node(nodenet_uid, node_uid):
    return runtime.get_node(nodenet_uid, node_uid)


@rpc("add_node", permission_required="manage nodenets")
def add_node(nodenet_uid, type, pos, nodespace, state=None, uid=None, name="", parameters={}):
    result, uid = runtime.add_node(nodenet_uid, type, pos, nodespace, state=state, uid=uid, name=name, parameters=parameters)
    if result:
        return dict(status="success", uid=uid)
    else:
        return dict(status="error", msg=uid)


@rpc("set_node_position", permission_required="manage nodenets")
def set_node_position(nodenet_uid, node_uid, pos):
    return runtime.set_node_position(nodenet_uid, node_uid, pos)


@rpc("set_node_name", permission_required="manage nodenets")
def set_node_name(nodenet_uid, node_uid, name):
    return runtime.set_node_name(nodenet_uid, node_uid, name)


@rpc("delete_node", permission_required="manage nodenets")
def delete_node(nodenet_uid, node_uid):
    return runtime.delete_node(nodenet_uid, node_uid)


@rpc("align_nodes", permission_required="manage nodenets")
def align_nodes(nodenet_uid, nodespace):
    return runtime.align_nodes(nodenet_uid, nodespace)


@rpc("get_available_node_types")
def get_available_node_types(nodenet_uid=None):
    return runtime.get_available_node_types(nodenet_uid)


@rpc("get_available_native_module_types")
def get_available_native_module_types(nodenet_uid):
    return runtime.get_available_native_module_types(nodenet_uid)


@rpc("get_nodefunction")
def get_nodefunction(nodenet_uid, node_type):
    return runtime.get_nodefunction(nodenet_uid, node_type)


@rpc("set_nodefunction", permission_required="manage nodenets")
def set_nodefunction(nodenet_uid, node_type, nodefunction=None):
    return runtime.set_nodefunction(nodenet_uid, node_type, nodefunction)


@rpc("set_node_parameters", permission_required="manage nodenets")
def set_node_parameters(nodenet_uid, node_uid, parameters):
    return runtime.set_node_parameters(nodenet_uid, node_uid, parameters)


@rpc("add_node_type", permission_required="manage nodenets")
def add_node_type(nodenet_uid, node_type, slots=[], gates=[], node_function=None, parameters=[]):
    return runtime.add_node_type(nodenet_uid, node_type, slots, gates, node_function, parameters)


@rpc("delete_node_type", permission_required="manage nodenets")
def delete_node_type(nodenet_uid, node_type):
    return runtime.delete_node_type(nodenet_uid, node_type)


@rpc("get_slot_types")
def get_slot_types(nodenet_uid, node_type):
    return runtime.get_slot_types(nodenet_uid, node_type)


@rpc("get_gate_types")
def get_gate_types(nodenet_uid, node_type):
    return runtime.get_gate_types(nodenet_uid, node_type)


@rpc("get_gate_function")
def get_gate_function(nodenet_uid, nodespace, node_type, gate_type):
    try:
        return runtime.get_gate_function(nodenet_uid, nodespace, node_type, gate_type)
    except KeyError:
        return dict(status='error', msg='Unknown nodenet or nodespace')


@rpc("set_gate_function", permission_required="manage nodenets")
@rpc("set_gate_function", permission_required="manage nodenets", method="POST")
def set_gate_function(nodenet_uid, nodespace, node_type, gate_type, gate_function=None, parameters=None):
    try:
        return runtime.set_gate_function(nodenet_uid, nodespace, node_type, gate_type, gate_function=gate_function)
    except KeyError:
        return dict(status='error', msg='Unknown nodenet or nodespace')


@rpc("set_gate_parameters", permission_required="manage nodenets")
def set_gate_parameters(nodenet_uid, node_uid, gate_type, parameters):
    return runtime.set_gate_parameters(nodenet_uid, node_uid, gate_type, parameters)


@rpc("get_available_datasources")
def get_available_datasources(nodenet_uid):
    return runtime.get_available_datasources(nodenet_uid)


@rpc("get_available_datatargets")
def get_available_datatargets(nodenet_uid):
    return runtime.get_available_datatargets(nodenet_uid)


@rpc("bind_datasource_to_sensor", permission_required="manage nodenets")
def bind_datasource_to_sensor(nodenet_uid, sensor_uid, datasource):
    return runtime.bind_datasource_to_sensor(nodenet_uid, sensor_uid, datasource)


@rpc("bind_datatarget_to_actor", permission_required="manage nodenets")
def bind_datatarget_to_actor(nodenet_uid, actor_uid, datatarget):
    return runtime.bind_datatarget_to_actor(nodenet_uid, actor_uid, datatarget)


@rpc("add_link", permission_required="manage nodenets")
def add_link(nodenet_uid, source_node_uid, gate_type, target_node_uid, slot_type, weight, uid):
    return runtime.add_link(nodenet_uid, source_node_uid, gate_type, target_node_uid, slot_type, weight=weight, uid=uid)


@rpc("set_link_weight", permission_required="manage nodenets")
def set_link_weight(nodenet_uid, link_uid, weight, certainty=1):
    return runtime.set_link_weight(nodenet_uid, link_uid, weight, certainty)


@rpc("get_link")
def get_link(nodenet_uid, link_uid):
    return runtime.get_link(nodenet_uid, link_uid)


@rpc("delete_link", permission_required="manage nodenets")
def delete_link(nodenet_uid, link_uid):
    return runtime.delete_link(nodenet_uid, link_uid)


@rpc("reload_native_modules", permission_required="manage nodenets")
def reload_native_modules(nodenet_uid=None):
    return runtime.reload_native_modules(nodenet_uid)


# -----------------------------------------------------------------------------------------------

def main(host=DEFAULT_HOST, port=DEFAULT_PORT):
    run(host=host, port=port, quiet=True)  # devV

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Start the %s server." % APPTITLE)
    parser.add_argument('-d', '--host', type=str, default=DEFAULT_HOST)
    parser.add_argument('-p', '--port', type=int, default=DEFAULT_PORT)
    args = parser.parse_args()
    main(host=args.host, port=args.port)
