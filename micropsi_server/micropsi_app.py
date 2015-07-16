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
from micropsi_core import tools
from micropsi_core import emoexpression

import micropsi_core.tools
from micropsi_server import usermanagement
from micropsi_server import bottle
from micropsi_server.bottle import Bottle, run, request, response, template, static_file, redirect
import argparse
import os
import json
import inspect
from micropsi_server import minidoc
import logging

from configuration import config as cfg

VERSION = cfg['micropsi2']['version']
APPTITLE = cfg['micropsi2']['apptitle']

APP_PATH = os.path.dirname(__file__)

micropsi_app = Bottle()

bottle.debug(cfg['micropsi2'].get('debug', False))  # devV

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

    This will return a JSON object, containing `status` and `data`
    status will either be "success" or "error", and data can be either empty, contain the requested information, or the error message, if status==error
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
        @micropsi_app.route(route_prefix + command, "POST")
        @micropsi_app.route(route_prefix + command + "()", method)
        @micropsi_app.route(route_prefix + command + "(:argument#.+#)", method)
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
                except (IndexError, ValueError) as err:
                    response.status = 400
                    return {'status': 'error', 'data': "Malformed arguments for remote procedure call: %s" % str(err)}
            else:
                try:
                    kwargs = request.json
                except ValueError:
                    if len(request.params) > 0:
                        kwargs = dict((key.strip('[]'), json.loads(val)) for key, val in request.params.iteritems())
            user_id, permissions, token = get_request_data()
            if permission_required and permission_required not in permissions:
                response.status = 401
                return {'status': 'error', 'data': "Insufficient permissions for remote procedure call"}
            else:
                # kwargs.update({"argument": argument, "permissions": permissions, "user_id": user_id, "token": token})
                if kwargs is not None:
                    arguments = dict((name, kwargs[name]) for name in inspect.getargspec(func).args if name in kwargs)
                    arguments.update(kwargs)
                else:
                    arguments = {}
                try:
                    result = func(**arguments)
                    if isinstance(result, tuple):
                        state, data = result
                    else:
                        state, data = result, None
                    return json.dumps({
                        'status': 'success' if state else 'error',
                        'data': data
                    })
                except Exception as err:
                    response.status = 500
                    import traceback
                    logging.getLogger('system').error("Error: " + str(err) + " \n " + traceback.format_exc())
                    return {'status': 'error', 'data': str(err), 'traceback': traceback.format_exc()}

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


@micropsi_app.route('/static/<filepath:path>')
def server_static(filepath):
    return static_file(filepath, root=os.path.join(APP_PATH, 'static'))


@micropsi_app.route("/")
def index():
    first_user = usermanager.users == {}
    user_id, permissions, token = get_request_data()
    return _add_world_list("viewer", mode="all", first_user=first_user, logging_levels=runtime.get_logging_levels(), version=VERSION, user_id=user_id, permissions=permissions)


@micropsi_app.route("/nodenet")
def nodenet():
    user_id, permissions, token = get_request_data()
    return template("viewer", mode="nodenet", version=VERSION, user_id=user_id, permissions=permissions)


@micropsi_app.route("/monitors")
def monitors():
    user_id, permissions, token = get_request_data()
    return template("viewer", mode="monitors", logging_levels=runtime.get_logging_levels(), version=VERSION, user_id=user_id, permissions=permissions)


@micropsi_app.route('/minidoc/<filepath:path>')
def document(filepath):
    return template("minidoc",
        navi=minidoc.get_navigation(),
        content=minidoc.get_documentation_body(filepath), title="Minidoc: " + filepath)


@micropsi_app.route("/world")
def world():
    user_id, permissions, token = get_request_data()
    return _add_world_list("viewer", mode="world", version=VERSION, user_id=user_id, permissions=permissions)


@micropsi_app.error(404)
def error_page(error):
    if request.is_xhr:
        response.content_type = "application/json"
        return json.dumps({
            "status": "error",
            "data": "Function not found"
        })
    return template("error.tpl", error=error, msg="Page not found.", img="/static/img/brazil.gif")


@micropsi_app.error(405)
def error_page_405(error):
    if request.is_xhr:
        response.content_type = "application/json"
        return json.dumps({
            "status": "error",
            "data": "Method not allowed"
        })
    return template("error.tpl", error=error, msg="Method not allowed.", img="/static/img/strangelove.gif")


