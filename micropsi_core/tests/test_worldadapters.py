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
    adapter.add_datasource("bar", initial_value=1)
    adapter.add_datasources(["baz", "qux"])
    adapter.add_datasources(["spam", "eggs"], initial_values=[1, 2])
    assert adapter.datasource_names == ["foo", "bar", "baz", "qux", "spam", "eggs"]

    # get
    assert adapter.get_available_datasources() == adapter.datasource_names
    assert adapter.get_datasource_value("eggs") == 2.0
    assert np.all(adapter.get_datasource_range("baz", 2) == np.asarray([0., 0.]))
    assert np.all(adapter.get_datasource_values() == np.asarray([0., 1., 0., 0., 1., 2.]))
    assert type(adapter.get_datasource_value("eggs")) == np.float64

    # index
    assert adapter.get_datasource_index("qux") == 3

    # set
    adapter.set_datasource_value("spam", 123.)
    assert adapter.get_datasource_value("spam") == 123.
    adapter.set_datasource_range("baz", [.34, .45])
    assert np.all(adapter.get_datasource_values() == np.asarray([0., 1., .34, .45, 123., 2.]))
    adapter.set_datasource_values(np.asarray([.1, .2, .3, .4, .5, .6]))
    assert np.all(adapter.get_datasource_values() == np.asarray([.1, .2, .3, .4, .5, .6]))
    with pytest.raises(AssertionError):
        assert adapter.set_datasource_values(np.asarray([.1, .2, .3, .4, .5]))

    # datatargets --------

    # add
    adapter.add_datatarget("t_foo")
    adapter.add_datatarget("t_bar", initial_value=1)
    adapter.add_datatargets(["t_baz", "t_qux"])
    adapter.add_datatargets(["t_spam", "t_eggs"], initial_values=[1, 2])
    assert adapter.datatarget_names == ["t_foo", "t_bar", "t_baz", "t_qux", "t_spam", "t_eggs"]

    # get
    assert adapter.get_available_datatargets() == adapter.datatarget_names
    assert adapter.get_datatarget_value("t_eggs") == 2.0
    assert np.all(adapter.get_datatarget_range("t_baz", 2) == np.asarray([0., 0.]))
    assert np.all(adapter.get_datatarget_values() == np.asarray([0., 1., 0., 0., 1., 2.]))
    assert type(adapter.get_datatarget_value("t_eggs")) == np.float64

    # index
    assert adapter.get_datatarget_index("t_qux") == 3

    # set
    adapter.set_datatarget_value("t_spam", .1)
    adapter.add_to_datatarget("t_spam", 123.)
    assert adapter.get_datatarget_value("t_spam") == 123.1
    adapter.set_datatarget_range("t_baz", [.34, .45])
    assert np.all(adapter.get_datatarget_values() == np.asarray([0., 1., .34, .45, 123.1, 2.]))
    adapter.set_datatarget_values(np.asarray([.1, .2, .3, .4, .5, .6]))
    assert np.all(adapter.get_datatarget_values() == np.asarray([.1, .2, .3, .4, .5, .6]))
    with pytest.raises(AssertionError):
        assert adapter.set_datatarget_values(np.asarray([.1, .2, .3, .4, .5]))

    # datatarget_feedback --------

    # get
    assert adapter.get_datatarget_feedback_value("t_eggs") == 2.0
    assert np.all(adapter.get_datatarget_feedback_range("t_baz", 2) == np.asarray([0., 0.]))
    assert np.all(adapter.get_datatarget_feedback_values() == np.asarray([0., 1., 0., 0., 1., 2.]))
    assert type(adapter.get_datatarget_feedback_value("t_eggs")) == np.float64

    # set
    adapter.set_datatarget_feedback_value("t_spam", 123.)
    assert adapter.get_datatarget_feedback_value("t_spam") == 123.
    adapter.set_datatarget_feedback_range("t_baz", [.34, .45])
    assert np.all(adapter.get_datatarget_feedback_values() == np.asarray([0., 1., .34, .45, 123., 2.]))
    adapter.set_datatarget_feedback_values(np.asarray([.1, .2, .3, .4, .5, .6]))
    assert np.all(adapter.get_datatarget_feedback_values() == np.asarray([.1, .2, .3, .4, .5, .6]))
    with pytest.raises(AssertionError):
        assert adapter.set_datatarget_feedback_values(np.asarray([.1, .2, .3, .4, .5]))


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
