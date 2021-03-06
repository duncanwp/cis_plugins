from cis.data_io.products import NetCDF_Gridded
import cis.data_io.gridded_data as gd

gd.CACHED_CUBES = {}

class multi_netcdf(NetCDF_Gridded):
    """
        Plugin for reading ECHAM-HAM NetCDF output files. 
    """
    priority=100

    @staticmethod
    def load_multiple_files_callback(cube, field, filename):
        # We need to remove the history field when reading multiple files so that the cubes can be properly merged
        cube.attributes.pop('history', None)
        cube.attributes.pop('date_time', None)
        cube.attributes.pop('host_name', None)
        return cube

    def create_data_object(self, filenames, variable):
        """Reads the data for a variable.
        :param filenames: list of names of files from which to read data
        :param variable: (optional) name of variable; if None, the file(s) must contain data for only one cube
        :return: iris.cube.Cube
        """
        from iris.aux_factory import HybridPressureFactory
        # Add the derived coordinates back (https://github.com/SciTools/iris/issues/2478)...
        cube = super().create_data_object(filenames, variable)
        if cube.coords('atmosphere_hybrid_sigma_pressure_coordinate') and not cube.coords('air_pressure'):
            cube.add_aux_factory(HybridPressureFactory(cube.coord('atmosphere_hybrid_sigma_pressure_coordinate'),
                                                       cube.coord('hybrid B coefficient at layer midpoints'),
                                                       cube.coord('surface pressure')))
        return cube
