from echam_ham_63 import ECHAM_HAM_63, _get_cubes
import numpy as np


class ECHAM_HAM_63_average_pressure(ECHAM_HAM_63):
    """
        Plugin for reading ECHAM-HAM NetCDF output files without at surface pressure field (e.g. time averaged)
    """
    priority = 100

    @staticmethod
    def load_single_file_callback(cube, field, filename):
        # Don't squeeze, since we need the length-one dims to reconstruct the pressure
        return cube

    def _add_available_aux_coords(self, cube, filenames):
        import iris
        from iris.aux_factory import HybridPressureFactory
        from iris.coords import DimCoord

        # Only do this for fields with a vertical component - this check is a bit hacky though (doesn't consider 3D with no time...)
        if len(cube.coords(long_name='hybrid level at layer midpoints')) > 0:
            # Only read the first file for these coefficients as they are time-independant and iris won't merge them
            hybrid_a = _get_cubes(filenames, 'hybrid A coefficient at layer midpoints')
            hybrid_b = _get_cubes(filenames, 'hybrid B coefficient at layer midpoints')

            surface_pressure_points = np.empty(cube.shape[1])
            hybrid_a_coord = AuxCoord(points=hybrid_a[0].data, long_name='hybrid A coefficient at layer midpoints', units='Pa')
            hybrid_b_coord = AuxCoord(points=hybrid_b[0].data, long_name='hybrid B coefficient at layer midpoints', units='1')

            if cube.coords('surface pressure'):
                surface_pressure = cube.coord('surface pressure')
            else:
                surface_pressure = AuxCoord(points=[1013.25], long_name='surface pressure', units='hPa')
                cube.add_aux_coord(surface_pressure, ())

            # First convert the hybrid coefficients to hPa, so that air pressure will be in hPa
            hybrid_a[0].convert_units('hPa')

            air_pressure = DimCoord(points=hybrid_a[0].data + hybrid_b[0].data*surface_pressure_points,
                                    standard_name='air_pressure', units='hPa')
            cube._remove_coord(cube.coord(long_name='hybrid level at layer midpoints'))
            cube.add_dim_coord(air_pressure, (1,))


    def get_file_type_error(self, filename):
        """
        Test that the file is of the correct signature
        :param filename: the file name for the file
        :return: list fo errors or None
        """
        return None

