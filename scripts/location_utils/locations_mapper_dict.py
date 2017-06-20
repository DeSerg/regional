# -*- coding: utf8 -*-

import pandas as pd
import sys
import numpy as np
class LocationsMapper:
    PROFILE_COL = 'Локация'
    LOC_COL = 'Стандартный регион'

    def __init__(self, toponyms_file):
        self.toponyms_file = toponyms_file
        self.toponyms_map = dict()
        self.regions = set()
        self.is_initialized = False

    def initialize(self):
        loc_data = pd.read_csv(self.toponyms_file, sep='\t')
        for i, row in loc_data.iterrows():
            loc, region = row[self.PROFILE_COL], row[self.LOC_COL]
            if region in ["?", "", np.nan]:
                region = "NA"
            self.toponyms_map[loc] = region
            self.regions.add(region)
        self.is_initialized = True

    def get_region(self, loc):
        if not self.is_initialized:
            self.initialize()
        if loc in self.regions:
            return loc
        return self.toponyms_map.get(loc, "NA")
