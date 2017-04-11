from cis.data_io.products.NCAR_NetCDF_RAF import NCAR_NetCDF_RAF, NCAR_NetCDF_RAF_variable_name_selector


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
        Override the default read-in to also read in CCN quality flag data and apply the appropriate mask
        """
        from cis.data_io.netcdf import read_many_files_individually
        from cis.utils import apply_mask_to_numpy_array
        coords = super(GASSP).create_coords(filenames, variable)
        if variable and variable.starts_with('CCN_COL'):
            # Work out the associated variable name for this column
            ccn_flag_var = "COL{}_FLAG".format(variable[:-1])
            # Read in the flags
            flags = read_many_files_individually(filenames, ccn_flag_var)[ccn_flag_var]
            # 0 and 1 are both OK
            mask = flags[:] < 2
            # If a variable was supplied then coords must be an ungridded data object, apply the mask to it
            coords.data = apply_mask_to_numpy_array(coords.data, mask)
        return coords

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
