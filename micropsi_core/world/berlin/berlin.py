from micropsi_core.world.world import World

import json
import worldobject
import os


class Berlin(World):

    supported_worldadapters = ['Default']

    coords = {
        'y1': 52.599034,
        'x1': 13.192637,
        'y2': 52.412211,
        'x2': 13.688858,
    }

    representation_2d = {
        'image': 'berlin/berlin_transit2.png',
        'x': 1445,
        'y': 900
    }

    def __init__(self, runtime, filename, world_type="", name="", owner="", uid=None, version=1):
        World.__init__(self, runtime, filename, world_type=world_type, name=name, owner=owner, uid=uid, version=version)
        self.data['representation_2d'] = self.representation_2d
        self.scale_x = (self.representation_2d['x'] / -(self.coords['x1'] - self.coords['x2']))
        self.scale_y = (self.representation_2d['y'] / -(self.coords['y1'] - self.coords['y2']))
        self.add_transit_stations()

    def add_transit_stations(self):
        filename = os.path.join(os.path.dirname(__file__), 'fahrinfo_berlin.json')
        with open(filename) as file:
            data = json.load(file)
            for key, entry in data["stations"].items():
                type = "other"
                entry.pop('line_names')
                traintypes = entry.pop('train_types')
                if "S" in traintypes:
                    if "U" in traintypes:
                        type = "S+U"
                    else:
                        type = "S"
                elif "U" in traintypes:
                    type = "U"
                elif "Tram" in traintypes:
                    type = "Tram"
                elif "Bus" in traintypes:
                    type = "Bus"
                entry['stationtype'] = type
                if 'lon' in entry and 'lat' in entry:
                    entry['pos'] = (((entry.pop('lon') - self.coords['x1']) * self.scale_x), ((entry.pop('lat') - self.coords['y1']) * self.scale_y))
                else:
                    entry['pos'] = (0, 0)
                self.objects[key] = worldobject.Station(self, 'objects', uid=key, **entry)
