from cis.data_io.products.AProduct import AProduct


class my_product(AProduct):
    def get_file_signature(self):
        return [r'cis\\-.\*\\.nc']

    def create_coords(self, filenames):
        from cis.data_io.netcdf import read_many_files_individually, get_metadata
        from cis.data_io.Coord import Coord, CoordList
        from cis.data_io.ungridded_data import UngriddedCoordinates, Metadata

        var_data = read_many_files_individually(filenames,
                                                ["longitude","latitude", "time"])

        lon = Coord(var_data["longitude"],
                    get_metadata(var_data["longitude"][0]),
                    axis="x")
        lat = Coord(var_data["latitude"],
                    get_metadata(var_data["latitude"][0]),
                    axis="y")
        time = Coord(var_data["time"],
                    get_metadata(var_data["time"][0]),
                    axis="t")
        coords = CoordList([lon, lat, time])

        return UngriddedCoordinates(coords)

    def create_data_object(self, filenames, variable):
        from cis.data_io.netcdf import read_many_files_individually, get_metadata
        from cis.data_io.Coord import Coord, CoordList
        from cis.data_io.ungridded_data import UngriddedData

        var_data = read_many_files_individually(filenames,
                                                [variable, "longitude","latitude", "time"])

        lon = Coord(var_data["longitude"],
                    get_metadata(var_data["longitude"][0]),
                    axis="x")
        lat = Coord(var_data["latitude"],
                    get_metadata(var_data["latitude"][0]),
                    axis="y")
        time = Coord(var_data["time"],
                    get_metadata(var_data["time"][0]),
                    axis="t")
        coords = CoordList([lon, lat, time])

        return UngriddedData(var_data[variable],
                             get_metadata(var_data[variable][0]),
                             coords)
