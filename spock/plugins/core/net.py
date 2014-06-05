import sys
import socket
import select
from spock import utils
from spock.utils import pl_announce
from spock.mcp import mcpacket, mcdata
from Crypto.Cipher import AES

class AESCipher:
    def __init__(self, SharedSecret):
        #Name courtesy of dx
        self.encryptifier = AES.new(SharedSecret, AES.MODE_CFB, IV=SharedSecret)
        self.decryptifier = AES.new(SharedSecret, AES.MODE_CFB, IV=SharedSecret)

    def encrypt(self, data):
        return self.encryptifier.encrypt(data)

    def decrypt(self, data):
        return self.decryptifier.decrypt(data)

class SelectSocket:
    def __init__(self, timer):
        self.sending = False
        self.timer = timer
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.recv = self.sock.recv
        self.send = self.sock.send

    def poll(self):
        flags = []
        if self.sending:
            self.sending = False
            slist = [(self.sock,), (self.sock,), ()]
        else:
            slist = [(self.sock,), (), ()]
        timeout = self.timer.get_timeout()
        if timeout > 0:
            slist.append(timeout)
        try:
            rlist, wlist, xlist = select.select(*slist)
        except select.error as e:
            print(str(e))
            rlist = []
            wlist = []
        if rlist:         flags.append('SOCKET_RECV')
        if wlist:         flags.append('SOCKET_SEND')
        return flags

    def reset(self):
        self.sock.close()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self, host, port):
        self.sock.connect((host, port))
        self.sock.setblocking(False)

rmask = select.POLLIN|select.POLLPRI|select.POLLERR|select.POLLHUP|select.POLLNVAL
smask = rmask|select.POLLOUT
class PollSocket(SelectSocket):
    def __init__(self, timer):
        super().__init__(timer)
        self.pollobj = select.poll()

    def poll(self):
        flags = []
        if self.sending:
            self.pollobj.register(self.sock, smask)
            self.sending = False
        else:
            self.pollobj.register(self.sock, rmask)
        try:
            poll = self.pollobj.poll(self.timer.get_timeout() * 1000)
        except select.error as e:
            print(str(e))
            poll = []
            raise e
        if poll:
            poll = poll[0][1]
            if poll & select.POLLERR:  flags.append('SOCKET_ERR')
            if poll & select.POLLHUP:  flags.append('SOCKET_HUP')
            if poll & select.POLLNVAL: flags.append('SOCKET_HUP')
            if poll & select.POLLIN:   flags.append('SOCKET_RECV')
            if poll & select.POLLOUT:  flags.append('SOCKET_SEND')
        return flags


class NetCore:
    trace = False

    def __init__(self, sock, event):
        self.sock = sock
        self.event = event
        self.host = None
        self.port = None
        self.connected = False
        self.encrypted = False
        self.proto_state = mcdata.HANDSHAKE_STATE
        self.sbuff = b''
        self.rbuff = utils.BoundBuffer()

    def connect(self, host = 'localhost', port = 25565):
        self.host = host
        self.port = port
        print("Attempting to connect to host:", self.host, "port:", self.port)
        self.sock.connect(self.host, self.port)
        self.connected = True
        print("Connected")

    def change_state(self, state):
        if self.trace:
            print("!!! Changing to state", mcdata.state_names[state])
        self.proto_state = state

    def push(self, packet):
        if self.trace:
            print(repr(packet))

        if packet.state != self.proto_state:
            raise ValueError("Cannot send packet {0} while in {1} state".format(repr(packet), mcdata.state_names[self.proto_state]))
        if packet.direction != mcdata.CLIENT_TO_SERVER:
            raise ValueError("Cannot send packet {0} from client to server".format(repr(packet)))

        data = packet.encode()
        self.sbuff += (self.cipher.encrypt(data) if self.encrypted else data)
        self.event.emit(packet.ident(), packet)
        self.sock.sending = True

    def read_packet(self, data = b''):
        self.rbuff.append(self.cipher.decrypt(data) if self.encrypted else data)
        while True:
            self.rbuff.save()
            try:
                packet = mcpacket.Packet(ident=(
                    self.proto_state,
                    mcdata.SERVER_TO_CLIENT,
                )).decode(self.rbuff)
            except utils.BufferUnderflowException:
                self.rbuff.revert()
                break

            if self.trace:
                print(repr(packet))

            self.event.emit(packet.ident(), packet)

    def enable_crypto(self, secret_key):
        self.cipher = AESCipher(secret_key)
        self.encrypted = True

    def disable_crypto(self):
        self.cipher = None
        self.encrypted = False

    def reset(self):
        self.sock.reset()
        self.__init__(self.sock, self.event)

    disconnect = reset

