"""

Contains RPC calls for the core runtime

"""
import json

from micropsi_core import runtime
from micropsi_core import tools

from micropsi_server.bottle import Bottle
from micropsi_server.tools import get_request_data, usermanager, rpc


core_rpc_api = Bottle()


@rpc(core_rpc_api, "get_nodenet_metadata", method="GET")
def get_nodenet_metadata(nodenet_uid, nodespace='Root'):
    """ Return metadata for the given nodenet_uid """
    return runtime.get_nodenet_metadata(nodenet_uid)


@rpc(core_rpc_api, "get_nodes")
def get_nodes(nodenet_uid, nodespaces=[], include_links=True, links_to_nodespaces=[]):
    """ Return content of the given nodenet, filtered by nodespaces.
    Optionally also returns links to and from the nodespaces listed in `links_to_nodespaces` """
    return True, runtime.get_nodes(nodenet_uid, nodespaces, include_links, links_to_nodespaces=links_to_nodespaces)


@rpc(core_rpc_api, "new_nodenet")
def new_nodenet(name, owner=None, engine='dict_engine', template=None, worldadapter=None, world_uid=None, use_modulators=None, worldadapter_config={}, device_map={}):
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
        worldadapter_config=worldadapter_config,
        device_map=device_map)


@rpc(core_rpc_api, "get_calculation_state")
def get_calculation_state(nodenet_uid, nodenet=None, nodenet_diff=None, world=None, monitors=None, dashboard=None):
    """ Return the current simulation state for any of the following: the given nodenet, world, monitors, dashboard
    Return values depend on the parameters:
        if you provide the nodenet-parameter (a dict, with all-optional keys: nodespaces, include_links, links_to_nodespaces) you will get the contents of the nodenet
        if you provide the nodenet_diff-parameter (a dict, with key "step" (the step to which the diff is calculated, and optional nodespaces) you will get a diff of the nodenet
        if you provide the world-parameter (anything) you will get the state of the nodenet's environment
        if you provide the monitor-parameter (anything), you will get data of all monitors registered in the nodenet
        if you provide the dashboard-parameter (anything) you will get a dict of dashboard data
    """
    return runtime.get_calculation_state(nodenet_uid, nodenet=nodenet, nodenet_diff=nodenet_diff, world=world, monitors=monitors, dashboard=dashboard)


@rpc(core_rpc_api, "get_nodenet_changes")
def get_nodenet_changes(nodenet_uid, nodespaces=[], since_step=0):
    """ Return a diff of the nodenets state between the given since_step and the current state. optionally filtered by nodespaces"""
    data = runtime.get_nodenet_activation_data(nodenet_uid, nodespaces=nodespaces, last_call_step=int(since_step))
    if data['has_changes']:
        data['changes'] = runtime.get_nodespace_changes(nodenet_uid, nodespaces=nodespaces, since_step=int(since_step))
    else:
        data['changes'] = {}
    return True, data


@rpc(core_rpc_api, "generate_uid", method="GET")
def generate_uid():
    """ Return a unique identifier"""
    return True, tools.generate_uid()


@rpc(core_rpc_api, "create_auth_token")
def create_auth_token(user, password, remember=True):
    """ Create a session for the user, and returns a token for identification"""
    token = usermanager.start_session(user, password, tools.parse_bool(remember))
    if token:
        return True, token
    else:
        if user in usermanager.users:
            return False, "User name and password do not match"
        else:
            return False, "User unknown"


@rpc(core_rpc_api, "invalidate_auth_token")
def invalidate_auth_token(token):
    """ Terminate the session of the user associated with this token"""
    usermanager.end_session(token)
    return True


@rpc(core_rpc_api, "get_available_nodenets", method="GET")
def get_available_nodenets(user_id=None):
    """ Return a dict of available nodenets, optionally filtered by owner"""
    if user_id and user_id not in usermanager.users:
        return False, 'User not found'
    return True, runtime.get_available_nodenets(owner=user_id)


