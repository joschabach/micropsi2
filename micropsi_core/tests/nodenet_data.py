
fixed_nodenet_data = """{
    "uid": "fixed_test_nodenet",
    "links": {
        "B1B2": {
            "certainty": 1,
            "source_gate_name": "sub",
            "source_node": "B1",
            "source_node_uid": "B1",
            "target_node": "B2",
            "target_node_uid": "B2",
            "target_slot_name": "gen",
            "uid": "B1B2",
            "weight": 1
        },
        "A1A2": {
            "certainty": 1,
            "source_gate_name": "por",
            "source_node": "A1",
            "source_node_uid": "A1",
            "target_node": "A2",
            "target_node_uid": "A2",
            "target_slot_name": "gen",
            "uid": "A1A2",
            "weight": 1
        },
        "SB1": {
            "certainty": 1,
            "source_gate_name": "gen",
            "source_node": "S",
            "source_node_uid": "S",
            "target_node": "B1",
            "target_node_uid": "B1",
            "target_slot_name": "gen",
            "uid": "SB1",
            "weight": 1
        },
        "SA1": {
            "certainty": 1,
            "source_gate_name": "gen",
            "source_node": "S",
            "source_node_uid": "S",
            "target_node": "A1",
            "target_node_uid": "A1",
            "target_slot_name": "gen",
            "uid": "SA1",
            "weight": 1
        }
    },
    "name": "fixed",
    "nodes": {
        "A1": {
            "activation": 0,
            "index": 2,
            "name": "",
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
                "datasource": "default"
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
            "name": "testnode",
            "parameters": {
                "foo": "23"
            },
            "parent_nodespace": "Root",
            "position": [
                567,
                118
            ],
            "type": "test_type",
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
    },
    "nodetypes": {
            "test_type": {
                "gatetypes": [
                    "gen",
                    "por",
                    "ret",
                    "sub",
                    "sur",
                    "isa",
                    "exp"
                ],
                "name": "test_type",
                "nodefunction_definition": "for type, gate in node.gates.items(): gate.gate_function(node.activation)",
                "parameters": [
                    "foo"
                ],
                "slottypes": [
                    "gen"
                ],
                "states": []
            }
        }
}"""