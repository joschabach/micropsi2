
import os
import json
import logging
import inspect
from micropsi_server.bottle import request, response

from configuration import config as cfg
from micropsi_core import tools
from micropsi_server import usermanagement

usermanager = usermanagement.UserManager()
VERSION = cfg['micropsi2']['version']
APPTITLE = cfg['micropsi2']['apptitle']
APP_PATH = os.path.dirname(__file__)


def get_request_data():
    # Helper function to determine the current user, permissions and token
    if request.get_cookie("token"):
        token = request.get_cookie("token")
    else:
        token = None
    permissions = usermanager.get_permissions_for_session_token(token)
    user_id = usermanager.get_user_id_for_session_token(token)
    return user_id, permissions, token


def rpc(app, command, method="POST", permission_required=None):
    # Defines a decorator for accessing API calls. Use it by specifying the
    # API method, followed by the permissions necessary to execute the method.
    # Within the calling web page, use http://<url>/rpc/<method>?arg1=val1&arg2=val2
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
        @app.route('/' + command, "POST")
        @app.route('/' + command, method)
        def _wrapper(argument=None):
            response.content_type = 'application/json; charset=utf8'
            kwargs = {}
            if request.method == "GET":
                kwargs = {}
                for key in request.params:
                    kwargs[key] = request.params.getall(key)
                    if len(kwargs[key]) == 1:
                        kwargs[key] = kwargs[key][0]
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
                    tools.post_mortem()
                    return {'status': 'error', 'data': str(err), 'traceback': traceback.format_exc()}
                # except TypeError as err:
                #     response.status = 400
                #     return {"Error": "Bad parameters in remote procedure call: %s" % err}
        return _wrapper
    return _decorator
