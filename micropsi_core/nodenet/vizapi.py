import os
import numpy as np

import matplotlib
import platform

# we need special backends to work around the default behaviour
# expecting the main-thread to do gui-stuff, since we're
# (a) a multithreaded webserver, and
# (b) plot from the runner-thread as well as the frontend
# find os: http://stackoverflow.com/q/1854
# find supported backends: http://stackoverflow.com/a/13731150
# if tested, include here:
# if platform.system() == "Darwin":
#     matplotlib.use('macosx')
# else:
matplotlib.use('agg')

import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

from io import BytesIO
import base64


class NodenetPlot(object):
    """ A NodenetPlot object represents an image, that can hold various plots
    in a grid-layout. You can specify the size of the image, and the layout in
    rows and cols.
    Then, you can add plots to the image, which will be filled into the gridlayout line by line.
    If the image is complete, you can either retrieve a base64-encoded string-representation of the
    image, that can be delivered to the client, or save the generated image to a file
    e.g.:
    >>> image = NodenetPlot(cols=2)
    >>> image.add_activation_plot(netapi.get_activations(ns1, group1))
    >>> image.add_linkweights_plot(netapi.get_link_weights(ns1, group1, ns2, group2))
    >>> image.save_to_file('/tmp/plot.png')

    If you provide a name for the plots, you can later update them:
    >>> image = NodenetPlot(cols=2)
    >>> image.add_activation_plot(np.random.rand(10), name="group_activation_plot")
    >>> new_data = np.random.rand(10)
    >>> image.update_plot('group_activation_plot', new_data)

    """

    def __init__(self, plotsize=(6.0, 6.0), rows=1, cols=1, wspace=0.1, hspace=0.1):
        """ Creates a new empty figure.
        The figure can contain a variable number of plots, that are specified via
        the rows and cols parameters.
        Parameters:
            plotsize - A tuple indicating the (x, y) size of the Image, defaults to (6, 6)
            rows - the number of rows of plots, defaults to 1
            cols - the number of cols of plots, defaults to 1
            wspace - vertical spacing between plots, defaults to 0.1
            hspace - horizontal spacing between plots, defaults to 0.1
        """
        plt.close()  # attempt to close old instance
        self.figure = plt.figure(figsize=plotsize)
        self.plots = {}
        self.plotindex = 0
        self.rows = rows
        self.cols = cols
        self.grid = gridspec.GridSpec(rows, cols, wspace=wspace, hspace=hspace)

    def update_plot(self, name, new_data):
        """ update a named plot in this Image with the new data
        returns True on success, False otherwise.
        Parameters:
            name - the name you gave when adding the plot
            new_data - the new data for the plot
        """
        if name in self.plots:
            plot, shape = self.plots[name]
            if new_data.shape != shape:
                new_data = new_data.reshape(shape)
            if type(plot) == list:
                # 4d plot
                row, col, inner_row, inner_col = shape
                for r in range(row):
                    row_data = new_data[r, :]
                    for c in range(col):
                        plot[r+c].set_data(row_data[c, :])
            else:
                # 2d plot
                plot.set_data(new_data)
            return True
        return False

    def add_activation_plot(self, activations, name=None, rows=-1, cols=-1, vmin=None, vmax=None):
        """ Adds a plot of node-activations to the figure.
        Per default, the plot will attempt to render the activations into a square image
        If you have non-quadratic data, you have to give numbers for rows and cols so that the
        numbers can be reshaped accordingly
        Parameters:
            activations - array of activations
            name - optional identification for later updates
            rows - number of rows, defaults to sqrt()
            cols - number of cols, defaults to sqrt()
            vmin - minimal value, defaults to 0
            vmax - maximal value, defaults to 1
        """
        data = np.array(activations)
        if rows > 0 or cols > 0:
            matrix = data.reshape((rows, cols))
        else:
            sz = int(np.ceil(np.sqrt(data.shape[0])))
            matrix = data.reshape((sz, sz))

        self.add_2d_matrix_plot(matrix, name=name, vmin=vmin, vmax=vmax)

    def add_linkweights_plot(self, linkweights, name=None, wspace=0.1, hspace=0.1, rows_outer=0, cols_outer=0, rows_inner=0, cols_inner=0):
        """ Adds a plot of linkweights to the figure.
        Parameters:
            linkweights - output of netapi.get_link_weights
            name - optional identification for later updates
            wspace - vertical spacing, defaults to 0.1
            hspace - horizontal spacing, defaults to 0.1
            rows_outer - number of rows of linkweight-plots, defaults to sqrt()
            cols_outer - number of cols of linkweight-plots, defaults to sqrt()
            rows_inner - number of pixel-rows per linkweight-plot, defaults to sqrt()
            cols_inner - number of pixel-cols per linkweight-plot, defaults to sqrt()
        """
        data = np.array(linkweights)
        r, c = data.shape
        outer_sqrt = int(np.ceil(np.sqrt(r)))
        inner_sqrt = int(np.ceil(np.sqrt(c)))
        matrix = data.reshape((
            rows_outer or outer_sqrt,
            cols_outer or outer_sqrt,
            rows_inner or inner_sqrt,
            cols_inner or inner_sqrt
        ))
        result = self.add_4d_matrix_plot(matrix, name=name, wspace=wspace, hspace=hspace)

    def add_2d_matrix_plot(self, matrix, name=None, vmin=None, vmax=None):
        """ General plotter function to add a two-dimensional plot. The shape
        of the passed matrix determins the layout in rows and cols of the
        plot
        Parameters:
            data - 2-dimensional numpy matrix
            vmin - minimal value
            vmax - maximal value
        """
        ax = plt.Subplot(self.figure, self.grid[self.plotindex])
        ax.set_xticks([])
        ax.set_yticks([])
        thing = ax.imshow(matrix, cmap=matplotlib.cm.gray, vmin=vmin, vmax=vmax)
        self.figure.add_subplot(ax)
        self.plotindex += 1
        if name is not None:
            self.plots[name] = thing, matrix.shape

    def add_4d_matrix_plot(self, data, name=None, wspace=0, hspace=0, vmin=None, vmax=None):
        """ General plotter function to add a grid of several two-dimensional plots
        The shape of the passed matrix determins the layout in rows and cols of the
        plot
        Parameters:
            data - 4-dimensional numpy matrix
            wspace - vertical spacing
            hspace - horizontal spacing
            vmin - minimal value
            vmax - maximal value
        """
        # compute rows & cols
        row, col, inner_row, inner_col = data.shape
        grid = gridspec.GridSpecFromSubplotSpec(row, col, subplot_spec=self.grid[self.plotindex], wspace=wspace, hspace=hspace)
        plots = []
        for r in range(row):
            row_data = data[r, :]
            for c in range(col):
                ax = plt.Subplot(self.figure, grid[(r * col + c)])
                ax.set_xticks([])
                ax.set_yticks([])
                plots.append(ax.imshow(row_data[c, :], cmap=matplotlib.cm.gray, vmin=vmin, vmax=vmax))
                self.figure.add_subplot(ax)
        self.plotindex += 1
        if name is not None:
            self.plots[name] = plots, data.shape

    def save_to_file(self, filename, format="png", **params):
        """ saves the generated figure to the given file
        Parameters:
            filename - the target filename. expects absolute paths, or saves to toolkit-root
            format - the file-format. defaults to png
            takes additional keyword-arguments for savefig, see http://matplotlib.org/api/pyplot_api.html#matplotlib.pyplot.savefig
        """
        filepath = os.path.abspath(filename)
        self.figure.savefig(filepath, format=format, **params)
        return filepath

    def to_base64(self, format="png", **params):
        """ returns the base64 encoded bytestring of the generated figure
        Parameters:
            format - the file-format. defaults to png
            takes additional keyword-arguments for savefig, see http://matplotlib.org/api/pyplot_api.html#matplotlib.pyplot.savefig
        """
        bio = BytesIO()
        self.figure.savefig(bio, format=format, **params)
        return ''.join(base64.encodebytes(bio.getvalue()).decode("utf-8").splitlines())
