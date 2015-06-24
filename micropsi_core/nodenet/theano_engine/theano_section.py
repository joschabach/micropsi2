

import json
import os
import copy
import warnings

import theano
from theano import tensor as T
import numpy as np
import scipy.sparse as sp
import scipy

from configuration import config as settings

class TheanoSection():

    def __init__(self, nodenet):

        self.nodenet = nodenet
        self.logger = nodenet.logger

        # array, index is node id, value is numeric node type
        self.allocated_nodes = None

        self.allocated_nodes = np.zeros(self.nodenet.NoN, dtype=np.int32)
