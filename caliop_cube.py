import logging
from cis.data_io import hdf as hdf
from cis.data_io.hdf_vd import get_data, VDS
from cis.data_io.products import AProduct
import cis.utils as utils


MIXED_RESOLUTION_VARIABLES = ['Atmospheric_Volume_Description', 'CAD_Score',
                              'Extinction_QC_Flag_1064', 'Extinction_QC_Flag_532']


class Caliop_L2_cube(AProduct):
    def get_file_signature(self):
        return [r'CAL_LID_L2.*hdf']

    def get_variable_names(self, filenames, data_type=None):
        try:
            from pyhdf.SD import SD
        except ImportError:
            raise ImportError("HDF support was not installed, please reinstall with pyhdf to read HDF files.")

        variables = set([])

        # Determine the valid shape for variables
        sd = SD(filenames[0])
        datasets = sd.datasets()
        len_x = datasets['Latitude'][1][0]  # Assumes that latitude shape == longitude shape (it should)
        alt_data = get_data(VDS(filenames[0], "Lidar_Data_Altitudes"), True)
        len_y = alt_data.shape[0]
        valid_shape = (len_x, len_y)

        for filename in filenames:
            sd = SD(filename)
            for var_name, var_info in sd.datasets().items():
                if var_info[1] == valid_shape:
                    variables.add(var_name)

        return variables

    def create_data_object(self, filenames, variable, index_offset=1):
        from cis.data_io.hdf_vd import get_data
        from cis.data_io.hdf_vd import VDS
        from pyhdf.error import HDF4Error
        from cis.data_io import hdf_sd
        from iris.coords import DimCoord, AuxCoord
        from iris.cube import Cube
        from cis.data_io.gridded_data import GriddedData
        from cis.time_util import cis_standard_time_unit

        logging.debug("Creating data object for variable " + variable)

        variables = ['Latitude', 'Longitude', "Profile_Time", "Pressure"]
        logging.info("Listing coordinates: " + str(variables))

        variables.append(variable)

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

        alt_coord = DimCoord(alt_data, standard_name='altitude', units='km')
        alt_coord.convert_units('m')

        lat_data = hdf.read_data(sdata['Latitude'], self._get_calipso_data)[:, index_offset]
        lat_coord = AuxCoord(lat_data, standard_name='latitude')

        pres_data = hdf.read_data(sdata['Pressure'], self._get_calipso_data)
        pres_coord = AuxCoord(pres_data, standard_name='air_pressure', units='hPa')

        # longitude
        lon = sdata['Longitude']
        lon_data = hdf.read_data(lon, self._get_calipso_data)[:, index_offset]
        lon_coord = AuxCoord(lon_data, standard_name='longitude')

        # profile time, x
        time = sdata['Profile_Time']
        time_data = hdf.read_data(time, self._get_calipso_data)[:, index_offset]
        time_coord = DimCoord(time_data, long_name='Profile_Time', standard_name='time',
                              units="seconds since 1993-01-01 00:00:00")
        time_coord.convert_units(cis_standard_time_unit)

        # retrieve data + its metadata
        var = sdata[variable]
        metadata = hdf.read_metadata(var, "SD")

        if variable in MIXED_RESOLUTION_VARIABLES:
            logging.warning("Using Level 2 resolution profile for mixed resolution variable {}. See CALIPSO "
                            "documentation for more details".format(variable))
            data = hdf.read_data(var, self._get_mixed_resolution_calipso_data)
        else:
            data = hdf.read_data(var, self._get_calipso_data)

        cube = Cube(data, long_name=metadata.long_name, units=self.clean_units(metadata.units),
                    dim_coords_and_dims=[(alt_coord, 1), (time_coord, 0)], aux_coords_and_dims=[(lat_coord, (0,)),
                                                                                                (lon_coord, (0,)),
                                                                                                (pres_coord, (0, 1))])
        gd = GriddedData.make_from_cube(cube)
        return gd

    @staticmethod
    def clean_units(units):
        lookup = {'NoUnits': '', 'sr^-1km^-1': 'sr^-1 km^-1', 'per kilometer': 'km-1'}
        # Get the units from the lookup, if they're not in there use the original
        return lookup.get(units, units)

    def create_coords(self, filenames, variable=None):
        raise NotImplemented()

    def _get_mixed_resolution_calipso_data(self, sds):
        # The first slice of the last dimension corresponds to the higher (in altitude) element of each
        # sub-Level-2-resolution bin.
        return self._get_calipso_data(sds)[:, :, 0]

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
            data = create_masked_array_for_missing_data(data, missing_val)

        # Now handle valid range mask
        valid_range = attributes.get('valid_range', None)
        if valid_range is not None:
            # Split the range into two numbers of the right type
            v_range = np.asarray(valid_range.split("..."), dtype=data.dtype)
            # Some valid_ranges appear to have only one value, so ignore those...
            if len(v_range) == 2:
                logging.debug("Masking all values {} > v > {}.".format(*v_range))
                data = np.ma.masked_outside(data, *v_range)
            else:
                logging.warning("Invalid valid_range: {}. Not masking values.".format(valid_range))

        # Offsets and scaling.
        offset = attributes.get('add_offset', 0)
        scale_factor = attributes.get('scale_factor', 1)
        data = self._apply_scaling_factor_CALIPSO(data, scale_factor, offset)

        return data

    def _apply_scaling_factor_CALIPSO(self, data, scale_factor, offset):
        """
        Apply scaling factor Calipso data.

        This isn't explicitly documented, but is referred to in the CALIOP docs here:
        http://www-calipso.larc.nasa.gov/resources/calipso_users_guide/data_summaries/profile_data.php#cloud_layer_fraction

        And also confirmed by email with jason.l.tackett@nasa.gov

        :param data:
        :param scale_factor:
        :param offset:
        :return:
        """
        logging.debug("Applying 'science_data = (packed_data / {scale}) + {offset}' "
                      "transformation to data.".format(scale=scale_factor, offset=offset))
        return (data / scale_factor) + offset

    def get_file_format(self, filename):
        return "HDF4/CaliopL2"

