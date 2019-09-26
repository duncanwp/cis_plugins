from cis.data_io.products.AProduct import AProduct
from cis.data_io.Coord import Coord, CoordList
from cis.data_io.ungridded_data import UngriddedData,UngriddedCoordinates
from cis.data_io.ungridded_data import Metadata
import iris
import numpy as np
import cf_units
import netCDF4

class IPSL_daily(AProduct):

    def get_file_signature(self):
        return [r'.*IPSL*.nc']

    def _create_coord_list(self, filenames, data=None):
        if data is None:
            data = {} #initialise data dictionary
            inData = netCDF4.Dataset(filenames[0]) #open netCDF file
            data['longitude'] = np.array(inData.variables['lon']) #extract longitudes
            data['latitude'] = np.array(inData.variables['lat']) #extract latitudes
            origTimes = np.array(inData.variables['time_counter']) #extract times
            #Convert time to days since 
            niceDateTime = cf_units.num2date(origTimes,'seconds since 1999-01-01 00:00:00', 'gregorian')
            data['time_counter'] = cf_units.date2num(niceDateTime,'days since 1600-01-01 00:00:00', 'gregorian')
            inData.close() #close netCDF file
        coords = CoordList() #initialise coordinate list
        #Append latitudes and longitudes to coordinate list:
        coords.append(Coord(data['longitude'],Metadata(name="longitude",long_name='longitude',standard_name='longitude',shape=(len(data),),missing_value=-999.0,units="degrees_east",range=(-180, 180)),"x"))
        coords.append(Coord(data['latitude'],Metadata(name="latitude",long_name='latitude',standard_name='latitude',shape=(len(data),),missing_value=-999.0,units="degrees_north",range=(-90, 90)),"y"))
        coords.append(Coord(data['time'],Metadata(name="time",long_name='time',standard_name='time',shape=(len(data),),missing_value=-999.0,units="days since 1600-01-01 00:00:00"),"t"))
        return coords

    def create_coords(self, filenames, variable=None):
        return UngriddedCoordinates(self._create_coord_list(filenames))

    def create_data_object(self, filenames, variable):
        data_dict = {} #initialise data dictionary
        inData = netCDF4.Dataset(filenames[0]) #open netCDF file
        data_dict['longitude'] = np.array(inData.variables['lon']) #extract longitudes
        data_dict['latitude'] = np.array(inData.variables['lat']) #extract latitudes
        origTimes = np.array(inData.variables['time_counter']) #extract times
        #Convert time to days since 
        niceDateTime = cf_units.num2date(origTimes,'seconds since 1999-01-01 00:00:00', 'gregorian')
        data_dict['time'] = cf_units.date2num(niceDateTime,'days since 1600-01-01 00:00:00', 'gregorian')
        data_dict[variable] = np.array(inData.variables[variable])  #extract requested variable
        inData.close() #close netCDF file
        coords = self._create_coord_list(filenames,data_dict)
        return UngriddedData(data_dict[variable],Metadata(name=variable,long_name=variable,shape=(len(data_dict),),missing_value=-999.0,units="1"),coords)
        
    def get_variable_names(self, filenames, data_type=None):
        return ['Info unavailable with this plugin']
