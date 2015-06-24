
fixed_nodenet_data = """{
    "uid": "fixed_test_nodenet",
    "links": {
        "n0003:sub:gen:n0004": {
            "certainty": 1,
            "source_gate_name": "sub",
            "source_node_uid": "n0003",
            "target_node_uid": "n0004",
            "target_slot_name": "gen",
            "uid": "n0003:sub:gen:n0004",
            "weight": 1
        },
        "n0001:por:gen:n0002": {
            "certainty": 1,
            "source_gate_name": "por",
            "source_node_uid": "n0001",
            "target_node_uid": "n0002",
            "target_slot_name": "gen",
            "uid": "n0001:por:gen:n0002",
            "weight": 1
        },
        "n0005:gen:gen:n0003": {
            "certainty": 1,
            "source_gate_name": "gen",
            "source_node_uid": "n0005",
            "target_node_uid": "n0003",
            "target_slot_name": "gen",
            "uid": "n0005:gen:gen:n0003",
            "weight": 1
        },
        "n0005:gen:gen:n0001": {
            "certainty": 1,
            "source_gate_name": "gen",
            "source_node_uid": "n0005",
            "target_node_uid": "n0001",
            "target_slot_name": "gen",
            "uid": "n0005:gen:gen:n0001",
            "weight": 1
        }
    },
    "name": "fixed",
    "nodes": {
        "n0001": {
            "activation": 0,
            "index": 2,
            "name": "A1",
            "parameters": {},
            "parent_nodespace": "Root",
            "position": [
                367,
                115
            ],
            "type": "Pipe",
            "uid": "n0001"
        },
        "n0005": {
            "activation": 0,
            "index": 1,
            "name": "S",
            "parameters": {
                "datasource": "brightness_l"
            },
            "parent_nodespace": "Root",
            "position": [
                163,
                138
            ],
            "type": "Sensor",
            "uid": "n0005"
        },
        "n0002": {
            "activation": 0,
            "index": 4,
            "name": "A2",
            "parameters": {
                "foo": "23"
            },
            "parent_nodespace": "Root",
            "position": [
                567,
                118
            ],
            "type": "Pipe",
            "uid": "n0002"
        },
        "n0003": {
            "activation": 0,
            "index": 3,
            "name": "B1",
            "parameters": {},
            "parent_nodespace": "Root",
            "position": [
                367,
                296
            ],
            "type": "Pipe",
            "uid": "n0003"
        },
        "n0006": {
            "activation": 0,
            "index": 6,
            "name": "ACTA",
            "parameters": {
                "type": "por"
            },
            "parent_nodespace": "Root",
            "position": [
                749,
                103
            ],
            "type": "Activator",
            "uid": "n0006"
        },
        "n0004": {
            "activation": 0,
            "index": 5,
            "name": "B2",
            "parameters": {},
            "parent_nodespace": "Root",
            "position": [
                568,
                298
            ],
            "type": "Pipe",
            "uid": "n0004"
        }
    }
}"""