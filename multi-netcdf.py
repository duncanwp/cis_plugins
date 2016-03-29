from cis.data_io.products import NetCDF_Gridded


class multi_netcdf(NetCDF_Gridded):
    """
        Plugin for reading ECHAM-HAM NetCDF output files. 
    """

    @staticmethod
    def load_multiple_files_callback(cube, field, filename):
        # We need to remove the history field when reading multiple files so that the cubes can be properly merged
        cube.attributes.pop('history')
        return cube

