#!/bin/bash
# -*- coding: utf-8 -*-

if [[ -a bin/activate ]]; then
	source bin/activate
	./start_micropsi_server.py
else
	./start_micropsi_server.py
fi