@rpc(core_rpc_api, "delete_nodenet", permission_required="manage nodenets")
def delete_nodenet(nodenet_uid):
    """ Delete the given nodenet """
    return runtime.delete_nodenet(nodenet_uid)


@rpc(core_rpc_api, "set_nodenet_properties", permission_required="manage nodenets")
def set_nodenet_properties(nodenet_uid, nodenet_name=None, worldadapter=None, world_uid=None, owner=None, worldadapter_config={}, device_map={}):
    """ Set the nodenet's properties. """
    return runtime.set_nodenet_properties(nodenet_uid, nodenet_name=nodenet_name, worldadapter=worldadapter, world_uid=world_uid, owner=owner, worldadapter_config=worldadapter_config, device_map=device_map)


@rpc(core_rpc_api, "set_node_state")
def set_node_state(nodenet_uid, node_uid, state):
    """ Set a state-value of the given node """
    if state == "":
        state = None
    return runtime.set_node_state(nodenet_uid, node_uid, state)


@rpc(core_rpc_api, "set_node_activation")
def set_node_activation(nodenet_uid, node_uid, activation):
    """ Set the node's activation (aka the activation of the first gate) """
    return runtime.set_node_activation(nodenet_uid, node_uid, activation)


@rpc(core_rpc_api, "start_calculation", permission_required="manage nodenets")
def start_calculation(nodenet_uid):
    """ Start the runner of the given nodenet """
    return runtime.start_nodenetrunner(nodenet_uid)


@rpc(core_rpc_api, "set_runner_condition", permission_required="manage nodenets")
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


@rpc(core_rpc_api, "remove_runner_condition", permission_required="manage nodenets")
def remove_runner_condition(nodenet_uid):
    """ Remove a configured stop-condition"""
    return runtime.remove_runner_condition(nodenet_uid)


@rpc(core_rpc_api, "set_runner_properties", permission_required="manage server")
def set_runner_properties(timestep, infguard=False, profile_nodenet=False, profile_world=False, log_levels={}, log_file=None):
    """ Configure the server-settings for the runner """
    return runtime.set_runner_properties(int(timestep), tools.parse_bool(infguard), tools.parse_bool(profile_nodenet), tools.parse_bool(profile_world), log_levels, log_file)


@rpc(core_rpc_api, "get_runner_properties", method="GET")
def get_runner_properties():
    """ Return the server-settings, returning timestep in a dict"""
    return True, runtime.get_runner_properties()


@rpc(core_rpc_api, "get_is_calculation_running", method="GET")
def get_is_calculation_running(nodenet_uid):
    """ Return True if the given calculation of the given nodenet is currentyly runnning """
    return True, runtime.get_is_nodenet_running(nodenet_uid)


@rpc(core_rpc_api, "stop_calculation", permission_required="manage nodenets")
def stop_calculation(nodenet_uid):
    """ Stop the given nodenet's calculation"""
    return runtime.stop_nodenetrunner(nodenet_uid)


@rpc(core_rpc_api, "step_calculation", permission_required="manage nodenets")
def step_calculation(nodenet_uid):
    """ Manually advance the calculation of the given nodenet by 1 step"""
    return True, runtime.step_nodenet(nodenet_uid)


@rpc(core_rpc_api, "revert_calculation", permission_required="manage nodenets")
def revert_calculation(nodenet_uid):
    """ Revert the state of the nodenet and its world to the persisted one"""
    return runtime.revert_nodenet(nodenet_uid, True)


@rpc(core_rpc_api, "revert_nodenet", permission_required="manage nodenets")
def revert_nodenet(nodenet_uid):
    """ Revert the state of the nodenet to the persisted one"""
    return runtime.revert_nodenet(nodenet_uid)


@rpc(core_rpc_api, "reload_and_revert", permission_required="manage nodenets")
def reload_and_revert(nodenet_uid):
    """ reload code, and revert calculation"""
    return runtime.reload_and_revert(nodenet_uid)


