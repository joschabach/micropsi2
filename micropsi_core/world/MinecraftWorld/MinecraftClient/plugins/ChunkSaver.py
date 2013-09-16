import sys
from micropsi_core.world.MinecraftWorld.MinecraftClient.spock.mcp.mcdata import structs
from micropsi_core.world.MinecraftWorld.MinecraftClient.spock.net.cflags import cflags

class ChunkSaverPlugin:
	def __init__(self, client):
		self.client = client
		client.register_dispatch(self.savechunk, 0x38)


	def savechunk(self, packet):
		pass
'''
			#Map Chunk Bulk
	0x38: (
		("short", "chunk_column_count"),
		("int", "data_size"),
		("bool", "sky_light")),
'''
