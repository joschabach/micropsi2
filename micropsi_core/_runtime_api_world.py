# -*- coding: utf-8 -*-

"""
Runtime API: operations for creating and maintaining worlds (environments for nodenet driven agents)
"""

import json
import os
import logging
import micropsi_core
from micropsi_core import tools
from micropsi_core.tools import Bunch
from micropsi_core.world import world

__author__ = 'joscha'
__date__ = '11.12.12'


# World
def get_available_worlds(owner=None):
    """Returns a dict of uids: World of (running and stored) worlds.

    Arguments:
        owner (optional): when submitted, the list is filtered by this owner
    """
    if owner:
        return dict((uid, micropsi_core.runtime.world_data[uid]) for uid in micropsi_core.runtime.world_data if
                    micropsi_core.runtime.world_data[uid].get('owner') is None or micropsi_core.runtime.world_data[uid].get('owner') == owner)
    else:
        return micropsi_core.runtime.world_data


def get_world_uid_by_name(name):
    """ Returns the uid of the world with the given name, or None if no matching world was found """
    for uid in micropsi_core.runtime.world_data:
        if micropsi_core.runtime.world_data[uid]['name'] == name:
            return uid
    else:
        return None


def get_world_properties(world_uid):
    """ Returns some information about the current world for the client:
    * Available worldadapters
    * Datasources and -targets offered by the world / worldadapter
    * Available Nodetypes

    Arguments:
        world_uid: the uid of the worldad

    Returns:
        dictionary containing the information
    """

    data = micropsi_core.runtime.worlds[world_uid].data
    data['worldadapters'] = get_worldadapters(world_uid)
    data['available_worldobjects'] = [key for key in micropsi_core.runtime.worlds[world_uid].supported_worldobjects]
    data['available_worldadapters'] = [key for key in micropsi_core.runtime.worlds[world_uid].supported_worldadapters]
    return data


def get_worldadapters(world_uid, nodenet_uid=None):
    """ Returns the world adapters available in the given world. Provide an optional nodenet_uid of an agent
    in the given world to obtain datasources and datatargets for the agent's worldadapter"""
    data = {}
    worlddata = micropsi_core.runtime.world_data[world_uid]
    supported_worldadapters = get_world_class_from_name(worlddata.get('world_type', 'World')).get_supported_worldadapters()
    for name, worldadapter in supported_worldadapters.items():
        data[name] = {
            'name': worldadapter.__name__,
            'description': worldadapter.__doc__,
            'config_options': worldadapter.get_config_options()
        }
    if world_uid in micropsi_core.runtime.worlds:
        world = micropsi_core.runtime.worlds[world_uid]
        if nodenet_uid and nodenet_uid in world.agents:
            agent = world.agents[nodenet_uid]
            data[agent.__class__.__name__]['config'] = micropsi_core.runtime.nodenets[nodenet_uid].metadata['worldadapter_config']
            data[agent.__class__.__name__]['datasources'] = agent.get_available_datasources()
            data[agent.__class__.__name__]['datatargets'] = agent.get_available_datatargets()
    return data


def get_world_objects(world_uid, type=None):
    if world_uid in micropsi_core.runtime.worlds:
        return micropsi_core.runtime.worlds[world_uid].get_world_objects(type)
    return False


def delete_worldobject(world_uid, object_uid):
    return micropsi_core.runtime.worlds[world_uid].delete_object(object_uid)


def add_worldobject(world_uid, type, position, orientation=0.0, name="", parameters=None):
    return micropsi_core.runtime.worlds[world_uid].add_object(type, position, orientation=orientation, name=name,
                                                              parameters=parameters)


def set_worldobject_properties(world_uid, uid, position=None, orientation=None, name=None, parameters=None):
    return micropsi_core.runtime.worlds[world_uid].set_object_properties(uid, position, orientation, name,
                                                                         parameters)


def set_worldagent_properties(world_uid, uid, position=None, orientation=None, name=None, parameters=None):
    return micropsi_core.runtime.worlds[world_uid].set_agent_properties(uid, position, orientation, name, parameters)


