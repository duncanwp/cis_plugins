from echam_ham_pascals import ECHAM_HAM_Pascals


class ECHAM_HAM(ECHAM_HAM_Pascals):
    """
        Plugin for reading ECHAM-HAM NetCDF output files. **Air pressure is converted to hPa**
    """

    def _add_available_aux_coords(self, cube, filenames):
        from iris.aux_factory import HybridPressureFactory

        # First convert the hybrid coefficients to hPa, so that air pressure will be in hPa
        cube.coord('hybrid A coefficient at layer midpoints').convert_units('hPa')
        cube.coord('surface pressure').convert_units('hPa')

        if len(cube.coords(long_name='hybrid level at layer midpoints')) > 0:
            cube.add_aux_factory(HybridPressureFactory(delta=cube.coord('hybrid A coefficient at layer midpoints'),
                                                       sigma=cube.coord('hybrid B coefficient at layer midpoints'),
                                                       surface_air_pressure=cube.coord('surface pressure')))

