#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
MicroPsi server application.

This version of MicroPsi is meant to be deployed as a web server, and accessed through a browser.
For local use, simply start this server and point your browser to "http://localhost:6543".
The latter parameter is the default port and can be changed as needed.

The path to the JSON API is `/rpc`
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

INCLUDE_CONSOLE = cfg['micropsi2']['host'] == 'localhost'

APP_PATH = os.path.dirname(__file__)

micropsi_app = Bottle()

bottle.debug(cfg['micropsi2'].get('debug', False))  # devV

bottle.TEMPLATE_PATH.insert(0, os.path.join(APP_PATH, 'view', ''))
bottle.TEMPLATE_PATH.insert(1, os.path.join(APP_PATH, 'static', ''))

bottle.BaseRequest.MEMFILE_MAX = 5 * 1024 * 1024

theano_available = True
try:
    import theano
except ImportError:
    theano_available = False

bottle.BaseTemplate.defaults['theano_available'] = theano_available

# runtime = micropsi_core.runtime.MicroPsiRuntime()
usermanager = usermanagement.UserManager()


def rpc(command, route_prefix="/rpc/", method="GET", permission_required=None):
    # Defines a decorator for accessing API calls. Use it by specifying the
    # API method, followed by the permissions necessary to execute the method.
    # Within the calling web page, use http://<url>/rpc/<method>(arg1="val1", arg2="val2", ...)
    # Import these arguments into your decorated function:
    #     @rpc("my_method")
    #     def this_is_my_method(arg1, arg2):
    #         pass

    # This will return a JSON object, containing `status` and `data`
    # status will either be "success" or "error", and data can be either empty, contain the requested information, or the error message, if status==error
    # The decorated function can optionally import the following parameters (by specifying them in its signature):
    #     argument: the original argument string
    #     token: the current session token
    #     user_id: the id of the user associated with the current session token
    #     permissions: the set of permissions associated with the current session token

    # Arguments:
    #     command: the command against which we want to match
    #     method (optional): the request method
    #     permission_required (optional): the type of permission necessary to execute the method;
    #         if omitted, permissions won't be tested by the decorator

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
                        try:
                            kwargs = dict((key.strip('[]'), json.loads(val)) for key, val in request.params.iteritems())
                        except json.JSONDecodeError:
                            response.status = 400
                            return {'status': 'error', 'data': "Malformed arguments for remote procedure call: %s" % str(request.params.__dict__)}

            user_id, permissions, token = get_request_data()
            if permission_required and permission_required not in permissions:
                response.status = 401
                return {'status': 'error', 'data': "Insufficient permissions for remote procedure call"}
            else:
                # kwargs.update({"argument": argument, "permissions": permissions, "user_id": user_id, "token": token})
                if kwargs is not None:
                    signature = inspect.signature(func)
                    arguments = dict((name, kwargs[name]) for name in signature.parameters if name in kwargs)
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

                    # either drop to debugger in the offending stack frame, or just display a message and the trace.
                    on_exception = cfg['micropsi2'].get('on_exception', None)
                    if on_exception == 'debug':
                        import sys
                        # use the nice ipdb if it is there, but don't throw a fit if it isnt:
                        try:
                            import ipdb as pdb
                        except ImportError:
                            import pdb
                        _, _, tb = sys.exc_info()
                        pdb.post_mortem(tb)
                    else:
                        return {'status': 'error', 'data': str(err), 'traceback': traceback.format_exc()}

                # except TypeError as err:
                #     response.status = 400
                #     return {"Error": "Bad parameters in remote procedure call: %s" % err}
        return _wrapper
    return _decorator


def get_request_data():
    # Helper function to determine the current user, permissions and token
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
    world_type = ""
    world_assets = {}
    world_template = ""
    if current_world:
        world_obj = runtime.load_world(current_world)
        world_type = world_obj.__class__.__name__
        if hasattr(world_obj, 'assets'):
            world_assets = world_obj.assets
        if 'template' in world_assets:
            import inspect
            basedir = os.path.dirname(inspect.getfile(world_obj.__class__))
            with open(os.path.join(basedir, world_assets['template'])) as fp:
                world_template = template(fp.read(), world_assets=world_assets)
    return template(template_name, current=current_world,
        mine=dict((uid, worlds[uid]) for uid in worlds if worlds[uid].get('owner') == params['user_id']),
        others=dict((uid, worlds[uid]) for uid in worlds if worlds[uid].get('owner') != params['user_id']),
        world_type=world_type,
        world_assets=world_assets,
        world_template=world_template,
        **params)


@micropsi_app.route('/static/<filepath:path>')
def server_static(filepath):
    return static_file(filepath, root=os.path.join(APP_PATH, 'static'))


@micropsi_app.route('/world_assets/<wtype>/<filepath:path>')
def server_static_world_asset(wtype, filepath):
    import inspect
    world = runtime.get_world_class_from_name(wtype, case_sensitive=False)
    return static_file(filepath, root=os.path.dirname(inspect.getfile(world)))


@micropsi_app.route("/")
def index():
    first_user = usermanager.users == {}
    user_id, permissions, token = get_request_data()
    return _add_world_list("viewer",
        mode="all",
        first_user=first_user,
        logging_levels=runtime.get_logging_levels(),
        version=VERSION,
        user_id=user_id,
        permissions=permissions,
        console=INCLUDE_CONSOLE)


@micropsi_app.route("/agent")
def nodenet():
    user_id, permissions, token = get_request_data()
    return template("viewer", mode="nodenet", version=VERSION, user_id=user_id, permissions=permissions, console=INCLUDE_CONSOLE)


@micropsi_app.route("/monitors")
def monitors():
    user_id, permissions, token = get_request_data()
    return template("viewer", mode="monitors", logging_levels=runtime.get_logging_levels(), version=VERSION, user_id=user_id, permissions=permissions)


@micropsi_app.route('/minidoc')
def minidoc_base():
    return template("minidoc",
        navi=minidoc.get_navigation(),
        content=minidoc.get_documentation_body(), title="Minidoc")


@micropsi_app.route('/minidoc/<filepath:path>')
def minidoc_file(filepath):
    return template("minidoc",
        navi=minidoc.get_navigation(),
        content=minidoc.get_documentation_body(filepath), title="Minidoc: " + filepath)


