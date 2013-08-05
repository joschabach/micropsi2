import threading
import micropsi_core.world.minecraft.spock.spock.net.client
from micropsi_core.world.minecraft.spock.spock.net.cflags import cflags
from micropsi_core.world.minecraft.spock.spock.net.timer import ThreadedTimer
from micropsi_core.world.minecraft.spock.spock.smpmap import World
from micropsi_core.world.minecraft.spock.riker.packet_queue import PacketQueue

class RikerClient(micropsi_core.world.minecraft.spock.spock.net.client.Client):
	def __init__(self, plugins):
		self.plugins = plugins
		self.world = World()
		micropsi_core.world.minecraft.spock.spock.net.client.Client.__init__(self, plugins = plugins, world = self.world)
		self.move_queue = PacketQueue()

		self.stop_event = threading.Event()
		self.register_dispatch(self.start_timer, 0x01)
		self.register_handler(self.stop_timer, cflags['SOCKET_ERR'], cflags['SOCKET_HUP'], cflags['KILL_EVENT'])
		#self.register_handler(self.s.close(), cflags['SOCKET_ERR'], cflags['SOCKET_HUP'], cflags['KILL_EVENT'])
		self.register_dispatch(self.stop_timer, 0xFF)

	def start_timer(self, *args):
		ThreadedTimer(self.stop_event, .05, self._send_move, -1).start()

	def stop_timer(self, *args):
		self.stop_event.set()
		self.stop_event = threading.Event()

	def push_move(self, packet):
		self.move_queue.push(packet)

	def _send_move(self):
		if self.move_queue:
			self.push(self.move_queue.pop())

	def move_to(x, y, z):
		pass