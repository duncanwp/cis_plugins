from cis.data_io.products import NetCDF_Gridded
from cis.utils import demote_warnings


class ICON_Gridded(NetCDF_Gridded):
    """
        Plugin for reading regridded ICON NetCDF output files.
    """

    @staticmethod
    def load_single_file_callback(cube, field, filename):
        from iris.util import squeeze
        # Sometimes it's useful to remove length one dimensions from cubes, squeeze does this for us...
        return squeeze(cube)

    @staticmethod
    def load_multiple_files_callback(cube, field, filename):
        # We need to remove these global attributes when reading multiple files so that the cubes can be properly merged
        cube.attributes.pop('history', None)
        return cube

    def _add_available_aux_coords(self, cube, filenames):
        from iris.coords import AuxCoord
        import iris

        with demote_warnings():
            height_cube = iris.load_cube(filenames, 'geometric height at full level center',
                                         callback=self.load_multiple_files_callback)

        height = AuxCoord(points=height_cube.data, long_name='geometric height at full level center',
                          units='m')
        cube.add_aux_coord(height, (1, 2, 3))

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
            title = atts['title']
        except KeyError as ex:
            errors = ['No title attribute found in {}'.format(filename)]
        else:
            if 'ICON' not in title:
                    errors = ['Title ({}) does not contain ICON in {}'.format(title, filename)]
        return errors


