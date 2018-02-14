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

import os
import json
import argparse
from threading import Thread

from configuration import config as cfg

import micropsi_core
from micropsi_core import runtime

from micropsi_server import bottle
from micropsi_server import minidoc
from micropsi_server import usermanagement

from micropsi_server.bottle import Bottle, run, request, response, template, static_file, redirect
from micropsi_server.tools import APP_PATH, APPTITLE, VERSION, get_request_data, usermanager

micropsi_app = Bottle()

bottle.debug(cfg['micropsi2'].get('debug', False))  # devV

bottle.TEMPLATE_PATH.insert(0, os.path.join(APP_PATH, 'view', ''))
bottle.TEMPLATE_PATH.insert(1, os.path.join(APP_PATH, 'static', ''))

bottle.BaseRequest.MEMFILE_MAX = 5 * 1024 * 1024

theano_available = True
numpy_available = True
try:
    import theano
except ImportError:
    theano_available = False
try:
    import numpy
except ImportError:
    numpy_available = False

bottle.BaseTemplate.defaults['theano_available'] = theano_available
bottle.BaseTemplate.defaults['numpy_available'] = numpy_available

from micropsi_server.core_rpc_api import core_rpc_api

# add core json RPC
micropsi_app.mount("/rpc", core_rpc_api)


# ----------------------------------------------------------------------------------
#
#   C O R E
#   H T T P
#   R O U T E S
#
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
        permissions=permissions)


@micropsi_app.route("/agent")
def nodenet():
    user_id, permissions, token = get_request_data()
    return template("viewer", mode="nodenet", version=VERSION, user_id=user_id, permissions=permissions)


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
@core_rpc_api.error(404)
def error_page(error):
    if request.is_xhr:
        response.content_type = "application/json"
        return json.dumps({
            "status": "error",
            "data": "Function not found"
        })
    return template("error.tpl", error=error, msg="Page not found.")


@micropsi_app.error(405)
@core_rpc_api.error(405)
def error_page_405(error):
    if request.is_xhr:
        response.content_type = "application/json"
        return json.dumps({
            "status": "error",
            "data": "Method not allowed"
        })
    return template("error.tpl", error=error, msg="Method not allowed.")


@micropsi_app.error(500)
@core_rpc_api.error(500)
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