@micropsi_app.route('/apidoc')
def apidoc_base():
    return template("minidoc",
        navi=minidoc.get_api_navigation(),
        content=minidoc.get_api_doc(), title="Api Documentation")


@micropsi_app.route('/apidoc/<filepath:path>')
def apidoc_file(filepath):
    return template("minidoc",
        navi=minidoc.get_api_navigation(),
        content=minidoc.get_api_doc(filepath), title="Api Documentation: " + filepath)


@micropsi_app.route("/environment")
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
    return template("error.tpl", error=error, msg="Page not found.")


@micropsi_app.error(405)
def error_page_405(error):
    if request.is_xhr:
        response.content_type = "application/json"
        return json.dumps({
            "status": "error",
            "data": "Method not allowed"
        })
    return template("error.tpl", error=error, msg="Method not allowed.")


@micropsi_app.error(500)
def error_page_500(error):
    return template("error.tpl", error=error, msg="Internal server error.")


@micropsi_app.route("/about")
def about():
    user_id, permissions, token = get_request_data()
    return template("about", version=VERSION, user_id=user_id, permissions=permissions, config=runtime.runtime_info())


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
    params = dict((key, request.forms.getunicode(key)) for key in request.forms)
    user_id = params['userid']
    password = params['password']
    # log in new user
    token = usermanager.start_session(user_id, password, params.get("keep_logged_in"))
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
        first_user=False,
        cookie_warning=(token is None))


@micropsi_app.post("/signup_submit")
def signup_submit():
    params = dict((key, request.forms.getunicode(key)) for key in request.forms)
    user_id, permissions, token = get_request_data()
    userid = params['userid']
    password = params['password']
    role = params.get('permissions')
    firstuser = not usermanager.users
    (success, result) = micropsi_core.tools.check_for_url_proof_id(userid, existing_ids=usermanager.users.keys())
    if success:
        # check if permissions in form are consistent with internal permissions
        if ((role == "Administrator" and ("create admin" in permissions or not usermanager.users)) or
            (role == "Full" and "create full" in permissions) or
            (role == "Restricted" and "create restricted" in permissions)):
            if usermanager.create_user(userid, password, role, uid=micropsi_core.tools.generate_uid()):
                # log in new user
                token = usermanager.start_session(userid, password, params.get("keep_logged_in"))
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
            title="Create a new user for the %s server" % APPTITLE, first_user=firstuser,
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
    params = dict((key, request.forms.getunicode(key)) for key in request.forms)
    user_id, permissions, token = get_request_data()
    if token:
        old_password = params['old_password']
        new_password = params['new_password']
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
    params = dict((key, request.forms.getunicode(key)) for key in request.forms)
    user_id, permissions, token = get_request_data()
    userid = params['userid']
    password = params['password']
    role = params.get('permissions')
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
    params = dict((key, request.forms.getunicode(key)) for key in request.forms)
    user_id, permissions, token = get_request_data()
    if "manage users" in permissions:
        userid = params['userid']
        password = params['password']
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


@micropsi_app.route("/agent_mgt")
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
    return template("error", msg="Insufficient rights to access agent console")


@micropsi_app.route("/select_nodenet_from_console/<nodenet_uid>")
def select_nodenet_from_console(nodenet_uid):
    user_id, permissions, token = get_request_data()
    result, uid = runtime.load_nodenet(nodenet_uid)
    if not result:
        return template("error", msg="Could not select agent")
    response.set_cookie("selected_nodenet", nodenet_uid + "/", path="/")
    redirect("/")


@micropsi_app.route("/delete_nodenet_from_console/<nodenet_uid>")
def delete_nodenet_from_console(nodenet_uid):
    user_id, permissions, token = get_request_data()
    if "manage nodenets" in permissions:
        runtime.delete_nodenet(nodenet_uid)
        response.set_cookie('notification', '{"msg":"Agent deleted", "status":"success"}', path='/')
        redirect('/agent_mgt')
    return template("error", msg="Insufficient rights to access agent console")


@micropsi_app.route("/save_all_nodenets")
def save_all_nodenets():
    user_id, permissions, token = get_request_data()
    if "manage nodenets" in permissions:
        for uid in runtime.nodenets:
            runtime.save_nodenet(uid)
        response.set_cookie('notification', '{"msg":"All agents saved", "status":"success"}', path='/')
        redirect('/agent_mgt')
    return template("error", msg="Insufficient rights to access agent console")


@micropsi_app.route("/agent/import")
def import_nodenet_form():
    token = request.get_cookie("token")
    return template("upload.tpl", title='Import Agent', message='Select a file to upload and use for importing', action='/agent/import',
        version=VERSION,
        userid=usermanager.get_user_id_for_session_token(token),
        permissions=usermanager.get_permissions_for_session_token(token))


@micropsi_app.route("/agent/import", method="POST")
def import_nodenet():
    user_id, p, t = get_request_data()
    data = request.files['file_upload'].file.read()
    data = data.decode('utf-8')
    nodenet_uid = runtime.import_nodenet(data, owner=user_id)
    return dict(status='success', msg="Agent imported", nodenet_uid=nodenet_uid)


@micropsi_app.route("/agent/merge/<nodenet_uid>")
def merge_nodenet_form(nodenet_uid):
    token = request.get_cookie("token")
    return template("upload.tpl", title='Merge Agent', message='Select a file to upload and use for merging',
        action='/agent/merge/%s' % nodenet_uid,
        version=VERSION,
        userid=usermanager.get_user_id_for_session_token(token),
        permissions=usermanager.get_permissions_for_session_token(token))


@micropsi_app.route("/agent/merge/<nodenet_uid>", method="POST")
def merge_nodenet(nodenet_uid):
    data = request.files['file_upload'].file.read()
    data = data.decode('utf-8')
    runtime.merge_nodenet(nodenet_uid, data)
    return dict(status='success', msg="Agent merged")


@micropsi_app.route("/agent/export/<nodenet_uid>")
def export_nodenet(nodenet_uid):
    response.set_header('Content-type', 'application/json')
    response.set_header('Content-Disposition', 'attachment; filename="agent.json"')
    return runtime.export_nodenet(nodenet_uid)


