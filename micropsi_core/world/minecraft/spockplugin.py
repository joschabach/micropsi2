import logging
from spock.mcmap import smpmap
from spock.mcp import mcdata, mcpacket
from spock.mcp.mcpacket import Packet
from spock.utils import pl_announce

STANCE_ADDITION = 1.620
STEP_LENGTH = 1.0
JUMPING_MAGIC_NUMBER = 0  # 2 used to work


@pl_announce('Micropsi')
class MicropsiPlugin(object):

    inventory = []
    quickslots = []

    def __init__(self, ploader, settings):

        # register required plugins
        self.net = ploader.requires('Net')
        self.event = ploader.requires('Event')
        self.world = ploader.requires('World')
        self.clientinfo = ploader.requires('ClientInfo')
        self.threadpool = ploader.requires('ThreadPool')

        self.event.reg_event_handler(
            (3, 0, 48),
            self.update_inventory
        )

        # make references between micropsi world and MicropsiPlugin
        self.micropsi_world = settings['micropsi_world']
        self.micropsi_world.spockplugin = self

    def chat(self, message):
        if not (self.is_connected()):
            raise RuntimeError("Spock is not connected")
        # else push chat message
        self.net.push(Packet(ident='PLAY>Chat Message', data={'message': message}))

    def is_connected(self):
        return self.net.connected and self.net.proto_state

    def dispatchMovement(self, bot_coords, move_x, move_z):
        target_coords = (self.normalize_coordinate(bot_coords[0] + (STEP_LENGTH if (move_x > 0) else 0) + (-STEP_LENGTH if (move_x < 0) else 0)),
                         bot_coords[1],
                         self.normalize_coordinate(bot_coords[2] + (STEP_LENGTH if (move_z > 0) else 0) + (-STEP_LENGTH if (move_z < 0) else 0)))

        target_block_coords = (self.normalize_block_coordinate(target_coords[0]),
                               self.normalize_block_coordinate(target_coords[1]),
                               self.normalize_block_coordinate(target_coords[2]))
        ground_offset = 0
        for y in range(0, 16):
            if self.get_block_type(target_block_coords[0], y, target_block_coords[2]) != 0:
                ground_offset = y + 1
        if target_coords[1] // 16 * 16 + ground_offset - target_coords[1] <= 1:
            self.move(position={
                'x': target_coords[0],
                'y': target_coords[1] // 16 * 16 + ground_offset,
                'z': target_coords[2],
                'yaw': self.clientinfo.position['yaw'],
                'pitch': self.clientinfo.position['pitch'],
                'on_ground': self.clientinfo.position['on_ground'],
                'stance': target_coords[1] // 16 * 16 + ground_offset + STANCE_ADDITION
            })

    def get_block_type(self, x, y, z):
        """ Jonas' get_voxel_blocktype(..) """
        key = (x // 16, z // 16)
        columns = self.world.columns
        if key not in columns:
            return -1
        current_column = columns[key]
        if len(current_column.chunks) <= y // 16:
            return -1
        try:
            current_section = current_column.chunks[y // 16]
        except IndexError:
            return -1
        if current_section is None:
            return -1
        else:
            block_type_id = current_section.block_data.get(x % 16, y % 16, z % 16)
            # print('blocktype: %s' % str( block_type_id/ 16))
            return int(block_type_id / 16)

    def eat(self):
        """ Attempts to eat the held item. Assumes held item implements eatable """
        data = {
            'location': {
                'x': int(self.clientinfo.position['x']),
                'y': int(self.clientinfo.position['y']),
                'z': int(self.clientinfo.position['z'])
            },
            'direction': -1,
            'held_item': {
                'id': 297,
                'amount': 1,
                'damage': 0
            },
            'cur_pos_x': -1,
            'cur_pos_y': -1,
            'cur_pos_z': -1
        }
        self.net.push(Packet(ident='PLAY>Player Block Placement', data=data))

    def give_item(self, item, amount=1):
        message = "/item %s %d" % (str(item), amount)
        self.net.push(Packet(ident='PLAY>Chat Message', data={'message': message}))

    def update_inventory(self, event, packet):
        self.inventory = packet.data['slots']
        self.quickslots = packet.data['slots'][36:9]

    def change_held_item(self, target_slot):
        """ Changes the held item to a quick inventory slot """
        self.net.push(Packet(ident='PLAY>Held Item Change', data={'Slot': target_slot}))

    def move(self, position=None):

        if not (self.net.connected and self.net.proto_state == mcdata.PLAY_STATE):
            return
        # writes new data to clientinfo which is pulled and pushed to Minecraft by ClientInfoPlugin
        self.clientinfo.position = position

    def normalize_coordinate(self, coordinate):
        return coordinate // 1 + 0.5

    def normalize_block_coordinate(self, coordinate):
        return int(coordinate // 1 % 16)
