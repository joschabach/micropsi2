#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""

  Extracts wordnet definitions (glossary) and wordnet
  relations from a freebase dump.
  writes the glossary to en_wordnet_glossary.tsv
  writes the relations to en_wordnet_relations.tsv
  takes around 20 minutes

"""

en_c = open('en_wordnet_glossary.tsv', 'w')
en_r = open('en_wordnet_relations.tsv', 'w')

with open('freebase.tsv', 'r') as fp:
    for line in fp:
        if "wordnet" in line:
            parts = line.strip("\n\t\r ").split("\t")
            if len(parts) == 4:
                if parts[2] == "/lang/en":
                    en_c.write(line)
            elif len(parts) == 3:
                en_r.write(line)

en_c.close()
en_r.close()
