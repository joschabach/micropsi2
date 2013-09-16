__author__ = 'jonas'
from micropsi_core.world.MinecraftWorld.MinecraftClient.spock.mcp.mcpacket import Packet
import json
layers = 2

def dispatch_psicraft_command(antwort, client, komm):
	if antwort == "x-":
		psicraft_xminus(client, komm)
	elif antwort == "x+":
		psicraft_xplus(client, komm)
	elif antwort == "z-":
		psicraft_zminus(client, komm)
	elif antwort == "z+":
		psicraft_zplus(client, komm)
	elif antwort == "query_chunk":
		psicraft_query_chunk(client, komm)
	elif antwort == "query_bot":
		psicraft_query_bot(client, komm)
	elif antwort == "more_layers":
		global layers
		layers = layers + 1
		komm.send(json.dumps([layers, "Bot now sends %s layers to webinterface" % layers]).encode())
	elif antwort == "fewer_layers":
		global layers
		layers = layers - 1
		komm.send(json.dumps([layers, "Bot now sends %s layers to webinterface" % layers]).encode())
	elif antwort == "kill":
		psicraft_kill(client)

def psicraft_xminus(client, komm):
	print("old coords -> x: %s y: %s z: %s" % (client.position['x'], client.position['y'], client.position['z']))
	client.push(Packet(ident = 0x0B, data = {
					'x': (client.position['x'] - 1) // 1,
					'y': client.position['y'] // 1,
					'z': client.position['z'] // 1,
					'on_ground': False,
					'stance': client.position['y'] + 0.11
					}))
	print("new coords -> x: %s y: %s z: %s" % (client.position['x'], client.position['y'], client.position['z']))
	komm.send(json.dumps("Bot received command x-. New Bot position is x: %s y: %s z: %s" % (client.position['x'], client.position['y'], client.position['z'])).encode())

def psicraft_xplus(client, komm):
	print("old coords -> x: %s y: %s z: %s" % (client.position['x'], client.position['y'], client.position['z']))
	client.push(Packet(ident = 0x0B, data = {
					'x': (client.position['x'] + 1)  // 1,
					'y': client.position['y'] // 1,
					'z': client.position['z'] // 1,
					'on_ground': False,
					'stance': client.position['y'] + 0.11
					}))
	print("new coords -> x: %s y: %s z: %s" % (client.position['x'], client.position['y'], client.position['z']))
	komm.send(json.dumps("Bot received command x-. New Bot position is x: %s y: %s z: %s" % (client.position['x'], client.position['y'], client.position['z'])).encode())

def psicraft_zminus(client, komm):
	print("old coords -> x: %s y: %s z: %s" % (client.position['x'], client.position['y'], client.position['z']))
	client.push(Packet(ident = 0x0B, data = {
					'x': client.position['x'] // 1,
					'y': client.position['y'] // 1,
					'z': (client.position['z'] - 1)  // 1,
					'on_ground': False,
					'stance': client.position['y'] + 0.11
					}))
	print("new coords -> x: %s y: %s z: %s" % (client.position['x'], client.position['y'], client.position['z']))
	komm.send(json.dumps("Bot received command x-. New Bot position is x: %s y: %s z: %s" % (client.position['x'], client.position['y'], client.position['z'])).encode())

def psicraft_zplus(client, komm):
	print("old coords -> x: %s y: %s z: %s" % (client.position['x'], client.position['y'], client.position['z']))
	client.push(Packet(ident = 0x0B, data = {
					'x': client.position['x'] // 1,
					'y': client.position['y'] // 1,
					'z': (client.position['z'] + 1) // 1,
					'on_ground': False,
					'stance': client.position['y'] + 0.11
					}))
	print("new coords -> x: %s y: %s z: %s" % (client.position['x'], client.position['y'], client.position['z']))
	komm.send(json.dumps("Bot received command x-. New Bot position is x: %s y: %s z: %s" % (client.position['x'], client.position['y'], client.position['z'])).encode())

def psicraft_query_chunk(client, komm):
	print("trying to send chunk do webinterface")

	x_chunk = client.position['x'] // 16
	z_chunk = client.position['z'] // 16

	block_types_json = [[[0 for i in range(16)] for i in range(layers)] for j in range(16)]

	bot_block = [client.position['x'], client.position['y'], client.position['z']]

	for y in range (0,layers):
		for x in range (0,16):
			for z in range (0,16):
				if client.world.columns[(x_chunk, z_chunk)].chunks[int((bot_block[1]+y)//16)] != None:
					block_types_json[x][y][z] = client.world.columns[(x_chunk, z_chunk)].chunks[int((bot_block[1]+y-layers//2)//16)]['block_data'].get(x,int((bot_block[1]+y-layers//2)%16),z)

	komm.send(json.dumps([bot_block, block_types_json, "Received chunk from Bot", layers]).encode())

def psicraft_query_bot(client, komm):
	print("trying to send bot_block do webinterface")

	bot_block = [client.position['x'], client.position['y'], client.position['z']]

	komm.send(json.dumps([bot_block, "Received bot position from Bot", layers]).encode())

def psicraft_kill(client):
	client.kill_flag = True