@micropsi_app.route("/agent/edit")
def edit_nodenet():
    user_id, permissions, token = get_request_data()
    nodenet_uid = request.params.get('id')
    title = 'Edit Agent' if nodenet_uid is not None else 'New Agent'
    return template("nodenet_form.tpl", title=title,
        nodenet=None if not nodenet_uid else runtime.get_nodenet(nodenet_uid).metadata,
        devices=runtime.get_devices(),
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
    device_map = {}
    for key in params:
        if key.startswith('worldadapter_%s_' % worldadapter_name):
            strip = len("worldadapter_%s_" % worldadapter_name)
            wa_params[key[strip:]] = params[key]
        elif key.startswith('device-map-'):
            uid = key[11:]
            device_map[uid] = params['device-name-%s' % uid]

    if "manage nodenets" in permissions:
        if not params.get('nodenet_uid'):
            result, nodenet_uid = runtime.new_nodenet(
                params['nn_name'],
                engine=params['nn_engine'],
                worldadapter=params['nn_worldadapter'],
                template=params.get('nn_template'),
                owner=user_id,
                world_uid=params.get('nn_world'),
                use_modulators=params.get('nn_modulators', False),
                worldadapter_config=wa_params,
                device_map=device_map)
            if result:
                return dict(status="success", msg="Agent created", nodenet_uid=nodenet_uid)
            else:
                return dict(status="error", msg="Error saving agent: %s" % nodenet_uid)
        else:
            result = runtime.set_nodenet_properties(
                params['nodenet_uid'],
                nodenet_name=params['nn_name'],
                worldadapter=params['nn_worldadapter'],
                world_uid=params['nn_world'],
                owner=user_id,
                worldadapter_config=wa_params,
                device_map=device_map)
            if result:
                return dict(status="success", msg="Changes saved")
            else:
                return dict(status="error", msg="Error saving changes!")
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
    worldtypes = runtime.get_available_world_types()
    world_data = runtime.world_data
    return template("world_form.tpl",
        worldtypes=worldtypes,
        world_data=world_data,
        version=VERSION,
        user_id=usermanager.get_user_id_for_session_token(token),
        permissions=usermanager.get_permissions_for_session_token(token))


@micropsi_app.route("/device/edit")
def edit_device_form():
    token = request.get_cookie("token")
    device_types = runtime.get_device_types()
    device_data = runtime.get_devices()
    return template("device_form.tpl",
        device_types=device_types,
        device_data=device_data,
        version=VERSION,
        user_id=usermanager.get_user_id_for_session_token(token),
        permissions=usermanager.get_permissions_for_session_token(token))


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
        log_levels = {
            'agent': request.params.get('log_level_agent'),
            'system': request.params.get('log_level_system'),
            'world': request.params.get('log_level_world')
        }
        result, msg = runtime.set_runner_properties(
            int(request.params['timestep']),
            bool(request.params.get('infguard')),
            bool(request.params.get('profile_nodenet')),
            bool(request.params.get('profile_world')),
            log_levels,
            request.params.get('log_file'))
        return dict(status="success" if result else "error", msg="Settings saved" if result else msg)
    else:
        return template("runner_form", action="/config/runner", value=runtime.get_runner_properties())


@micropsi_app.route("/create_worldadapter_selector/")
@micropsi_app.route("/create_worldadapter_selector/<world_uid>")
def create_worldadapter_selector(world_uid=None):
    return template("worldadapter_selector",
        world_uid=world_uid,
        nodenets=runtime.get_available_nodenets(),
        worlds=runtime.get_available_worlds(),
        worldtypes=runtime.get_available_world_types())


@micropsi_app.route("/dashboard")
def show_dashboard():
    user_id, permissions, token = get_request_data()
    return template("viewer", mode="dashboard", logging_levels=runtime.get_logging_levels(), user_id=user_id, permissions=permissions, token=token, version=VERSION)


# ----------------------------------------------------------------------------------
#
#   S T A R T U P
#
# ----------------------------------------------------------------------------------


consolethread = None
console_is_started = False


def signal_handler(sig, msg):
    from micropsi_core import runtime
    if consolethread:
        from ipykernel.zmqshell import ZMQInteractiveShell
        from IPython.core.history import HistoryManager
        import IPython
        IPython.sys.stdout.write("""
######################
#                    #
#       ERROR        #
#                    #
######################

The runtime for this console has been shut down!\n\n\n""")

        ZMQInteractiveShell._instance.quiet = False

        def empty(a):
            pass
        HistoryManager.end_session = empty

        try:
            ZMQInteractiveShell.exiter.__call__(keep_alive=False)
        except AttributeError:  # explodes, if no ipython session present
            pass
    # call the runtime's signal handler
    runtime.signal_handler(sig, msg)


def ipython_kernel_thread(ip="127.0.0.1"):
    from unittest import mock
    import IPython
    from ipykernel.zmqshell import ZMQInteractiveShell
    from ipykernel import kernelapp
    kernelapp._ctrl_c_message = "Starting Ipython Kernel"
    from IPython.core.autocall import ZMQExitAutocall

    class KeepAlive(ZMQExitAutocall):
        def __call__(self, keep_alive=True):
            super().__call__(keep_alive)
    ZMQInteractiveShell.exiter = KeepAlive()

    if ip == "0.0.0.0":
        ip = "*"
    elif ip == "localhost":
        ip = "127.0.0.1"

    with mock.patch('signal.signal'):
        with mock.patch('ipykernel.kernelbase.signal'):
            IPython.embed_kernel()


def start_ipython_console(host="127.0.0.1"):
    import sys
    import time
    global consolethread
    global console_is_started

    consolethread = Thread(target=ipython_kernel_thread, args=[host])
    consolethread.daemon = True
    consolethread.start()

    count = 0
    # wait until ipython hijacked the streams
    while (sys.stderr == sys.__stderr__) and count < 10:
        count += 1
        time.sleep(0.1)

    # revert input and error back to their original state
    sys.stdin, sys.stderr = sys.__stdin__, sys.__stderr__

    console_is_started = True


def main(host=None, port=None, console=True):
    host = host or cfg['micropsi2']['host']
    port = port or cfg['micropsi2']['port']
    print("Starting app on port %s, serving for %s" % (str(port), str(host)))

    # register our own signal handlers first.
    import threading
    if threading.current_thread() == threading.main_thread():
        import signal
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGABRT, signal_handler)

    # start the console if desired
    if console:
        try:
            import IPython
            import ipykernel
            start_ipython_console(host)
        except ImportError as err:
            print("Warning: IPython console not available: " + err.msg)
    else:
        print("Starting without ipython console")

    # init the runtime
    runtime.initialize()

    # start the webserver
    try:
        from cherrypy import wsgiserver
        server = 'cherrypy'
        kwargs = {'numthreads': 30}
    except ImportError:
        server = 'wsgiref'
        kwargs = {}

    run(micropsi_app, host=host, port=port, quiet=True, server=server, **kwargs)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Start the %s server." % APPTITLE)
    parser.add_argument('-d', '--host', type=str, default=cfg['micropsi2']['host'])
    parser.add_argument('-p', '--port', type=int, default=cfg['micropsi2']['port'])
    parser.add_argument('--console', dest='console', action='store_true')
    parser.add_argument('--no-console', dest='console', action='store_false')
    parser.set_defaults(console=True)
    args = parser.parse_args()
    main(host=args.host, port=args.port, console=args.console)
