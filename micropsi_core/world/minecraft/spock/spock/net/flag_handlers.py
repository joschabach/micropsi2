import socket
import logging
from micropsi_core.world.minecraft.spock.spock.mcp.mcpacket import read_packet, Packet
from micropsi_core.world.minecraft.spock.spock.net.cflags import cflags
from micropsi_core.world.minecraft.spock.spock.bound_buffer import BufferUnderflowException
from micropsi_core.world.minecraft.spock.spock import utils

fhandles = {}
def fhandle(ident):
	def inner(cl):
		fhandles[ident] = cl
		return cl
	return inner

#SOCKET_ERR - Socket Error has occured
@fhandle(cflags['SOCKET_ERR'])
def handleERR(client):
	if client.sock_quit and not client.kill:
		print("Socket Error has occured, stopping...")
		client.kill = True
	utils.ResetClient(client)

#SOCKET_HUP - Socket has hung up
@fhandle(cflags['SOCKET_HUP'])
def handleHUP(client):
	if client.sock_quit and not client.kill:
		print("Socket has hung up, stopping...")
		client.kill = True
	utils.ResetClient(client)

#SOCKET_RECV - Socket is ready to recieve data
@fhandle(cflags['SOCKET_RECV'])
def handleSRECV(client):
	try:
		data = client.sock.recv(client.bufsize)
		client.rbuff.append(client.cipher.decrypt(data) if client.encrypted else data)
	except socket.error as error:
		logging.info(str(error))
	try:
		while True:
			client.rbuff.save()
			packet = read_packet(client.rbuff)
			client.dispatch_packet(packet)
	except BufferUnderflowException:
		client.rbuff.revert()

#SOCKET_SEND - Socket is ready to send data and Send buffer contains data to send
@fhandle(cflags['SOCKET_SEND'])
def handleSEND(client):
	try:
		sent = client.sock.send(client.sbuff)
		client.sbuff = client.sbuff[sent:]
	except socket.error as error:
		logging.info(str(error))