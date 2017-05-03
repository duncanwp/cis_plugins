from cis.data_io.products.caliop import Caliop_L2
import logging
from cis.data_io import hdf as hdf
from cis.data_io.Coord import Coord, CoordList
from cis.data_io.ungridded_data import Metadata, UngriddedData
import cis.utils as utils


MIXED_RESOLUTION_VARIABLES = ['Atmospheric_Volume_Description', 'CAD_Score',
                              'Extinction_QC_Flag_1064', 'Extinction_QC_Flag_532']


class Caliop_V4(Caliop_L2):
    def get_file_signature(self):
        return [r'CAL_LID_L2_05kmAPro.*hdf']

    def _get_mixed_resolution_calipso_data(self, sds):
        # The first slice of the last dimension corresponds to the higher (in altitude) element of each
        # sub-Level-2-resolution bin.
        return self._get_calipso_data(sds)[:, :, 0]

    def _create_one_dimensional_coord_list(self, filenames, index_offset=1):
        """
        Create a set of coordinates appropriate for a ond-dimensional (column integrated) variable
        :param filenames:
        :param int index_offset: For 5km products this will choose the coordinates which represent the start (0),
        middle (1) and end (2) of the 15 shots making up each column retrieval.
        :return:
        """
        from pyhdf.error import HDF4Error
        from cis.data_io import hdf_sd
        import datetime as dt
        from cis.time_util import convert_sec_since_to_std_time, cis_standard_time_unit

        variables = ['Latitude', 'Longitude', "Profile_Time"]
        logging.info("Listing coordinates: " + str(variables))

        # reading data from files
        sdata = {}
        for filename in filenames:
            try:
                sds_dict = hdf_sd.read(filename, variables)
            except HDF4Error as e:
                raise IOError(str(e))

            for var in list(sds_dict.keys()):
                utils.add_element_to_list_in_dict(sdata, var, sds_dict[var])

        # latitude
        lat_data = hdf.read_data(sdata['Latitude'], self._get_calipso_data)[:, index_offset]
        lat_metadata = hdf.read_metadata(sdata['Latitude'], "SD")
        lat_coord = Coord(lat_data, lat_metadata, 'Y')

        # longitude
        lon = sdata['Longitude']
        lon_data = hdf.read_data(lon, self._get_calipso_data)[:, index_offset]
        lon_metadata = hdf.read_metadata(lon, "SD")
        lon_coord = Coord(lon_data, lon_metadata, 'X')

        # profile time, x
        time = sdata['Profile_Time']
        time_data = hdf.read_data(time, self._get_calipso_data)[:, index_offset]
        time_data = convert_sec_since_to_std_time(time_data, dt.datetime(1993, 1, 1, 0, 0, 0))
        time_coord = Coord(time_data, Metadata(name='Profile_Time', standard_name='time', shape=time_data.shape,
                                               units=cis_standard_time_unit), "T")

        # create the object containing all coordinates
        coords = CoordList()
        coords.append(lat_coord)
        coords.append(lon_coord)
        coords.append(time_coord)

        return coords

    def create_data_object(self, filenames, variable):
        logging.debug("Creating data object for variable " + variable)

        # reading coordinates
        if variable.startswith('Column'):
            coords = self._create_one_dimensional_coord_list(filenames, index_offset=1)
        else:
            coords = self._create_coord_list(filenames, index_offset=1)

        # reading of variables
        sdata, vdata = hdf.read(filenames, variable)

        # retrieve data + its metadata
        var = sdata[variable]
        metadata = hdf.read_metadata(var, "SD")

        if variable in MIXED_RESOLUTION_VARIABLES:
            logging.warning("Using Level 2 resolution profile for mixed resolution variable {}. See CALIPSO "
                            "documentation for more details".format(variable))
            callback = self._get_mixed_resolution_calipso_data
        else:
            callback = self._get_calipso_data

        return UngriddedData(var, metadata, coords, callback)
