from micropsi_core.world.minecraft.spock.riker.rkclient import RikerClient
from plugins import DebugPlugin, ReConnect, EchoPacket, Gravity, AntiAFK, ChatMessage, ChunkSaver
#from login import username, password

username = "ownspock"
password = ""

plugins = [DebugPlugin.DebugPlugin, ChatMessage.ChatMessagePlugin, ChunkSaver.ChunkSaverPlugin]
client = RikerClient(plugins = plugins)
client.start()