@rpc(core_rpc_api, "save_nodenet", permission_required="manage nodenets")
def save_nodenet(nodenet_uid):
    """ Persist the current state of the nodenet"""
    return runtime.save_nodenet(nodenet_uid)


@rpc(core_rpc_api, "export_nodenet", method="GET")
def export_nodenet_rpc(nodenet_uid):
    """ Return a json dump of the nodenet"""
    return True, runtime.export_nodenet(nodenet_uid)


@rpc(core_rpc_api, "import_nodenet", permission_required="manage nodenets")
def import_nodenet_rpc(nodenet_data):
    """ Import a json dump of a whole nodenet"""
    user_id, _, _ = get_request_data()
    return True, runtime.import_nodenet(nodenet_data, user_id)


@rpc(core_rpc_api, "merge_nodenet", permission_required="manage nodenets")
def merge_nodenet_rpc(nodenet_uid, nodenet_data):
    """ Merge a json dump into the given nodenet"""
    return runtime.merge_nodenet(nodenet_uid, nodenet_data)


@rpc(core_rpc_api, "start_behavior")
def start_behavior_rpc(nodenet_uid, condition=None, worldadapter_param=None):
    """ Start nodenet with the stop condition """
    return runtime.start_behavior(nodenet_uid, condition, worldadapter_param)


@rpc(core_rpc_api, "get_behavior_state", method="GET")
def get_behavior_state_rpc(token):
    """ Return the state of the behavior execution identified by token """
    return runtime.get_behavior_state(token)


@rpc(core_rpc_api, "abort_behavior")
def abort_behavior_rpc(token):
    """ Abort behavior identified with the token """
    return runtime.abort_behavior(token)


@rpc(core_rpc_api, "get_status_tree", method="GET")
def get_status_tree(nodenet_uid, level="debug"):
    """ Return status tree as an array of dicts """
    return runtime.get_status_tree(nodenet_uid, level)


# Device

@rpc(core_rpc_api, "get_device_types", method="GET")
def get_device_types():
    """ Return a dict with device types as keys and config dict as value """
    data = runtime.get_device_types()
    return True, data


@rpc(core_rpc_api, "get_devices", method="GET")
def get_devices():
    """ Return a dict with device uids as keys and config dict as value """
    data = runtime.get_devices()
    return True, data


@rpc(core_rpc_api, "add_device")
def add_device(device_type, config={}):
    """ Create a new device of the given type with the given configuration """
    return runtime.add_device(device_type, config)


@rpc(core_rpc_api, "remove_device")
def remove_device(device_uid):
    """ Remove the device specified by the uid """
    return runtime.remove_device(device_uid)


@rpc(core_rpc_api, "set_device_properties")
def set_device_properties(device_uid, config):
    """ Reconfigure the device specified by the uid """
    return runtime.set_device_properties(device_uid, config)


# World

@rpc(core_rpc_api, "step_nodenets_in_world")
def step_nodenets_in_world(world_uid, nodenet_uid=None, steps=1):
    """ Advance all nodenets registered in the given world
    (or, only the given nodenet) by the given number of steps"""
    return runtime.step_nodenets_in_world(world_uid, nodenet_uid=nodenet_uid, steps=int(steps))


@rpc(core_rpc_api, "get_available_worlds", method="GET")
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


@rpc(core_rpc_api, "get_world_properties", method="GET")
def get_world_properties(world_uid):
    """ Return a bunch of properties for the given world (name, type, config, agents, ...)"""
    try:
        return True, runtime.get_world_properties(world_uid)
    except KeyError:
        return False, 'World %s not found' % world_uid


