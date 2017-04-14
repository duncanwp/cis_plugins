from cis.data_io.products.caliop import Caliop_L2


class Caliop_V4(Caliop_L2):
    def get_file_signature(self):
        return [r'CAL_LID_L2_05kmAPro.*hdf']

