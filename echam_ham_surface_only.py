from echam_ham import ECHAM_HAM
from cis.data_io.products.gridded_NetCDF import DisplayConstraint


class ECHAM_HAM_surface_only(ECHAM_HAM):
    """
        Plugin for reading ECHAM-HAM NetCDF output files. 
    """

    def _create_cube(self, filenames, variable):
        """Creates a cube for the specified variable.
        :param filenames: List of filenames to read coordinates from
        :param variable: Optional variable to read while we're reading the coordinates, can be a string or a
        VariableConstraint object
        :return: If variable was specified this will return an UngriddedData object, otherwise a CoordList
        """
        from cis.exceptions import InvalidVariableError
        from cis.data_io import gridded_data
        import iris

        # Check if the files given actually exist.
        for filename in filenames:
            with open(filename) as f:
                pass

        variable_constraint = variable
        if isinstance(variable, str):
            variable_constraint = DisplayConstraint(cube_func=(lambda c: c.var_name == variable or
                                                                c.standard_name == variable or
                                                                c.long_name == variable), display=variable,
                                                    coord_values={'hybrid level at layer midpoints':
                                                                      (lambda lev: lev == 31)})
        if len(filenames) == 1:
            callback_function = self.load_single_file_callback
        else:
            callback_function = self.load_multiple_files_callback

        try:
            cube = gridded_data.load_cube(filenames, variable_constraint, callback=callback_function)
        except iris.exceptions.ConstraintMismatchError as e:
            if variable is None:
                message = "File contains more than one cube variable name must be specified"
            elif e.message == "no cubes found":
                message = "Variable not found: {} \nTo see a list of variables run: cis info {}" \
                    .format(str(variable), filenames[0])
            else:
                message = e.message
            raise InvalidVariableError(message)
        except ValueError as e:
            raise IOError(str(e))

        self._add_available_aux_coords(cube, filenames)

        return cube