@micropsi_app.route("/recorder/export/<nodenet_uid>-<recorder_uid>")
def export_recorder(nodenet_uid, recorder_uid):
    data = runtime.export_recorders(nodenet_uid, [recorder_uid])
    recorder = runtime.get_recorder(nodenet_uid, recorder_uid)
    response.set_header('Content-type', 'application/octet-stream')
    response.set_header('Content-Disposition', 'attachment; filename="recorder_%s.npz"' % recorder.name)
    return data


@micropsi_app.route("/recorder/export/<nodenet_uid>", method="POST")
def export_recorders(nodenet_uid):
    uids = []
    for param in request.params.allitems():
        if param[0] == 'recorder_uids[]':
            uids.append(param[1])
    data = runtime.export_recorders(nodenet_uid, uids)
    response.set_header('Content-type', 'application/octet-stream')
    response.set_header('Content-Disposition', 'attachment; filename="recorders_%s.npz"' % nodenet_uid)
    return data


@micropsi_app.route("/agent/edit")
def edit_nodenet():
    user_id, permissions, token = get_request_data()
    nodenet_uid = request.params.get('id')
    title = 'Edit Agent' if nodenet_uid is not None else 'New Agent'

    return template("nodenet_form.tpl", title=title,
        # nodenet_uid=nodenet_uid,
        nodenets=runtime.get_available_nodenets(),
        worldtypes=runtime.get_available_world_types(),
        templates=runtime.get_available_nodenets(),
        worlds=runtime.get_available_worlds(),
        version=VERSION, user_id=user_id, permissions=permissions)


@micropsi_app.route("/agent/edit", method="POST")
def write_nodenet():
    user_id, permissions, token = get_request_data()
    params = dict((key, request.forms.getunicode(key)) for key in request.forms)
    worldadapter_name = params['nn_worldadapter']
    wa_params = {}
    for key in params:
        if key.startswith('worldadapter_%s_' % worldadapter_name):
            strip = len("worldadapter_%s_" % worldadapter_name)
            wa_params[key[strip:]] = params[key]
    if "manage nodenets" in permissions:
        result, nodenet_uid = runtime.new_nodenet(
            params['nn_name'],
            engine=params['nn_engine'],
            worldadapter=params['nn_worldadapter'],
            template=params.get('nn_template'),
            owner=user_id,
            world_uid=params.get('nn_world'),
            use_modulators=params.get('nn_modulators', False),
            worldadapter_config=wa_params)
        if result:
            return dict(status="success", msg="Agent created", nodenet_uid=nodenet_uid)
        else:
            return dict(status="error", msg="Error saving agent: %s" % nodenet_uid)
    return dict(status="error", msg="Insufficient rights to write agent")


@micropsi_app.route("/environment/import")
def import_world_form():
    token = request.get_cookie("token")
    return template("upload.tpl", title='Environment import', message='Select a file to upload and use for importing',
        action='/environment/import',
        version=VERSION,
        user_id=usermanager.get_user_id_for_session_token(token),
        permissions=usermanager.get_permissions_for_session_token(token))


@micropsi_app.route("/environment/import", method="POST")
def import_world():
    user_id, p, t = get_request_data()
    data = request.files['file_upload'].file.read()
    data = data.decode('utf-8')
    world_uid = runtime.import_world(data, owner=user_id)
    return dict(status='success', msg="Environment imported", world_uid=world_uid)


@micropsi_app.route("/environment/export/<world_uid>")
def export_world(world_uid):
    response.set_header('Content-type', 'application/json')
    response.set_header('Content-Disposition', 'attachment; filename="environment.json"')
    return runtime.export_world(world_uid)


@micropsi_app.route("/environment/edit")
def edit_world_form():
    token = request.get_cookie("token")
    world_uid = request.params.get('id', None)
    world = None
    if world_uid:
        world = runtime.worlds.get(world_uid)
    title = 'Edit Environment' if world is not None else 'New Environment'
    worldtypes = runtime.get_available_world_types()
    return template("world_form.tpl", title=title,
        worldtypes=worldtypes,
        world=world,
        version=VERSION,
        user_id=usermanager.get_user_id_for_session_token(token),
        permissions=usermanager.get_permissions_for_session_token(token))


@micropsi_app.route("/environment/edit", method="POST")
def edit_world():
    params = dict((key, request.forms.getunicode(key)) for key in request.forms)
    world_uid = params.get('world_uid')
    if world_uid:
        world_type = runtime.worlds[world_uid].__class__.__name__
    else:
        world_type = params['world_type']
    config = {}
    for p in params:
        if p.startswith(world_type + '_'):
            config[p[len(world_type) + 1:]] = params[p]
    user_id, permissions, token = get_request_data()
    if "manage worlds" in permissions:
        if world_uid:
            runtime.set_world_properties(world_uid, world_name=params['world_name'], config=config)
            return dict(status="success", msg="Environment changes saved")
        else:
            result, uid = runtime.new_world(params['world_name'], world_type, user_id, config=config)
            if result:
                return dict(status="success", msg="Environment created", world_uid=uid)
            else:
                return dict(status="error", msg=": %s" % result)
    return dict(status="error", msg="Insufficient rights to create environment")


@micropsi_app.route("/agent_list/")
@micropsi_app.route("/agent_list/<current_nodenet>")
def nodenet_list(current_nodenet=None):
    user_id, permissions, token = get_request_data()
    nodenets = runtime.get_available_nodenets()
    return template("nodenet_list", type="agent", user_id=user_id,
        current=current_nodenet,
        mine=dict((uid, nodenets[uid]) for uid in nodenets if nodenets[uid].owner == user_id),
        others=dict((uid, nodenets[uid]) for uid in nodenets if nodenets[uid].owner != user_id))


@micropsi_app.route("/environment_list/")
@micropsi_app.route("/environment_list/<current_world>")
def world_list(current_world=None):
    user_id, permissions, token = get_request_data()
    worlds = runtime.get_available_worlds()
    return template("nodenet_list", type="environment", user_id=user_id,
        current=current_world,
        mine=dict((uid, worlds[uid]) for uid in worlds if worlds[uid].owner == user_id),
        others=dict((uid, worlds[uid]) for uid in worlds if worlds[uid].owner != user_id))


@micropsi_app.route("/config/runner")
@micropsi_app.route("/config/runner", method="POST")
def edit_runner_properties():
    user_id, permissions, token = get_request_data()
    if len(request.params) > 0:
        runtime.set_runner_properties(int(request.params['timestep']), bool(request.params.get('infguard')))
        return dict(status="success", msg="Settings saved")
    else:
        return template("runner_form", action="/config/runner", value=runtime.get_runner_properties())


