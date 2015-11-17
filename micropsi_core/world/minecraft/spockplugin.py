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

    def __init__(self, ploader, settings):

        # register required plugins
        self.net = ploader.requires('Net')
        self.event = ploader.requires('Event')
        self.world = ploader.requires('World')
        self.clientinfo = ploader.requires('ClientInfo')
        self.threadpool = ploader.requires('ThreadPool')

        self.inventory = []
        self.quickslots = []

        self.event.reg_event_handler(
            (3, 0, 48),
            self.update_inventory
        )

        self.worldadapter = None

        # make references between micropsi world and MicropsiPlugin
        self.micropsi_world = settings['micropsi_world']
        self.micropsi_world.spockplugin = self

    def chat(self, message):
        # else push chat message
        self.net.push(Packet(ident='PLAY>Chat Message', data={'message': message}))

    def is_connected(self):
        return self.net.connected and self.net.proto_state

    def dispatchMovement(self, move_x, move_z):
        target_coords = self.get_int_coordinates()
        if move_x:
            target_coords['x'] += 1
        elif move_z:
            target_coords['z'] += 1

        ground_offset = 2  # assume impossible
        y = target_coords['y'] - 1  # current block agent is standing on

        # check if the next step is possible: nothing in the way, height diff <= 1
        if self.get_block_type(target_coords['x'], y + 2, target_coords['z']) > 0:
            ground_offset = 2
        elif self.get_block_type(target_coords['x'], y + 1, target_coords['z']) > 0 and \
                self.get_block_type(target_coords['x'], y + 3, target_coords['z']) <= 0:
            ground_offset = 1
        elif self.get_block_type(target_coords['x'], y, target_coords['z']) > 0:
            ground_offset = 0
        elif self.get_block_type(target_coords['x'], y - 1, target_coords['z']) > 0:
            ground_offset = -1

        if ground_offset < 2:
            self.clientinfo.position['x'] = target_coords['x'] + .5
            self.clientinfo.position['y'] = target_coords['y'] + ground_offset
            self.clientinfo.position['stance'] = target_coords['y'] + ground_offset + STANCE_ADDITION
            self.clientinfo.position['z'] = target_coords['z'] + .5
            self.clientinfo.position['on_ground'] = True

    def get_block_type(self, x, y, z):
        """
        Get the block type of a particular voxel.
        """
        x, y, z = int(x), int(y), int(z)
        x, rx = divmod(x, 16)
        y, ry = divmod(y, 16)
        z, rz = divmod(z, 16)

        if y > 0x0F:
            return -1  # was 0
        try:
            column = self.world.columns[(x, z)]
            chunk = column.chunks[y]
        except KeyError:
            return -1

        if chunk is None:
            return -1  # was 0
        return chunk.block_data.get(rx, ry, rz) >> 4

    def get_biome_info(self, pos=None):
        from spock.mcmap.mapdata import biomes
        if pos is None:
            pos = self.get_int_coordinates()
        key = (pos['x'] // 16, pos['z'] // 16)
        columns = self.world.columns
        if key not in columns:
            return None
        current_column = columns[key]
        biome_id = current_column.biome.get(pos['x'] % 16, pos['z'] % 16)
        if biome_id >= 0:
            return biomes[biome_id]
        else:
            return None

    def get_temperature(self, pos=None):
        if pos is None:
            pos = self.get_int_coordinates()
        biome = self.get_biome_info(pos=pos)
        if biome:
            temp = biome['temperature']
            if pos['y'] > 64:
                temp -= (0.00166667 * (pos['y'] - 64))
            return temp
        else:
            return None

    def eat(self):
        """ Attempts to eat the held item. Assumes held item implements eatable """
        self.worldadapter.logger.debug('eating a bread')
        data = {
            'location': self.get_int_coordinates(),
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
        # 0     = crafting output
        # 1-4   = crafting ingredients
        # 5-8   = wearables from helm to boot
        # 9-35  = inventory by rows
        # 36-44 = quickslots
        self.inventory = packet.data['slots']
        self.quickslots = packet.data['slots'][36:45]

    def count_inventory_item(self, item):
        count = 0
        for slot in self.inventory:
            if slot and slot['id'] == item:
                count += slot['amount']
        return count

    def change_held_item(self, target_slot):
        """ Changes the held item to a quick inventory slot """
        self.net.push(Packet(ident='PLAY>Held Item Change', data={'slot': target_slot}))

    def move(self, position=None):
        if not (self.net.connected and self.net.proto_state == mcdata.PLAY_STATE):
            return
        # writes new data to clientinfo which is pulled and pushed to Minecraft by ClientInfoPlugin
        self.clientinfo.position = position

    def get_int_coordinates(self):
        return {
            'x': int(self.clientinfo.position['x']),
            'y': int(self.clientinfo.position['y']),
            'z': int(self.clientinfo.position['z'])
        }
