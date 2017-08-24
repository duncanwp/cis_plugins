from cis.data_io.products import NetCDF_Gridded


class squeeze_netcdf(NetCDF_Gridded):
    """
        Plugin for reading ECHAM-HAM NetCDF output files. 
    """

    @staticmethod
    def load_single_file_callback(cube, field, filename):
        from iris.util import squeeze
        # Sometimes it's useful to remove length one dimensions from cubes, squeeze does this for us...
        return squeeze(cube)

    @staticmethod
    def load_multiple_files_callback(cube, field, filename):
        from iris.util import squeeze
        # We need to remove these global attributes when reading multiple files so that the cubes can be properly merged
        cube.attributes.pop('host_name', None)
        cube.attributes.pop('date_time', None)
        cube.attributes.pop('history', None)
        return squeeze(cube)