@micropsi_app.error(500)
def error_page_500(error):
    return template("error.tpl", error=error, msg="Internal server error.", img="/static/img/brainstorm.gif")


@micropsi_app.route("/about")
def about():
    user_id, permissions, token = get_request_data()
    return template("about", version=VERSION, user_id=user_id, permissions=permissions)


@micropsi_app.route("/docs")
def documentation():
    return template("documentation", version=VERSION)


@micropsi_app.route("/contact")
def contact():
    return template("contact", version=VERSION)


@micropsi_app.route("/logout")
def logout():
    user_id, permissions, token = get_request_data()
    usermanager.end_session(token)
    response.delete_cookie("token")
    redirect("/")


@micropsi_app.route("/login")
def login():
    if not usermanager.users:  # create first user
        return template("signup", version=VERSION, first_user=True, userid="admin",
            title="Create the administrator for the %s server" % APPTITLE)

    return template("login",
        title="Log in to the %s server" % APPTITLE,
        version=VERSION,
        user_id=usermanager.get_user_id_for_session_token(None),
        permissions=usermanager.get_permissions_for_session_token(None))


@micropsi_app.post("/login_submit")
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


@micropsi_app.route("/signup")
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


@micropsi_app.post("/signup_submit")
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


@micropsi_app.route("/change_password")
def change_password():
    user_id, permissions, token = get_request_data()
    if token:
        return template("change_password", title="Change password", version=VERSION, user_id=user_id, permissions=permissions)
    else:
        return dict(status="error", msg="Cannot change password outside of a session")


@micropsi_app.post("/change_password_submit")
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


@micropsi_app.route("/user_mgt")
def user_mgt():
    user_id, permissions, token = get_request_data()
    if "manage users" in permissions:
        return template("user_mgt", version=VERSION, permissions=permissions,
            user_id=user_id,
            userlist=usermanager.list_users())
    return template("error", msg="Insufficient rights to access user console")


@micropsi_app.route("/set_permissions/<user_key>/<role>")
def set_permissions(user_key, role):
    user_id, permissions, token = get_request_data()
    if "manage users" in permissions:
        if user_key in usermanager.users and role in usermanagement.USER_ROLES:
            usermanager.set_user_role(user_key, role)
        redirect('/user_mgt')
    return template("error", msg="Insufficient rights to access user console")


@micropsi_app.route("/create_user")
def create_user():
    user_id, permissions, token = get_request_data()
    if "manage users" in permissions:
        return template("create_user", version=VERSION, user_id=user_id,
            title="Create a user for the %s server" % APP_PATH, permissions=permissions)
    return template("error", msg="Insufficient rights to access user console")


@micropsi_app.post("/create_user_submit")
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


@micropsi_app.route("/set_password/<userid>")
def set_password(userid):
    user_id, permissions, token = get_request_data()
    if "manage users" in permissions:
        return template("set_password", version=VERSION, permissions=permissions,
            title="Change Password",
            user_id=user_id,
            userid=userid)
    return template("error", msg="Insufficient rights to access user console")


@micropsi_app.post("/set_password_submit")
def set_password_submit():
    user_id, permissions, token = get_request_data()
    if "manage users" in permissions:
        userid = request.forms.userid
        password = request.forms.password
        if userid in usermanager.users:
            usermanager.set_user_password(userid, password)
        return dict(status='success', msg="New password saved")
    return dict(status="error", msg="Insufficient rights to access user console")


@micropsi_app.route("/delete_user/<userid>")
def delete_user(userid):
    user_id, permissions, token = get_request_data()
    if "manage users" in permissions:
        if userid in usermanager.users:
            usermanager.delete_user(userid)
        redirect("/user_mgt")
    return template("error", msg="Insufficient rights to access user console")


@micropsi_app.route("/login_as/<userid>")
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


@micropsi_app.route("/nodenet_mgt")
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


@micropsi_app.route("/select_nodenet_from_console/<nodenet_uid>")
def select_nodenet_from_console(nodenet_uid):
    user_id, permissions, token = get_request_data()
    result, uid = runtime.load_nodenet(nodenet_uid)
    if not result:
        return template("error", msg="Could not select nodenet")
    response.set_cookie("selected_nodenet", nodenet_uid, path="/")
    redirect("/")


