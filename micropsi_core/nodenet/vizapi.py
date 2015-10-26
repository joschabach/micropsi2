import os
import numpy as np

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

from io import BytesIO
import base64

netapi = None  # the netapi itself will fill this parameter


class NodenetPlot(object):
    """ A NodenetPlot object represents an image, that can hold various plots
    in a grid-layout. You specify the size, and the number of rows and cols of the layout
    in the constructor.
    Then, you can add plots to the image, which will be filled into the gridlayout line by line.
    If the image is complete, you can either retrieve a base64-encoded string-representation of the
    image, that can be delivered to the client, or save the generated image to a file"""

    def __init__(self, plotsize=(6.0, 6.0), rows=1, cols=1, wspace=0.1, hspace=0.1):
        """ Creates a new empty figure.
        The figure can contain a variable number of plots, that are specified via
        the rows and cols parameters.
        Parameters:
            plotsize - A tuple indicating the (x, y) size of the Image
            rows - the number of rows of plots
            cols - the number of cols of plots
            wspace - vertical spacing between plots
            hspace - horizontal spacing between plots
        """
        self.figure = plt.figure(figsize=plotsize)
        self.plotindex = 0
        self.rows = rows
        self.cols = cols
        self.grid = gridspec.GridSpec(rows, cols, wspace=wspace, hspace=hspace)

    def add_activation_plot(self, nodespace, groupname):
        """ Adds a plot of node-activations to the figure
        Parameters:
            nodespace - the uid of the nodespace where the group of nodes resides
            groupname - the name of the group of nodes
        """
        activations = netapi.get_activations(nodespace, groupname)
        act = np.array(activations)
        sz = int(np.ceil(np.sqrt(act.shape[0])))
        _A = act.reshape((sz, sz))
        ax = plt.Subplot(self.figure, self.grid[self.plotindex])
        ax.set_xticks([])
        ax.set_yticks([])
        ax.imshow(_A, cmap=matplotlib.cm.gray, vmin=0.0, vmax=1.0)
        self.figure.add_subplot(ax)
        self.plotindex += 1

    def add_linkweights_plot(self, from_nodespace, from_group, to_nodespace, to_group, wspace=0.1, hspace=0.1):
        """ Adds a plot of linkweights to the figure.
        Parameters:
            from_nodespace - nodespace uid of from_group
            from_group - the name of the group where the links originate
            to_nodespace - nodespace uid of to_group
            to_group - the name of the group where the links terminate
            wspace - vertical spacing between the tiles
            hspace - horizontal spacing between the tiles
        """
        values = netapi.get_link_weights(from_nodespace, from_group, to_nodespace, to_group)
        _A = np.array(values)
        # compute rows & cols
        (row, col) = _A.shape
        sz = int(np.ceil(np.sqrt(row)))
        n = int(np.ceil(np.sqrt(col)))
        m = int(np.ceil(col / n))
        grid = gridspec.GridSpecFromSubplotSpec(sz, sz, subplot_spec=self.grid[self.plotindex], wspace=wspace, hspace=hspace)
        for r in range(row):
            ax = plt.Subplot(self.figure, grid[r])
            ax.set_xticks([])
            ax.set_yticks([])
            # clim = np.max(np.abs(A[r, :]))  # np.max(np.abs(A)
            # plt.imshow(A[r, :].reshape((n, n)) / clim, cmap=matplotlib.cm.gray)
            ax.imshow(_A[r, :].reshape((m, n)), cmap=matplotlib.cm.gray)  # , vmin=-1.0, vmax=1.0)
            self.figure.add_subplot(ax)
        self.plotindex += 1

    def save_to_file(self, filename):
        """ saves the generated figure to the given file"""
        filepath = os.path.abspath(filename)
        self.figure.savefig(filepath, format="png")
        return filepath

    def to_base64(self):
        """ returns the base64 encoded bytestring of the generated figure"""
        bio = BytesIO()
        self.figure.savefig(bio, format="png")
        return base64.encodebytes(bio.getvalue()).decode("utf-8")

