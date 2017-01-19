from cis.data_io.products import cis
from cis.data_io.ungridded_data import UngriddedData, UngriddedCoordinates
from cis.data_io.netcdf import get_metadata


class cis_nsd(cis):

    @staticmethod
    def _add_aux_coordinate(dim_coords, filename, aux_coord_name, length):
        """
        Add an auxiliary coordinate to a list of (reshaped) dimension coordinates

        :param dim_coords: CoordList of one-dimensional coordinates representing physical dimensions
        :param filename: The data file containing the aux coord
        :param aux_coord_name: The name of the aux coord to add to the coord list
        :param length: The length of the data dimensions which this auxiliary coordinate should span
        :return: A CoordList of reshaped (2D) physical coordinates plus the 2D auxiliary coordinate
        """
        from cis.data_io.Coord import Coord
        from cis.utils import expand_1d_to_2d_array
        from cis.data_io.netcdf import read

        # We assume that the auxilliary coordinate is the same shape across files
        d = read(filename, [aux_coord_name])[aux_coord_name]
        # Reshape to the length given
        aux_data = expand_1d_to_2d_array(d[:], length, axis=0)
        # Get the length of the auxiliary coordinate
        len_y = d[:].size

        for dim_coord in dim_coords:
            dim_coord.data = expand_1d_to_2d_array(dim_coord.data, len_y, axis=1)

        all_coords = dim_coords + [Coord(aux_data, get_metadata(d))]

        return all_coords

    def create_coords(self, filenames, variable=None):
        """
        Reads the coordinates and data if required from the files
        :param filenames: List of filenames to read coordinates from
        :param variable: load a variable for the data
        :return: Coordinates
        """
        from cis.data_io.netcdf import read_many_files_individually
        from cis.data_io.Coord import Coord, CoordList
        from cis.exceptions import InvalidVariableError

        variables = [("longitude", "x"), ("latitude", "y"), ("altitude", "z"), ("time", "t"), ("air_pressure", "p")]

        dim_coords = CoordList()
        for v in variables:
            try:
                var_data = read_many_files_individually(filenames, v[0])[v[0]]
                dim_coords.append(Coord(var_data, get_metadata(var_data[0]), axis=v[1]))
            except InvalidVariableError:
                pass

        if variable is None:
            return UngriddedCoordinates(dim_coords)
        else:
            all_coords = self._add_aux_coordinate(dim_coords, filenames[0], 'DP_MID',
                                                  dim_coords.get_coord(standard_name='time').data.size)

            usr_var_data = read_many_files_individually(filenames, variable)[variable]
            return UngriddedData(usr_var_data, get_metadata(usr_var_data[0]), all_coords)
