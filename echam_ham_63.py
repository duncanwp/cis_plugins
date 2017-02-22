from echam_ham_pascals import ECHAM_HAM_Pascals


class ECHAM_HAM_63(ECHAM_HAM_Pascals):
    """
        Plugin for reading ECHAM-HAM NetCDF output files. **Air pressure is converted to hPa**
    """

    def _add_available_aux_coords(self, cube, filenames):
        import iris
        from iris.aux_factory import HybridPressureFactory
        from iris.coords import AuxCoord
        from iris.exceptions import CoordinateNotFoundError

        hybrid_a = iris.load_cube(filenames, 'hybrid A coefficient at layer midpoints')
        hybrid_b = iris.load_cube(filenames, 'hybrid B coefficient at layer midpoints')

        hybrid_a_coord = AuxCoord(points=hybrid_a.data, long_name='hybrid A coefficient at layer midpoints', units='Pa')
        hybrid_b_coord = AuxCoord(points=hybrid_b.data, long_name='hybrid B coefficient at layer midpoints', units='1')

        try:
            surface_pressure = cube.coord('surface pressure')
        except CoordinateNotFoundError as e:
            # If there isn't a surface pressure coordinate we can try and pull out the lowest pressure level
            surface_pressure_cube = iris.load_cube(filenames, 'atmospheric pressure at interfaces')[:,-1,:,:]
            surface_pressure = AuxCoord(points=surface_pressure_cube.data, long_name='surface pressure', units='Pa')
            cube.add_aux_coord(surface_pressure, (0, 2, 3))

        # First convert the hybrid coefficients to hPa, so that air pressure will be in hPa
        hybrid_a_coord.convert_units('hPa')
        surface_pressure.convert_units('hPa')

        cube.add_aux_coord(hybrid_a_coord, (1,))
        cube.add_aux_coord(hybrid_b_coord, (1,))

        if len(cube.coords(long_name='hybrid level at layer midpoints')) > 0:
            cube.add_aux_factory(HybridPressureFactory(delta=hybrid_a_coord, sigma=hybrid_b_coord,
                                                       surface_air_pressure=surface_pressure))

