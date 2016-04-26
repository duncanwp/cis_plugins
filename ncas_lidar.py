import logging
from cis.data_io.Coord import Coord, CoordList
from cis.data_io.products import AProduct
from cis.data_io.netcdf import read, get_metadata, read_many_files_individually
from cis.data_io.ungridded_data import Metadata, UngriddedCoordinates, UngriddedData
import cis.utils as utils
from cis.exceptions import InvalidVariableError


class ncas_lidar(AProduct):
    def get_file_signature(self):
        '''
        To be implemented by subclcass
        :return:
        '''
        return [r'ncas-lidar.*nc']

    priority = 20

    def _create_coord_list(self, filename):
        import numpy as np

        coords = CoordList()

        time_data = read(filename, 'time')['time']
        len_x = time_data.shape[0]

        try:
            alt_data = read(filename, 'altitude')['altitude']
        except InvalidVariableError:
            alt_data = read(filename, 'range')['range']

        len_y = alt_data.shape[0]

        time_arr = utils.expand_1d_to_2d_array(time_data[:], len_y, axis=1)
        t_coord = Coord(time_arr, get_metadata(time_data), axis='x')
        t_coord.convert_to_std_time()
        coords.append(t_coord)

        alt_arr = utils.expand_1d_to_2d_array(alt_data[:], len_x, axis=0)
        coords.append(Coord(alt_arr, get_metadata(alt_data), axis='y'))

        lat_data = read(filename, 'latitude')['latitude']
        lat_arr = np.ones(alt_arr.shape) * lat_data[:]
        coords.append(Coord(lat_arr, get_metadata(lat_data)))

        lon_data = read(filename, 'longitude')['longitude']
        lon_arr = np.ones(alt_arr.shape) * lon_data[:]
        coords.append(Coord(lon_arr, get_metadata(lon_data)))

        #
        #
        # # reading data from files
        # sdata = {}
        # for filename in filenames:
        #     try:
        #         sds_dict = hdf_sd.read(filename, variables)
        #     except HDF4Error as e:
        #         raise IOError(str(e))
        #
        #     for var in sds_dict.keys():
        #         utils.add_element_to_list_in_dict(sdata, var, sds_dict[var])
        #
        # alt_name = "altitude"
        # logging.info("Additional coordinates: '" + alt_name + "'")
        #
        # # work out size of data arrays
        # # the coordinate variables will be reshaped to match that.
        # # NOTE: This assumes that all Caliop_L1 files have the same altitudes.
        # #       If this is not the case, then the following line will need to be changed
        # #       to concatenate the data from all the files and not just arbitrarily pick
        # #       the altitudes from the first file.
        # alt_data = get_data(VDS(filenames[0], "Lidar_Data_Altitudes"), True)
        # alt_data *= 1000.0  # Convert to m
        # len_x = alt_data.shape[0]
        #
        # lat_data = hdf.read_data(sdata['Latitude'], "SD")
        # len_y = lat_data.shape[0]
        #
        # new_shape = (len_x, len_y)
        #
        # # altitude
        # alt_data = utils.expand_1d_to_2d_array(alt_data, len_y, axis=0)
        # alt_metadata = Metadata(name=alt_name, standard_name=alt_name, shape=new_shape)
        # alt_coord = Coord(alt_data, alt_metadata)
        #
        # # pressure
        # pres_data = hdf.read_data(sdata['Pressure'], "SD")
        # pres_metadata = hdf.read_metadata(sdata['Pressure'], "SD")
        # # Fix badly formatted units which aren't CF compliant and will break if they are aggregated
        # if pres_metadata.units == "hPA":
        #     pres_metadata.units = "hPa"
        # pres_metadata.shape = new_shape
        # pres_coord = Coord(pres_data, pres_metadata, 'P')
        #
        # # latitude
        # lat_data = utils.expand_1d_to_2d_array(lat_data[:, index_offset], len_x, axis=1)
        # lat_metadata = hdf.read_metadata(sdata['Latitude'], "SD")
        # lat_metadata.shape = new_shape
        # lat_coord = Coord(lat_data, lat_metadata, 'Y')
        #
        # # longitude
        # lon = sdata['Longitude']
        # lon_data = hdf.read_data(lon, "SD")
        # lon_data = utils.expand_1d_to_2d_array(lon_data[:, index_offset], len_x, axis=1)
        # lon_metadata = hdf.read_metadata(lon, "SD")
        # lon_metadata.shape = new_shape
        # lon_coord = Coord(lon_data, lon_metadata, 'X')
        #
        # # profile time, x
        # time = sdata['Profile_Time']
        # time_data = hdf.read_data(time, "SD")
        # time_data = convert_sec_since_to_std_time(time_data, dt.datetime(1993, 1, 1, 0, 0, 0))
        # time_data = utils.expand_1d_to_2d_array(time_data[:, index_offset], len_x, axis=1)
        # time_coord = Coord(time_data, Metadata(name='Profile_Time', standard_name='time', shape=time_data.shape,
        #                                        units=str(cis_standard_time_unit),
        #                                        calendar=cis_standard_time_unit.calendar), "T")
        #
        # # create the object containing all coordinates
        # coords = CoordList()
        # coords.append(lat_coord)
        # coords.append(lon_coord)
        # coords.append(time_coord)
        # coords.append(alt_coord)
        # if pres_data.shape == alt_data.shape:
        #     # For MODIS L1 this may is not be true, so skips the air pressure reading. If required for MODIS L1 then
        #     # some kind of interpolation of the air pressure would be required, as it is on a different (smaller) grid
        #     # than for the Lidar_Data_Altitudes.
        #     coords.append(pres_coord)

        return coords

    def create_coords(self, filenames, variable=None):
        return UngriddedCoordinates(self._create_coord_list(filenames))

    def create_data_object(self, filenames, variable):
        logging.debug("Creating data object for variable " + variable)

        # reading coordinates
        # the variable here is needed to work out whether to apply interpolation to the lat/lon data or not
        coords = self._create_coord_list(filenames[0])

        usr_var_data = read_many_files_individually(filenames, variable)[variable]

        return UngriddedData(usr_var_data, get_metadata(usr_var_data[0]), coords)

    def get_file_format(self, filename):
        return "NetCDF/NCASLidar"

