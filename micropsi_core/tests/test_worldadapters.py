#!/usr/local/bin/python
# -*- coding: utf-8 -*-

"""

"""
import os
import mock
import pytest
from micropsi_core import runtime

from micropsi_core.world import worldadapter as wa

numpy_available = False
try:
    import numpy as np
    numpy_available = True
except ImportError:
    pass


def test_default_worldadater(default_world):

    adapter = wa.Default(runtime.worlds[default_world])

    sources = adapter.get_available_datasources()
    assert set(["static_on", "static_off", "random"]) == set(sources)
    targets = adapter.get_available_datatargets()
    assert set(["echo"]) == set(targets)

    assert adapter.get_datasource_value('static_on') == 1
    assert len(adapter.get_datasource_values()) == 3

    adapter.add_to_datatarget("echo", 0.3)
    adapter.add_to_datatarget("echo", 0.25)
    assert adapter.datatargets["echo"] == 0.55

    adapter.set_datatarget_values([0.7])
    assert adapter.datatargets["echo"] == 0.7

    adapter.update()

    assert adapter.get_datatarget_feedback_value("echo") == 0.7
    assert adapter.get_datatarget_feedback_values() == [0.7]

    adapter.set_datatarget_feedback_value("echo", 0.1)
    assert adapter.get_datatarget_feedback_values() == [0.1]


@pytest.mark.skipif(not numpy_available, reason="requires numpy")
def test_arrayworldadapter(default_world):

    class TestArrayWA(wa.ArrayWorldAdapter):
        def update_data_sources_and_targets(self):
            self.datasource_values = np.copy(self.datatarget_values) * 2
            self.datatarget_feedback_values = np.copy(self.datatarget_values)

    adapter = TestArrayWA(runtime.worlds[default_world])

    # datasources --------

    # add
    adapter.add_datasource("foo")
    adapter.add_datasource("bar", initial_value=0.7)
    assert adapter.datasource_names == ["foo", "bar"]

    # get
    assert adapter.get_available_datasources() == adapter.datasource_names
    assert np.allclose(adapter.get_datasource_value("bar"), 0.7)
    assert np.allclose(adapter.get_datasource_values(), np.asarray([0., .7]))

    # index
    assert adapter.get_datasource_index("bar") == 1

    # set
    adapter.set_datasource_value("foo", 123.)
    assert np.allclose(adapter.get_datasource_value("foo"), 123.)
    assert np.allclose(adapter.get_datasource_values(), np.asarray([123., 0.7]))
    adapter.set_datasource_values(np.asarray([.1, .2]))
    assert np.allclose(adapter.get_datasource_values(), np.asarray([.1, .2]))
    with pytest.raises(AssertionError):
        assert adapter.set_datasource_values(np.asarray([.1, .2, .3, .4, .5]))

    # datatargets --------

    # add
    adapter.add_datatarget("t_foo")
    adapter.add_datatarget("t_bar", initial_value=.6)
    assert adapter.datatarget_names == ["t_foo", "t_bar"]

    # get
    assert adapter.get_available_datatargets() == adapter.datatarget_names
    assert np.allclose(adapter.get_datatarget_value("t_bar"), 0.6)
    assert np.allclose(adapter.get_datatarget_values(), np.asarray([0., 0.6]))

    # index
    assert adapter.get_datatarget_index("t_bar") == 1

    # set
    adapter.set_datatarget_value("t_foo", .1)
    adapter.add_to_datatarget("t_foo", 2.1)
    assert np.allclose(adapter.get_datatarget_value("t_foo"), 2.2)
    assert np.allclose(adapter.get_datatarget_values(), np.asarray([2.2, 0.6]))
    adapter.set_datatarget_values(np.asarray([.1, .2]))
    assert np.allclose(adapter.get_datatarget_values(), np.asarray([.1, .2]))
    with pytest.raises(AssertionError):
        assert adapter.set_datatarget_values(np.asarray([.1, .2, .3, .4, .5]))

    # datatarget_feedback --------

    # get
    assert adapter.get_datatarget_feedback_value("t_foo") == 0.
    assert np.allclose(adapter.get_datatarget_feedback_values(), np.asarray([0, 0.6]))

    # set
    adapter.set_datatarget_feedback_value("t_bar", 123.)
    assert adapter.get_datatarget_feedback_value("t_bar") == 123.
    assert np.allclose(adapter.get_datatarget_feedback_values(), np.asarray([0., 123.]))
    adapter.set_datatarget_feedback_values(np.asarray([.1, .2]))
    assert np.allclose(adapter.get_datatarget_feedback_values(), np.asarray([.1, .2]))
    with pytest.raises(AssertionError):
        assert adapter.set_datatarget_feedback_values(np.asarray([.1, .2, .3, .4, .5]))