@rpc(core_rpc_api, "get_worldadapters", method="GET")
def get_worldadapters(world_uid, nodenet_uid=None):
    """ Return the world adapters available in the given world. Provide an optional nodenet_uid of an agent
    in the given world to obtain datasources and datatargets for the agent's worldadapter """
    return True, runtime.get_worldadapters(world_uid, nodenet_uid=nodenet_uid)


@rpc(core_rpc_api, "get_world_objects", method="GET")
def get_world_objects(world_uid, type=None):
    """ Returns a dict of worldobjects present in the world, optionally filtered by type """
    try:
        return True, runtime.get_world_objects(world_uid, type)
    except KeyError:
        return False, 'World %s not found' % world_uid


@rpc(core_rpc_api, "add_worldobject")
def add_worldobject(world_uid, type, position, orientation=0.0, name="", parameters=None):
    """ Add a worldobject of the given type """
    return runtime.add_worldobject(world_uid, type, position, orientation=float(orientation), name=name, parameters=parameters)


@rpc(core_rpc_api, "delete_worldobject")
def delete_worldobject(world_uid, object_uid):
    """ Delete the given worldobject """
    return runtime.delete_worldobject(world_uid, object_uid)


@rpc(core_rpc_api, "set_worldobject_properties")
def set_worldobject_properties(world_uid, uid, position=None, orientation=None, name=None, parameters=None):
    """ Set the properties of a worldobject in the given world """
    if runtime.set_worldobject_properties(world_uid, uid, position, float(orientation), name, parameters):
        return dict(status="success")
    else:
        return dict(status="error", msg="unknown environment or world object")


@rpc(core_rpc_api, "set_worldagent_properties")
def set_worldagent_properties(world_uid, uid, position=None, orientation=None, name=None, parameters=None):
    """ Set the properties of an agent in the given world """
    if runtime.set_worldagent_properties(world_uid, uid, position, float(orientation), name, parameters):
        return dict(status="success")
    else:
        return dict(status="error", msg="unknown environment or world object")


@rpc(core_rpc_api, "new_world", permission_required="manage worlds")
def new_world(world_name, world_type, owner=None, config={}):
    """ Create a new world with the given name, of the given type """
    if owner is None:
        owner, _, _ = get_request_data()
    return runtime.new_world(world_name, world_type, owner=owner, config=config)


@rpc(core_rpc_api, "get_available_world_types", method="GET")
def get_available_world_types():
    """ Return a dict with world_types as keys and their configuration-dicts as value  """
    data = runtime.get_available_world_types()
    for key in data:
        del data[key]['class']  # remove class reference for json
    return True, data


@rpc(core_rpc_api, "delete_world", permission_required="manage worlds")
def delete_world(world_uid):
    """ Delete the given world """
    return runtime.delete_world(world_uid)


@rpc(core_rpc_api, "get_world_view", method="GET")
def get_world_view(world_uid, step):
    """ Return a dict containing current_step, agents, objetcs"""
    return True, runtime.get_world_view(world_uid, int(step))


@rpc(core_rpc_api, "set_world_properties", permission_required="manage worlds")
def set_world_properties(world_uid, world_name=None, owner=None, config=None):
    """ Set the properties of the given world """
    return runtime.set_world_properties(world_uid, world_name, owner, config)


@rpc(core_rpc_api, "set_world_data")
def set_world_data(world_uid, data):
    """ Set user-data for the given world. Format and content depends on the world's implementation"""
    return runtime.set_world_data(world_uid, data)


@rpc(core_rpc_api, "revert_world", permission_required="manage worlds")
def revert_world(world_uid):
    """ Revert the world to the persisted state """
    return runtime.revert_world(world_uid)


@rpc(core_rpc_api, "save_world", permission_required="manage worlds")
def save_world(world_uid):
    """ Persist the current world state"""
    return runtime.save_world(world_uid)


@rpc(core_rpc_api, "export_world", method="GET")
def export_world_rpc(world_uid):
    """ Return a complete json dump of the world's state"""
    return True, runtime.export_world(world_uid)


