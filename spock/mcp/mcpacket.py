import copy
from time import gmtime, strftime
from spock import utils
from spock.mcp import datautils, mcdata
from spock.mcp.mcpacket_extensions import hashed_extensions
from spock.mcp.mcdata import (
    MC_BOOL, MC_UBYTE, MC_BYTE, MC_USHORT, MC_SHORT, MC_UINT, MC_INT,
    MC_LONG, MC_FLOAT, MC_DOUBLE, MC_STRING, MC_VARINT, MC_SLOT, MC_META
)

#TODO: Wow this class ended up a bit of a mess, cleanup and refactor soon^TM
from spock.utils import BufferUnderflowException


class Packet(object):
    length = None
    id = 0x00
    state = None
    direction = None

    def __init__(self, ident=(mcdata.HANDSHAKE_STATE, mcdata.CLIENT_TO_SERVER, 0x00), data=None):
        if isinstance(ident, str):
            ident = mcdata.packet_idents[ident]

        if len(ident) == 3:
            self.state, self.direction, self.id = ident
        else:
            self.state, self.direction = ident

        self.__hash_ident()
        self.data = data if data else {}

    def __hash_ident(self):
        self.__hashed_ident = (self.state, self.direction, self.id)

    def clone(self):
        return Packet(ident=self.ident(), data=copy.deepcopy(self.data))

    def ident(self, state=None, direction=None, id=None):
        if state is not None:
            self.state = state
            self.__hashed_ident = None
        if direction is not None:
            self.direction = direction
            self.__hashed_ident = None
        if id is not None:
            self.id = id
            self.__hashed_ident = None
        if self.__hashed_ident is None:
            self.__hash_ident()
        return self.__hashed_ident

    def decode(self, bbuff):
        self.data = {}
        self.length = datautils.unpack(MC_VARINT, bbuff)
        encoded = bbuff.recv(self.length)
        try:
            pbuff = utils.BoundBuffer(encoded)

            #Ident
            self.id = datautils.unpack(MC_VARINT, pbuff)
            self.__hash_ident()

            #Payload
            for dtype, name in mcdata.hashed_structs[self.__hashed_ident]:
                try:
                    self.data[name] = datautils.unpack(dtype, pbuff)
                except BufferUnderflowException:
                    raise Exception("Failed to parse field {0}:{1} from packet {2}".format(name, dtype, repr(self)))

            #Extension
            if self.__hashed_ident in hashed_extensions:
                hashed_extensions[self.__hashed_ident].decode_extra(self, pbuff)

            return self

        except BufferUnderflowException:
            raise Exception("Failed to parse packet: ", repr(self))

    def encode(self):
        #Ident
        o = datautils.pack(MC_VARINT, self.id)
        #Payload
        for dtype, name in mcdata.hashed_structs[self.__hashed_ident]:
            o += datautils.pack(dtype, self.data[name])
        #Extension
        if self.__hashed_ident in hashed_extensions:
            o += hashed_extensions[self.__hashed_ident].encode_extra(self)
        return datautils.pack(MC_VARINT, len(o)) + o

    def __repr__(self):
        if self.direction == mcdata.CLIENT_TO_SERVER:
            s = ">>>"
        else:
            s = "<<<"

        if self.length is None:
            length = "?"
        else:
            length = str(self.length)

        data = copy.copy(self.data)
        if self.ident() == mcdata.packet_idents['PLAY<Map Chunk Bulk']:
            del data['data']

        format = "%s (0x%02X, 0x%02X) [%s]: %-"+str(max([len(i) for i in mcdata.hashed_names.values()])+1)+"s%s"
        return format % (s, self.state, self.id, length, mcdata.hashed_names[self.__hashed_ident], str(data))