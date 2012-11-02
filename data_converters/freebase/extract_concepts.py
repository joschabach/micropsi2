#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""

  Extracts all english concepts from the freebase dump into the file
  en_concepts.tsv
  takes around 20 minutes

"""

en = open('en_concepts.tsv', 'w')
with open('freebase.tsv') as fp:
    for line in fp:
        parts = line.strip("\n\t\r ").split("\t")
        if len(parts) == 4:
            if "wordnet" not in parts[1]:
                if parts[2] == "/lang/en":
                    en.write(line)

en.close()
