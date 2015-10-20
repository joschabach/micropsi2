import os
import numpy as np
import math
import matplotlib
import matplotlib.pyplot as plt
from io import BytesIO
import base64


def plot_sensor_input(activations, plot_color=False):
    pass


def plotter_activation_grayscale(activations, items_per_row=2):
    """ Creates a plot of a bunch of group activations """

    plotsize = 4.0

    if type(activations) != list:
        activations = [activations]

    rows = math.ceil(len(activations) / items_per_row)
    cols = items_per_row if rows > 1 else len(activations)

    fig = plt.figure(figsize=(cols * plotsize, rows * plotsize))

    for idx, patch in enumerate(activations):
        act = np.array(patch)
        sz = int(np.ceil(np.sqrt(act.shape[0])))
        _A = act.reshape((sz, sz))
        ax = plt.subplot(rows, cols, (idx + 1 // items_per_row) + 1)
        plt.setp(ax.get_xticklabels(), visible=False)
        plt.setp(ax.get_yticklabels(), visible=False)
        ax.xaxis.set_ticks_position('none')
        ax.yaxis.set_ticks_position('none')
        plt.imshow(_A, cmap=matplotlib.cm.gray, vmin=0.0, vmax=1.0)
        fig.tight_layout()

    return fig


def plotter_linkweights_grayscale(linkweights):
    """ Creates a plot of link activations"""
    fig = plt.figure(figsize=(6.0, 6.0))  # in inches
    _A = np.array(linkweights)
    # rescale
    # A = A - np.average(A)
    # compute rows & cols
    (row, col) = _A.shape
    sz = int(np.ceil(np.sqrt(row)))
    n = int(np.ceil(np.sqrt(col)))
    m = int(np.ceil(col / n))
    # set figure properties
    for r in range(row):
        ax = plt.subplot(sz, sz, r + 1)
        plt.setp(ax.get_xticklabels(), visible=False)
        plt.setp(ax.get_yticklabels(), visible=False)
        ax.xaxis.set_ticks_position('none')
        ax.yaxis.set_ticks_position('none')
        # clim = np.max(np.abs(A[r, :]))  # np.max(np.abs(A)
        # plt.imshow(A[r, :].reshape((n, n)) / clim, cmap=matplotlib.cm.gray)
        plt.imshow(_A[r, :].reshape((m, n)), cmap=matplotlib.cm.gray)  # , vmin=-1.0, vmax=1.0)
    return fig


class VizAPI(object):

    def __init__(self, nodenet, netapi):
        self.netapi = netapi
        self.nodenet = nodenet

    def _plot_custom(self, plotfunc, filename=None, **plotter_params):
        fig = plotfunc(**plotter_params)
        filepath = os.path.abspath(filename)
        if filename:
            fig.savefig(filepath, format="png")
            return filepath
        else:
            bio = BytesIO()
            fig.savefig(bio, format="png")
            return base64.encodebytes(bio.getvalue()).decode("utf-8")

    def plot_activations(self, groups, filename=None, **plotter_params):
        """ Plots activations from a bunch of nodegroups with the specified plotter.
        Writes the image to the disk, if you give a filename, or otherwise returns base64 encoded bytestream.
        Parameters:
            groups: an array of (nodespace, groupname) tuples
        """
        activations = []
        for nodespace, groupname in groups:
            activations.append(self.netapi.get_activations(nodespace, groupname))
        plotter_params['activations'] = activations
        return self._plot_custom(plotter_activation_grayscale, filename, **plotter_params)

    def plot_linkweights(self, from_nodespace, from_group, to_nodespace, to_group, filename=None, **plotter_params):
        """ Plots link-weights from one nodegroup to another with the specified plotter.
        Writes the image to the disk, if you give a filename, or otherwise returns base64 encoded bytestream.
        """
        plotter_params['linkweights'] = self.netapi.get_link_weights(from_nodespace, from_group, to_nodespace, to_group)
        return self._plot_custom(plotter_linkweights_grayscale, filename, **plotter_params)