@micropsi_app.route("/create_worldadapter_selector/<world_uid>")
def create_worldadapter_selector(world_uid):
    return template("worldadapter_selector",
        world_uid=world_uid,
        nodenets=runtime.get_available_nodenets(),
        worlds=runtime.get_available_worlds(),
        worldtypes=runtime.get_available_world_types())


@micropsi_app.route("/dashboard")
def show_dashboard():
    user_id, permissions, token = get_request_data()
    return template("viewer", mode="dashboard", logging_levels=runtime.get_logging_levels(), user_id=user_id, permissions=permissions, token=token, version=VERSION)


#################################################################
#
#
#         ##   #####   #####    ##   ##
#         ##  ##      ##   ##   ###  ##
#         ##  ###### ##     ##  ## # ##
#         ##      ##  ##   ##   ##  ###
#        ##   #####    #####    ##   ## JSON
#
#
#################################################################


@rpc("get_nodenet_metadata")
def get_nodenet_metadata(nodenet_uid, nodespace='Root', include_links=True):
    """ Return metadata for the given nodenet_uid """
    return runtime.get_nodenet_metadata(nodenet_uid)


@rpc("get_nodes")
def get_nodes(nodenet_uid, nodespaces=[], include_links=True, links_to_nodespaces=[]):
    """ Return content of the given nodenet, filtered by nodespaces.
    Optionally also returns links to and from the nodespaces listed in `links_to_nodespaces` """
    return True, runtime.get_nodes(nodenet_uid, nodespaces, include_links, links_to_nodespaces=links_to_nodespaces)


@rpc("new_nodenet")
def new_nodenet(name, owner=None, engine='dict_engine', template=None, worldadapter=None, world_uid=None, use_modulators=None, worldadapter_config={}):
    """ Create a new nodenet with the given configuration """
    if owner is None:
        owner, _, _ = get_request_data()
    return runtime.new_nodenet(
        name,
        engine=engine,
        worldadapter=worldadapter,
        template=template,
        owner=owner,
        world_uid=world_uid,
        use_modulators=use_modulators,
        worldadapter_config=worldadapter_config)


@rpc("get_calculation_state")
def get_calculation_state(nodenet_uid, nodenet=None, nodenet_diff=None, world=None, monitors=None, dashboard=None, recorders=None):
    """ Return the current simulation state for any of the following: the given nodenet, world, monitors, dashboard, recorders
    Return values depend on the parameters:
        if you provide the nodenet-parameter (a dict, with all-optional keys: nodespaces, include_links, links_to_nodespaces) you will get the contents of the nodenet
        if you provide the nodenet_diff-parameter (a dict, with key "step" (the step to which the diff is calculated, and optional nodespaces) you will get a diff of the nodenet
        if you provide the world-parameter (anything) you will get the state of the nodenet's environment
        if you provide the monitor-parameter (anything), you will get data of all monitors registered in the nodenet
        if you provide the dashboard-parameter (anything) you will get a dict of dashboard data
        if you provide the recorder-parameter (anything), you will get data of all recorders registered in the nodenet
    """
    return runtime.get_calculation_state(nodenet_uid, nodenet=nodenet, nodenet_diff=nodenet_diff, world=world, monitors=monitors, dashboard=dashboard, recorders=recorders)


@rpc("get_nodenet_changes")
def get_nodenet_changes(nodenet_uid, nodespaces=[], since_step=0):
    """ Return a diff of the nodenets state between the given since_step and the current state. optionally filtered by nodespaces"""
    data = runtime.get_nodenet_activation_data(nodenet_uid, nodespaces=nodespaces, last_call_step=since_step)
    if data['has_changes']:
        data['changes'] = runtime.get_nodespace_changes(nodenet_uid, nodespaces=nodespaces, since_step=since_step)
    else:
        data['changes'] = {}
    return True, data


@rpc("generate_uid")
def generate_uid():
    """ Return a unique identifier"""
    return True, tools.generate_uid()


@rpc("create_auth_token")
def create_auth_token(user, password, remember=True):
    """ Create a session for the user, and returns a token for identification"""
    token = usermanager.start_session(user, password, remember)
    if token:
        return True, token
    else:
        if user in usermanager.users:
            return False, "User name and password do not match"
        else:
            return False, "User unknown"


@rpc("invalidate_auth_token")
def invalidate_auth_token(token):
    """ Terminate the session of the user associated with this token"""
    usermanager.end_session(token)
    return True


@rpc("get_available_nodenets")
def get_available_nodenets(user_id=None):
    """ Return a dict of available nodenets, optionally filtered by owner"""
    if user_id and user_id not in usermanager.users:
        return False, 'User not found'
    return True, runtime.get_available_nodenets(owner=user_id)


@rpc("delete_nodenet", permission_required="manage nodenets")
def delete_nodenet(nodenet_uid):
    """ Delete the given nodenet """
    return runtime.delete_nodenet(nodenet_uid)


@rpc("set_nodenet_properties", permission_required="manage nodenets")
def set_nodenet_properties(nodenet_uid, nodenet_name=None, worldadapter=None, world_uid=None, owner=None, worldadapter_config={}):
    """ Set the nodenet's properties. """
    return runtime.set_nodenet_properties(nodenet_uid, nodenet_name=nodenet_name, worldadapter=worldadapter, world_uid=world_uid, owner=owner, worldadapter_config=worldadapter_config)


@rpc("set_node_state")
def set_node_state(nodenet_uid, node_uid, state):
    """ Set a state-value of the given node """
    if state == "":
        state = None
    return runtime.set_node_state(nodenet_uid, node_uid, state)


@rpc("set_node_activation")
def set_node_activation(nodenet_uid, node_uid, activation):
    """ Set the node's activation (aka the activation of the first gate) """
    return runtime.set_node_activation(nodenet_uid, node_uid, activation)


@rpc("start_calculation", permission_required="manage nodenets")
def start_calculation(nodenet_uid):
    """ Start the runner of the given nodenet """
    return runtime.start_nodenetrunner(nodenet_uid)


