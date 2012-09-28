#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Experimental decoder for parsing schedule and geographic information from the open data repository of Berlin's
public transport.

Our goal is to build the following data structures:
- a dict of stations within the area of Berlin, along with names and coordinates
- a dict of traffic lines, with names and included stations, preceding and following stations,
    and for each station, traffic schedules for normal days and weekends
- a sorted list of timepoints, sorted by days, with information about the line and station
- a system state with a dict of vehicles, occupying positions at a given time

Vehicles are instantiated whenever a new timepoint refers to them, and they are not available in the previous station.
Otherwise they are just moved.
Vehicles are removed whenever they reach the final destination of the line.
"""

__author__ = 'joscha'
__date__ = '25.09.12'

import json
import os
import warnings

def parse_files():
    """Read a number of predefined json files into dicts"""

    RESOURCE_PATH = os.path.join(os.path.dirname(__file__),"fahrinfo_WINKOMP526_2012_09")

    # train data:
    # id, trainNumber, trainType, firstStop, lastStop (all numerical)
    planATR = read_json_file(os.path.join(RESOURCE_PATH, "PLANATR_data1.json"))

    # station data:
    # b1_id, IBNR, name (name is alphanum; in case of Berlin, it contains "(Berlin)")
    planB = read_json_file(os.path.join(RESOURCE_PATH, "PLANB_data.json"))

    # train companies
    # betr1Id, nameShort, nameLong
    planBetr1 = read_json_file(os.path.join(RESOURCE_PATH, "PLANBETR_list1.json"))

    # mapping from train company id2 to id1
    # betr2Id, betr1Id
    planBetr2 = read_json_file(os.path.join(RESOURCE_PATH, "PLANBETR_list2.json"))

    # mapping from train numbers to train company id2
    # zugId, betr2Id
    planBetr3 = read_json_file(os.path.join(RESOURCE_PATH, "PLANBETR_list3.json"))

    # Geo coordinates of stations
    # id, lon, lat (lon and lat are geo coordinates with a decimal point in them)
    planKGeo = read_json_file(os.path.join(RESOURCE_PATH, "PLANKGEO_data.json"))

    # train types
    # gatId, nameShort, nameLong
    planGat = read_json_file(os.path.join(RESOURCE_PATH, "PLANGAT_data1.json"))

    # train schedule (numerical keys)
    # bz2_id, train_id, arr, dep, bz1_ref
    planBZ = read_json_file(os.path.join(RESOURCE_PATH, "PLANBZ_2.json"))

    # List of train stops (train routes; same line may have multiple routes)
    # id, stops = [] (stops are numerical keys)
    planLauf = read_json_file(os.path.join(RESOURCE_PATH, "PLANLAUF_data.json"))

    # Names of train lines
    # lineId, lineName (lineName is a string)
    planLine = read_json_file(os.path.join(RESOURCE_PATH, "PLANLINE_data.json"))

    # days when the plan is valid
    # id, days (days is a string, where 0 means invalid, l means valid, first day is "Thu Aug 30 2012")
    planW = read_json_file(os.path.join(RESOURCE_PATH, "PLANW_data.json"))

    # all train journeys
    # id, frequency:{iterations, interval}, wId, trainNumber, trainType, laufId, richId
    planZug = read_json_file(os.path.join(RESOURCE_PATH, "PLANZUG_data.json"))

    print "done reading"

    # sort geo-coords by id
    geo_coords = { i["id"]:{"lat": i["lat"], "lon": i["lon"]} for i in planKGeo }

    # create list of trains
    _betr_names = { i["betr1Id"]:{"company_long":i["nameLong"], "company":i["nameType"]} for i in planBetr1 }
    _betr1 = { i["betr2Id"]:i["betr1Id"] for i in planBetr2 }
    trains_to_companies = { i["zugId"]:_betr_names.get(_betr1.get(i["betr2Id"])) for i in planBetr3 }

    # sort lines by id
    line_names = { i["lineId"]:i["lineName"] for i in planLine }
    train_types = { i["gatId"]: i["nameLong"] for i in planGat}
    train_lines = { i["laufId"]:{
        "train_number":i["trainNumber"],
        "train_type": train_types.get(i["trainType"]),
        "line_name":line_names.get(i["trainNumber"])}
                    for i in planZug}

    # sort train lines by stops
    stops = dict()
    for i in planLauf:
        for stop in i["stops"]:
            if stop in stops:
                stops[stop].append(i["id"])
            else:
                stops[stop] = [i["id"]]

    # compile a list of stations in Berlin
    berlin_stations = dict()
    for station in planB:
        if " (Berlin)" in station["name"]:
            coord = geo_coords.get(station["b1_id"])
            station_lines = { i: train_lines.get(i) for i in stops.get(station["b1_id"], [])}
            station_line_names = []
            station_train_types = []
            for i in station_lines:
                name = station_lines[i].get("line_name")
                if name and not name in station_line_names: station_line_names.append(name)
                train_type = station_lines[i].get("train_type")
                if train_type and not train_type in station_train_types: station_train_types.append(train_type)

            berlin_stations[station["b1_id"]] = {
                "name": station["name"].replace( " (Berlin)", ""),
                "IBNR": station["IBNR"],
                "lat": coord.get("lat"),
                "lon": coord.get("lon"),
                # "lines": station_lines,
                "train_types": station_train_types,
                "line_names": station_line_names
            }

    #with open(os.path.join(os.path.dirname(__file__),"fahrinfo_stations.json"), mode='w+') as file:
    #    json.dump(berlin_stations, file, indent = 4)

    # compile a list of trains in Berlin, with a list of lines on each, and for each line, a list of stations and times
    lines = { i["id"]:i["stops"] for i in planLauf }

    movements = { i["bz2_id"]:{
        "train_id":i["train_id"],
        "arr":i["arr"],
        "dep":i["dep"],
        "station_id":i["bz1_ref"]
    } for i in planBZ if i["bz1_ref"] in berlin_stations}

    berlin_train_runs = { movements[i]["train_id"]:i for i in movements }

    train_runs = { i["id"]:{
        "train_number":i["trainNumber"],
        "train_type": train_types.get(i["trainType"]),
        "line_name":line_names.get(i["trainNumber"]),
        "line_id":i["laufId"],
        "schedule_number":i["wId"]
    } for i in planZug if i["id"] in berlin_train_runs}

    with open(os.path.join(os.path.dirname(__file__),"train_runs.json"), mode='w+') as file:
        json.dump(train_runs, file, indent = 4)

    # sort the train runs by day indices
    train_runs_by_schedule_number = dict()
    for i in train_runs:
        if not train_runs_by_schedule_number.has_key(train_runs[i]["schedule_number"]):
            train_runs_by_schedule_number[train_runs[i]["schedule_number"]] = dict()
        train_runs_by_schedule_number[train_runs[i]["schedule_number"]][i]=train_runs[i]

    with open(os.path.join(os.path.dirname(__file__),"train_runs_by_schedule_number.json"), mode='w+') as file:
        json.dump(train_runs_by_schedule_number, file, indent = 4)

    # create an index of days to schedule_numbers
    day_list = [i["days"] for i in planW]
    day_to_schedule_numbers = dict()
    for day in range (0, 101):
        day_to_schedule_numbers[day] = []
        for schedule_number in range (1, len(day_list)):
            if day_list[schedule_number][day]=="l":
                day_to_schedule_numbers[day].append(schedule_number)
    with open(os.path.join(os.path.dirname(__file__),"day_to_schedule_numbers.json"), mode='w+') as file:
        json.dump(day_to_schedule_numbers, file, indent = 4)

    # create a list of timed events for each day

    days_to_train_ids = dict()
    for day in range (0, 101):
        train_ids = set()
        for i in day_to_schedule_numbers[day]:
            if i in train_runs_by_schedule_number:
                for j in train_runs_by_schedule_number[i]:
                    train_ids.add(j)
        days_to_train_ids[day]=list(train_ids)

    with open(os.path.join(os.path.dirname(__file__),"days_to_train_ids.json"), mode='w+') as file:
        json.dump(days_to_train_ids, file, indent = 4)

    # sort arrivals/departures by trains
    events_by_trains = dict()
    for i in movements:
        if not events_by_trains.has_key(movements[i]["train_id"]):
            events_by_trains[movements[i]["train_id"]] = {"arr":{}, "dep":{}}
        if movements[i]["arr"]>=0:
            if events_by_trains[movements[i]["train_id"]]["arr"].has_key(movements[i]["arr"]):
                print "double ",movements[i]["arr"],": ", events_by_trains[movements[i]["train_id"]]["arr"][movements[i]["arr"]]
                print "       ",movements[i]["arr"],": ", movements[i]["station_id"]



            events_by_trains[movements[i]["train_id"]]["arr"][movements[i]["arr"]] = movements[i]["station_id"]
        if movements[i]["dep"]>=0:

            events_by_trains[movements[i]["train_id"]]["dep"][movements[i]["dep"]] = movements[i]["station_id"]

    with open(os.path.join(os.path.dirname(__file__),"events_by_trains.json"), mode='w+') as file:
        json.dump(events_by_trains, file, indent = 4)

    # train_ids to movements

    # for each day, a list of events: time: arrivals: (train, station); departures: (train, station)

    # züge nach tagen sortieren
    days_to_trains = dict()

    # zu den zügen die arrs und depts zuordnen, und zwar als liste von depts:{deptstation, nextstation, arrival}

def read_json_file(filename):
    try:
        with open(filename) as file:
            data = json.load(file)
        return data
    except ValueError:
        warnings.warn("Could not read plan data at %s" % filename)
    except IOError:
        warnings.warn("Could not open plan data at %s" % filename)
    return False

def main():
    parse_files()

if __name__ == '__main__':
    main()




