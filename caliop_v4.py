from cis.data_io.products.caliop import Caliop_L2, Caliop_L2_NO_PRESSURE
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