def new_world(world_name, world_type, owner="admin", config={}):
    """Creates a new world  and registers it.

    Arguments:
        world_name (string): the name of the world
        world_type (string): the type of the world
        owner (string, optional): the creator of this world
        config (dict, optional): configuration for the new world instance

    Returns
        world_uid if successful,
        None if failure
    """
    uid = tools.generate_uid()

    if world_type.startswith('Minecraft'):
        for uid in micropsi_core.runtime.worlds:
            if micropsi_core.runtime.worlds[uid].__class__.__name__.startswith('Minecraft'):
                raise RuntimeError("Only one instance of a minecraft environment is supported right now")

    world_class = get_world_class_from_name(world_type)

    # default missing config values
    for item in world_class.get_config_options():
        if item['name'] not in config:
            config[item['name']] = item.get('default')

    filename = os.path.join(micropsi_core.runtime.PERSISTENCY_PATH, micropsi_core.runtime.WORLD_DIRECTORY, uid + ".json")
    micropsi_core.runtime.world_data[uid] = Bunch(uid=uid, name=world_name, world_type=world_type, filename=filename,
                    version=world.WORLD_VERSION, owner=owner, config=config)
    with open(filename, 'w+', encoding="utf-8") as fp:
        fp.write(json.dumps(micropsi_core.runtime.world_data[uid], sort_keys=True, indent=4))
    try:
        kwargs = micropsi_core.runtime.world_data[uid]
        micropsi_core.runtime.worlds[uid] = world_class(**kwargs)
    except Exception as e:
        os.remove(filename)
        raise e
    return True, uid


def delete_world(world_uid):
    """Removes the world with the given uid from the server (and unloads it from memory if it is running.)"""

    if world_uid not in micropsi_core.runtime.world_data:
        raise KeyError("Environment not found")

    # remove a running instance if there should be one
    if world_uid in micropsi_core.runtime.worlds:
        world = micropsi_core.runtime.worlds[world_uid]
        for uid in list(world.agents.keys()):
            world.unregister_nodenet(uid)
            micropsi_core.runtime.nodenets[uid].worldadapter_instance = None
            micropsi_core.runtime.nodenets[uid].world = None
        micropsi_core.runtime.worlds[world_uid].__del__()
        del micropsi_core.runtime.worlds[world_uid]

    # delete metadata
    os.remove(micropsi_core.runtime.world_data[world_uid].filename)
    del micropsi_core.runtime.world_data[world_uid]
    return True


def get_world_view(world_uid, step):
    """Returns the current state of the world for UI purposes, if current step is newer than the supplied one."""
    if world_uid not in micropsi_core.runtime.worlds:
        raise KeyError("Environment not found")
    if world_uid in micropsi_core.runtime.MicropsiRunner.last_world_exception:
        e = micropsi_core.runtime.MicropsiRunner.last_world_exception[world_uid]
        del micropsi_core.runtime.MicropsiRunner.last_world_exception[world_uid]
        raise Exception("Error while stepping environment").with_traceback(e[2]) from e[1]
    if step <= micropsi_core.runtime.worlds[world_uid].current_step:
        return micropsi_core.runtime.worlds[world_uid].get_world_view(step)
    return {}


def set_world_properties(world_uid, world_name=None, owner=None, config=None):
    """Sets the supplied parameters (and only those) for the world with the given uid."""
    if world_uid not in micropsi_core.runtime.world_data:
        raise KeyError("Environment not found")

    if world_name is not None:
        micropsi_core.runtime.world_data[world_uid]['name'] = world_name
    if owner is not None:
        micropsi_core.runtime.world_data[world_uid]['owner'] = owner
    if config is not None:
        micropsi_core.runtime.world_data[world_uid]['config'].update(config)

    filename = os.path.join(micropsi_core.runtime.PERSISTENCY_PATH, micropsi_core.runtime.WORLD_DIRECTORY, world_uid)
    with open(filename + '.json', 'w+', encoding="utf-8") as fp:
        fp.write(json.dumps(micropsi_core.runtime.world_data[world_uid], sort_keys=True, indent=4))

    # if this world is running, revert to new settings and re-register agents
    if world_uid in micropsi_core.runtime.worlds:

        agent_data = {}
        for uid, net in micropsi_core.runtime.nodenets.items():
            if net.world == world_uid:
                agent_data[uid] = {
                    'nodenet_name': net.name,
                    'worldadapter': net.worldadapter,
                    'config': net.metadata['worldadapter_config']
                }

        micropsi_core.runtime.revert_world(world_uid)
        # re-register all agents:
        for uid, data in agent_data.items():
            result, worldadapter_instance = micropsi_core.runtime.worlds[world_uid].register_nodenet(data.pop('worldadapter'), uid, **data)
            if result:
                micropsi_core.runtime.nodenets[uid].worldadapter_instance = worldadapter_instance
            else:
                micropsi_core.runtime.nodenets[uid].worldadapter_instance = None
                logging.getLogger("system").warning("Could not spawn agent %s in environment %s" % (uid, world_uid))
    return True


