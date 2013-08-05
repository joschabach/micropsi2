from micropsi_core.world.minecraft.spock.spock.mcp.mcdata import structs
from micropsi_core.world.minecraft.spock.spock.mcp.mcpacket import Packet
import socket

class ChatMessagePlugin:
	def __init__(self, client):
		self.client = client
		client.register_dispatch(self.chatmessage, 0x03)

	def chatmessage(self, packet):
		if packet.data['text'] == "[Server] u there?":
			self.client.push(Packet(ident = 0x03, data = {
						'text': "is this real life?"
						}))

		if packet.data['text'] == "<moejoe> do something!":
			self.client.push(Packet(ident = 0x03, data = {
						'text': "I'll try!"
						}))
			self.client.push(Packet(ident = 0x0C, data = {
						'yaw': 75,
						'pitch': 45,
						'on_ground': False
						}))
			self.client.push(Packet(ident = 0x0B, data = {
						'x': self.client.position['x'] + 1,
						'y': self.client.position['y'],
						'z': self.client.position['z'],
						'on_ground': False,
						'stance': self.client.position['y'] + 0.11
						}))

			#for i in range (0,265):
			#	for j in range (1,265):
			#		print("i: %s j: %s chunk_data: %s" % (i, j, self.client.world.get(self.client.position['x'],j,self.client.position['z'], j)))

			#x_chunk = self.client.position['x'] // 16
			#z_chunk = self.client.position['z'] // 16
			#for i in range (0,16):
			#	for x in range (0,16):
			#		for y in range (0,16):
			#			for z in range (0,16):
			#				print(self.client.world.columns[(x_chunk, z_chunk)].chunks[i]['block_data'].get(x,y,z))

