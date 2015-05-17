
fixed_nodenet_data = """{
    "uid": "fixed_test_nodenet",
    "links": {
        "B1:sub:gen:B2": {
            "certainty": 1,
            "source_gate_name": "sub",
            "source_node_uid": "B1",
            "target_node_uid": "B2",
            "target_slot_name": "gen",
            "uid": "B1:sub:gen:B2",
            "weight": 1
        },
        "A1:por:gen:A2": {
            "certainty": 1,
            "source_gate_name": "por",
            "source_node_uid": "A1",
            "target_node_uid": "A2",
            "target_slot_name": "gen",
            "uid": "A1:por:gen:A2",
            "weight": 1
        },
        "S:gen:gen:B1": {
            "certainty": 1,
            "source_gate_name": "gen",
            "source_node_uid": "S",
            "target_node_uid": "B1",
            "target_slot_name": "gen",
            "uid": "S:gen:gen:B1",
            "weight": 1
        },
        "S:gen:gen:A1": {
            "certainty": 1,
            "source_gate_name": "gen",
            "source_node_uid": "S",
            "target_node_uid": "A1",
            "target_slot_name": "gen",
            "uid": "S:gen:gen:A1",
            "weight": 1
        }
    },
    "name": "fixed",
    "nodes": {
        "A1": {
            "activation": 0,
            "index": 2,
            "name": "A1",
            "parameters": {},
            "parent_nodespace": "Root",
            "position": [
                367,
                115
            ],
            "type": "Concept",
            "uid": "A1"
        },
        "S": {
            "activation": 0,
            "index": 1,
            "name": "",
            "parameters": {
                "datasource": "brightness_l"
            },
            "parent_nodespace": "Root",
            "position": [
                163,
                138
            ],
            "type": "Sensor",
            "uid": "S"
        },
        "A2": {
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
            "type": "Concept",
            "uid": "A2"
        },
        "B1": {
            "activation": 0,
            "index": 3,
            "name": "",
            "parameters": {},
            "parent_nodespace": "Root",
            "position": [
                367,
                296
            ],
            "type": "Concept",
            "uid": "B1"
        },
        "ACTA": {
            "activation": 0,
            "index": 6,
            "name": "",
            "parameters": {
                "type": "por"
            },
            "parent_nodespace": "Root",
            "position": [
                749,
                103
            ],
            "type": "Activator",
            "uid": "ACTA"
        },
        "B2": {
            "activation": 0,
            "index": 5,
            "name": "",
            "parameters": {},
            "parent_nodespace": "Root",
            "position": [
                568,
                298
            ],
            "type": "Concept",
            "uid": "B2"
        },
        "ACTB": {
            "activation": 0,
            "index": 7,
            "name": "",
            "parameters": {
                "type": "sub"
            },
            "parent_nodespace": "Root",
            "position": [
                743,
                336
            ],
            "type": "Activator",
            "uid": "ACTB"
        }
    }
}"""