@pytest.mark.skipif(not numpy_available, reason="requires numpy")
def test_flow_datasources(default_world):

    class TestArrayWA(wa.ArrayWorldAdapter):
        def update_data_sources_and_targets(self):
            self.datasource_values = np.random.rand(self.datasource_values.shape).astype(self.floatX)
            self.datatarget_feedback_values = np.copy(self.datatarget_values).astype(self.floatX)

    adapter = TestArrayWA(runtime.worlds[default_world])

    vision_shape = (2, 5)
    vision_init = np.random.rand(*vision_shape).astype(adapter.floatX)
    adapter.add_datasource("s_foo")
    adapter.add_flow_datasource("s_vision", shape=vision_shape, initial_values=vision_init)
    adapter.add_datasource("s_bar")

    assert adapter.get_available_datasources() == ['s_foo', 's_bar']
    assert adapter.get_available_flow_datasources() == ['s_vision']

    motor_shape = (3, 2)
    adapter.add_datatarget("t_execute")
    adapter.add_flow_datatarget("t_motor", shape=motor_shape)

    assert adapter.get_available_datatargets() == ['t_execute']
    assert adapter.get_available_flow_datatargets() == ['t_motor']

    vision = np.random.rand(*vision_shape).astype(adapter.floatX)
    motor = np.random.rand(*motor_shape).astype(adapter.floatX)

    adapter.set_flow_datasource("s_vision", vision)
    adapter.add_to_flow_datatarget("t_motor", motor)
    adapter.add_to_flow_datatarget("t_motor", motor)

    assert np.allclose(adapter.get_flow_datasource("s_vision"), vision)
    assert np.allclose(adapter.get_flow_datatarget("t_motor"), 2 * motor)
    assert np.allclose(adapter.get_flow_datatarget_feedback("t_motor"), np.zeros((3, 2)))


def test_worldadapter_mixin(default_world):

    class TestMixin(wa.WorldAdapterMixin):

        @staticmethod
        def get_config_options():
            return [{"name": "some_setting", "default": 23}]

        def __init__(self, world, **data):
            super().__init__(world, **data)
            self.add_datasource("some_setting")

        def update_datasources_and_targets(self):
            super().update_datasources_and_targets()
            self.set_datasource_value("some_setting", self.some_setting)

    class TestArrayWA(TestMixin, wa.ArrayWorldAdapter):

        @staticmethod
        def get_config_options():
            params = TestMixin.get_config_options()
            params.extend([{"name": "other_setting", "default": 42}])
            return params

        def __init__(self, world, **data):
            super().__init__(world, **data)
            self.add_datasource("blubb")

        def update_data_sources_and_targets(self):
            super().update_datasources_and_targets()
            self.set_datasource_value("blubb", 21)

    world = runtime.worlds[default_world]
    adapter = TestArrayWA(world)
    adapter.update_data_sources_and_targets()
    assert adapter.get_datasource_value("blubb") == 21
    assert adapter.get_datasource_value("some_setting") == 23
    assert adapter.some_setting == 23
    assert adapter.other_setting == 42


def test_worldadapter_update_config(default_world, default_nodenet):
    runtime.set_nodenet_properties(default_nodenet, worldadapter="Default", world_uid=default_world)
    runtime.save_nodenet(default_nodenet)
    assert runtime.nodenets[default_nodenet].worldadapter_instance.foo == 'bar'
    runtime.set_nodenet_properties(default_nodenet, worldadapter="Default", world_uid=default_world, worldadapter_config={'foo': 'changed'})
    assert runtime.nodenets[default_nodenet].worldadapter_instance.foo == 'changed'
    assert runtime.nodenets[default_nodenet].worldadapter_instance.config['foo'] == 'changed'
    assert runtime.worlds[default_world].agents[default_nodenet].foo == 'changed'
