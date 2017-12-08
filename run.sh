#!/bin/bash
# -*- coding: utf-8 -*-

if [[ -a bin/activate ]]; then
	source bin/activate
fi


# with --console, start jupyter console as well
if [ "$1" == '--console' ]; then
(
	sleep 2
	jupyter qtconsole --existing --gui-completion='ncurses' --style fruity
)&
fi

if [ "$1" == '--no-console' ]; then
    ./start_micropsi_server.py --no-console
else
    ./start_micropsi_server.py
fi