@rpc(core_rpc_api, "import_world", permission_required="manage worlds")
def import_world_rpc(worlddata):
    """ Import a new world from the provided json dump"""
    user_id, _, _ = get_request_data()
    return True, runtime.import_world(worlddata, user_id)


# Monitor

@rpc(core_rpc_api, "add_gate_monitor")
def add_gate_monitor(nodenet_uid, node_uid, gate, name=None, color=None):
    """ Add a gate monitor to the given node, recording outgoing activation"""
    return True, runtime.add_gate_monitor(nodenet_uid, node_uid, gate, name=name, color=color)


@rpc(core_rpc_api, "add_slot_monitor")
def add_slot_monitor(nodenet_uid, node_uid, slot, name=None, color=None):
    """ Add a slot monitor to the given node, recording incoming activation"""
    return True, runtime.add_slot_monitor(nodenet_uid, node_uid, slot, name=name, color=color)


@rpc(core_rpc_api, "add_link_monitor")
def add_link_monitor(nodenet_uid, source_node_uid, gate_type, target_node_uid, slot_type, name, color=None):
    """ Add a link monitor to the given link, recording the link's weight"""
    return True, runtime.add_link_monitor(nodenet_uid, source_node_uid, gate_type, target_node_uid, slot_type, name, color=color)


@rpc(core_rpc_api, "add_modulator_monitor")
def add_modulator_monitor(nodenet_uid, modulator, name, color=None):
    """ Add a modulator monitor, recording the value of the emotional modulator"""
    return True, runtime.add_modulator_monitor(nodenet_uid, modulator, name, color=color)


@rpc(core_rpc_api, "add_custom_monitor")
def add_custom_monitor(nodenet_uid, function, name, color=None):
    """ Add a custom monitor - provide the python code as string in function."""
    return True, runtime.add_custom_monitor(nodenet_uid, function, name, color=color)


@rpc(core_rpc_api, "add_group_monitor")
def add_group_monitor(nodenet_uid, nodespace, name, node_name_prefix='', node_uids=[], gate='gen', color=None):
    """ Add a group monitor recording the activations of the group """
    return True, runtime.add_group_monitor(nodenet_uid, nodespace, name, node_name_prefix=node_name_prefix, node_uids=node_uids, gate=gate, color=color)


@rpc(core_rpc_api, "remove_monitor")
def remove_monitor(nodenet_uid, monitor_uid):
    """ Delete the given monitor"""
    try:
        runtime.remove_monitor(nodenet_uid, monitor_uid)
        return dict(status='success')
    except KeyError:
        return dict(status='error', msg='unknown agent or monitor')


@rpc(core_rpc_api, "clear_monitor")
def clear_monitor(nodenet_uid, monitor_uid):
    """ Clear the monitor's history """
    try:
        runtime.clear_monitor(nodenet_uid, monitor_uid)
        return dict(status='success')
    except KeyError:
        return dict(status='error', msg='unknown agent or monitor')


@rpc(core_rpc_api, "get_monitor_data", method="GET")
def get_monitor_data(nodenet_uid, step=0, monitor_from=0, monitor_count=-1):
    """ Return data for monitors in this nodenet """
    return True, runtime.get_monitor_data(nodenet_uid, int(step), from_step=int(monitor_from), count=int(monitor_count))


# Nodenet

@rpc(core_rpc_api, "get_nodespace_list", method="GET")
def get_nodespace_list(nodenet_uid):
    """ Return a list of nodespaces in the given nodenet."""
    return True, runtime.get_nodespace_list(nodenet_uid)


@rpc(core_rpc_api, "get_nodespace_activations")
def get_nodespace_activations(nodenet_uid, nodespaces, last_call_step=-1):
    """ Return a dict of uids to lists of activation values"""
    return True, runtime.get_nodenet_activation_data(nodenet_uid, nodespaces, int(last_call_step))


