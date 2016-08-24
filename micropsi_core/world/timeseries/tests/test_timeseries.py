#!/usr/local/bin/python
# -*- coding: utf-8 -*-

import pytest

# skip these tests if numpy is not installed
pytest.importorskip("numpy")

import os
import numpy as np
import time
from datetime import datetime
from micropsi_core import runtime


def worldconfig():
    return {
        "time_series_data_file": 'test.npz',
        "shuffle": "False",
        "z_transform": "False",
        "clip_and_scale": "False",
        "sigmoid": "False",
        "realtime_per_entry": '0',
        "dummy_data": "False"
    }


def prepare_datafile(resourcepath):
    filename = os.path.join(resourcepath, "test.npz")
    timestamps = []
    data = []
    for i in range(5):
        data.append([i*0.1, i*0.2])
        timestamps.append(datetime.now())
    np.savez(
        filename,
        data=data,
        ids=['foo', 'bar'],
        timestamps=timestamps,
    )
    return filename, timestamps, data


def test_timeseries_world(resourcepath):
    filename, timestamps, data = prepare_datafile(resourcepath)
    config = worldconfig()
    config['time_series_data_file'] = filename
    success, world_uid = runtime.new_world("Timseries", "TimeSeries", owner="tester", config=config)
    assert success
    world = runtime.worlds[world_uid]
    assert world.__class__.__name__ == 'TimeSeries'

    for item in world.__class__.get_config_options():
        assert item['name'] in config

    result, worldadapter = world.register_nodenet('TimeSeriesRunner', 'test', nodenet_name='test')

    # step to the first dataset
    world.step()
    assert np.all(worldadapter.datasource_values == data[0])

    # manually set the world to timestamp #3
    world.set_user_data({'step': 3})

    # assert we're delivering the right data
    view = world.get_world_view(0)
    assert view['first_timestamp'] == timestamps[0].isoformat()
    assert view['last_timestamp'] == timestamps[-1].isoformat()
    assert view['total_timestamps'] == 5
    assert view['current_timestamp'] == timestamps[3].isoformat()
    assert view['current_step'] == 3

    # assert the worldadapter has the respective values: step 3 is 3rd timestamp, is index 2
    assert np.all(worldadapter.datasource_values == data[2])


def test_timeseries_shuffle(resourcepath):
    filename, timestamps, data = prepare_datafile(resourcepath)
    config = worldconfig()
    config['time_series_data_file'] = filename
    config['shuffle'] = "True"
    success, world_uid = runtime.new_world("Timseries", "TimeSeries", owner="tester", config=config)
    world = runtime.worlds[world_uid]
    result, worldadapter = world.register_nodenet('TimeSeriesRunner', 'test', nodenet_name='test')
    world.set_user_data({'step': 3})
    assert list(worldadapter.datasource_values) in data


def test_timeseries_sigmoid(resourcepath):
    filename, timestamps, data = prepare_datafile(resourcepath)
    config = worldconfig()
    config['time_series_data_file'] = filename
    config['sigmoid'] = "True"
    success, world_uid = runtime.new_world("Timseries", "TimeSeries", owner="tester", config=config)
    world = runtime.worlds[world_uid]
    result, worldadapter = world.register_nodenet('TimeSeriesRunner', 'test', nodenet_name='test')
    world.set_user_data({'step': 3})
    data = worldadapter.datasource_values
    assert round(data[0], 6) == 0.268941


def test_timeseries_dummydata(resourcepath):
    filename, timestamps, data = prepare_datafile(resourcepath)
    config = worldconfig()
    config['time_series_data_file'] = filename
    config['dummy_data'] = "True"
    success, world_uid = runtime.new_world("Timseries", "TimeSeries", owner="tester", config=config)
    world = runtime.worlds[world_uid]
    result, worldadapter = world.register_nodenet('TimeSeriesRunner', 'test', nodenet_name='test')
    world.set_user_data({'step': 3})
    assert len(worldadapter.datasource_values) == 10


def test_timeseries_invalid_file():
    config = worldconfig()
    config['time_series_data_file'] = '/tmp/nothere.npz'
    success, world_uid = runtime.new_world("Timseries", "TimeSeries", owner="tester", config=config)
    world = runtime.worlds[world_uid]
    assert world.timestamps == [0]
