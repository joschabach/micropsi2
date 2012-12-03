from micropsi_core.world.world import World

import json
import os
import png


class Island(World):

    """ mandatory: list of world adapters that are supported"""
    supported_worldadapters = ['Braitenberg']

    groundmap = {
        'image': "psi_1.png",
        'startpos': (100, 100),
        'scaling': (500, 500)
    }

    assets = {
        'background': "island/background.jpg",
        'js': "island/island.js"
    }

    def __init__(self, runtime, filename, world_type="Island", name="", owner="", uid=None, version=1):
        World.__init__(self, runtime, filename, world_type=world_type, name=name, owner=owner, uid=uid, version=version)
        self.data['groundmap'] = self.groundmap
        self.load_groundmap(self.groundmap["image"])
        self.scale_x = (self.representation_2d['x'] / -(self.coords['x1'] - self.coords['x2']))
        self.scale_y = (self.representation_2d['y'] / -(self.coords['y1'] - self.coords['y2']))
        self.current_step = 0
        self.load_json_data()

    def load_json_data(self):
        filename = os.path.join(os.path.dirname(__file__), 'fahrinfo_berlin.json')
        with open(filename) as file:
            self.fahrinfo_berlin = json.load(file)
        self.load_stations()
        self.load_trains_for_current_timestep()

    def get_world_objects(self, type=None):
        """ overwrite world.get_world_objects"""
        if type == 'stations':
            return self.stations
        else:
            return self.trains

    def get_world_view(self, step):
        """ overwrite.world.get_world_view to add a status message """
        data = super(Island, self).get_world_view(step)
        data['status_message'] = "Day %s, at %s:%s:%s" % (str(self.day), str(int(self.minute) / 60), str(int(self.minute) % 60).zfill(2), str(int((self.minute - int(self.minute)) * 60)).zfill(2))
        return data

    def load_stations(self):
        self.stations = self.fahrinfo_berlin["stations"]
        for key in self.stations:
            type = "other"
            if "S" in self.stations[key]['train_types']:
                if "U" in self.stations[key]['train_types']:
                    type = "S+U"
                else:
                    type = "S"
            elif "U" in self.stations[key]['train_types']:
                type = "U"
            elif "Tram" in self.stations[key]['train_types']:
                type = "Tram"
            elif "Bus" in self.stations[key]['train_types']:
                type = "Bus"
            self.stations[key]['stationtype'] = type
            if 'lon' in self.stations[key] and 'lat' in self.stations[key]:
                self.stations[key]['pos'] = (((self.stations[key]['lon'] - self.coords['x1']) * self.scale_x), ((self.stations[key]['lat'] - self.coords['y1']) * self.scale_y))
            else:
                self.stations[key]['pos'] = (0, 0)

    def load_trains_for_current_timestep(self):

        self.minute = (self.current_step / 8.0) % 1440
        self.day = (self.current_step / 8) / 1440

        lines = {}
        trains = {}

        # step function
        train_data = self.fahrinfo_berlin["train_data"]
        todays_trains = self.fahrinfo_berlin["trains_by_day"][str(self.day)]
        err = 0
        moving = 0
        for item in todays_trains:
            train_id = str(item)
            if train_data[train_id]["begin"] <= self.minute <= train_data[train_id]["end"]:  # and train_data[train_id]['line_name'] == 'U5':
                train = train_data[train_id]
                if not train_id in trains:
                    trains[train_id] = {
                        "traintype": train["train_type"],
                        "line": train["line_name"],
                        "station_index": 0,
                        "moving": 0  # if 0, the train is stopping
                    }
                    if train["line_name"] not in lines:
                        lines[train["line_name"]] = 1
                    else:
                        lines[train["line_name"]] += 1

                # find current station
                station_index = trains[train_id]["station_index"]
                while train["stops"][station_index]["arr"] < self.minute and station_index < len(train["stops"]) - 1:
                    station_index += 1
                if len(train["stops"]) - 1 > station_index and train["stops"][station_index + 1]["arr"] > self.minute:
                    station_index -= 1

                current_station = str(train["stops"][station_index]["station_id"])
                if train["stops"][station_index]["arr"] <= self.minute <= train["stops"][station_index]["dep"]:
                    # stopping at station
                    trains[train_id]["lat"] = self.stations[current_station]["lat"]
                    trains[train_id]["lon"] = self.stations[current_station]["lon"]
                    trains[train_id]["moving"] = 0
                else:
                    if train["stops"][station_index]["arr"] <= self.minute and (train["stops"][station_index]["dep"] < 0 or station_index == len(train["stops"]) - 1):
                        # final destination
                        trains[train_id]["lat"] = self.stations[current_station]["lat"]
                        trains[train_id]["lon"] = self.stations[current_station]["lon"]
                        trains[train_id]["moving"] = 0
                    else:
                        # traveling between stations
                        moving += 1
                        if self.minute < train["stops"][station_index]["arr"]:
                            station_index -= 1
                            current_station = str(train["stops"][station_index]["station_id"])
                        try:
                            next_station = str(train["stops"][station_index + 1]["station_id"])
                        except IndexError:
                            err += 1
                            print "next station not found: %s " % train_id
                            continue
                        dep = train["stops"][station_index]["dep"]
                        arr = train["stops"][station_index + 1]["arr"]
                        if arr == dep:
                            dep -= 0.1  # avoid division by zero
                        distance = (self.minute - dep) / (arr - dep)
                        clat = self.stations[current_station]["lat"]
                        nlat = self.stations[next_station]["lat"]
                        trains[train_id]["lat"] = clat + (nlat - clat) * distance
                        clon = self.stations[current_station]["lon"]
                        nlon = self.stations[next_station]["lon"]
                        trains[train_id]["lon"] = clon + (nlon - clon) * distance
                        trains[train_id]["moving"] = distance

                if 'lon' in trains[train_id] and 'lat' in trains[train_id]:
                    trains[train_id]['pos'] = (((trains[train_id]['lon'] - self.coords['x1']) * self.scale_x), ((trains[train_id]['lat'] - self.coords['y1']) * self.scale_y))
                else:
                    err += 1
                    print "coords not found: %s" % train_id
                    del trains[train_id]
        self.trains = trains
        self.data['trains'] = self.trains

    def step(self):
        """ overwrite world.step """
        ret = super(Island, self).step()
        self.load_trains_for_current_timestep()
        return ret