@rpc(core_rpc_api, "get_nodespace_properties", method="GET")
def get_nodespace_properties(nodenet_uid, nodespace_uid=None):
    """ Return a dict of properties of the nodespace"""
    return True, runtime.get_nodespace_properties(nodenet_uid, nodespace_uid)


@rpc(core_rpc_api, "set_nodespace_properties")
def set_nodespace_properties(nodenet_uid, nodespace_uid, properties):
    """ Set a dict of properties of the nodespace"""
    return True, runtime.set_nodespace_properties(nodenet_uid, nodespace_uid, properties)


@rpc(core_rpc_api, "get_node", method="GET")
def get_node(nodenet_uid, node_uid):
    """ Return the complete json data for this node"""
    return runtime.get_node(nodenet_uid, node_uid)


@rpc(core_rpc_api, "add_node", permission_required="manage nodenets")
def add_node(nodenet_uid, type, position, nodespace, state=None, name="", parameters={}):
    """ Create a new node"""
    return runtime.add_node(nodenet_uid, type, position, nodespace, state=state, name=name, parameters=parameters)


@rpc(core_rpc_api, "add_nodespace", permission_required="manage nodenets")
def add_nodespace(nodenet_uid, nodespace, name="", options=None):
    """ Create a new nodespace"""
    return runtime.add_nodespace(nodenet_uid, nodespace, name=name, options=options)


@rpc(core_rpc_api, "clone_nodes", permission_required="manage nodenets")
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


@rpc(core_rpc_api, "set_node_positions", permission_required="manage nodenets")
def set_node_positions(nodenet_uid, positions):
    """ Set the positions of the nodes. Expects a dict node_uid to new position"""
    return runtime.set_node_positions(nodenet_uid, positions)


@rpc(core_rpc_api, "set_node_name", permission_required="manage nodenets")
def set_node_name(nodenet_uid, node_uid, name):
    """ Set the name of the given node"""
    return runtime.set_node_name(nodenet_uid, node_uid, name)


@rpc(core_rpc_api, "delete_nodes", permission_required="manage nodenets")
def delete_nodes(nodenet_uid, node_uids):
    """ Delete the given nodes. Expects a list of uids"""
    return runtime.delete_nodes(nodenet_uid, node_uids)


@rpc(core_rpc_api, "delete_nodespace", permission_required="manage nodenets")
def delete_nodespace(nodenet_uid, nodespace):
    """ Delete the given nodespace and all its contents"""
    return runtime.delete_nodespace(nodenet_uid, nodespace)


@rpc(core_rpc_api, "align_nodes", permission_required="manage nodenets")
def align_nodes(nodenet_uid, nodespace):
    """ Automatically align the nodes in the given nodespace """
    return runtime.align_nodes(nodenet_uid, nodespace)


@rpc(core_rpc_api, "generate_netapi_fragment", permission_required="manage nodenets")
def generate_netapi_fragment(nodenet_uid, node_uids):
    """ Return Python code that can recreate the selected nodes and their states"""
    return True, runtime.generate_netapi_fragment(nodenet_uid, node_uids)


@rpc(core_rpc_api, "get_available_node_types", method="GET")
def get_available_node_types(nodenet_uid):
    """ Return a dict of available built-in node types and native module types"""
    return True, runtime.get_available_node_types(nodenet_uid)


@rpc(core_rpc_api, "get_available_native_module_types", method="GET")
def get_available_native_module_types(nodenet_uid):
    """ Return a dict of available native module types"""
    return True, runtime.get_available_native_module_types(nodenet_uid)


@rpc(core_rpc_api, "set_node_parameters", permission_required="manage nodenets")
def set_node_parameters(nodenet_uid, node_uid, parameters):
    """ Set the parameters of this node"""
    return runtime.set_node_parameters(nodenet_uid, node_uid, parameters)


