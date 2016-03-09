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
        from cis.data_io.Coord import Coord
        from cf_units import Unit
        import logging

        coordinate_data_objects = []
        for d in data_variables[data_variable_name]:
            m = get_metadata(d)
            m.alter_standard_name(standard_name)
            if standard_name == 'air_pressure':
                if ',' in m.units:
                    m.units = m.units.split(',')[0]
                if m.units == 'mb' or m.units == 'Mb':
                    m.units = 'mbar'
                cfunit = Unit(m.units)
                logging.info("Parsed air pressure units '{old}' as {new} ".format(old=m.units, new=cfunit))
                logging.info('Converting to hPa')
                data = Unit(m.units).convert(d[:], 'hPa')
                m.units = 'hPa'
            else:
                data = d
            coordinate_data_objects.append(Coord(data, m, coord_axis))


        return Coord.from_many_coordinates(coordinate_data_objects)
