import os
import numpy as np

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

from io import BytesIO
import base64

netapi = None  # the netapi itself will fill this parameter


class NodenetPlot(object):

    def __init__(self, plotsize=(6.0, 6.0), rows=1, cols=1, wspace=0.1, hspace=0.1):
        self.figure = plt.figure(figsize=plotsize)
        self.plotindex = 0
        self.rows = rows
        self.cols = cols
        self.grid = gridspec.GridSpec(rows, cols, wspace=wspace, hspace=hspace)

    def add_activation_plot(self, nodespace, groupname):
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
        """ Plots link-weights from one nodegroup to another with the specified plotter.
        Writes the image to the disk, if you give a filename, or otherwise returns base64 encoded bytestream.
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
        """ saves a figure, or an array of figures to the given file"""
        filepath = os.path.abspath(filename)
        self.figure.savefig(filepath, format="png")
        return filepath

    def to_base64(self):
        """ returns the base64 encoded bytestring of a figure, or an array of figures"""
        bio = BytesIO()
        self.figure.savefig(bio, format="png")
        return base64.encodebytes(bio.getvalue()).decode("utf-8")