@rpc(core_rpc_api, "set_gate_configuration", permission_required="manage nodenets")
def set_gate_configuration(nodenet_uid, node_uid, gate_type, gatefunction=None, gatefunction_parameters=None):
    """ Set the gatefunction and its parameters for the given node"""
    for key in list(gatefunction_parameters.keys()):
        try:
            gatefunction_parameters[key] = float(gatefunction_parameters[key])
        except ValueError:
            del gatefunction_parameters[key]
    return runtime.set_gate_configuration(nodenet_uid, node_uid, gate_type, gatefunction, gatefunction_parameters)


@rpc(core_rpc_api, "get_available_gatefunctions", method="GET")
def get_available_gatefunctions(nodenet_uid):
    """ Return a dict of possible gatefunctions and their parameters"""
    return True, runtime.get_available_gatefunctions(nodenet_uid)


@rpc(core_rpc_api, "get_available_datasources", method="GET")
def get_available_datasources(nodenet_uid):
    """ Return an ordered list of available datasources """
    return True, runtime.get_available_datasources(nodenet_uid)


@rpc(core_rpc_api, "get_available_datatargets", method="GET")
def get_available_datatargets(nodenet_uid):
    """ Return an ordered list of available datatargets """
    return True, runtime.get_available_datatargets(nodenet_uid)


@rpc(core_rpc_api, "bind_datasource_to_sensor", permission_required="manage nodenets")
def bind_datasource_to_sensor(nodenet_uid, sensor_uid, datasource):
    """ Assign the given sensor to the given datasource """
    return runtime.bind_datasource_to_sensor(nodenet_uid, sensor_uid, datasource)


@rpc(core_rpc_api, "bind_datatarget_to_actuator", permission_required="manage nodenets")
def bind_datatarget_to_actuator(nodenet_uid, actuator_uid, datatarget):
    """ Assign the  given actuator to the given datatarget"""
    return runtime.bind_datatarget_to_actuator(nodenet_uid, actuator_uid, datatarget)


@rpc(core_rpc_api, "add_link", permission_required="manage nodenets")
def add_link(nodenet_uid, source_node_uid, gate_type, target_node_uid, slot_type, weight=1):
    """ Create a link between the given nodes """
    return runtime.add_link(nodenet_uid, source_node_uid, gate_type, target_node_uid, slot_type, weight=float(weight))


@rpc(core_rpc_api, "set_link_weight", permission_required="manage nodenets")
def set_link_weight(nodenet_uid, source_node_uid, gate_type, target_node_uid, slot_type, weight):
    """ Set the weight of an existing link between the given nodes """
    return runtime.set_link_weight(nodenet_uid, source_node_uid, gate_type, target_node_uid, slot_type, float(weight))


@rpc(core_rpc_api, "get_links_for_nodes")
def get_links_for_nodes(nodenet_uid, node_uids=[]):
    """ Return a dict, containing
    "links": List of links starting or ending at one of the given nodes
    "nodes": a dict of nodes that are connected by these links, but reside in other nodespaces
    """
    return True, runtime.get_links_for_nodes(nodenet_uid, node_uids)


@rpc(core_rpc_api, "delete_link", permission_required="manage nodenets")
def delete_link(nodenet_uid, source_node_uid, gate_type, target_node_uid, slot_type):
    """ Delete the given link"""
    return runtime.delete_link(nodenet_uid, source_node_uid, gate_type, target_node_uid, slot_type)


@rpc(core_rpc_api, "reload_code", permission_required="manage nodenets")
def reload_code():
    """ Reload the contents of the code-folder """
    return runtime.reload_code()


@rpc(core_rpc_api, "user_prompt_response")
def user_prompt_response(nodenet_uid, node_uid, key, parameters, resume_nodenet):
    """ Respond to a user-prompt issued by a node. """
    runtime.user_prompt_response(nodenet_uid, node_uid, key, parameters, resume_nodenet)
    return True