def set_world_data(world_uid, data):
    """ Sets some data for the world. Whatever the world supports"""
    if world_uid not in micropsi_core.runtime.worlds:
        raise KeyError("Environment not found")
    micropsi_core.runtime.worlds[world_uid].set_user_data(data)
    return True


def revert_world(world_uid):
    """Reverts the world to the last saved state."""
    unload_world(world_uid)
    load_world(world_uid)
    return True


def unload_world(world_uid):
    if world_uid in micropsi_core.runtime.worlds:
        micropsi_core.runtime.worlds[world_uid].__del__()
        del micropsi_core.runtime.worlds[world_uid]
    return True


def load_world(world_uid):
    if world_uid not in micropsi_core.runtime.worlds:
        if world_uid in micropsi_core.runtime.world_data:
            data = micropsi_core.runtime.world_data[world_uid]
            if "world_type" in data:
                try:
                    micropsi_core.runtime.worlds[world_uid] = get_world_class_from_name(data.world_type)(**data)
                except Exception as e:
                    logging.getLogger("system").error("Could not load world %s: %s - %s" % (data.world_type, e.__class__.__name__, str(e)))
            else:
                micropsi_core.runtime.worlds[world_uid] = world.World(**data)
    return micropsi_core.runtime.worlds.get(world_uid)


def save_world(world_uid):
    """Stores the world state on the server."""
    data = micropsi_core.runtime.worlds[world_uid].data
    filename = os.path.join(micropsi_core.runtime.PERSISTENCY_PATH, micropsi_core.runtime.WORLD_DIRECTORY, world_uid)
    with open(filename + '.json', 'w+', encoding="utf-8") as fp:
        fp.write(json.dumps(data, sort_keys=True, indent=4))
    return True


def export_world(world_uid):
    """Returns a JSON string with the current state of the world."""
    return json.dumps(micropsi_core.runtime.worlds[world_uid].data, sort_keys=True, indent=4)


def import_world(worlddata, owner=None):
    """Imports a JSON string with world data. May not overwrite an existing world."""
    data = json.loads(worlddata)
    if 'uid' not in data:
        data['uid'] = tools.generate_uid()
    else:
        if data['uid'] in micropsi_core.runtime.worlds:
            raise RuntimeError("An environment with this ID already exists.")
    if owner is not None:
        data['owner'] = owner
    filename = os.path.join(micropsi_core.runtime.PERSISTENCY_PATH, micropsi_core.runtime.WORLD_DIRECTORY, data['uid'] + '.json')
    data['filename'] = filename
    with open(filename, 'w+', encoding="utf-8") as fp:
        fp.write(json.dumps(data))
    micropsi_core.runtime.world_data[data['uid']] = micropsi_core.runtime.parse_definition(data, filename)
    micropsi_core.runtime.worlds[data['uid']] = get_world_class_from_name(
        micropsi_core.runtime.world_data[data['uid']].world_type)(
        **micropsi_core.runtime.world_data[data['uid']])
    return data['uid']


def get_world_class_from_name(world_type, case_sensitive=True):
    """Returns the class from a world type, if it is known"""
    from micropsi_core.world.world import World
    if case_sensitive:
        return micropsi_core.runtime.world_classes[world_type]
    else:
        for key in micropsi_core.runtime.world_classes:
            if key.lower() == world_type.lower():
                return micropsi_core.runtime.world_classes[key]


def get_available_world_types():
    """Returns a mapping of the available world type names to their classes"""
    data = {}
    for name, cls in micropsi_core.runtime.world_classes.items():
        data[name] = {
            'class': cls,
            'config': cls.get_config_options(),
        }
    return data