@rpc("set_runner_condition", permission_required="manage nodenets")
def set_runner_condition(nodenet_uid, steps=-1, monitor=None):
    """ Register a stop-condition for the nodenet-runner, depending on the parameter:
    steps (int): Stop runner after having calculated this many steps
    monitor (dict, containing "uid", and "value"): Stop if the monitor with the given uid has the given value
    """
    if monitor and 'value' in monitor:
        monitor['value'] = float(monitor['value'])
    if steps:
        steps = int(steps)
        if steps < 0:
            steps = None
    return runtime.set_runner_condition(nodenet_uid, monitor, steps)


@rpc("remove_runner_condition", permission_required="manage nodenets")
def remove_runner_condition(nodenet_uid):
    """ Remove a configured stop-condition"""
    return runtime.remove_runner_condition(nodenet_uid)


@rpc("set_runner_properties", permission_required="manage server")
def set_runner_properties(timestep, infguard):
    """ Configure the server-settings:
    timestep: miliseconds per nodenet-step"""
    return runtime.set_runner_properties(timestep, infguard)


@rpc("get_runner_properties")
def get_runner_properties():
    """ Return the server-settings, returning timestep in a dict"""
    return True, runtime.get_runner_properties()


@rpc("get_is_calculation_running")
def get_is_calculation_running(nodenet_uid):
    """ Return True if the given calculation of the given nodenet is currentyly runnning """
    return True, runtime.get_is_nodenet_running(nodenet_uid)


@rpc("stop_calculation", permission_required="manage nodenets")
def stop_calculation(nodenet_uid):
    """ Stop the given nodenet's calculation"""
    return runtime.stop_nodenetrunner(nodenet_uid)


@rpc("step_calculation", permission_required="manage nodenets")
def step_calculation(nodenet_uid):
    """ Manually advance the calculation of the given nodenet by 1 step"""
    return True, runtime.step_nodenet(nodenet_uid)


@rpc("revert_calculation", permission_required="manage nodenets")
def revert_calculation(nodenet_uid):
    """ Revert the state of the nodenet and its world to the persisted one"""
    return runtime.revert_nodenet(nodenet_uid, True)


@rpc("revert_nodenet", permission_required="manage nodenets")
def revert_nodenet(nodenet_uid):
    """ Revert the state of the nodenet to the persisted one"""
    return runtime.revert_nodenet(nodenet_uid)


@rpc("reload_and_revert", permission_required="manage nodenets")
def reload_and_revert(nodenet_uid):
    """ reload code, and revert calculation"""
    return runtime.reload_and_revert(nodenet_uid)


@rpc("save_nodenet", permission_required="manage nodenets")
def save_nodenet(nodenet_uid):
    """ Persist the current state of the nodenet"""
    return runtime.save_nodenet(nodenet_uid)


@rpc("export_nodenet")
def export_nodenet_rpc(nodenet_uid):
    """ Return a json dump of the nodenet"""
    return True, runtime.export_nodenet(nodenet_uid)


@rpc("import_nodenet", permission_required="manage nodenets")
def import_nodenet_rpc(nodenet_data):
    """ Import a json dump of a whole nodenet"""
    user_id, _, _ = get_request_data()
    return True, runtime.import_nodenet(nodenet_data, user_id)


@rpc("merge_nodenet", permission_required="manage nodenets")
def merge_nodenet_rpc(nodenet_uid, nodenet_data):
    """ Merge a json dump into the given nodenet"""
    return runtime.merge_nodenet(nodenet_uid, nodenet_data)


# World

@rpc("step_nodenets_in_world")
def step_nodenets_in_world(world_uid, nodenet_uid=None, steps=1):
    """ Advance all nodenets registered in the given world
    (or, only the given nodenet) by the given number of steps"""
    return runtime.step_nodenets_in_world(world_uid, nodenet_uid=nodenet_uid, steps=steps)


@rpc("get_available_worlds")
def get_available_worlds(user_id=None):
    """ Return a dict of available worlds, optionally filtered by owner)"""
    data = {}
    for uid, world in runtime.get_available_worlds(user_id).items():
        data[uid] = dict(
                uid=world.uid,
                name=world.name,
                world_type=world.world_type,
                filename=world.filename,
                config={},
                owner=world.owner)  # fixme
                                    # ok I might but couldcha tell me more about wat is broken wid ya?
        if hasattr(world, 'config'):
            data[uid]['config'] = world.config
    return True, data


@rpc("get_world_properties")
def get_world_properties(world_uid):
    """ Return a bunch of properties for the given world (name, type, config, agents, ...)"""
    try:
        return True, runtime.get_world_properties(world_uid)
    except KeyError:
        return False, 'World %s not found' % world_uid


@rpc("get_worldadapters")
def get_worldadapters(world_uid, nodenet_uid=None):
    """ Return the world adapters available in the given world. Provide an optional nodenet_uid of an agent
    in the given world to obtain datasources and datatargets for the agent's worldadapter """
    return True, runtime.get_worldadapters(world_uid, nodenet_uid=nodenet_uid)


@rpc("get_world_objects")
def get_world_objects(world_uid, type=None):
    """ Returns a dict of worldobjects present in the world, optionally filtered by type """
    try:
        return True, runtime.get_world_objects(world_uid, type)
    except KeyError:
        return False, 'World %s not found' % world_uid


@rpc("add_worldobject")
def add_worldobject(world_uid, type, position, orientation=0.0, name="", parameters=None):
    """ Add a worldobject of the given type """
    return runtime.add_worldobject(world_uid, type, position, orientation=orientation, name=name, parameters=parameters)


@rpc("delete_worldobject")
def delete_worldobject(world_uid, object_uid):
    """ Delete the given worldobject """
    return runtime.delete_worldobject(world_uid, object_uid)


@rpc("set_worldobject_properties")
def set_worldobject_properties(world_uid, uid, position=None, orientation=None, name=None, parameters=None):
    """ Set the properties of a worldobject in the given world """
    if runtime.set_worldobject_properties(world_uid, uid, position, int(orientation), name, parameters):
        return dict(status="success")
    else:
        return dict(status="error", msg="unknown environment or world object")


@rpc("set_worldagent_properties")
def set_worldagent_properties(world_uid, uid, position=None, orientation=None, name=None, parameters=None):
    """ Set the properties of an agent in the given world """
    if runtime.set_worldagent_properties(world_uid, uid, position, orientation, name, parameters):
        return dict(status="success")
    else:
        return dict(status="error", msg="unknown environment or world object")


