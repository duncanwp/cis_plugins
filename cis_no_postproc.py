"""
Don't drop points with invalid coordinates - there's currently no keyword arg for this
"""
from cis.data_io.products import cis


class cis_no_postproc(cis):

    def create_data_object(self, filenames, variable):
        data = self.create_coords(filenames, variable)

        # This is pretty hacky but does the job
        data._post_process = lambda: None
        data.update_range()
        return data

