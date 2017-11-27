from cis.data_io.products.NCAR_NetCDF_RAF import NCAR_NetCDF_RAF, NCAR_NetCDF_RAF_variable_name_selector


def expand_1d_to_2d_array(array, length, axis=0):
    """
    General utility routine to 'extend arbitrary dimensional array into a higher dimension
    by duplicating the data along a given 'axis' (default is 0) of size 'length'.

    Examples::

        >>> a = np.array([1, 2, 3, 4])
        >>> expand_1d_to_2d_array(a, 4, axis=0)
        [[1 2 3 4]
         [1 2 3 4]
         [1 2 3 4]
         [1 2 3 4]]

        >>> a = np.array([1, 2, 3, 4])
        >>> expand_1d_to_2d_array(a, 4, axis=1)
        [[1 1 1 1]
         [2 2 2 2]
         [3 3 3 3]
         [4 4 4 4]]

    :param array:
    :param length:
    :param axis:
    :return:
    """
    import numpy as np

    if axis == 0:
        array_2d = np.broadcast_to(array, (length, array.size))
        if isinstance(array, np.ma.MaskedArray):
            array_2d = np.ma.array(array_2d, mask=np.broadcast_to(array.mask, (length, array.size)))
    else:
        reshaped = array.reshape(array.size, 1)
        array_2d = np.broadcast_to(reshaped, (array.size, length))
        if isinstance(reshaped, np.ma.MaskedArray):
            array_2d = np.ma.array(array_2d, mask=np.broadcast_to(reshaped.mask, (array.size, length)))

    return array_2d


class GASSP_variable_name_selector(NCAR_NetCDF_RAF_variable_name_selector):
    # Static air pressure value for faam rack measurements
    CORRECTED_PRESSURE_VAR_NAME = 'PS_RVSM'
    # Standard static air pressure variable name
    PRESSURE_VAR_NAME = 'AIR_PRESSURE'

    @staticmethod
    def _parse_station_lat_lon(lat_lon_string):
        """
        Parse a station's latitude or longitude string. Will try and read it directly as a float, otherwise will try and
         read the first white-space separated part of the string (e.g. '80 degrees north' -> float(80)).
        :param lat_lon_string:
        :return:
        """
        from cis.exceptions import InvalidVariableError
        try:
            return float(lat_lon_string)
        except ValueError:
            try:
                return float(lat_lon_string.split()[0])
            except ValueError:
                raise InvalidVariableError("Couldn't parse station attribute '{}'".format(lat_lon_string))

    def _stationary_setup(self):
        """
        Set up object when latitude and longitude are fixed
        """
        from cis.exceptions import InvalidVariableError
        if self.STATION_LATITUDE_NAME.lower() not in self._attributes[0]:
            raise InvalidVariableError("No attributes indicating latitude, expecting '{}'"
                                       .format(self.STATION_LATITUDE_NAME))
        # We need a bunch of different latitudes for different files
        self.station_latitude = [self._parse_station_lat_lon(attr[self.STATION_LATITUDE_NAME.lower()])
                                 for attr in self._attributes]

        if self.STATION_LONGITUDE_NAME.lower() not in self._attributes[0]:
            raise InvalidVariableError("No attributes indicating longitude, expecting '{}'"
                                       .format(self.STATION_LONGITUDE_NAME))
        self.station_longitude = [self._parse_station_lat_lon(attr[self.STATION_LONGITUDE_NAME.lower()])
                                  for attr in self._attributes]
        self.station = True

        if self.STATION_ALTITUDE_NAME.lower() in self._attributes[0]:
            self.altitude = [self._parse_station_altitude(attr[self.STATION_ALTITUDE_NAME.lower()])
                             for attr in self._attributes]
        else:
            self.altitude = [self.DEFAULT_ALTITUDE for attr in self._attributes]

    def find_auxiliary_coordinate(self, variable):
        """
        Find the variable name of an auxiliary coordinate for the given variable (if there is one).

        :param str variable: The data variable we're checking for any auxiliary coordinates
        :return str or None: The name of the variable holding the auxiliary coordinate or None
        """
        aux_coord_name = None
        dim_coord_names = [self.latitude_variable_name, self.longitude_variable_name,
                           self.altitude_variable_name, self.pressure_variable_name] + list(self.time_dimensions)
        # Find the *dimension* which corresponds to the auxiliary coordinate
        aux_coords = [dim for dim in self._variable_dimensions[0][variable] if dim not in dim_coord_names]
        if len(aux_coords) > 1:
            raise InvalidVariableError("CIS currently only supports reading data variables with one auxilliary "
                                       "coordinate")
        elif len(aux_coords) == 1:
            # If there is also a variable named after that dimension then this is the variable we're after
            if aux_coords[0] in self._variable_dimensions[0]:
                aux_coord_name = aux_coords[0]
            # Otherwise we need to look through all the variables and choose the first variable whose dimension is only
            #  the auxiliary dimension.
            else:
                for v, dims in self._variable_dimensions[0].items():
                    if dims[0] == aux_coords[0]:
                        aux_coord_name = v
                        break
        return aux_coord_name


class GASSP(NCAR_NetCDF_RAF):

    def __init__(self, variable_selector_class=GASSP_variable_name_selector):
        """
        Setup NCAR RAF data product, allow a different variable selector class if needed
        :param variable_selector_class: the class to use for variable selection
        :return:nothing
        """
        super(GASSP, self).__init__(variable_selector_class=variable_selector_class)

    @staticmethod
    def _add_aux_coordinate(dim_coords, filename, aux_coord_name, length):
        """
        Add an auxiliary coordinate to a list of (reshaped) dimension coordinates

        :param dim_coords: CoordList of one-dimensional coordinates representing physical dimensions
        :param filename: The data file containing the aux coord
        :param aux_coord_name: The name of the aux coord to add to the coord list
        :param length: The length of the data dimensions which this auxiliary coordinate should span
        :return: A CoordList of reshaped (2D) physical coordinates plus the 2D auxiliary coordinate
        """
        from cis.data_io.Coord import Coord
        from cis.data_io.netcdf import read, get_metadata

        # We assume that the auxilliary coordinate is the same shape across files
        d = read(filename, [aux_coord_name])[aux_coord_name]
        # Reshape to the length given
        aux_data = expand_1d_to_2d_array(d[:], length, axis=0)
        # Get the length of the auxiliary coordinate
        len_y = d[:].size

        for dim_coord in dim_coords:
            dim_coord.data = expand_1d_to_2d_array(dim_coord.data, len_y, axis=1)

        all_coords = dim_coords + [Coord(aux_data, get_metadata(d))]

        return all_coords

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
                flags = concatenate(read_many_files_individually(filenames, ccn_flag_var)[ccn_flag_var])
                # 0 and 1 are both OK
                mask = flags[:] > 1
                # If a variable was supplied then coords must be an ungridded data object, apply the mask to it
                var_data = apply_mask_to_numpy_array(concatenate(var_data), mask)

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
        from cis.data_io.netcdf import get_metadata, get_data
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
