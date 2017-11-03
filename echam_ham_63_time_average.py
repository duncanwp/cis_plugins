from echam_ham_63 import ECHAM_HAM_63, _get_cubes


class ECHAM_HAM_63_average_pressure(ECHAM_HAM_63):
    """
        Plugin for reading ECHAM-HAM NetCDF output files without at surface pressure field (e.g. time averaged)
    """
    priority = 100

    def _add_available_aux_coords(self, cube, filenames):
        import iris
        from iris.aux_factory import HybridPressureFactory
        from iris.coords import AuxCoord

        # Only do this for fields with a vertical component - this check is a bit hacky though (doesn't consider 3D with no time...)
        if cube.ndim == 4:
            # Only read the first file for these coefficients as they are time-independant and iris won't merge them
            hybrid_a = _get_cubes(filenames, 'hybrid A coefficient at layer midpoints')
            hybrid_b = _get_cubes(filenames, 'hybrid B coefficient at layer midpoints')

            hybrid_a_coord = AuxCoord(points=hybrid_a[0].data, long_name='hybrid A coefficient at layer midpoints', units='Pa')
            hybrid_b_coord = AuxCoord(points=hybrid_b[0].data, long_name='hybrid B coefficient at layer midpoints', units='1')

            if cube.coords('surface pressure'):
                surface_pressure = cube.coord('surface pressure')
            else:
                surface_pressure = AuxCoord(points=[1013.25], long_name='surface pressure', units='hPa')
                cube.add_aux_coord(surface_pressure, (0, 2, 3))

            # First convert the hybrid coefficients to hPa, so that air pressure will be in hPa
            hybrid_a_coord.convert_units('hPa')

            cube.add_aux_coord(hybrid_a_coord, (1,))
            cube.add_aux_coord(hybrid_b_coord, (1,))

            if len(cube.coords(long_name='hybrid level at layer midpoints')) > 0:
                cube.add_aux_factory(HybridPressureFactory(delta=hybrid_a_coord, sigma=hybrid_b_coord,
                                                           surface_air_pressure=surface_pressure))
