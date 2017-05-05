from cis.collocation.col_framework import AbstractDataOnlyKernel
import numpy as np

BINS = ['Not determined', 'Clean marine', 'Dust', 'Polluted continental',
        'Clean continental', 'Polluted dust', 'Smoke', 'Other']


class BinKernel(AbstractDataOnlyKernel):
    # return_size = np.amax(aerosol_types.data) + 1
    return_size = len(BINS)

    def get_value_for_data_only(self, values):
        return np.bincount(values, minlength=self.return_size)

    def get_variable_details(self, var_name, var_long_name, var_standard_name, var_units):
        """Sets name and units for mean, standard deviation and number of points variables, based
        on those of the base variable or overridden by those specified as kernel parameters.
        :param var_name: base variable name
        :param var_long_name: base variable long name
        :param var_standard_name: base variable standard name
        :param var_units: base variable units
        :return: tuple of tuples each containing (variable name, variable long name, variable units)
        """
        return [("_".join(t.split()), t, "", 1) for t in BINS]
