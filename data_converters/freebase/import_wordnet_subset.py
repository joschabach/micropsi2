#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""

  Imports the basic wordnet subset from a freebase dump.
  relies on the outputs of both
  extract_concepts.py and extract_wordnet_relations.py

  the parameters for the data source files are defaulted accordingly

  the "nodenet" parameter defines the name of the nodenet.
  if a nodenet with that name exists, it will be used. Otherwise,
  a new nodenet will be created.

"""

import argparse
import sys

# hack
sys.path[0:0] = [
    '../../'
]

parser = argparse.ArgumentParser(description="micropsi freebase importer")
parser.add_argument('-c', '--conceptfile', type=str, default="en_concepts.tsv")
parser.add_argument('-r', '--relfile', type=str, default="en_wordnet_relations.tsv")
parser.add_argument('-n', '--nodenet', type=str, default="freebase wordnet")
args = parser.parse_args()

from micropsi_server.dispatcher import micropsi


def add_concept(name, id=None):
    global micropsi, uid, label_nodespace, nodenet
    if id not in micropsi.nodenets[uid].nodes:
        res, id = micropsi.add_node(uid, "Concept", (0, 0), "Root", name=name, uid=id)
        res, label = micropsi.add_node(uid, "Label", (0, 0), label_nodespace, name=name)
        micropsi.add_link(uid, id, "sym", label, "gen", 1, certainty=1)
        micropsi.add_link(uid, label, "ref", id, "gen", 1, certainty=1)
    return id


def find_label(text):
    global micropsi, uid, label_nodespace
    data = micropsi.get_nodespace(uid, label_nodespace, -1)
    for id in data['nodes']:
        if data['nodes'][id]['name'] == parts:
            return text
    return None


label_nodespace = False
uid = False
available = micropsi.get_available_nodenets()
for id in available:
    if available[id].name == args.nodenet:
        uid = id
        res, uid = micropsi.load_nodenet(uid)
        break

if not uid:
    res, uid = micropsi.new_nodenet(args.nodenet, "Default")
    res, uid = micropsi.load_nodenet(uid)
if not res:
    print "error: unknown nodenet"
    sys.exit(1)

for key in micropsi.nodenets[uid].nodespaces:
    if micropsi.nodenets[uid].nodespaces[key].name == "Labels":
        label_nodespace = key
        break
if not label_nodespace:
    res, label_nodespace = micropsi.add_node(uid, "Nodespace", (0, 0), "Root", name="Labels")

wn_concept_ids = {}
with open('en_wordnet_glossary.tsv') as fp:
    for line in fp:
        parts = line.strip("\n\t\r ").split("\t")
        wn_concept_ids[parts[0]] = 1

print "got %d concept ids" % len(wn_concept_ids)
nodenet = micropsi.nodenets[uid]
c = 0
i = 0

with open(args.conceptfile) as fp:
    for line in fp:
        parts = line.strip("\n\t\r ").split("\t")
        i += 1
        try:
            foo = wn_concept_ids[parts[0]]
        except KeyError:
            continue
        if len(parts) == 4:
            # concept:
            name = parts[3]
            if ".noun." in name:
                name = name[:-8]
            elif ".adjective." in name:
                name = name[:-13]
            elif ".adverb." in name:
                name = name[:-10]
            elif ".verb." in name:
                name = name[:-8]
            add_concept(name, id=parts[0])
            c += 1
            if c % 100 == 0:
                print "%d items extracted" % c
        if i % 1000 == 0:
            print "%d items processed" % i

print "concepts done. now fetching relations"

i = 0
with open(args.relfile) as fp:
    for line in fp:
        parts = line.strip("\n\t\r ").split("\t")
        if len(parts) == 3:
            # relation.
            # switch relation types:
            type = None
            if parts[1][-9:] == "caused_by":
                type = "ret"
            elif parts[1][-6:] == "causes":
                type = "por"
            elif parts[1][-8:] == "hyponymy":
                type = "cat"
            elif parts[1][-8:] == "instance"  or parts[1][-8:] == "hypernym":
                type = "exp"
            elif parts[1][-7:] == "holonym":
                type = "sub"
            elif parts[1][-7:] == "meronym":
                type = "sur"
            if type is not None:
                try:
                    micropsi.add_link(uid, parts[0], type, parts[2], "gen", 1, certainty=1)
                    i += 1
                except KeyError:
                    # source or target node not found. ignore
                    pass

print "Extracted %d links" % i
print "Done. Saving."
micropsi.save_nodenet(uid)
print "Saved, Aligning nodes"
micropsi.align_nodes(uid, "Root")
micropsi.align_nodes(uid, label_nodespace)
print "Nodes aligned. Saving again"
micropsi.save_nodenet(uid)
print "ALL DONE"
