from cis.data_io.products.MODIS import MODIS_L2, _get_MODIS_SDS_data
import logging
from cis.data_io import hdf as hdf
from cis.data_io.Coord import Coord, CoordList


class MODIS_LST(MODIS_L2):

    def get_file_signature(self):
        product_names = ['MYD11_L2']
        regex_list = [r'.*' + product + '.*\.hdf' for product in product_names]
        return regex_list

    def __get_data_scale(self, filename, variable):
        # Note this is only here because it doesn't get inherited...
        from cis.exceptions import InvalidVariableError
        from pyhdf.SD import SD

        try:
            meta = SD(filename).datasets()[variable][0][0]
        except KeyError:
            raise InvalidVariableError("Variable " + variable + " not found")

        for scaling in self.modis_scaling:
            if scaling in meta:
                return scaling
        return None

    def _parse_datetime(self, metadata_dict, keyword):
        import re
        res = ""
        for s in metadata_dict.values():
            i_start = s.find(keyword)
            ssub = s[i_start:len(s)]
            i_end = ssub.find("END_OBJECT")
            ssubsub = s[i_start:i_start + i_end]
            matches = re.findall('".*"', ssubsub)
            if len(matches) > 0:
                res = matches[0].replace('\"', '')
                if res is not "":
                    break
        return res

    def _get_start_date(self, filename):
        import datetime as dt
        metadata_dict = hdf.get_hdf4_file_metadata(filename)
        date = self._parse_datetime(metadata_dict, 'RANGEBEGINNINGDATE')
        time = self._parse_datetime(metadata_dict, 'RANGEBEGINNINGTIME')
        datetime_str = date + " " + time
        return dt.datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S.%f")

    def _create_coord_list(self, filenames, variable=None):
        import datetime as dt
        from cis.time_util import convert_time_since_to_std_time, cis_standard_time_unit
        from cis.utils import concatenate
        from cf_units import Unit
        from geotiepoints import modis5kmto1km

        variables = ['Latitude', 'Longitude', 'View_time']
        logging.info("Listing coordinates: " + str(variables))

        sdata, vdata = hdf.read(filenames, variables)

        apply_interpolation = False
        if variable is not None:
            scale = self.__get_data_scale(filenames[0], variable)
            apply_interpolation = True if scale is "1km" else False

        lat_data = hdf.read_data(sdata['Latitude'], _get_MODIS_SDS_data)
        lat_metadata = hdf.read_metadata(sdata['Latitude'], "SD")

        lon_data = hdf.read_data(sdata['Longitude'], _get_MODIS_SDS_data)
        lon_metadata = hdf.read_metadata(sdata['Longitude'], "SD")

        if apply_interpolation:
            lon_data, lat_data = modis5kmto1km(lon_data, lat_data)

        lat_coord = Coord(lat_data, lat_metadata, 'Y')
        lon_coord = Coord(lon_data, lon_metadata, 'X')

        time = sdata['View_time']
        time_metadata = hdf.read_metadata(time, "SD")
        # Ensure the standard name is set
        time_metadata.standard_name = 'time'
        time_metadata.units = cis_standard_time_unit

        t_arrays = []
        for f, d in zip(filenames, time):
            time_start = self._get_start_date(f)
            t_data = _get_MODIS_SDS_data(d) / 24.0  # Convert hours since to days since
            t_offset = time_start - dt.datetime(1600, 1, 1)  # Convert to CIS time
            t_arrays.append(t_data + t_offset.days)

        time_coord = Coord(concatenate(t_arrays), time_metadata, "T")

        return CoordList([lat_coord, lon_coord, time_coord])
