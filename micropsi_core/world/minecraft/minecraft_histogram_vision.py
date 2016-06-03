import random
from configuration import config as cfg
from .minecraft_graph_locomotion import MinecraftGraphLocomotion
from .minecraft_projection_mixin import MinecraftProjectionMixin


class MinecraftHistogramVision(MinecraftGraphLocomotion, MinecraftProjectionMixin):

    # specs for vision /fovea
    # focal length larger 0 means zoom in, smaller 0 means zoom out
    # ( small values of focal length distort the image if things are close )
    # image proportions define the part of the world that can be viewed
    # patch dimensions define the size of the sampled patch that's stored to file
    focal_length = 0.5    # distance of image plane from projective point /fovea
    max_dist = 64         # maximum distance for raytracing
    resolution_w = 1.0    # number of rays per tick in viewport /camera coordinate system
    resolution_h = 1.0    # number of rays per tick in viewport /camera coordinate system
    im_width = 128        # width of projection /image plane in the world
    im_height = 64        # height of projection /image plane in the world
    cam_width = 1.        # width of normalized device /camera /viewport
    cam_height = 1.       # height of normalized device /camera /viewport
    # Note: adapt patch width to be smaller than or equal to resolution x image dimension
    patch_width = 32      # width of a fovea patch  # 128 || 32
    patch_height = 32     # height of a patch  # 64 || 32
    num_fov = 6           # the root number of fov__ sensors, ie. there are num_fov x num_fov fov__ sensors
    num_steps_to_keep_vision_stable = 3

    # Note: actors fov_x, fov_y and the saccader's gates fov_x, fov_y ought to be parametrized [0.,2.] w/ threshold 1.
    # -- 0. means inactivity, values between 1. and 2. are the scaled down movement in x/y direction on the image plane

    def __init__(self, world, uid=None, **data):
        super().__init__(world, uid, **data)
        self.datasources.update({
            'fov_x': 0,    # fovea sensors receive their input from the fovea actors
            'fov_y': 0,
            'fov_hist__-01': 0,  # these names must be the most commonly observed block types
            'fov_hist__000': 0,
            'fov_hist__001': 0,
            'fov_hist__002': 0,
            'fov_hist__003': 0,
            'fov_hist__004': 0,
            'fov_hist__009': 0,
            'fov_hist__012': 0,
            'fov_hist__017': 0,
            'fov_hist__018': 0,
            'fov_hist__020': 0,
            'fov_hist__026': 0,
            'fov_hist__031': 0,
            'fov_hist__064': 0,
            'fov_hist__106': 0,
        })

        targets = {
            'orientation': 0,
            'fov_x': 0,
            'fov_y': 0
        }

        self.datatargets.update(targets)
        self.datatarget_feedback.update(targets)

        # add datasources for fovea
        for i in range(self.num_fov):
            for j in range(self.num_fov):
                name = "fov__%02d_%02d" % (i, j)
                self.datasources[name] = 0.

        self.simulated_vision = False
        if 'simulate_vision' in cfg['minecraft']:
            self.simulated_vision = True
            self.simulated_vision_datafile = cfg['minecraft']['simulate_vision']
            self.logger.info("Setting up minecraft_graph_locomotor to simulate vision from data file %s", self.simulated_vision_datafile)

            import os
            import csv
            self.simulated_vision_data = None
            self.simulated_vision_datareader = csv.reader(open(self.simulated_vision_datafile))
            if os.path.getsize(self.simulated_vision_datafile) < (500 * 1024 * 1024):
                self.simulated_vision_data = [[float(datapoint) for datapoint in sample] for sample in self.simulated_vision_datareader]
                self.simulated_data_entry_index = 0
                self.simulated_data_entry_max = len(self.simulated_vision_data) - 1

        if 'record_vision' in cfg['minecraft']:
            self.record_file = open(cfg['minecraft']['record_vision'], 'a')

    def update_data_sources_and_targets(self):
        """called on every world calculation step to advance the life of the agent"""

        if self.waiting_for_spock:
            super().update_data_sources_and_targets()

        else:
            if self.simulated_vision:
                self.simulate_visual_input()
            else:
                super().update_data_sources_and_targets()

                # change pitch and yaw every x world steps to increase sensory variation
                # < ensures some stability to enable learning in the autoencoder
                if self.world.current_step % self.num_steps_to_keep_vision_stable == 0:
                    # for patches pitch = 10 and yaw = random.randint(-10,10) were used
                    # for visual field pitch = randint(0, 30) and yaw = randint(1, 360) were used
                    self.spockplugin.clientinfo.position['pitch'] = 10
                    self.spockplugin.clientinfo.position['yaw'] = random.randint(-10, 10)
                    self.datatargets['pitch'] = self.spockplugin.clientinfo.position['pitch']
                    self.datatargets['yaw'] = self.spockplugin.clientinfo.position['yaw']
                    # Note: datatargets carry spikes not continuous signals, ie. pitch & yaw will be 0 in the next step
                    self.datatarget_feedback['pitch'] = 1.0
                    self.datatarget_feedback['yaw'] = 1.0

                #
                orientation = self.datatargets['orientation']  # x_axis + 360 / orientation  degrees
                self.datatarget_feedback['orientation'] = 1.0
                # self.datatargets['orientation'] = 0

                # sample all the time
                # update fovea sensors, get sensory input, provide action feedback
                # make sure fovea datasources don't go below 0.
                self.datasources['fov_x'] = self.datatargets['fov_x'] - 1. if self.datatargets['fov_x'] > 0. else 0.
                self.datasources['fov_y'] = self.datatargets['fov_y'] - 1. if self.datatargets['fov_y'] > 0. else 0.
                loco_label = self.current_loco_node['name']  # because python uses call-by-object
                self.get_visual_input(self.datasources['fov_x'], self.datasources['fov_y'], loco_label)

                # Note: saccading can't fail because fov_x, fov_y are internal actors, hence we return immediate feedback
                if self.datatargets['fov_x'] > 0.0:
                    self.datatarget_feedback['fov_x'] = 1.0
                if self.datatargets['fov_y'] > 0.0:
                    self.datatarget_feedback['fov_y'] = 1.0

    def get_visual_input(self, fov_x, fov_y, label):
        """
        Spans an image plane.

        Note that the image plane is walked left to right, top to bottom ( before rotation )!
        This means that fov__00_00 gets the top left pixel, fov__15_15 gets the bottom right pixel.
        """
        # set agent position
        pos_x = self.spockplugin.clientinfo.position['x']
        pos_y = self.spockplugin.clientinfo.position['y'] + 0.620  # add some stance to y pos ( which is ground + 1 )
        pos_z = self.spockplugin.clientinfo.position['z']

        # set yaw and pitch ( in degrees )
        yaw = self.spockplugin.clientinfo.position['yaw']
        # consider setting yaw to a random value between 0 and 359
        pitch = self.spockplugin.clientinfo.position['pitch']

        # compute ticks per dimension
        tick_w = self.cam_width / self.im_width / self.resolution_w
        tick_h = self.cam_height / self.im_height / self.resolution_h

        # span image plane
        # the horizontal plane is split half-half, the vertical plane is shifted upwards
        h_line = [i for i in self.frange(pos_x - 0.5 * self.cam_width, pos_x + 0.5 * self.cam_width, tick_w)]
        v_line = [i for i in self.frange(pos_y - 0.05 * self.cam_height, pos_y + 0.95 * self.cam_height, tick_h)]

        # scale up fov_x, fov_y
        fov_x = round(fov_x * (self.im_width * self.resolution_w - self.patch_width))
        fov_y = round(fov_y * (self.im_height * self.resolution_h - self.patch_height))

        x0, y0, z0 = pos_x, pos_y, pos_z  # agent's position aka projective point
        zi = z0 + self.focal_length

        v_line.reverse()

        # compute block type values for the whole patch /fovea
        patch = []
        for i in range(self.patch_height):
            for j in range(self.patch_width):
                try:
                    block_type, distance = self.project(h_line[fov_x + j], v_line[fov_y + i], zi, x0, y0, z0, yaw, pitch)
                except IndexError:
                    block_type, distance = -1, -1
                    self.logger.warning("IndexError at (%d,%d)" % (fov_x + j, fov_y + i))
                patch.append(block_type)

        # write block type histogram values to self.datasources['fov_hist__*']
        # for every block type seen in patch, if there's a datasource for it, fill it with its normalized frequency
        normalizer = self.patch_width * self.patch_height
        # reset fov_hist sensors, then fill them with new values
        for k in self.datasources.keys():
            if k.startswith('fov_hist__'):
                self.datasources[k] = 0.
        for bt in set(patch):
            name = "fov_hist__%03d" % bt
            if name in self.datasources:
                self.datasources[name] = patch.count(bt) / normalizer

        # COMPUTE VALUES FOR fov__%02d_%02d SENSORS
        # if all values in the patch are the same, write zeros
        if patch[1:] == patch[:-1]:

            zero_patch = True
            patch_resc = [0.0] * self.patch_width * self.patch_height

        else:

            zero_patch = False
            # convert block types into binary values: map air and emptiness to black (0), everything else to white (1)
            patch_ = [0.0 if v <= 0 else 1.0 for v in patch]

            # normalize block type values
            # subtract the sample mean from each of its pixels
            mean = float(sum(patch_)) / len(patch_)
            patch_avg = [x - mean for x in patch_]  # TODO: throws error in ipython - why not here !?

            # truncate to +/- 3 standard deviations and scale to -1 and +1

            var = [x ** 2.0 for x in patch_avg]
            std = (sum(var) / len(var)) ** 0.5  # ASSUMPTION: all values of x are equally likely
            pstd = 3.0 * std
            # if block types are all the same number, eg. -1, std will be 0, therefore
            if pstd == 0.0:
                patch_std = [0.0 for x in patch_avg]
            else:
                patch_std = [max(min(x, pstd), -pstd) / pstd for x in patch_avg]

            # scale from [-1,+1] to [0.1,0.9] and write values to sensors
            patch_resc = [(1.0 + x) * 0.4 + 0.1 for x in patch_std]

        self.write_visual_input_to_datasources(patch_resc, self.patch_width, self.patch_height)

        if 'record_vision' in cfg['minecraft']:
            # do *not* record homogeneous and replayed patches
            if not zero_patch and not self.simulated_vision:
                if label == self.current_loco_node['name']:
                    data = "{0}".format(",".join(str(b) for b in patch))
                    self.record_file.write("%s,%s,%d,%d,%d,%d\n" % (data, label, pitch, yaw, fov_x, fov_y))
                else:
                    self.logger.warning('potentially corrupt data were ignored')

    def simulate_visual_input(self):
        """
        Every <self.num_steps_to_keep_vision_stable> steps read the next line
        from the vision file and fill its values into fov__*_* datasources.
        """
        if self.world.current_step % self.num_steps_to_keep_vision_stable == 0:
            line = None
            if self.simulated_vision_data is None:
                line = next(self.simulated_vision_datareader, None)
                if line is None:
                    self.logger.info("Simulating vision from data file, starting over...")
                    import csv
                    self.simulated_vision_datareader = csv.reader(open(self.simulated_vision_datafile))
                    line = next(self.simulated_vision_datareader)
                line = [float(entry) for entry in line]
            else:
                self.simulated_data_entry_index += 1
                if self.simulated_data_entry_index > self.simulated_data_entry_max:
                    self.logger.info("Simulating vision from memory, starting over, %s entries.", self.simulated_data_entry_max + 1)
                    self.simulated_data_entry_index = 0
                line = self.simulated_vision_data[self.simulated_data_entry_index]
            self.write_visual_input_to_datasources(line, self.num_fov, self.num_fov)

    def write_visual_input_to_datasources(self, patch, patch_width, patch_height):
        """
        Write a patch of the size self.num_fov times self.num_fov to self.datasourcesp['fov__*_*'].
        If num_fov is less than patch height and width, chose the horizontally centered , vertically 3/4 lower patch.
        """
        left_margin = max(0, (int(patch_width - self.num_fov) // 2) - 1)
        top_margin = max(0, (int(patch_height - self.num_fov) // 4 * 3) - 1)
        for i in range(self.num_fov):
            for j in range(self.num_fov):
                name = 'fov__%02d_%02d' % (i, j)
                self.datasources[name] = patch[(patch_height * (i + top_margin)) + j + left_margin]
