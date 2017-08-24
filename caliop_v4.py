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


class Caliop_V4_NO_PRESSURE(Caliop_V4):

    def _create_coord_list(self, filenames, index_offset=0):
        from cis.data_io.hdf_vd import get_data
        from cis.data_io.hdf_vd import VDS
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

        alt_name = "altitude"
        logging.info("Additional coordinates: '" + alt_name + "'")

        # work out size of data arrays
        # the coordinate variables will be reshaped to match that.
        # NOTE: This assumes that all Caliop_L1 files have the same altitudes.
        #       If this is not the case, then the following line will need to be changed
        #       to concatenate the data from all the files and not just arbitrarily pick
        #       the altitudes from the first file.
        alt_data = get_data(VDS(filenames[0], "Lidar_Data_Altitudes"), True)
        alt_data *= 1000.0  # Convert to m
        len_x = alt_data.shape[0]

        lat_data = hdf.read_data(sdata['Latitude'], self._get_calipso_data)
        len_y = lat_data.shape[0]

        new_shape = (len_x, len_y)

        # altitude
        alt_data = utils.expand_1d_to_2d_array(alt_data, len_y, axis=0)
        alt_metadata = Metadata(name=alt_name, standard_name=alt_name, shape=new_shape)
        alt_coord = Coord(alt_data, alt_metadata)

        # latitude
        lat_data = utils.expand_1d_to_2d_array(lat_data[:, index_offset], len_x, axis=1)
        lat_metadata = hdf.read_metadata(sdata['Latitude'], "SD")
        lat_metadata.shape = new_shape
        lat_coord = Coord(lat_data, lat_metadata, 'Y')

        # longitude
        lon = sdata['Longitude']
        lon_data = hdf.read_data(lon, self._get_calipso_data)
        lon_data = utils.expand_1d_to_2d_array(lon_data[:, index_offset], len_x, axis=1)
        lon_metadata = hdf.read_metadata(lon, "SD")
        lon_metadata.shape = new_shape
        lon_coord = Coord(lon_data, lon_metadata, 'X')

        # profile time, x
        time = sdata['Profile_Time']
        time_data = hdf.read_data(time, self._get_calipso_data)
        time_data = convert_sec_since_to_std_time(time_data, dt.datetime(1993, 1, 1, 0, 0, 0))
        time_data = utils.expand_1d_to_2d_array(time_data[:, index_offset], len_x, axis=1)
        time_coord = Coord(time_data, Metadata(name='Profile_Time', standard_name='time', shape=time_data.shape,
                                               units=cis_standard_time_unit), "T")

        # create the object containing all coordinates
        coords = CoordList()
        coords.append(lat_coord)
        coords.append(lon_coord)
        coords.append(time_coord)
        coords.append(alt_coord)

        return coords


class Caliop_V4_QC_directly_creating_vars(Caliop_V4_NO_PRESSURE):

    def create_data_object(self, filenames, variable):
        from pywork.CALIOP_utils import mask_data

        logging.debug("Creating *QC'd* data object for variable " + variable)

        # reading of variables
        sdata, vdata = hdf.read(filenames, [variable, "Pressure", "Extinction_QC_Flag_532", "CAD_Score"])

        # retrieve data + its metadata
        var = sdata[variable]
        metadata = hdf.read_metadata(var, "SD")

        if variable in MIXED_RESOLUTION_VARIABLES:
            logging.warning("Using Level 2 resolution profile for mixed resolution variable {}. See CALIPSO "
                            "documentation for more details".format(variable))
            callback = self._get_mixed_resolution_calipso_data
        else:
            callback = self._get_calipso_data

        var_data = hdf.read_data(sdata[variable], callback)

        extinction_qc = hdf.read_data(sdata["Extinction_QC_Flag_532"], self._get_mixed_resolution_calipso_data)
        cad_score = hdf.read_data(sdata["CAD_Score"], self._get_mixed_resolution_calipso_data)

        qcd_var_data, = mask_data(var_data, cad_score, extinction_qc)

        # reading coordinates
        if variable.startswith('Column'):
            coords = self._create_one_dimensional_coord_list(filenames, index_offset=1)
        else:
            coords = self._create_coord_list(filenames, index_offset=1)

            pres_data = hdf.read_data(sdata['Pressure'], self._get_calipso_data)
            pres_metadata = hdf.read_metadata(sdata['Pressure'], "SD")
            # Fix badly formatted units which aren't CF compliant and will break if they are aggregated
            if str(pres_metadata.units) == "hPA":
                pres_metadata.units = "hPa"

            qcd_pres_data = mask_data(pres_data, cad_score, extinction_qc)
            pres_coord = Coord(qcd_pres_data, pres_metadata, 'P')
            coords.append(pres_coord)

        return UngriddedData(qcd_var_data, metadata, coords)


class Caliop_V4_QC(Caliop_V4_NO_PRESSURE):

    def create_data_object(self, filenames, variable):
        from pywork.CALIOP_utils import mask_data

        # Read all the vars without pressure
        var_data = super().create_data_object(filenames, variable)
        extinction_qc = super().create_data_object(filenames, "Extinction_QC_Flag_532")
        cad_score = super().create_data_object(filenames, "CAD_Score")

        qcd_var_data, = mask_data([var_data], cad_score, extinction_qc)

        if not variable.startswith('Column'):
            # Read pressure separately, as it's own variable
            pressure = super().create_data_object(filenames, "Pressure")

            qcd_pres, = mask_data([pressure], cad_score, extinction_qc)

            qcd_pres_coord = Coord(qcd_pres.data, qcd_pres.metadata, 'P')
            # Fix badly formatted units which aren't CF compliant and will break if they are aggregated
            if str(qcd_pres_coord.units) == "hPA":
                qcd_pres_coord.units = "hPa"

            qcd_var_data._coords.append(qcd_pres_coord)
            qcd_var_data._post_process()

        return qcd_var_data


class Caliop_V4_QC_NO_PRESSURE(Caliop_V4_NO_PRESSURE):

    def create_data_object(self, filenames, variable):
        from pywork.CALIOP_utils import mask_data

        # Read all the vars without pressure
        var_data = super().create_data_object(filenames, variable)
        extinction_qc = super().create_data_object(filenames, "Extinction_QC_Flag_532")
        cad_score = super().create_data_object(filenames, "CAD_Score")

        qcd_var_data, = mask_data([var_data], cad_score, extinction_qc)

        return qcd_var_data
