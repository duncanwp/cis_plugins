from ncar_raf_cube import NCAR_NetCDF_RAF_Cube, NCAR_NetCDF_RAF_variable_name_selector


class GASSP_variable_name_selector(NCAR_NetCDF_RAF_variable_name_selector):
    # Static air pressure value for faam rack measurements
    CORRECTED_PRESSURE_VAR_NAME = 'PS_RVSM'
    # Standard static air pressure variable name
    PRESSURE_VAR_NAME = 'AIR_PRESSURE'


class GASSP_Cube(NCAR_NetCDF_RAF_Cube):

    def __init__(self, variable_selector_class=GASSP_variable_name_selector):
        """
        Setup NCAR RAF data product, allow a different variable selector class if needed
        :param variable_selector_class: the class to use for variable selection
        :return:nothing
        """
        super(GASSP_Cube, self).__init__(variable_selector_class=variable_selector_class)

    def _create_coord(self, coord_axis, data_variable_name, data_variables, standard_name):
        """
        Create a coordinate for the co-ordinate list
        :param coord_axis: axis of the coordinate in the coords
        :param data_variable_name: the name of the variable in the data
        :param data_variables: the data variables
        :param standard_name: the standard name it should have
        :return: a coords object
        """
        from cis.data_io.netcdf import get_metadata
        from iris.coords import AuxCoord
        from cis.utils import concatenate
        from cf_units import Unit
        import logging

        data = concatenate([get_data(d) for d in data_variables[data_variable_name]])

        m = get_metadata(data_variables[data_variable_name][0])
        m._name = m._name.lower()
        m.standard_name = standard_name
        if standard_name == 'air_pressure':
            if not isinstance(m.units, Unit):
                if ',' in m.units:
                    # Try splitting any commas out
                    m.units = m.units.split(',')[0]
                if ' ' in m.units:
                    # Try splitting any spaces out
                    m.units = m.units.split()[0]
            if str(m.units) == 'mb' or str(m.units) == 'Mb':
                # Try converting to standard nomencleture
                m.units = 'mbar'
            if str(m.units) == 'hpa':
                m.units = 'hPa'

            logging.info("Parsed air pressure units {old}".format(old=m.units))
            logging.info('Converting to hPa')
            if not isinstance(m.units, str):
                data = m.units.convert(data, 'hPa')
                m.units = 'hPa'

        return AuxCoord(data, units=m.units, standard_name=standard_name)


def get_data(var):
    # FIXME: THIS IS COPIED FROM CIS 1.6, and is a nasty hack needed because of crap data
    from cis.data_io.netcdf import apply_offset_and_scaling, get_data
    import numpy as np
    import logging

    var.set_auto_mask(False)

    data = get_data(var)

    return data
