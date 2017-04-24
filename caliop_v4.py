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

        if variable in MIXED_RESOLUTION_VARIABLES:
            logging.warning("Using Level 2 resolution profile for mixed resolution variable {}. See CALIPSO "
                            "documentation for more details".format(variable))
            callback = self._get_mixed_resolution_calipso_data
        else:
            callback = self._get_calipso_data

        return UngriddedData(var, metadata, coords, callback)
