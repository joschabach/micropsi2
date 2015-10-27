import os
import numpy as np

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

from io import BytesIO
import base64


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
        plt.close()  # attempt to close old instance
        self.figure = plt.figure(figsize=plotsize)
        self.plotindex = 0
        self.rows = rows
        self.cols = cols
        self.grid = gridspec.GridSpec(rows, cols, wspace=wspace, hspace=hspace)

    def add_activation_plot(self, activations, rows=-1, cols=-1, vmin=0, vmax=1):
        """ Adds a plot of node-activations to the figure.
        Per default, the plot will attempt to render the activations into a square image
        If you have non-quadratic data, you have to give numbers for rows and cols so that the
        numbers can be reshaped accordingly
        Parameters:
            activations - array of activations
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
        self.add_2d_matrix_plot(matrix, vmin=vmin, vmax=vmax)

    def add_linkweights_plot(self, linkweights, wspace=0.1, hspace=0.1, rows_outer=0, cols_outer=0, rows_inner=0, cols_inner=0):
        """ Adds a plot of linkweights to the figure.
        Parameters:
            linkweights - output of netapi.get_link_weights
            wspace - vertical spacing, defaults to 0.1
            hspace - horizontal spacing, defaults to 0.1
            rows_outer - number of rows of linkweight-plots, defaults to sqrt()
            cols_outer - number of cols of linkweight-plots, defaults to sqrt()
            rows_inner - number of pixel-rows per linkweight-plot, defaults to sqrt()
            cols_inner - number of pixel-cols per linkweight-plot, defaults to sqrt()
        """
        data = np.array(linkweights)
        (r, c) = data.shape
        outer_sqrt = int(np.ceil(np.sqrt(r)))
        inner_sqrt = int(np.ceil(np.sqrt(c)))
        matrix = data.reshape((
            rows_outer or outer_sqrt,
            cols_outer or outer_sqrt,
            rows_inner or inner_sqrt,
            cols_inner or inner_sqrt
        ))
        self.add_4d_matrix_plot(matrix, wspace=wspace, hspace=hspace)

    def add_2d_matrix_plot(self, matrix, vmin=0, vmax=1):
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
        ax.imshow(matrix, cmap=matplotlib.cm.gray, vmin=vmin, vmax=vmax)
        self.figure.add_subplot(ax)
        self.plotindex += 1

    def add_4d_matrix_plot(self, data, wspace=0, hspace=0, vmin=0, vmax=1):
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
        (row, col, inner_row, inner_col) = data.shape
        grid = gridspec.GridSpecFromSubplotSpec(row, col, subplot_spec=self.grid[self.plotindex], wspace=wspace, hspace=hspace)
        for r in range(row):
            row_data = data[r, :]
            for c in range(col):
                ax = plt.Subplot(self.figure, grid[(r * col + c)])
                ax.set_xticks([])
                ax.set_yticks([])
                ax.imshow(row_data[c, :], cmap=matplotlib.cm.gray, vmin=vmin, vmax=vmax)
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