@micropsi_app.route("/delete_nodenet_from_console/<nodenet_uid>")
def delete_nodenet_from_console(nodenet_uid):
    user_id, permissions, token = get_request_data()
    if "manage nodenets" in permissions:
        runtime.delete_nodenet(nodenet_uid)
        response.set_cookie('notification', '{"msg":"Nodenet deleted", "status":"success"}', path='/')
        redirect('/nodenet_mgt')
    return template("error", msg="Insufficient rights to access nodenet console")


@micropsi_app.route("/save_all_nodenets")
def save_all_nodenets():
    user_id, permissions, token = get_request_data()
    if "manage nodenets" in permissions:
        for uid in runtime.nodenets:
            runtime.save_nodenet(uid)
        response.set_cookie('notification', '{"msg":"All nodenets saved", "status":"success"}', path='/')
        redirect('/nodenet_mgt')
    return template("error", msg="Insufficient rights to access nodenet console")


@micropsi_app.route("/nodenet/import")
def import_nodenet_form():
    token = request.get_cookie("token")
    return template("upload.tpl", title='Import Nodenet', message='Select a file to upload and use for importing', action='/nodenet/import',
        version=VERSION,
        userid=usermanager.get_user_id_for_session_token(token),
        permissions=usermanager.get_permissions_for_session_token(token))


@micropsi_app.route("/nodenet/import", method="POST")
def import_nodenet():
    user_id, p, t = get_request_data()
    data = request.files['file_upload'].file.read()
    data = data.decode('utf-8')
    nodenet_uid = runtime.import_nodenet(data, owner=user_id)
    return dict(status='success', msg="Nodenet imported", nodenet_uid=nodenet_uid)


@micropsi_app.route("/nodenet/merge/<nodenet_uid>")
def merge_nodenet_form(nodenet_uid):
    token = request.get_cookie("token")
    return template("upload.tpl", title='Merge Nodenet', message='Select a file to upload and use for merging',
        action='/nodenet/merge/%s' % nodenet_uid,
        version=VERSION,
        userid=usermanager.get_user_id_for_session_token(token),
        permissions=usermanager.get_permissions_for_session_token(token))


@micropsi_app.route("/nodenet/merge/<nodenet_uid>", method="POST")
def merge_nodenet(nodenet_uid):
    data = request.files['file_upload'].file.read()
    data = data.decode('utf-8')
    runtime.merge_nodenet(nodenet_uid, data)
    return dict(status='success', msg="Nodenet merged")


@micropsi_app.route("/nodenet/export/<nodenet_uid>")
def export_nodenet(nodenet_uid):
    response.set_header('Content-type', 'application/json')
    response.set_header('Content-Disposition', 'attachment; filename="nodenet.json"')
    return runtime.export_nodenet(nodenet_uid)


@micropsi_app.route("/nodenet/edit")
def edit_nodenet():
    user_id, permissions, token = get_request_data()
    # nodenet_id = request.params.get('id', None)
    title = 'Edit Nodenet' if id is not None else 'New Nodenet'

    theano_available = True
    try:
        import theano
    except ImportError:
        theano_available = False

    return template("nodenet_form.tpl", title=title,
        # nodenet_uid=nodenet_uid,
        nodenets=runtime.get_available_nodenets(),
        templates=runtime.get_available_nodenets(),
        worlds=runtime.get_available_worlds(),
        version=VERSION, user_id=user_id, permissions=permissions, theano_available=theano_available)


@micropsi_app.route("/nodenet/edit", method="POST")
def write_nodenet():
    user_id, permissions, token = get_request_data()
    if "manage nodenets" in permissions:
        result, nodenet_uid = runtime.new_nodenet(request.params['nn_name'], engine=request.params['nn_engine'], worldadapter=request.params['nn_worldadapter'], template=request.params.get('nn_template'), owner=user_id, world_uid=request.params.get('nn_world'))
        if result:
            return dict(status="success", msg="Nodenet created", nodenet_uid=nodenet_uid)
        else:
            return dict(status="error", msg="Error saving nodenet: %s" % nodenet_uid)
    return dict(status="error", msg="Insufficient rights to write nodenet")


