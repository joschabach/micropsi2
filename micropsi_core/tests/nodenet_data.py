
fixed_nodenet_data = """{
    "links": {
        "7bf9769f-141e-4186-9a42-e62b40f91e2b": {
            "certainty": 1,
            "source_gate_name": "sub",
            "source_node": "7d101cf3-05a5-4d5d-976d-918690a09f83",
            "source_node_uid": "7d101cf3-05a5-4d5d-976d-918690a09f83",
            "target_node": "b807a7d8-2814-4809-bcee-6f8e1d33490c",
            "target_node_uid": "b807a7d8-2814-4809-bcee-6f8e1d33490c",
            "target_slot_name": "gen",
            "uid": "7bf9769f-141e-4186-9a42-e62b40f91e2b",
            "weight": 1
        },
        "ada8ae37-4bad-412b-afd2-77e6f2dfe0f7": {
            "certainty": 1,
            "source_gate_name": "por",
            "source_node": "21faed9c-f3b1-48e9-950f-bb219e655376",
            "source_node_uid": "21faed9c-f3b1-48e9-950f-bb219e655376",
            "target_node": "6380cb9c-beb2-494c-b649-2a514d70f858",
            "target_node_uid": "6380cb9c-beb2-494c-b649-2a514d70f858",
            "target_slot_name": "gen",
            "uid": "ada8ae37-4bad-412b-afd2-77e6f2dfe0f7",
            "weight": 1
        },
        "f136049a-63f6-4fe1-be92-21527565e649": {
            "certainty": 1,
            "source_gate_name": "gen",
            "source_node": "359095b7-7fe7-47fb-9fa6-136871edfe07",
            "source_node_uid": "359095b7-7fe7-47fb-9fa6-136871edfe07",
            "target_node": "7d101cf3-05a5-4d5d-976d-918690a09f83",
            "target_node_uid": "7d101cf3-05a5-4d5d-976d-918690a09f83",
            "target_slot_name": "gen",
            "uid": "f136049a-63f6-4fe1-be92-21527565e649",
            "weight": 1
        },
        "f3d12f50-3a70-4066-84e6-0262ad335277": {
            "certainty": 1,
            "source_gate_name": "gen",
            "source_node": "359095b7-7fe7-47fb-9fa6-136871edfe07",
            "source_node_uid": "359095b7-7fe7-47fb-9fa6-136871edfe07",
            "target_node": "21faed9c-f3b1-48e9-950f-bb219e655376",
            "target_node_uid": "21faed9c-f3b1-48e9-950f-bb219e655376",
            "target_slot_name": "gen",
            "uid": "f3d12f50-3a70-4066-84e6-0262ad335277",
            "weight": 1
        }
    },
    "name": "fixed",
    "nodes": {
        "21faed9c-f3b1-48e9-950f-bb219e655376": {
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
            "uid": "21faed9c-f3b1-48e9-950f-bb219e655376"
        },
        "359095b7-7fe7-47fb-9fa6-136871edfe07": {
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
            "uid": "359095b7-7fe7-47fb-9fa6-136871edfe07"
        },
        "6380cb9c-beb2-494c-b649-2a514d70f858": {
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
            "uid": "6380cb9c-beb2-494c-b649-2a514d70f858"
        },
        "7d101cf3-05a5-4d5d-976d-918690a09f83": {
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
            "uid": "7d101cf3-05a5-4d5d-976d-918690a09f83"
        },
        "88994f98-1e6e-488f-851c-896e779f4570": {
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
            "uid": "88994f98-1e6e-488f-851c-896e779f4570"
        },
        "b807a7d8-2814-4809-bcee-6f8e1d33490c": {
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
            "uid": "b807a7d8-2814-4809-bcee-6f8e1d33490c"
        },
        "d4e7ef80-12e5-4807-9b70-43191195934e": {
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
            "uid": "d4e7ef80-12e5-4807-9b70-43191195934e"
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