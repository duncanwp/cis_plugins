from cis.collocation.col_framework import AbstractDataOnlyKernel
import numpy as np


class median(AbstractDataOnlyKernel):
    """
    Calculate mean of data points
    """

    def get_value_for_data_only(self, values):
        """
        return the mean
        """
        return np.median(values)