@micropsi_app.route("/world/import")
def import_world_form():
    token = request.get_cookie("token")
    return template("upload.tpl", title='World import', message='Select a file to upload and use for importing',
        action='/world/import',
        version=VERSION,
        user_id=usermanager.get_user_id_for_session_token(token),
        permissions=usermanager.get_permissions_for_session_token(token))


@micropsi_app.route("/world/import", method="POST")
def import_world():
    user_id, p, t = get_request_data()
    data = request.files['file_upload'].file.read()
    data = data.decode('utf-8')
    world_uid = runtime.import_world(data, owner=user_id)
    return dict(status='success', msg="World imported", world_uid=world_uid)


@micropsi_app.route("/world/export/<world_uid>")
def export_world(world_uid):
    response.set_header('Content-type', 'application/json')
    response.set_header('Content-Disposition', 'attachment; filename="world.json"')
    return runtime.export_world(world_uid)


@micropsi_app.route("/world/edit")
def edit_world_form():
    token = request.get_cookie("token")
    id = request.params.get('id', None)
    title = 'Edit World' if id is not None else 'New World'
    return template("world_form.tpl", title=title, worldtypes=runtime.get_available_world_types(),
        version=VERSION,
        user_id=usermanager.get_user_id_for_session_token(token),
        permissions=usermanager.get_permissions_for_session_token(token))


@micropsi_app.route("/world/edit", method="POST")
def edit_world():
    user_id, permissions, token = get_request_data()
    if "manage worlds" in permissions:
        result, uid = runtime.new_world(request.params['world_name'], request.params['world_type'], user_id)
        if result:
            return dict(status="success", msg="World created", world_uid=uid)
        else:
            return dict(status="error", msg=": %s" % result)
    return dict(status="error", msg="Insufficient rights to create world")


@micropsi_app.route("/nodenet_list/")
@micropsi_app.route("/nodenet_list/<current_nodenet>")
def nodenet_list(current_nodenet=None):
    user_id, permissions, token = get_request_data()
    nodenets = runtime.get_available_nodenets()
    return template("nodenet_list", type="nodenet", user_id=user_id,
        current=current_nodenet,
        mine=dict((uid, nodenets[uid]) for uid in nodenets if nodenets[uid].owner == user_id),
        others=dict((uid, nodenets[uid]) for uid in nodenets if nodenets[uid].owner != user_id))


@micropsi_app.route("/world_list/")
@micropsi_app.route("/world_list/<current_world>")
def world_list(current_world=None):
    user_id, permissions, token = get_request_data()
    worlds = runtime.get_available_worlds()
    return template("nodenet_list", type="world", user_id=user_id,
        current=current_world,
        mine=dict((uid, worlds[uid]) for uid in worlds if worlds[uid].owner == user_id),
        others=dict((uid, worlds[uid]) for uid in worlds if worlds[uid].owner != user_id))


@micropsi_app.route("/config/runner")
@micropsi_app.route("/config/runner", method="POST")
def edit_runner_properties():
    user_id, permissions, token = get_request_data()
    if len(request.params) > 0:
        runtime.set_runner_properties(int(request.params['timestep']), int(request.params['factor']))
        return dict(status="success", msg="Settings saved")
    else:
        return template("runner_form", action="/config/runner", value=runtime.get_runner_properties())


@micropsi_app.route("/create_new_nodenet_form")
def create_new_nodenet_form():
    user_id, permissions, token = get_request_data()
    nodenets = runtime.get_available_nodenets()
    worlds = runtime.get_available_worlds()
    return template("nodenet_form", user_id=user_id, template="None",
        nodenets=nodenets, worlds=worlds)


@micropsi_app.route("/create_worldadapter_selector/<world_uid>")
def create_worldadapter_selector(world_uid):
    nodenets = runtime.get_available_nodenets()
    worlds = runtime.get_available_worlds()
    return template("worldadapter_selector", world_uid=world_uid,
        nodenets=nodenets, worlds=worlds)


@micropsi_app.route("/face")
def show_face():
    user_id, permissions, token = get_request_data()
    return template("viewer", mode="face", user_id=user_id, permissions=permissions, token=token, version=VERSION)


#################################################################
#
#
#         ##   #####   #####    ##   ##
#         ##  ##      ##   ##   ###  ##
#         ##  ###### ##     ##  ## # ##
#         ##      ##  ##   ##   ##  ###
#        ##   #####    #####    ##   ##
#
#
#################################################################


