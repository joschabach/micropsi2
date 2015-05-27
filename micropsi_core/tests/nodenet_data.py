
fixed_nodenet_data = """{
    "uid": "fixed_test_nodenet",
    "links": {
        "n3:sub:gen:n4": {
            "certainty": 1,
            "source_gate_name": "sub",
            "source_node_uid": "n3",
            "target_node_uid": "n4",
            "target_slot_name": "gen",
            "uid": "n3:sub:gen:n4",
            "weight": 1
        },
        "n1:por:gen:n2": {
            "certainty": 1,
            "source_gate_name": "por",
            "source_node_uid": "n1",
            "target_node_uid": "n2",
            "target_slot_name": "gen",
            "uid": "n1:por:gen:n2",
            "weight": 1
        },
        "n5:gen:gen:n3": {
            "certainty": 1,
            "source_gate_name": "gen",
            "source_node_uid": "n5",
            "target_node_uid": "n3",
            "target_slot_name": "gen",
            "uid": "n5:gen:gen:n3",
            "weight": 1
        },
        "n5:gen:gen:n1": {
            "certainty": 1,
            "source_gate_name": "gen",
            "source_node_uid": "n5",
            "target_node_uid": "n1",
            "target_slot_name": "gen",
            "uid": "n5:gen:gen:n1",
            "weight": 1
        }
    },
    "name": "fixed",
    "nodes": {
        "n1": {
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
            "uid": "n1"
        },
        "n5": {
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
            "uid": "n5"
        },
        "n2": {
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
            "uid": "n2"
        },
        "n3": {
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
            "uid": "n3"
        },
        "n6": {
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
            "uid": "n6"
        },
        "n4": {
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
            "uid": "n4"
        }
    }
}"""