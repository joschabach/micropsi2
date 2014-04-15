defstruct = [
	('plugins', []),
	('plugin_settings', []),
	('mc_username', 'username', 'Bot'),
	('mc_password', 'password', ''),
	('daemon', False),
	('logfile', ''),
	('pidfile', ''),
	('authenticated', False),
	('bufsize', 4096),
	('timeout', -1),
	('sock_quit', True),
	('sess_quit', True),
	('proxy', {
		'enabled': False,
		'host': '',
		'port': 0,
	}),
]

for index, setting in enumerate(defstruct):
	if len(setting) == 2:
		defstruct[index] = (setting[0], setting[0], setting[1])