@rpc("new_world", permission_required="manage worlds")
def new_world(world_name, world_type, owner=None, config={}):
    """ Create a new world with the given name, of the given type """
    if owner is None:
        owner, _, _ = get_request_data()
    return runtime.new_world(world_name, world_type, owner=owner, config=config)


@rpc("get_available_world_types")
def get_available_world_types():
    """ Return a dict with world_types as keys and their configuration-dicts as value  """
    data = runtime.get_available_world_types()
    for key in data:
        del data[key]['class']  # remove class reference for json
    return True, data


@rpc("delete_world", permission_required="manage worlds")
def delete_world(world_uid):
    """ Delete the given world """
    return runtime.delete_world(world_uid)


@rpc("get_world_view")
def get_world_view(world_uid, step):
    """ Return a dict containing current_step, agents, objetcs"""
    return True, runtime.get_world_view(world_uid, step)


@rpc("set_world_properties", permission_required="manage worlds")
def set_world_properties(world_uid, world_name=None, owner=None, config=None):
    """ Set the properties of the given world """
    return runtime.set_world_properties(world_uid, world_name, owner, config)


@rpc("set_world_data")
def set_world_data(world_uid, data):
    """ Set user-data for the given world. Format and content depends on the world's implementation"""
    return runtime.set_world_data(world_uid, data)


@rpc("revert_world", permission_required="manage worlds")
def revert_world(world_uid):
    """ Revert the world to the persisted state """
    return runtime.revert_world(world_uid)


@rpc("save_world", permission_required="manage worlds")
def save_world(world_uid):
    """ Persist the current world state"""
    return runtime.save_world(world_uid)


@rpc("export_world")
def export_world_rpc(world_uid):
    """ Return a complete json dump of the world's state"""
    return True, runtime.export_world(world_uid)


@rpc("import_world", permission_required="manage worlds")
def import_world_rpc(worlddata):
    """ Import a new world from the provided json dump"""
    user_id, _, _ = get_request_data()
    return True, runtime.import_world(worlddata, user_id)


# Monitor

@rpc("add_gate_monitor")
def add_gate_monitor(nodenet_uid, node_uid, gate, name=None, color=None):
    """ Add a gate monitor to the given node, recording outgoing activation"""
    return True, runtime.add_gate_monitor(nodenet_uid, node_uid, gate, name=name, color=color)


@rpc("add_slot_monitor")
def add_slot_monitor(nodenet_uid, node_uid, slot, name=None, color=None):
    """ Add a slot monitor to the given node, recording incoming activation"""
    return True, runtime.add_slot_monitor(nodenet_uid, node_uid, slot, name=name, color=color)


@rpc("add_link_monitor")
def add_link_monitor(nodenet_uid, source_node_uid, gate_type, target_node_uid, slot_type, name, color=None):
    """ Add a link monitor to the given link, recording the link's weight"""
    return True, runtime.add_link_monitor(nodenet_uid, source_node_uid, gate_type, target_node_uid, slot_type, name, color=color)


@rpc("add_modulator_monitor")
def add_modulator_monitor(nodenet_uid, modulator, name, color=None):
    """ Add a modulator monitor, recording the value of the emotional modulator"""
    return True, runtime.add_modulator_monitor(nodenet_uid, modulator, name, color=color)


@rpc("add_custom_monitor")
def add_custom_monitor(nodenet_uid, function, name, color=None):
    """ Add a custom monitor - provide the python code as string in function."""
    return True, runtime.add_custom_monitor(nodenet_uid, function, name, color=color)


@rpc("add_group_monitor")
def add_group_monitor(nodenet_uid, nodespace, name, node_name_prefix='', node_uids=[], gate='gen', color=None):
    """ Add a group monitor recording the activations of the group """
    return True, runtime.add_group_monitor(nodenet_uid, nodespace, name, node_name_prefix=node_name_prefix, node_uids=node_uids, gate=gate, color=color)


@rpc("remove_monitor")
def remove_monitor(nodenet_uid, monitor_uid):
    """ Delete the given monitor"""
    try:
        runtime.remove_monitor(nodenet_uid, monitor_uid)
        return dict(status='success')
    except KeyError:
        return dict(status='error', msg='unknown agent or monitor')


@rpc("clear_monitor")
def clear_monitor(nodenet_uid, monitor_uid):
    """ Clear the monitor's history """
    try:
        runtime.clear_monitor(nodenet_uid, monitor_uid)
        return dict(status='success')
    except KeyError:
        return dict(status='error', msg='unknown agent or monitor')


@rpc("get_monitor_data")
def get_monitor_data(nodenet_uid, step=0, monitor_from=0, monitor_count=-1):
    """ Return data for monitors in this nodenet """
    return True, runtime.get_monitor_data(nodenet_uid, step, from_step=monitor_from, count=monitor_count)


# Nodenet

@rpc("get_nodespace_list")
def get_nodespace_list(nodenet_uid):
    """ Return a list of nodespaces in the given nodenet."""
    return True, runtime.get_nodespace_list(nodenet_uid)


@rpc("get_nodespace_activations")
def get_nodespace_activations(nodenet_uid, nodespaces, last_call_step=-1):
    """ Return a dict of uids to lists of activation values"""
    return True, runtime.get_nodenet_activation_data(nodenet_uid, nodespaces, last_call_step)


@rpc("get_nodespace_properties")
def get_nodespace_properties(nodenet_uid, nodespace_uid=None):
    """ Return a dict of properties of the nodespace"""
    return True, runtime.get_nodespace_properties(nodenet_uid, nodespace_uid)


@rpc("set_nodespace_properties")
def set_nodespace_properties(nodenet_uid, nodespace_uid, properties):
    """ Set a dict of properties of the nodespace"""
    return True, runtime.set_nodespace_properties(nodenet_uid, nodespace_uid, properties)


@rpc("get_node")
def get_node(nodenet_uid, node_uid):
    """ Return the complete json data for this node"""
    return runtime.get_node(nodenet_uid, node_uid)


@rpc("add_node", permission_required="manage nodenets")
def add_node(nodenet_uid, type, position, nodespace, state=None, name="", parameters={}):
    """ Create a new node"""
    return runtime.add_node(nodenet_uid, type, position, nodespace, state=state, name=name, parameters=parameters)