@rpc("select_nodenet")
def select_nodenet(nodenet_uid):
    return runtime.load_nodenet(nodenet_uid)


@rpc("load_nodenet")
def load_nodenet(nodenet_uid, nodespace='Root', include_links=True):
    result, uid = runtime.load_nodenet(nodenet_uid)
    if result:
        data = runtime.get_nodenet_data(nodenet_uid, nodespace, -1, include_links)
        data['nodetypes'] = runtime.get_available_node_types(nodenet_uid)
        data['recipes'] = runtime.get_available_recipes()
        return True, data
    else:
        return False, uid


@rpc("new_nodenet")
def new_nodenet(name, owner=None, engine='dict_engine', template=None, worldadapter=None, world_uid=None):
    if owner is None:
        owner, _, _ = get_request_data()
    return runtime.new_nodenet(
        name,
        engine=engine,
        worldadapter=worldadapter,
        template=template,
        owner=owner,
        world_uid=world_uid)


@rpc("get_current_state")
def get_current_state(nodenet_uid, nodenet=None, world=None, monitors=None):
    data = {}
    nodenet_obj = runtime.get_nodenet(nodenet_uid)
    if nodenet_obj is not None:
        if nodenet_uid in runtime.MicropsiRunner.conditions:
            data['simulation_condition'] = runtime.MicropsiRunner.conditions[nodenet_uid]
            if 'monitor' in data['simulation_condition']:
                data['simulation_condition']['monitor']['color'] = nodenet_obj.get_monitor(data['simulation_condition']['monitor']['uid']).color
        data['simulation_running'] = nodenet_obj.is_active
        data['current_nodenet_step'] = nodenet_obj.current_step
        data['current_world_step'] = nodenet_obj.world.current_step if nodenet_obj.world else 0
        if nodenet is not None:
            data['nodenet'] = runtime.get_nodenet_data(nodenet_uid=nodenet_uid, **nodenet)
        if world is not None and nodenet_obj.world:
            data['world'] = runtime.get_world_view(world_uid=nodenet_obj.world.uid, **world)
        if monitors is not None:
            data['monitors'] = runtime.get_monitoring_info(nodenet_uid=nodenet_uid, **monitors)
        return True, data
    else:
        return False, "No such nodenet"


@rpc("generate_uid")
def generate_uid():
    return True, tools.generate_uid()


@rpc("get_available_nodenets")
def get_available_nodenets(user_id):
    if user_id not in usermanager.users:
        return False, 'User not found'
    return True, runtime.get_available_nodenets(user_id)


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


@rpc("start_simulation", permission_required="manage nodenets")
def start_simulation(nodenet_uid):
    return runtime.start_nodenetrunner(nodenet_uid)


@rpc("set_runner_condition", permission_required="manage nodenets")
def set_runner_condition(nodenet_uid, steps=-1, monitor=None):
    if monitor and 'value' in monitor:
        monitor['value'] = float(monitor['value'])
    if steps:
        steps = int(steps)
        if steps < 0:
            steps = None
    return runtime.set_runner_condition(nodenet_uid, monitor, steps)


@rpc("remove_runner_condition", permission_required="manage nodenets")
def remove_runner_condition(nodenet_uid):
    return runtime.remove_runner_condition(nodenet_uid)


@rpc("set_runner_properties", permission_required="manage server")
def set_runner_properties(timestep, factor):
    return runtime.set_runner_properties(timestep, factor)


@rpc("get_runner_properties")
def get_runner_properties():
    return True, runtime.get_runner_properties()


@rpc("get_is_simulation_running")
def get_is_simulation_running(nodenet_uid):
    return True, runtime.get_is_nodenet_running(nodenet_uid)


@rpc("stop_simulation", permission_required="manage nodenets")
def stop_simulation(nodenet_uid):
    return runtime.stop_nodenetrunner(nodenet_uid)


@rpc("step_simulation", permission_required="manage nodenets")
def step_simulation(nodenet_uid):
    return True, runtime.step_nodenet(nodenet_uid)


@rpc("revert_nodenet", permission_required="manage nodenets")
def revert_nodenet(nodenet_uid):
    return runtime.revert_nodenet(nodenet_uid)


