__author__ = 'rvuine'

import micropsi_core.tools
from abc import ABCMeta, abstractmethod


class StepOperator(metaclass=ABCMeta):
    """
    A step operator will be executed once per net step on all nodes.
    """

    @property
    @abstractmethod
    def priority(self):
        """
        Returns a numerical priority value used to determine step operator order execution.
        Lower priority operators will be executed first.
        The lowest possible value 0 and 1 are reserved for the Propagate and Calculate operators to ensure all step
        operators will be executed after propagation and node function calculation.
        """
        pass  # pragma: no cover

    @abstractmethod
    def execute(self, nodenet, nodes, netapi):
        """
        Actually execute the operator.
        """
        pass  # pragma: no cover


class Propagate(StepOperator):
    """
    Every node net needs a propagate operator
    """
    @property
    def priority(self):
        return 0

    @abstractmethod
    def execute(self, nodenet, nodes, netapi):
        pass  # pragma: no cover


class Calculate(StepOperator):
    """
    Every node net needs a calculate operator
    """
    @property
    def priority(self):
        return 1

    def execute(self, nodenet, nodes, netapi):
        pass  # pragma: no cover
