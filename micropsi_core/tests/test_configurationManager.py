#!/usr/local/bin/python
# -*- coding: utf-8 -*-

"""

"""
import os
import tempfile
import pytest
from micropsi_core.config import ConfigurationManager


__author__ = 'joscha'
__date__ = '29.10.12'


@pytest.fixture(scope="session")
def path():
    return os.path.join(tempfile.gettempdir(), "configs.json")

@pytest.fixture(scope="session")
def path2():
    return os.path.join(tempfile.gettempdir(), "configs2.json")

def test_create_configs(path, path2):
    conf_mgr = ConfigurationManager(path)
    try:
        os.remove(path)
        os.remove(path2)
    except: pass
    assert not os.path.exists(path)
    conf_mgr.save_configs()
    assert os.path.exists(path)

    conf2 = ConfigurationManager(path2) # we can have two config managers

    conf_mgr["height"] = 20
    conf_mgr["name"] = "Klaus"
    conf_mgr["record"] = { "i":12 }
    conf2["color"] = "blue"

    assert "color" not in conf_mgr
    assert "height" not in conf2
    assert conf_mgr["height"] == 20
    assert conf_mgr["name"] == "Klaus"
    assert conf_mgr["record"]["i"] == 12
    assert conf2["color"] == "blue"
    del conf_mgr["name"]
    assert "name" not in conf_mgr

    del conf_mgr
    del conf2

    conf_mgr = ConfigurationManager(path)
    conf2 = ConfigurationManager(path2)

    assert "color" not in conf_mgr
    assert "height" not in conf2
    assert conf_mgr["height"] == 20
    assert "name" not in conf_mgr
    assert conf_mgr["record"]["i"] == 12
    assert conf2["color"] == "blue"

    with pytest.raises(RuntimeError):
        conf3 = ConfigurationManager(path) # we cannot have more than one config manager at a single path
