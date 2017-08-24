from echam_ham_pascals import ECHAM_HAM_Pascals


class ECHAM_HAM(ECHAM_HAM_Pascals):
    """
        Plugin for reading ECHAM-HAM NetCDF output files. **Air pressure is converted to hPa**
    """

    def _add_available_aux_coords(self, cube, filenames):
        from iris.aux_factory import HybridPressureFactory
        from iris.coords import AuxCoord
        from iris.exceptions import CoordinateNotFoundError
        import iris

        if cube.coords('hybrid A coefficient at layer midpoints'):

            # First convert the hybrid coefficients to hPa, so that air pressure will be in hPa
            cube.coord('hybrid A coefficient at layer midpoints').convert_units('hPa')

            try:
                surface_pressure = cube.coord('surface pressure')
            except iris.exceptions.CoordinateNotFoundError as e:
                # If there isn't a surface pressure coordinate we can try and pull out the lowest pressure level
                surface_pressure_cubes = iris.load(filenames, 'atmospheric pressure at interfaces',
                                                   callback=self.load_multiple_files_callback)
                surface_pressure_cube = surface_pressure_cubes.concatenate_cube()[:, -1, :, :]
                surface_pressure = AuxCoord(points=surface_pressure_cube.data, long_name='surface pressure', units='Pa')
                cube.add_aux_coord(surface_pressure, (0, 2, 3))
 
            surface_pressure.convert_units('hPa')
 
            if len(cube.coords(long_name='hybrid level at layer midpoints')) > 0:
                cube.add_aux_factory(HybridPressureFactory(delta=cube.coord('hybrid A coefficient at layer midpoints'),
                                                           sigma=cube.coord('hybrid B coefficient at layer midpoints'),
                                                          surface_air_pressure=surface_pressure))

