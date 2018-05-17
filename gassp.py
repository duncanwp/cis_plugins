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
        super(GASSP, self).__init__(variable_selector_class=variable_selector_class)

    def create_coords(self, filenames, variable=None):
        """
        Override the default read-in to also read in CCN quality flag data and apply the appropriate mask. We have
        to do this before creating the UngriddedData object so that the missing coords don't get fixed first
        """
        from cis.data_io.netcdf import read_many_files_individually, get_metadata
        from cis.utils import apply_mask_to_numpy_array, concatenate
        from cis.data_io.ungridded_data import UngriddedCoordinates, UngriddedData

        data_variables, variable_selector = self._load_data(filenames, variable)

        dim_coords = self._create_coordinates_list(data_variables, variable_selector)

        if variable is None:
            return UngriddedCoordinates(dim_coords)
        else:
            aux_coord_name = variable_selector.find_auxiliary_coordinate(variable)
            if aux_coord_name is not None:
                all_coords = self._add_aux_coordinate(dim_coords, filenames[0], aux_coord_name,
                                                      dim_coords.get_coord(standard_name='time').data.size)
            else:
                all_coords = dim_coords

            var_data = data_variables[variable]
            if variable and variable.startswith('CCN_COL'):
                # Work out the associated variable name for this column
                ccn_flag_var = "COL{}_FLAG".format(variable[-1])
                # Read in the flags
                flags = concatenate([get_data(v) for v in read_many_files_individually(filenames, ccn_flag_var)[
                    ccn_flag_var]])
                # 0 and 1 are both OK
                mask = flags > 1
                # If a variable was supplied then coords must be an ungridded data object, apply the mask to it
                var_data = apply_mask_to_numpy_array(concatenate([get_data(v) for v in var_data]), mask)

            return UngriddedData(var_data, get_metadata(data_variables[variable][0]), all_coords)

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
            data = get_data(d)
            m = get_metadata(d)
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

            coordinate_data_objects.append(Coord(data, m, coord_axis))

        return Coord.from_many_coordinates(coordinate_data_objects)


def get_data(var):
    # FIXME: THIS IS COPIED FROM CIS 1.6, and is a nasty hack needed because of crap data
    from cis.data_io.netcdf import apply_offset_and_scaling, get_data
    import numpy as np
    import logging

    var.set_auto_mask(False)

    data = get_data(var)

    return data