@rpc("add_nodespace", permission_required="manage nodenets")
def add_nodespace(nodenet_uid, nodespace, name="", options=None):
    """ Create a new nodespace"""
    return runtime.add_nodespace(nodenet_uid, nodespace, name=name, options=options)


@rpc("clone_nodes", permission_required="manage nodenets")
def clone_nodes(nodenet_uid, node_uids, clone_mode="all", nodespace=None, offset=[50, 50]):
    """ Clone a bunch of nodes. The nodes will get new unique node ids,
    a "copy" suffix to their name, and a slight positional offset.
    To specify whether the links should be copied too, you can give the following clone-modes:
    * "all" to clone all links
    * "internal" to only clone links within the clone set of nodes
    * "none" to not clone links at all.

    Per default, a clone of a node will appear in the same nodespace, slightly below the original node.
    If you however specify a nodespace, all clones will be copied to the given nodespace."""
    return runtime.clone_nodes(nodenet_uid, node_uids, clone_mode, nodespace=nodespace, offset=offset)


@rpc("set_node_positions", permission_required="manage nodenets")
def set_node_positions(nodenet_uid, positions):
    """ Set the positions of the nodes. Expects a dict node_uid to new position"""
    return runtime.set_node_positions(nodenet_uid, positions)


@rpc("set_node_name", permission_required="manage nodenets")
def set_node_name(nodenet_uid, node_uid, name):
    """ Set the name of the given node"""
    return runtime.set_node_name(nodenet_uid, node_uid, name)


@rpc("delete_nodes", permission_required="manage nodenets")
def delete_nodes(nodenet_uid, node_uids):
    """ Delete the given nodes. Expects a list of uids"""
    return runtime.delete_nodes(nodenet_uid, node_uids)


@rpc("delete_nodespace", permission_required="manage nodenets")
def delete_nodespace(nodenet_uid, nodespace):
    """ Delete the given nodespace and all its contents"""
    return runtime.delete_nodespace(nodenet_uid, nodespace)


@rpc("align_nodes", permission_required="manage nodenets")
def align_nodes(nodenet_uid, nodespace):
    """ Automatically align the nodes in the given nodespace """
    return runtime.align_nodes(nodenet_uid, nodespace)


@rpc("generate_netapi_fragment", permission_required="manage nodenets")
def generate_netapi_fragment(nodenet_uid, node_uids):
    """ Return Python code that can recreate the selected nodes and their states"""
    return True, runtime.generate_netapi_fragment(nodenet_uid, node_uids)


@rpc("get_available_node_types")
def get_available_node_types(nodenet_uid):
    """ Return a dict of available built-in node types and native module types"""
    return True, runtime.get_available_node_types(nodenet_uid)


@rpc("get_available_native_module_types")
def get_available_native_module_types(nodenet_uid):
    """ Return a dict of available native module types"""
    return True, runtime.get_available_native_module_types(nodenet_uid)


@rpc("set_node_parameters", permission_required="manage nodenets")
def set_node_parameters(nodenet_uid, node_uid, parameters):
    """ Set the parameters of this node"""
    return runtime.set_node_parameters(nodenet_uid, node_uid, parameters)


@rpc("set_gate_configuration", permission_required="manage nodenets")
def set_gate_configuration(nodenet_uid, node_uid, gate_type, gatefunction=None, gatefunction_parameters=None):
    """ Set the gatefunction and its parameters for the given node"""
    for key in list(gatefunction_parameters.keys()):
        try:
            gatefunction_parameters[key] = float(gatefunction_parameters[key])
        except ValueError:
            del gatefunction_parameters[key]
    return runtime.set_gate_configuration(nodenet_uid, node_uid, gate_type, gatefunction, gatefunction_parameters)


@rpc("get_available_gatefunctions")
def get_available_gatefunctions(nodenet_uid):
    """ Return a dict of possible gatefunctions and their parameters"""
    return True, runtime.get_available_gatefunctions(nodenet_uid)


@rpc("get_available_datasources")
def get_available_datasources(nodenet_uid):
    """ Return an ordered list of available datasources """
    return True, runtime.get_available_datasources(nodenet_uid)


@rpc("get_available_datatargets")
def get_available_datatargets(nodenet_uid):
    """ Return an ordered list of available datatargets """
    return True, runtime.get_available_datatargets(nodenet_uid)


@rpc("bind_datasource_to_sensor", permission_required="manage nodenets")
def bind_datasource_to_sensor(nodenet_uid, sensor_uid, datasource):
    """ Assign the given sensor to the given datasource """
    return runtime.bind_datasource_to_sensor(nodenet_uid, sensor_uid, datasource)


@rpc("bind_datatarget_to_actuator", permission_required="manage nodenets")
def bind_datatarget_to_actuator(nodenet_uid, actuator_uid, datatarget):
    """ Assign the  given actuator to the given datatarget"""
    return runtime.bind_datatarget_to_actuator(nodenet_uid, actuator_uid, datatarget)


@rpc("add_link", permission_required="manage nodenets")
def add_link(nodenet_uid, source_node_uid, gate_type, target_node_uid, slot_type, weight=1):
    """ Create a link between the given nodes """
    return runtime.add_link(nodenet_uid, source_node_uid, gate_type, target_node_uid, slot_type, weight=weight)


@rpc("set_link_weight", permission_required="manage nodenets")
def set_link_weight(nodenet_uid, source_node_uid, gate_type, target_node_uid, slot_type, weight):
    """ Set the weight of an existing link between the given nodes """
    return runtime.set_link_weight(nodenet_uid, source_node_uid, gate_type, target_node_uid, slot_type, weight)


@rpc("get_links_for_nodes")
def get_links_for_nodes(nodenet_uid, node_uids=[]):
    """ Return a dict, containing
    "links": List of links starting or ending at one of the given nodes
    "nodes": a dict of nodes that are connected by these links, but reside in other nodespaces
    """
    return True, runtime.get_links_for_nodes(nodenet_uid, node_uids)


@rpc("delete_link", permission_required="manage nodenets")
def delete_link(nodenet_uid, source_node_uid, gate_type, target_node_uid, slot_type):
    """ Delete the given link"""
    return runtime.delete_link(nodenet_uid, source_node_uid, gate_type, target_node_uid, slot_type)


