"""
Workaround for a bug introduced in 1.5.2 where all units got converted to lower case....
"""
from cis.data_io.products import cis
from cf_units import Unit


class cis_hpa(cis):

    def create_coords(self, filenames, usr_variable=None):
        o = cis.create_coords(self, filenames, usr_variable)

        try:
            air_pressure_coord = o.coord('air_pressure')
        except:
            pass
        else:
            if air_pressure_coord.units == 'hpa':
                air_pressure_coord.units = Unit('hPa')
        return o