@rpc("save_nodenet", permission_required="manage nodenets")
def save_nodenet(nodenet_uid):
    return runtime.save_nodenet(nodenet_uid)


@rpc("export_nodenet")
def export_nodenet_rpc(nodenet_uid):
    return True, runtime.export_nodenet(nodenet_uid)


@rpc("import_nodenet", permission_required="manage nodenets")
def import_nodenet_rpc(nodenet_data):
    user_id, _, _ = get_request_data()
    return True, runtime.import_nodenet(nodenet_data, user_id)


@rpc("merge_nodenet", permission_required="manage nodenets")
def merge_nodenet_rpc(nodenet_uid, nodenet_data):
    return runtime.merge_nodenet(nodenet_uid, nodenet_data)


# World
@rpc("get_available_worlds")
def get_available_worlds(user_id=None):
    data = {}
    for uid, world in runtime.get_available_worlds(user_id).items():
        data[uid] = {'name': world.name}  # fixme
    return True, data


@rpc("get_world_properties")
def get_world_properties(world_uid):
    try:
        return True, runtime.get_world_properties(world_uid)
    except KeyError:
        return False, 'World %s not found' % world_uid


@rpc("get_worldadapters")
def get_worldadapters(world_uid):
    try:
        return True, runtime.get_worldadapters(world_uid)
    except KeyError:
        return False, 'World %s not found' % world_uid


@rpc("get_world_objects")
def get_world_objects(world_uid, type=None):
    try:
        return True, runtime.get_world_objects(world_uid, type)
    except KeyError:
        return False, 'World %s not found' % world_uid


@rpc("add_worldobject")
def add_worldobject(world_uid, type, position, orientation=0.0, name="", parameters=None, uid=None):
    return runtime.add_worldobject(world_uid, type, position, orientation=orientation, name=name, parameters=parameters, uid=uid)


@rpc("delete_worldobject")
def delete_worldobject(world_uid, object_uid):
    return runtime.delete_worldobject(world_uid, object_uid)


@rpc("set_worldobject_properties")
def set_worldobject_properties(world_uid, uid, position=None, orientation=None, name=None, parameters=None):
    if runtime.set_worldobject_properties(world_uid, uid, position, int(orientation), name, parameters):
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
def new_world(world_name, world_type, owner=None):
    if owner is None:
        owner, _, _ = get_request_data()
    return runtime.new_world(world_name, world_type, owner)


@rpc("get_available_world_types")
def get_available_world_types():
    return True, runtime.get_available_world_types()


@rpc("delete_world", permission_required="manage worlds")
def delete_world(world_uid):
    return runtime.delete_world(world_uid)


@rpc("get_world_view")
def get_world_view(world_uid, step):
    return True, runtime.get_world_view(world_uid, step)


@rpc("set_world_properties", permission_required="manage worlds")
def set_world_data(world_uid, world_name=None, owner=None):
    return runtime.set_world_properties(world_uid, world_name, owner)


@rpc("revert_world", permission_required="manage worlds")
def revert_world(world_uid):
    return runtime.revert_world(world_uid)


@rpc("save_world", permission_required="manage worlds")
def save_world(world_uid):
    return runtime.save_world(world_uid)


@rpc("export_world")
def export_world_rpc(world_uid):
    return True, runtime.export_world(world_uid)


@rpc("import_world", permission_required="manage worlds")
def import_world_rpc(worlddata):
    user_id, _, _ = get_request_data()
    return True, runtime.import_world(worlddata, user_id)


# Monitor

@rpc("add_gate_monitor")
def add_gate_monitor(nodenet_uid, node_uid, gate, sheaf=None, name=None, color=None):
    return True, runtime.add_gate_monitor(nodenet_uid, node_uid, gate, sheaf=sheaf, name=name, color=color)


@rpc("add_slot_monitor")
def add_slot_monitor(nodenet_uid, node_uid, slot, sheaf=None, name=None, color=None):
    return True, runtime.add_slot_monitor(nodenet_uid, node_uid, slot, sheaf=sheaf, name=name, color=color)


@rpc("add_link_monitor")
def add_link_monitor(nodenet_uid, source_node_uid, gate_type, target_node_uid, slot_type, property, name, color=None):
    return True, runtime.add_link_monitor(nodenet_uid, source_node_uid, gate_type, target_node_uid, slot_type, property, name, color=color)


