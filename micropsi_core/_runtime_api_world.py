# -*- coding: utf-8 -*-

"""
Runtime API: operations for creating and maintaining worlds (environments for nodenet driven agents)
"""

import json
import os
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
        return dict((uid, micropsi_core.runtime.worlds[uid]) for uid in micropsi_core.runtime.worlds if
                    micropsi_core.runtime.worlds[uid].owner == owner)
    else:
        return micropsi_core.runtime.worlds


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


def get_worldadapters(world_uid):
    """Returns the world adapters available in the given world"""

    data = {}
    if world_uid in micropsi_core.runtime.worlds:
        for name, worldadapter in micropsi_core.runtime.worlds[world_uid].supported_worldadapters.items():
            data[name] = {
                'datasources': worldadapter.supported_datasources,
                'datatargets': worldadapter.supported_datatargets
            }
    return data


def get_world_objects(world_uid, type=None):
    if world_uid in micropsi_core.runtime.worlds:
        return micropsi_core.runtime.worlds[world_uid].get_world_objects(type)
    return False


def delete_worldobject(world_uid, object_uid):
    return micropsi_core.runtime.worlds[world_uid].delete_object(object_uid)


def add_worldobject(world_uid, type, position, orientation=0.0, name="", parameters=None, uid=None):
    return micropsi_core.runtime.worlds[world_uid].add_object(type, position, orientation=orientation, name=name,
                                                              parameters=parameters, uid=uid)


def set_worldobject_properties(world_uid, uid, position=None, orientation=None, name=None, parameters=None):
    return micropsi_core.runtime.worlds[world_uid].set_object_properties(uid, position, orientation, name,
                                                                         parameters)


def set_worldagent_properties(world_uid, uid, position=None, orientation=None, name=None, parameters=None):
    return micropsi_core.runtime.worlds[world_uid].set_agent_properties(uid, position, orientation, name, parameters)


def new_world(world_name, world_type, owner="", uid=None):
    """Creates a new world  and registers it.

    Arguments:
        world_name: the name of the world
        world_type: the type of the world
        owner (optional): the creator of this world

    Returns
        world_uid if successful,
        None if failure
    """
    if uid is None:
        uid = tools.generate_uid()

    filename = os.path.join(micropsi_core.runtime.RESOURCE_PATH, micropsi_core.runtime.WORLD_DIRECTORY, uid + ".json")
    micropsi_core.runtime.world_data[uid] = Bunch(uid=uid, name=world_name, world_type=world_type, filename=filename,
                                                  version=1,
                                                  owner=owner)
    with open(filename, 'w+') as fp:
        fp.write(json.dumps(micropsi_core.runtime.world_data[uid], sort_keys=True, indent=4))
    try:
        kwargs = micropsi_core.runtime.world_data[uid]
        micropsi_core.runtime.worlds[uid] = get_world_class_from_name(world_type)(**kwargs)
    except AttributeError:
        return False, "World type unknown"
    return True, uid


def delete_world(world_uid):
    """Removes the world with the given uid from the server (and unloads it from memory if it is running.)"""
    for uid in micropsi_core.runtime.nodenets:
        if micropsi_core.runtime.nodenets[uid].world and micropsi_core.runtime.nodenets[uid].world.uid == world_uid:
            micropsi_core.runtime.nodenets[uid].world = None
    del micropsi_core.runtime.worlds[world_uid]
    os.remove(micropsi_core.runtime.world_data[world_uid].filename)
    del micropsi_core.runtime.world_data[world_uid]
    return True


def get_world_view(world_uid, step):
    """Returns the current state of the world for UI purposes, if current step is newer than the supplied one."""
    if world_uid not in micropsi_core.runtime.worlds:
        raise KeyError("World not found")
    if world_uid in micropsi_core.runtime.MicropsiRunner.last_world_exception:
        e = micropsi_core.runtime.MicropsiRunner.last_world_exception[world_uid]
        del micropsi_core.runtime.MicropsiRunner.last_world_exception[world_uid]
        raise Exception("Error while stepping world").with_traceback(e[2]) from e[1]
    if step <= micropsi_core.runtime.worlds[world_uid].current_step:
        return micropsi_core.runtime.worlds[world_uid].get_world_view(step)
    return {}


def set_world_properties(world_uid, world_name=None, owner=None):
    """Sets the supplied parameters (and only those) for the world with the given uid."""
    if world_uid not in micropsi_core.runtime.worlds:
        raise KeyError("World not found")
    micropsi_core.runtime.worlds[world_uid].name = world_name
    micropsi_core.runtime.worlds[world_uid].owner = owner
    return True


def revert_world(world_uid):
    """Reverts the world to the last saved state."""
    data = micropsi_core.runtime.world_data[world_uid]
    micropsi_core.runtime.worlds[world_uid] = get_world_class_from_name(data.world_type)(**data)
    return True


def save_world(world_uid):
    """Stores the world state on the server."""
    with open(os.path.join(micropsi_core.runtime.RESOURCE_PATH, micropsi_core.runtime.WORLD_DIRECTORY,
                           world_uid) + '.json', 'w+') as fp:
        fp.write(json.dumps(micropsi_core.runtime.worlds[world_uid].data, sort_keys=True, indent=4))
    return True


def export_world(world_uid):
    """Returns a JSON string with the current state of the world."""
    return json.dumps(micropsi_core.runtime.worlds[world_uid].data, sort_keys=True, indent=4)


def import_world(worlddata, owner=None):
    """Imports a JSON string with world data. May not overwrite an existing world."""
    data = json.loads(worlddata)
    if not 'uid' in data:
        data['uid'] = tools.generate_uid()
    else:
        if data['uid'] in micropsi_core.runtime.worlds:
            raise RuntimeError("A world with this ID already exists.")
    if owner is not None:
        data['owner'] = owner
    filename = os.path.join(micropsi_core.runtime.RESOURCE_PATH, micropsi_core.runtime.WORLD_DIRECTORY, data['uid'] + '.json')
    data['filename'] = filename
    with open(filename, 'w+') as fp:
        fp.write(json.dumps(data))
    micropsi_core.runtime.world_data[data['uid']] = micropsi_core.runtime.parse_definition(data, filename)
    micropsi_core.runtime.worlds[data['uid']] = get_world_class_from_name(
        micropsi_core.runtime.world_data[data['uid']].world_type)(
        **micropsi_core.runtime.world_data[data['uid']])
    return data['uid']


def get_world_class_from_name(world_type):
    """Returns the class from a world type, if it is known"""
    from micropsi_core.world.world import World

    worldclasses = {cls.__name__: cls for cls in tools.itersubclasses(World)}
    return worldclasses.get(world_type, World)


def get_available_world_types():
    """Returns the names of the available world types"""
    import importlib
    from micropsi_core.world.world import World
    return [cls.__name__ for cls in tools.itersubclasses(vars()['World'])]
    for cls in tools.itersubclasses(World):
        if 'minecraft' in cls.__name__.toLower():
            try:
                import spock
            except:
                # requirement not satisfied, ignore
                continue
        available_worlds.append(cls.__name__)
    return available_worlds
