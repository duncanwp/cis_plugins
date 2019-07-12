from cis.data_io.products import NetCDF_Gridded
import cis.data_io.gridded_data as gd
import logging
from cis.utils import demote_warnings


class Grosvenor_CDNC(NetCDF_Gridded):
    """
        Plugin for reading Dan Grosvenor's MODIS CDNC files.
    """

    @staticmethod
    def load_multiple_files_callback(cube, field, filename):
        # We need to remove these global attributes when reading multiple files so that the cubes can be properly merged
        cube.attributes.pop('history', None)
        cube.attributes.pop('CreationDate', None)
        return cube

    def get_file_signature(self):
        return [r'.*\.nc']

    def create_data_object(self, filenames, variable):
        """Reads the data for a variable.
        :param filenames: list of names of files from which to read data
        :param variable: (optional) name of variable; if None, the file(s) must contain data for only one cube
        :return: iris.cube.Cube
        """
        from cis.time_util import convert_cube_time_coord_to_standard_time
        from cis.utils import single_warnings_only
        from iris.coords import DimCoord
        from numpy.ma import masked_invalid
        import iris

        # Filter the warnings so that they only appear once - otherwise you get lots of repeated warnings
        #  - partly because we open the files multiple times (to look for aux coords) and partly because iris
        #  will throw a warning every time it meets a variable with a non-CF dimension
        with single_warnings_only():
            cube = self._create_cube(filenames, variable)

        # For this data we actually need to add the dim coords...
        cubes = iris.load(filenames)

        cube.add_dim_coord(DimCoord(cubes.extract('lon')[0].data, units='degrees_east',
                                    standard_name='longitude'), 0)
        cube.add_dim_coord(DimCoord(cubes.extract('lat')[0].data, units='degrees_north',
                                    standard_name='latitude'), 1)
        cube.add_dim_coord(DimCoord(cubes.extract('time')[0].data, units='days since 1970-01-01 00:00:00',
                                    standard_name='time'), 2)

        if cube.attributes['invalid_units'] == 'cm^{-3}':
            cube.units = 'cm-3'

        # Mask the NaNs
        cube.data = masked_invalid(cube.data)

        cube = convert_cube_time_coord_to_standard_time(cube)

        return cube