@rpc("add_modulator_monitor")
def add_modulator_monitor(nodenet_uid, modulator, name, color=None):
    return True, runtime.add_modulator_monitor(nodenet_uid, modulator, name, color=color)


@rpc("add_custom_monitor")
def add_custom_monitor(nodenet_uid, function, name, color=None):
    return True, runtime.add_custom_monitor(nodenet_uid, function, name, color=color)


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
    return True, runtime.export_monitor_data(nodenet_uid, monitor_uid)


@rpc("get_monitor_data")
def get_monitor_data(nodenet_uid, step):
    return True, runtime.get_monitor_data(nodenet_uid, step)


# Nodenet

@rpc("get_nodespace_list")
def get_nodespace_list(nodenet_uid):
    """ returns a list of nodespaces in the given nodenet."""
    return True, runtime.get_nodespace_list(nodenet_uid)


@rpc("get_nodespace")
def get_nodespace(nodenet_uid, nodespace, step, include_links=True):
    return True, runtime.get_nodenet_data(nodenet_uid, nodespace, step, include_links)


@rpc("get_node")
def get_node(nodenet_uid, node_uid):
    return True, runtime.get_node(nodenet_uid, node_uid)


@rpc("add_node", permission_required="manage nodenets")
def add_node(nodenet_uid, type, position, nodespace, state=None, name="", parameters={}):
    return runtime.add_node(nodenet_uid, type, position, nodespace, state=state, name=name, parameters=parameters)


@rpc("add_nodespace", permission_required="manage nodenets")
def add_nodespace(nodenet_uid, position, nodespace, name="", options=None):
    return runtime.add_nodespace(nodenet_uid, position, nodespace, name=name, options=options)


@rpc("clone_nodes", permission_required="manage nodenets")
def clone_nodes(nodenet_uid, node_uids, clone_mode="all", nodespace=None, offset=[50, 50]):
    return runtime.clone_nodes(nodenet_uid, node_uids, clone_mode, nodespace=nodespace, offset=offset)


@rpc("set_node_position", permission_required="manage nodenets")
def set_node_position(nodenet_uid, node_uid, position):
    return runtime.set_node_position(nodenet_uid, node_uid, position)


@rpc("set_node_name", permission_required="manage nodenets")
def set_node_name(nodenet_uid, node_uid, name):
    return runtime.set_node_name(nodenet_uid, node_uid, name)


@rpc("delete_node", permission_required="manage nodenets")
def delete_node(nodenet_uid, node_uid):
    return runtime.delete_node(nodenet_uid, node_uid)


@rpc("delete_nodespace", permission_required="manage nodenets")
def delete_nodespace(nodenet_uid, nodespace_uid):
    return runtime.delete_nodespace(nodenet_uid, nodespace_uid)


@rpc("align_nodes", permission_required="manage nodenets")
def align_nodes(nodenet_uid, nodespace):
    return runtime.align_nodes(nodenet_uid, nodespace)


@rpc("generate_netapi_fragment", permission_required="manage nodenets")
def generate_netapi_fragment(nodenet_uid, node_uids):
    return True, runtime.generate_netapi_fragment(nodenet_uid, node_uids)


@rpc("get_available_node_types")
def get_available_node_types(nodenet_uid):
    return True, runtime.get_available_node_types(nodenet_uid)


@rpc("get_available_native_module_types")
def get_available_native_module_types(nodenet_uid):
    return True, runtime.get_available_native_module_types(nodenet_uid)


@rpc("set_node_parameters", permission_required="manage nodenets")
def set_node_parameters(nodenet_uid, node_uid, parameters):
    return runtime.set_node_parameters(nodenet_uid, node_uid, parameters)


@rpc("get_gatefunction")
def get_gatefunction(nodenet_uid, node_uid, gate_type):
    return True, runtime.get_gatefunction(nodenet_uid, node_uid, gate_type)


@rpc("set_gatefunction", permission_required="manage nodenets")
def set_gatefunction(nodenet_uid, node_uid, gate_type, gatefunction=None):
    return runtime.set_gatefunction(nodenet_uid, node_uid, gate_type, gatefunction=gatefunction)


