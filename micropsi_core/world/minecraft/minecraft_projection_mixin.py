from math import sqrt, radians, cos, sin


class MinecraftProjectionMixin(object):

    def project(self, xi, yi, zi, x0, y0, z0, yaw, pitch):
        """
        Given a point on the projection plane and the agent's position, cast a
        ray to find the nearest block type that isn't air and its distance from
        the projective plane.
        """
        distance = 0    # just a counter
        block_type = -1  # consider mapping nothingness to air, ie. -1 to 0

        # compute difference vector between projective point and image point
        diff = (xi - x0, yi - y0, zi - z0)

        # normalize difference vector
        magnitude = sqrt(diff[0] ** 2 + diff[1] ** 2 + diff[2] ** 2)
        if magnitude == 0.:
            magnitude = 1.
        norm = (diff[0] / magnitude, diff[1] / magnitude, diff[2] / magnitude)

        # rotate norm vector
        norm = self.rotate_around_x_axis(norm, pitch)
        norm = self.rotate_around_y_axis(norm, yaw)

        # rotate diff vector
        diff = self.rotate_around_x_axis(diff, pitch)
        diff = self.rotate_around_y_axis(diff, yaw)

        # add diff to projection point aka agent's position
        xb, yb, zb = x0 + diff[0], y0 + diff[1], z0 + diff[2]

        while block_type <= 0:  # which is air and nothingness

            # check block type of next distance point along ray
            # aka add normalized difference vector to image point
            # TODO: consider a more efficient way to move on the ray, eg. a log scale
            xb += norm[0]
            yb += norm[1]
            zb += norm[2]

            block_type = self.spockplugin.get_block_type(xb, yb, zb)

            distance += 1
            if distance >= self.max_dist:
                break

        return block_type, distance

    def rotate_around_x_axis(self, pos, angle):
        """ Rotate a 3D point around the x-axis given a specific angle. """

        # convert angle in degrees to radians
        theta = radians(angle)

        # rotate vector
        xx, y, z = pos
        yy = y * cos(theta) - z * sin(theta)
        zz = y * sin(theta) + z * cos(theta)

        return (xx, yy, zz)

    def rotate_around_y_axis(self, pos, angle):
        """ Rotate a 3D point around the y-axis given a specific angle. """

        # convert angle in degrees to radians
        theta = radians(angle)

        # rotate vector
        x, yy, z = pos
        xx = x * cos(theta) + z * sin(theta)
        zz = - x * sin(theta) + z * cos(theta)

        return (xx, yy, zz)

    def rotate_around_z_axis(self, pos, angle):
        """ Rotate a 3D point around the z-axis given a specific angle. """

        # convert angle in degrees to radians
        theta = radians(angle)

        # rotate vector
        x, y, zz = pos
        xx = x * cos(theta) - y * sin(theta)
        yy = x * sin(theta) + y * cos(theta)

        return (xx, yy, zz)

    def frange(self, start, end, step):
        """
        Range for floats.
        """
        while start < end:
            yield start
            start += step