# Face
@rpc(core_rpc_api, "get_emoexpression_parameters", method="GET")
def get_emoexpression_parameters(nodenet_uid):
    """ Return a dict of parameters to visualize the emotional state of the agent """
    from micropsi_core import emoexpression
    nodenet = runtime.get_nodenet(nodenet_uid)
    return True, emoexpression.calc_emoexpression_parameters(nodenet)


# --------- logging --------


@rpc(core_rpc_api, "get_logging_levels", method="GET")
def get_logging_levels():
    """ Set the logging levels """
    return True, runtime.get_logging_levels()


@rpc(core_rpc_api, "set_logging_levels")
def set_logging_levels(logging_levels):
    """ Set the logging levels """
    runtime.set_logging_levels(logging_levels)
    return True


@rpc(core_rpc_api, "get_logger_messages", method="GET")
def get_logger_messages(logger=[], after=0):
    """ Get Logger messages for the given loggers, after the given timestamp """
    return True, runtime.get_logger_messages(logger, int(after))


@rpc(core_rpc_api, "get_monitoring_info", method="GET")
def get_monitoring_info(nodenet_uid, logger=[], after=0, monitor_from=0, monitor_count=-1):
    """ Return monitor, logger data """
    data = runtime.get_monitoring_info(nodenet_uid, logger, int(after), int(monitor_from), int(monitor_count))
    return True, data


# --------- benchmark info --------

@rpc(core_rpc_api, "benchmark_info", method="GET")
def benchmark_info():
    """ Time some math operations to determine the speed of the underlying machine. """
    return True, runtime.benchmark_info()


# --- user scripts ---

@rpc(core_rpc_api, "run_recipe")
def run_recipe(nodenet_uid, name, parameters):
    """ Run the recipe with the given name """
    return runtime.run_recipe(nodenet_uid, name, parameters)


@rpc(core_rpc_api, 'get_available_recipes', method="GET")
def get_available_recipes():
    """ Return a dict of available recipes """
    return True, runtime.get_available_recipes()


@rpc(core_rpc_api, "run_operation")
def run_operation(nodenet_uid, name, parameters, selection_uids):
    """ Run an operation on the given selection of nodes """
    return runtime.run_operation(nodenet_uid, name, parameters, selection_uids)


@rpc(core_rpc_api, 'get_available_operations', method="GET")
def get_available_operations():
    """ Return a dict of available operations """
    return True, runtime.get_available_operations()


@rpc(core_rpc_api, 'get_agent_dashboard', method="GET")
def get_agent_dashboard(nodenet_uid):
    """ Return a dict of data to display the agent's state in a dashboard """
    return True, runtime.get_agent_dashboard(nodenet_uid)


@rpc(core_rpc_api, "flow")
def flow(nodenet_uid, source_uid, source_output, target_uid, target_input):
    """ Create a connection between two flow_modules """
    return runtime.flow(nodenet_uid, source_uid, source_output, target_uid, target_input)


@rpc(core_rpc_api, "unflow")
def unflow(nodenet_uid, source_uid, source_output, target_uid, target_input):
    """ Remove the connection between the given flow_modules """
    return runtime.unflow(nodenet_uid, source_uid, source_output, target_uid, target_input)


@rpc(core_rpc_api, "runtime_info", method="GET")
def runtime_info():
    """ Return a dict of information about this runtime, like version and configuration"""
    return True, runtime.runtime_info()


def get_console_info():
    from jupyter_client import find_connection_file
    import socket
    from micropsi_server.micropsi_app import console_is_started
    if not console_is_started:
        return None
    connection_file = find_connection_file()
    with open(connection_file) as connection_info_file:
        connection_info = json.load(connection_info_file)
        if connection_info["ip"] != "127.0.0.1":
            external_ip = socket.gethostbyname(socket.gethostname())
            connection_info["ip"] = external_ip
        return connection_info
    return None


@rpc(core_rpc_api, "console_info", method="GET")
def console_info():
    """ Return a dict of information about the IPython console"""
    return True, get_console_info()
