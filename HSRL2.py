import logging
from cis.data_io.Coord import Coord, CoordList
from cis.data_io.products import AProduct
from cis.data_io.netcdf import get_data, get_metadata, read_many_files_individually
from cis.data_io.ungridded_data import UngriddedCoordinates, UngriddedData
import cis.utils as utils
from cis.exceptions import InvalidVariableError


class hsrl(AProduct):
    def get_file_signature(self):
        return [r'HSRL2.*h5']

    priority = 20

    def get_variable_names(self, filenames, data_type=None):
        from cis.data_io.netcdf import get_netcdf_file_variables, remove_variables_with_non_spatiotemporal_dimensions
        variables = []
        for filename in filenames:
            file_variables = get_netcdf_file_variables(filename)
            remove_variables_with_non_spatiotemporal_dimensions(file_variables, self.valid_dimensions)
            variables.extend(file_variables)
        return set(variables)

    def _create_coord_list(self, filename, usr_variable=None):
        variables = [("ER2_IMU/Longitude", "x"), ("ER2_IMU/Latitude", "y"), ("ER2_IMU/gps_time", "t"),
                     ("State/Pressure", "p"), ("DataProducts/Altitude", "z")]

        if usr_variable is not None:
            variables.append((usr_variable, ''))

        logging.info("Listing coordinates: " + str(variables))

        coords = CoordList()
        var_data = read_many_files_individually(filename, [v[0] for v in variables])

        time_data = utils.concatenate([get_data(i) for i in var_data['ER2_IMU/gps_time']])
        alt_data = utils.concatenate([get_data(i) for i in var_data["DataProducts/Altitude"]])
        len_x = time_data.shape[0]
        len_y = alt_data.shape[1]

        # FIXME the time units here aren't working - I'm not sure how they're stored
        time_arr = utils.expand_1d_to_2d_array(time_data, len_y, axis=1)
        t_coord = Coord(time_arr, get_metadata(var_data['ER2_IMU/gps_time'][0]), axis='x')
        t_coord.convert_to_std_time()
        coords.append(t_coord)

        alt_arr = utils.expand_1d_to_2d_array(alt_data, len_x, axis=0)
        coords.append(Coord(alt_arr, get_metadata(var_data["DataProducts/Altitude"][0]), axis='y'))

        lat_data = utils.concatenate([get_data(i) for i in var_data['ER2_IMU/Latitude']])
        lat_arr = utils.expand_1d_to_2d_array(lat_data, len_y, axis=1)
        coords.append(Coord(lat_arr, get_metadata(var_data['ER2_IMU/Latitude'][0])))

        lon_data = utils.concatenate([get_data(i) for i in var_data['ER2_IMU/Longitude']])
        lon_arr = utils.expand_1d_to_2d_array(lon_data, len_y, axis=1)
        coords.append(Coord(lon_arr, get_metadata(var_data['ER2_IMU/Longitude'][0])))

        return coords

    def create_coords(self, filenames, variable=None):
        return UngriddedCoordinates(self._create_coord_list(filenames))

    def create_data_object(self, filenames, variable):
        logging.debug("Creating data object for variable " + variable)

        # reading coordinates
        # the variable here is needed to work out whether to apply interpolation to the lat/lon data or not
        coords = self._create_coord_list(filenames)

        usr_var_data = read_many_files_individually(filenames, variable)[variable]

        return UngriddedData(usr_var_data, get_metadata(usr_var_data[0]), coords)

    def get_file_format(self, filename):
        return "HDF5/HSRL2"