@pl_announce('Net')
class NetPlugin:
    def __init__(self, ploader, settings):
        if sys.platform != 'win32':
            self.sock = PollSocket(ploader.requires('Timers'))
        else:
            self.sock = SelectSocket(ploader.requires('Timers'))
        settings = ploader.requires('Settings')
        self.bufsize = settings['bufsize']
        self.sock_quit = settings['sock_quit']
        self.event = ploader.requires('Event')
        self.net = NetCore(self.sock, self.event)
        self.net.trace = settings['packet_trace']
        ploader.provides('Net', self.net)

        ploader.reg_event_handler('tick', self.tick)
        ploader.reg_event_handler('SOCKET_RECV', self.handleRECV)
        ploader.reg_event_handler('SOCKET_SEND', self.handleSEND)
        ploader.reg_event_handler('SOCKET_ERR', self.handleERR)
        ploader.reg_event_handler('SOCKET_HUP', self.handleHUP)
        ploader.reg_event_handler(mcdata.packet_idents['PLAY<Disconnect'], self.handle_server_disconnect)

        ploader.reg_event_handler(mcdata.packet_idents['HANDSHAKE>Handshake'], self.handle_handshake)
        ploader.reg_event_handler(mcdata.packet_idents['LOGIN<Login Success'], self.handle_login_success)

    def tick(self, name, data):
        for flag in self.sock.poll():
            self.event.emit(flag)

    #SOCKET_RECV - Socket is ready to recieve data
    def handleRECV(self, name, event):
        try:
            data = self.sock.recv(self.bufsize)
            #print('read:', len(data))
            if not data: #Just because we have to support socket.select
                self.event.emit('SOCKET_HUP')
                return
            self.net.read_packet(data)
        except socket.error as error:
            print("Socket error while sending:", error)
            self.event.kill()
            self.net.reset()

    #SOCKET_SEND - Socket is ready to send data and Send buffer contains data to send
    def handleSEND(self, name, event):
        try:
            sent = self.sock.send(self.net.sbuff)
            #print('write:', sent)
            self.net.sbuff = self.net.sbuff[sent:]
        except socket.error as error:
            print("Socket error while sending:", error)
            self.event.kill()
            self.net.reset()

    #SOCKET_ERR - Socket Error has occured
    def handleERR(self, name, event):
        if self.sock_quit and not self.event.kill_event:
            print("Socket Error has occured, stopping...")
            self.event.kill()
        self.net.reset()

    #SOCKET_HUP - Socket has hung up
    def handleHUP(self, name, event):
        if self.sock_quit and not self.event.kill_event:
            print("Socket has hung up, stopping...")
            self.event.kill()
        self.net.reset()

    def handle_server_disconnect(self, name, event):
        if self.sock_quit and not self.event.kill_event:
            print("Server sent disconnect packet, stopping...")
            self.event.kill()
        self.net.reset()

    #Handshake - Change to whatever the next state is going to be
    def handle_handshake(self, name, packet):
        self.net.change_state(packet.data['next_state'])

    #Login Success - Change to Play state
    def handle_login_success(self, name, packet):
        self.net.change_state(mcdata.PLAY_STATE)
