from echam_ham_pascals import ECHAM_HAM_Pascals


class ECHAM_HAM_63(ECHAM_HAM_Pascals):
    """
        Plugin for reading ECHAM-HAM NetCDF output files. **Air pressure is converted to hPa**
    """

    def get_variable_names(self, filenames, data_type=None):
        """
        This is exactly the same as the inherited version except I also exclude the mlev dimension
        """
        import iris
        import cf_units as unit
        variables = []
        cubes = iris.load(filenames)

        for cube in cubes:
            is_time_lat_lon_pressure_altitude_or_has_only_1_point = True
            for dim in cube.dim_coords:
                units = dim.units
                if dim.points.size > 1 and \
                        not units.is_time() and \
                        not units.is_time_reference() and \
                        not units.is_vertical() and \
                        not units.is_convertible(unit.Unit('degrees')) and \
                        dim.var_name != 'lev':
                    is_time_lat_lon_pressure_altitude_or_has_only_1_point = False
                    break
            if is_time_lat_lon_pressure_altitude_or_has_only_1_point:
                if cube.var_name:
                    variables.append(cube.var_name)
                else:
                    variables.append(cube.name())

        return set(variables)

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
            source = atts['source']
        except KeyError as ex:
            errors = ['No source attribute found in {}'.format(filename)]
        else:
            if source != 'ECHAM6.3':
                    errors = ['Source ({}) does not match ECHAM6.1 in {}'.format(source, filename)]
        return errors

