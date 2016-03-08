from cis.data_io.products.NCAR_NetCDF_RAF import NCAR_NetCDF_RAF, NCAR_NetCDF_RAF_variable_name_selector


class GASSP_variable_name_selector(NCAR_NetCDF_RAF_variable_name_selector):
    # Static air pressure value for faam rack measurements
    CORRECTED_PRESSURE_VAR_NAME = 'PS_RVSM'
    # Standard static air pressure variable name
    PRESSURE_VAR_NAME = 'AIR_PRESSURE'


class GASSP(NCAR_NetCDF_RAF):

    def __init__(self, variable_selector_class=GASSP_variable_name_selector):
        """
        Setup NCAR RAF data product, allow a different variable selector class if needed
        :param variable_selector_class: the class to use for variable selection
        :return:nothing
        """
        super(NCAR_NetCDF_RAF, self).__init__()
        self.variableSelectorClass = variable_selector_class
        self.valid_dimensions = ["Time"]
