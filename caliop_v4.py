from cis.data_io.products.caliop import Caliop_L2, Caliop_L2_NO_PRESSURE, Caliop_L1_NO_PRESSURE
import logging
from cis.data_io import hdf as hdf
from cis.data_io.Coord import Coord
from cis.data_io.ungridded_data import UngriddedData


MIXED_RESOLUTION_VARIABLES = ['Atmospheric_Volume_Description', 'CAD_Score',
                              'Extinction_QC_Flag_1064', 'Extinction_QC_Flag_532']


class Caliop_V4_QC_directly_creating_vars(Caliop_L2_NO_PRESSURE):

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


class Caliop_V4_QC(Caliop_L2):

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


class Caliop_V4_QC_NO_PRESSURE(Caliop_L2_NO_PRESSURE):

    def create_data_object(self, filenames, variable):
        from pywork.CALIOP_utils import mask_data

        # Read all the vars without pressure
        var_data = super().create_data_object(filenames, variable)
        extinction_qc = super().create_data_object(filenames, "Extinction_QC_Flag_532")
        cad_score = super().create_data_object(filenames, "CAD_Score")

        qcd_var_data, = mask_data([var_data], cad_score, extinction_qc)

        return qcd_var_data


class Caliop_L15(Caliop_L1_NO_PRESSURE):
    def get_file_signature(self):
        return [r'CAL_LID_L1.*hdf']

    def create_data_object(self, filenames, variable):
        logging.debug("Creating data object for variable " + variable)

        # reading coordinates
        # the variable here is needed to work out whether to apply interpolation to the lat/lon data or not
        coords = self._create_coord_list(filenames)

        # reading of variables
        sdata, vdata = hdf.read(filenames, variable)

        # retrieve data + its metadata
        var = sdata[variable]
        metadata = hdf.read_metadata(var, "SD")

        return UngriddedData(var, metadata, coords, self._get_calipso_data)

    def get_file_format(self, filename):
        return "HDF4/CaliopL1"

    def _create_coord_list(self, filenames, index_offset=0):
        import logging
        from cis.data_io import hdf as hdf
        from cis.data_io.Coord import Coord, CoordList
        from cis.data_io.ungridded_data import Metadata
        import cis.utils as utils
        from cis.data_io.hdf_vd import VDS
        from pyhdf.error import HDF4Error
        from cis.data_io import hdf_sd
        import datetime as dt
        from cis.time_util import convert_sec_since_to_std_time, cis_standard_time_unit

        variables = ['Latitude', 'Longitude', "Profile_Time", "Pressure"]
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

        # pressure
        if self.include_pressure:
            pres_data = hdf.read_data(sdata['Pressure'], self._get_calipso_data)
            pres_metadata = hdf.read_metadata(sdata['Pressure'], "SD")
            # Fix badly formatted units which aren't CF compliant and will break if they are aggregated
            if str(pres_metadata.units) == "hPA":
                pres_metadata.units = "hPa"
            pres_metadata.shape = new_shape
            pres_coord = Coord(pres_data, pres_metadata, 'P')

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
        if self.include_pressure and (pres_data.shape == alt_data.shape):
            # For MODIS L1 this may is not be true, so skips the air pressure reading. If required for MODIS L1 then
            # some kind of interpolation of the air pressure would be required, as it is on a different (smaller) grid
            # than for the Lidar_Data_Altitudes.
            coords.append(pres_coord)

        return coords

    def _get_calipso_data(self, sds):
        """
        Reads raw data from an SD instance. Automatically applies the
        scaling factors and offsets to the data arrays found in Calipso data.

        Returns:
            A numpy array containing the raw data with missing data is replaced by NaN.

        Arguments:
            sds        -- The specific sds instance to read

        """
        from cis.utils import create_masked_array_for_missing_data
        import numpy as np

        calipso_fill_values = {'Float_32': -9999.0,
                               # 'Int_8' : 'See SDS description',
                               'Int_16': -9999,
                               'Int_32': -9999,
                               'UInt_8': -127,
                               # 'UInt_16' : 'See SDS description',
                               # 'UInt_32' : 'See SDS description',
                               'ExtinctionQC Fill Value': 32768,
                               'FeatureFinderQC No Features Found': 32767,
                               'FeatureFinderQC Fill Value': 65535}

        data = sds.get()
        attributes = sds.attributes()

        # Missing data. First try 'fillvalue'
        missing_val = attributes.get('fillvalue', None)
        if missing_val is None:
            try:
                # Now try and lookup the fill value based on the data type
                missing_val = calipso_fill_values[attributes.get('format', None)]
            except KeyError:
                # Last guess
                missing_val = attributes.get('_FillValue', None)

        if missing_val is not None:
            data = create_masked_array_for_missing_data(data, float(missing_val))

        # Now handle valid range mask
        valid_range = attributes.get('valid_range', None)
        if valid_range is not None:
            # Split the range into two numbers of the right type (removing commas in the floats...)
            v_range = np.asarray(valid_range.replace(',','').split("..."), dtype=data.dtype)
            # Some valid_ranges appear to have only one value, so ignore those...
            if (len(v_range) == 2) and v_range[0] < v_range[1]:
                logging.debug("Masking all values {} > v > {}.".format(*v_range))
                data = np.ma.masked_outside(data, *v_range)
            else:
                logging.warning("Invalid valid_range: {}. Not masking values.".format(valid_range))

        # Offsets and scaling.
        offset = attributes.get('add_offset', 0)
        scale_factor = attributes.get('scale_factor', 1)
        data = self._apply_scaling_factor_CALIPSO(data, scale_factor, offset)

        return data


def get_data(vds, first_record=False, missing_values=None):
    """
    Actually read the data from the VDS handle. We shouldn't need to check for HDF being installed here because the
    VDS object which is being passed to us can only have come from pyhdf.

    :param vds:
    :param first_record:
    :param missing_values:
    :return:
    """
    import numpy as np
    from pyhdf.HDF import HDF, HDF4Error
    from cis.utils import create_masked_array_for_missing_values

    # get file and variable reference from tuple
    filename = vds.filename
    variable = vds.variable

    try:
        datafile = HDF(filename)
    except HDF4Error as e:
        raise IOError(e)

    vs = datafile.vstart()

    if first_record:
        # FIXME - This is the only bit that is actually different to the baseline
        vd = vs.attach('metadata')
        vd.setfields(variable)
        data = vd.read()
    else:
        # get data for that variable
        vd = vs.attach(variable)
        data = vd.read(nRec=vd.inquire()[0])

    # create numpy array from data
    data = np.array(data).flatten()

    # dealing with missing data
    if missing_values is None:
        v = _get_attribute_value(vd, 'missing')
        v = float(v) if v is not None else None
        missing_values = [v]

    data = create_masked_array_for_missing_values(data, missing_values)

    # detach and close
    vd.detach()
    vs.end()
    datafile.close()

    return data

def _get_attribute_value(vd, name, default=None):
    val = vd.attrinfo().get(name, None)
    # if the attribute is not present
    if val is None:
        return default
    else:
        # attrinfo() returns a tuple in which the value of interest is the 3rd item, hence the '[2]'
        return val[2]
