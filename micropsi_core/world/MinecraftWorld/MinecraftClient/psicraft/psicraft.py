import socket
from bottle import route, run, template, static_file
import json
import time
import datetime

#layers = 2 # 4 layers equal 1kb that are transferred to the webinterface
bot_ip = 'localhost'
bot_port = 50104


@route('/query_chunk')
def query_chunk():
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.connect((bot_ip, bot_port))
	s.send("query_chunk".encode())
	data = ""

	while True:
		data1 = s.recv(1)
		if not data1:
			s.close()
			break
		data += data1.decode()

	s.close()

	bot_and_chunk = json.loads(data)
	bot_block = bot_and_chunk[0]
	chunk = bot_and_chunk[1]
	answer = bot_and_chunk[2]
	layers = bot_and_chunk[3]
	bot_height = bot_block[1]

	return json.dumps([chunk, bot_block, layers, answer])

@route('/query_bot')
def query_bot():
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.connect((bot_ip, bot_port))
	s.send("query_bot".encode())
	data = ""

	while True:
		data1 = s.recv(1)
		if not data1:
			s.close()
			break
		data += data1.decode()

	s.close()

	bot_block_and_answer = json.loads(data)
	bot_block = bot_block_and_answer[0]
	answer = bot_block_and_answer[1]
	layers = bot_block_and_answer[2]

	return json.dumps([bot_block, layers, answer])

@route('/connect/<command>')
def connect_to_bot(command):
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.connect((bot_ip, bot_port))
	message = command
	s.send(message.encode())

	answer = ""

	while True:
		data1 = s.recv(1)
		if not data1:
			s.close()
			break
		answer += data1.decode()

	s.close()

	return answer

@route('/static/<filename:path>')
def server_static(filename):
	return static_file(filename, root='./')

@route('/bot')
def commence_webinterface():
	return template('psicraft_webinterface')


run(host='localhost', port=8080, debug=True)