@rpc("reload_code", permission_required="manage nodenets")
def reload_code():
    """ Reload the contents of the code-folder """
    return runtime.reload_code()


@rpc("user_prompt_response")
def user_prompt_response(nodenet_uid, node_uid, key, parameters, resume_nodenet):
    """ Respond to a user-prompt issued by a node. """
    runtime.user_prompt_response(nodenet_uid, node_uid, key, parameters, resume_nodenet)
    return True


# Face
@rpc("get_emoexpression_parameters")
def get_emoexpression_parameters(nodenet_uid):
    """ Return a dict of parameters to visualize the emotional state of the agent """
    nodenet = runtime.get_nodenet(nodenet_uid)
    return True, emoexpression.calc_emoexpression_parameters(nodenet)


# --------- recorder --------


@rpc("add_gate_activation_recorder")
def add_gate_activation_recorder(nodenet_uid, group_definition, name, interval=1):
    """ Add an activation recorder to a group of nodes."""
    return runtime.add_gate_activation_recorder(nodenet_uid, group_definition, name, interval)


@rpc("add_node_activation_recorder")
def add_node_activation_recorder(nodenet_uid, group_definition, name, interval=1):
    """ Add an activation recorder to a group of nodes."""
    return runtime.add_node_activation_recorder(nodenet_uid, group_definition, name, interval)


@rpc("add_linkweight_recorder")
def add_linkweight_recorder(nodenet_uid, from_group_definition, to_group_definition, name, interval=1):
    """ Add a linkweight recorder to links between to groups."""
    return runtime.add_linkweight_recorder(nodenet_uid, from_group_definition, to_group_definition, name, interval)


@rpc("remove_recorder")
def remove_recorder(nodenet_uid, recorder_uid):
    """ Delete a recorder."""
    return runtime.remove_recorder(nodenet_uid, recorder_uid)


@rpc("clear_recorder")
def clear_recorder(nodenet_uid, recorder_uid):
    """ Clear the recorder's history """
    return runtime.clear_recorder(nodenet_uid, recorder_uid)


@rpc("get_recorders")
def get_recorders(nodenet_uid):
    """ Return a dict of recorders"""
    return runtime.get_recorder_data(nodenet_uid)

# --------- logging --------


@rpc("get_logging_levels")
def get_logging_levels():
    """ Set the logging levels """
    return True, runtime.get_logging_levels()


@rpc("set_logging_levels")
def set_logging_levels(logging_levels):
    """ Set the logging levels """
    runtime.set_logging_levels(logging_levels)
    return True


@rpc("get_logger_messages")
def get_logger_messages(logger=[], after=0):
    """ Get Logger messages for the given loggers, after the given timestamp """
    return True, runtime.get_logger_messages(logger, after)


@rpc("get_monitoring_info")
def get_monitoring_info(nodenet_uid, logger=[], after=0, monitor_from=0, monitor_count=-1, with_recorders=False):
    """ Return monitor, logger, recorder data """
    data = runtime.get_monitoring_info(nodenet_uid, logger, after, monitor_from, monitor_count, with_recorders=with_recorders)
    return True, data


# --------- benchmark info --------

@rpc("benchmark_info")
def benchmark_info():
    """ Time some math operations to determine the speed of the underlying machine. """
    return True, runtime.benchmark_info()


# --- user scripts ---

@rpc("run_recipe")
def run_recipe(nodenet_uid, name, parameters):
    """ Run the recipe with the given name """
    return runtime.run_recipe(nodenet_uid, name, parameters)


@rpc('get_available_recipes')
def get_available_recipes():
    """ Return a dict of available recipes """
    return True, runtime.get_available_recipes()


@rpc("run_operation")
def run_operation(nodenet_uid, name, parameters, selection_uids):
    """ Run an operation on the given selection of nodes """
    return runtime.run_operation(nodenet_uid, name, parameters, selection_uids)


@rpc('get_available_operations')
def get_available_operations():
    """ Return a dict of available operations """
    return True, runtime.get_available_operations()


@rpc('get_agent_dashboard')
def get_agent_dashboard(nodenet_uid):
    """ Return a dict of data to display the agent's state in a dashboard """
    return True, runtime.get_agent_dashboard(nodenet_uid)


@rpc("run_netapi_command", permission_required="manage nodenets")
def run_netapi_command(nodenet_uid, command):
    """ Run a netapi command from the netapi console """
    if INCLUDE_CONSOLE:
        return runtime.run_netapi_command(nodenet_uid, command)
    else:
        raise RuntimeError("Netapi console only available if serving to localhost only")


@rpc("get_netapi_signatures")
def get_netapi_autocomplete_data(nodenet_uid, name=None):
    """ Return autocomplete-options for the netapi console. """
    return True, runtime.get_netapi_autocomplete_data(nodenet_uid, name=None)


@rpc("flow")
def flow(nodenet_uid, source_uid, source_output, target_uid, target_input):
    """ Create a connection between two flow_modules """
    return runtime.flow(nodenet_uid, source_uid, source_output, target_uid, target_input)


@rpc("unflow")
def unflow(nodenet_uid, source_uid, source_output, target_uid, target_input):
    """ Remove the connection between the given flow_modules """
    return runtime.unflow(nodenet_uid, source_uid, source_output, target_uid, target_input)


@rpc("runtime_info")
def runtime_info():
    """ Return a dict of information about this runtime, like version and configuration"""
    return True, runtime.runtime_info()

# -----------------------------------------------------------------------------------------------


def main(host=None, port=None):
    host = host or cfg['micropsi2']['host']
    port = port or cfg['micropsi2']['port']
    print("Starting App on Port " + str(port))
    runtime.initialize()
    try:
        from cherrypy import wsgiserver
        server = 'cherrypy'
        kwargs = {'numthreads': 30}
    except ImportError:
        server = 'wsgiref'
        kwargs = {}

    run(micropsi_app, host=host, port=port, quiet=False, server=server, **kwargs)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Start the %s server." % APPTITLE)
    parser.add_argument('-d', '--host', type=str, default=cfg['micropsi2']['host'])
    parser.add_argument('-p', '--port', type=int, default=cfg['micropsi2']['port'])
    args = parser.parse_args()
    main(host=args.host, port=args.port)