@rpc("get_available_gatefunctions")
def get_available_gatefunctions(nodenet_uid):
    return True, runtime.get_available_gatefunctions(nodenet_uid)


@rpc("set_gate_parameters", permission_required="manage nodenets")
def set_gate_parameters(nodenet_uid, node_uid, gate_type, parameters):
    return runtime.set_gate_parameters(nodenet_uid, node_uid, gate_type, parameters)


@rpc("get_available_datasources")
def get_available_datasources(nodenet_uid):
    return True, runtime.get_available_datasources(nodenet_uid)


@rpc("get_available_datatargets")
def get_available_datatargets(nodenet_uid):
    return True, runtime.get_available_datatargets(nodenet_uid)


@rpc("bind_datasource_to_sensor", permission_required="manage nodenets")
def bind_datasource_to_sensor(nodenet_uid, sensor_uid, datasource):
    return runtime.bind_datasource_to_sensor(nodenet_uid, sensor_uid, datasource)


@rpc("bind_datatarget_to_actor", permission_required="manage nodenets")
def bind_datatarget_to_actor(nodenet_uid, actor_uid, datatarget):
    return runtime.bind_datatarget_to_actor(nodenet_uid, actor_uid, datatarget)


@rpc("add_link", permission_required="manage nodenets")
def add_link(nodenet_uid, source_node_uid, gate_type, target_node_uid, slot_type, weight=1):
    return runtime.add_link(nodenet_uid, source_node_uid, gate_type, target_node_uid, slot_type, weight=weight)


@rpc("set_link_weight", permission_required="manage nodenets")
def set_link_weight(nodenet_uid, source_node_uid, gate_type, target_node_uid, slot_type, weight, certainty=1):
    return runtime.set_link_weight(nodenet_uid, source_node_uid, gate_type, target_node_uid, slot_type, weight, certainty)


@rpc("get_links_for_nodes")
def get_links_for_nodes(nodenet_uid, node_uids=[]):
    return True, runtime.get_links_for_nodes(nodenet_uid, node_uids)


@rpc("delete_link", permission_required="manage nodenets")
def delete_link(nodenet_uid, source_node_uid, gate_type, target_node_uid, slot_type):
    return runtime.delete_link(nodenet_uid, source_node_uid, gate_type, target_node_uid, slot_type)


@rpc("reload_native_modules", permission_required="manage nodenets")
def reload_native_modules():
    return runtime.reload_native_modules()


@rpc("user_prompt_response")
def user_prompt_response(nodenet_uid, node_uid, values, resume_nodenet):
    runtime.user_prompt_response(nodenet_uid, node_uid, values, resume_nodenet)
    return True


# Face
@rpc("get_emoexpression_parameters")
def get_emoexpression_parameters(nodenet_uid):
    nodenet = runtime.get_nodenet(nodenet_uid)
    return True, emoexpression.calc_emoexpression_parameters(nodenet)

# --------- logging --------


@rpc("set_logging_levels")
def set_logging_levels(system=None, world=None, nodenet=None):
    runtime.set_logging_levels(system, world, nodenet)
    return True


@rpc("get_logger_messages")
def get_logger_messages(logger=[], after=0):
    return True, runtime.get_logger_messages(logger, after)


@rpc("get_monitoring_info")
def get_monitoring_info(nodenet_uid, logger=[], after=0):
    data = runtime.get_monitoring_info(nodenet_uid, logger, after)
    return True, data


# --- user scripts ---

@rpc("run_recipe")
def run_recipe(nodenet_uid, name, parameters):
    return runtime.run_recipe(nodenet_uid, name, parameters)


@rpc('get_available_recipes')
def get_available_recipes():
    return True, runtime.get_available_recipes()


# -----------------------------------------------------------------------------------------------

def main(host=None, port=None):
    host = host or cfg['micropsi2']['host']
    port = port or cfg['micropsi2']['port']
    server = cfg['micropsi2']['server']
    print("Starting App on Port " + str(port))
    run(micropsi_app, host=host, port=port, quiet=True, server=server)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Start the %s server." % APPTITLE)
    parser.add_argument('-d', '--host', type=str, default=cfg['micropsi2']['host'])
    parser.add_argument('-p', '--port', type=int, default=cfg['micropsi2']['port'])
    args = parser.parse_args()
    main(host=args.host, port=args.port)
