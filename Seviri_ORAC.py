"""
Workaround for a bug introduced in 1.5.2 where all units got converted to lower case....
"""
from cis.data_io.products import AProduct, NetCDF_Gridded
from cf_units import Unit
import logging


class seviri_ORAC(AProduct):

    def get_file_signature(self):
        return [r'SEVIRI-L2-CLOUD-CLD-SEVIRI_V1.0_MSG3_.*\.nc']

    def create_coords(self, filenames, usr_variable=None):
        from cis.data_io.netcdf import read_many_files_individually, get_metadata
        from cis.data_io.Coord import Coord, CoordList
        from cis.data_io.ungridded_data import UngriddedCoordinates, UngriddedData
        from cis.exceptions import InvalidVariableError

        variables = [("lon", "x"), ("lat", "y")]

        # if usr_variable is not None:
        #     variables.append((usr_variable, ''))

        logging.info("Listing coordinates: " + str(variables))

        coords = CoordList()
        var_data = read_many_files_individually(filenames, [v[0] for v in variables])
        for var, (name, axis) in zip(var_data.values(), variables):
            try:
                coords.append(Coord(var, get_metadata(var[0]), axis=axis))
            except InvalidVariableError:
                pass

        # Note - We don't need to convert this time coord as it should have been written in our
        #  'standard' time unit

        if usr_variable is None:
            res = UngriddedCoordinates(coords)
        else:
            usr_var_data = read_many_files_individually(filenames, usr_variable)[usr_variable]
            res = UngriddedData(usr_var_data, get_metadata(usr_var_data[0]), coords)

        return res

    def create_data_object(self, filenames, variable):
        return self.create_coords(filenames, variable)

    def get_file_format(self, filename):
        return "NetCDF/SEVIRI"

    def get_file_type_error(self, filename):
        """
        Test that the file is of the correct signature
        :param filename: the file name for the file
        :return: list fo errors or None
        """
        from cis.data_io.netcdf import get_netcdf_file_attributes
        atts = get_netcdf_file_attributes(filename)
        errors = None
        try:
            source = atts['title']
        except KeyError as ex:
            errors = ['No title attribute found in {}'.format(filename)]
        else:
            if not source.startswith('ESA Cloud CCI Retrieval Products'):
                errors = ['Source ({}) does not match SEVIRI in {}'.format(source, filename)]
        return errors


class seviri_ORAC_gridded(NetCDF_Gridded):

    def get_file_signature(self):
        return [r'SEVIRI-L2-CLOUD-CLD-SEVIRI_V1.0_MSG3_.*\.nc']

    # @staticmethod
    # def load_single_file_callback(cube, field, filename):
    #     from iris.util import squeeze
    #     # Sometimes it's useful to remove length one dimensions from cubes, squeeze does this for us...
    #     return squeeze(cube)
    #
    # @staticmethod
    # def load_multiple_files_callback(cube, field, filename):
    #     # We need to remove these global attributes when reading multiple files so that the cubes can be properly merged
    #     cube.attributes.pop('host_name', None)
    #     cube.attributes.pop('date_time', None)
    #     return cube

    def _add_available_aux_coords(self, cube, filenames):
        from iris.coords import AuxCoord
        import iris

        cube.add_aux_coord(AuxCoord(iris.load_cube(filenames, 'latitude').data, 'latitude'), (0, 1))
        cube.add_aux_coord(AuxCoord(iris.load_cube(filenames, 'longitude').data, 'longitude'), (0, 1))

    def get_file_format(self, filename):
        return "NetCDF/SEVIRI"

    def get_file_type_error(self, filename):
        """
        Test that the file is of the correct signature
        :param filename: the file name for the file
        :return: list fo errors or None
        """
        from cis.data_io.netcdf import get_netcdf_file_attributes
        atts = get_netcdf_file_attributes(filename)
        errors = None
        try:
            source = atts['title']
        except KeyError as ex:
            errors = ['No title attribute found in {}'.format(filename)]
        else:
            if not source.startswith('ESA Cloud CCI Retrieval Products'):
                errors = ['Source ({}) does not match SEVIRI in {}'.format(source, filename)]
        return errors

