import logging
from cis.data_io.Coord import Coord, CoordList
from cis.data_io.products import AProduct
from cis.data_io.netcdf import read, get_metadata, read_many_files_individually
from cis.data_io.ungridded_data import UngriddedCoordinates, UngriddedData
import cis.utils as utils
from cis.exceptions import InvalidVariableError


class ncas_lidar(AProduct):
    """
    CIS plugin for NCAS Halo Photonics Lidars. Example cis call:

    .. code:: bash
        cis plot attenuated_aerosol_backscatter_coefficient:Stare_05_20150414_11.nc:product=ncas_lidar,itemstyle="o",itemwidth="1" --type scatter2d --xaxis time --yaxis range --logv --cmap Greens --ymin 0 --ymax 6000 --xmin 2015-04-14T11:00:00 --xmax 2015-01-14T12:00:00 -o Stare_05_20150414_11-cis.png

    """
    def get_file_signature(self):
        return [r'ncas-lidar.*nc']

    priority = 20

    def _create_coord_list(self, filename):
        import numpy as np

        coords = CoordList()

        time_data = read(filename, 'time')['time']

        try:
            alt_data = read(filename, 'altitude')['altitude']
        except InvalidVariableError:
            alt_data = read(filename, 'range')['range']
        len_y = alt_data.shape[1]

        time_arr = utils.expand_1d_to_2d_array(time_data[:], len_y, axis=1)
        t_coord = Coord(time_arr, get_metadata(time_data), axis='x')
        t_coord.convert_to_std_time()
        coords.append(t_coord)

        #alt_arr = utils.expand_1d_to_2d_array(alt_data[:], len_x, axis=0)
        alt_arr = alt_data[:,:,0] #eliminate "angle" axis
        #alt_arr = alt_data #eliminate "angle" axis
        coords.append(Coord(alt_arr, get_metadata(alt_data), axis='y'))

        lat_data = read(filename, 'latitude')['latitude']
        lat_arr = np.ones(alt_arr.shape) * lat_data[:]
        coords.append(Coord(lat_arr, get_metadata(lat_data)))

        lon_data = read(filename, 'longitude')['longitude']
        lon_arr = np.ones(alt_arr.shape) * lon_data[:]
        coords.append(Coord(lon_arr, get_metadata(lon_data)))

        return coords

    def create_coords(self, filenames, variable=None):
        return UngriddedCoordinates(self._create_coord_list(filenames))

    def create_data_object(self, filenames, variable):
        logging.debug("Creating data object for variable " + variable)

        # reading coordinates
        # the variable here is needed to work out whether to apply interpolation to the lat/lon data or not
        coords = self._create_coord_list(filenames[0])

        usr_var_data = read_many_files_individually(filenames, variable)[variable]
        qc_flag = read_many_files_individually(filenames, "qc_flag")["qc_flag"]

        import numpy as np
        mask = (qc_flag[0][:, :, 0] != 1)

        #retdata = np.ma.array(usr_var_data[0][:, :, 0],mask = mask)
        from cis.utils import apply_mask_to_numpy_array, concatenate
        retdata = apply_mask_to_numpy_array(usr_var_data[0][:, :, 0], mask)

        return UngriddedData(retdata, get_metadata(usr_var_data[0]), coords)

    def get_file_format(self, filename):
        return "NetCDF/NCASLidar"

