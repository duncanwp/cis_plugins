from cis.data_io.products.NCAR_NetCDF_RAF import NCAR_NetCDF_RAF, NCAR_NetCDF_RAF_variable_name_selector


class GASSP_variable_name_selector(NCAR_NetCDF_RAF_variable_name_selector):
    # Attribute name for the attribute holding the time coordinate
    TIME_COORDINATE_NAME = 'time'
    # Attribute name for the attribute holding the latitude coordinate
    LATITUDE_COORDINATE_NAME = 'PosLat'
    # Attribute name for the attribute holding the longitude coordinate
    LONGITUDE_COORDINATE_NAME = 'PosLon'
    # Variable name for the dataset for corrected pressure
    CORRECTED_PRESSURE_VAR_NAME = 'pstatic'


class CARIBIC(NCAR_NetCDF_RAF):

    def __init__(self, variable_selector_class=GASSP_variable_name_selector):
        """
        Setup NCAR RAF data product, allow a different variable selector class if needed
        :param variable_selector_class: the class to use for variable selection
        :return:nothing
        """
        super(NCAR_NetCDF_RAF, self).__init__(variable_selector_class=variable_selector_class)
