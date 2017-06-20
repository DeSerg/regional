"""
Модуль для для формирования словаря Руслана с колонкой
стандартизованных локаций
"""

import pandas as pd
import numpy as np
import re
import location_utils.locations_freq as lf
import sys


class LocationsMapper:
    PROFILE_COL = '"Местонахождение" в профиле'
    CITY_COL = 'унифицированное место'
    LOC_COL = 'регион'

    def __init__(self, toponyms_data, ruslans_data):
        self.toponyms_data = toponyms_data
        self.ruslans_data = ruslans_data

        self._memo = {}  # Weird memoization mechanism in Python?

    def toponyms_data_for(self, loc):
        loc_data = self.toponyms_data[(self.toponyms_data[self.LOC_COL] == loc)
                                      | (self.toponyms_data[self.CITY_COL] == loc)
                                      | (self.toponyms_data[self.PROFILE_COL] == loc)]

        if (not loc_data.empty):
            row = loc_data.iloc[0]
            return {self.LOC_COL: row[self.LOC_COL],
                    self.CITY_COL: row[self.CITY_COL]}
        else:
            return None

    def make_mapping(self):
        mapping = {}
        for loc in self.ruslans_data['location']:
            if loc not in mapping:
                mapping[loc] = ("", "")

            row = self.toponyms_data_for(loc)
            if row:
                mapping[loc] = (row[self.CITY_COL], row[self.LOC_COL])

        self.mapping = mapping

    def save_mapping(self):
        arr = [["Original location", "City", "Loc"]]
        for orig_city in sorted(self.mapping):
            locations = self.mapping[orig_city]
            arr.append([orig_city, locations[0], locations[1]])
        lf.save_to_file('files/ruslans_toponyms_map.csv', arr)


def ruslan_data():
    filename = 'files/dict_locations_20_11_2014.csv'
    return pd.read_csv(filename, sep='\t')


def toponyms_data():
    filename = 'files/toponims-utf8.csv'
    return pd.read_csv(filename, sep='\t')


def make_ruslans_dict_with_mapped_locations(toponyms_map_filename, dict_filename, save_filename):
    toponyms_map = pd.read_csv(toponyms_map_filename,
                               sep='\t', header=None)
    locs_map = {k:str(v) for k,v in zip(list(toponyms_map[0]), list(toponyms_map[2]))}

    locations_column = 'filtered_locations'
    sheet = pd.ExcelFile(dict_filename).parse('Sheet1')
    old_locs = [loc_str.split(', ') for loc_str in sheet[locations_column]]
    standard_locs = []
    for old_loc_arr in old_locs:
        standard_loc_arr = [locs_map[old_loc] for old_loc in old_loc_arr]
        standard_locs.append(", ".join(standard_loc_arr))
    sheet['Standartized locations'] = standard_locs
    sheet.to_excel(save_filename, index=False)


def run(args):
    if len(args) < 3:
        sys.exit("Pass toponyms_map_hand filename, ruslans dict with \
                  filtered locations and save_filename")
    toponyms_map_filename = args[0]
    ruslans_dict_filename = args[1]
    save_filename = args[2]
    make_ruslans_dict_with_mapped_locations(toponyms_map_filename,
                                            ruslans_dict_filename,
                                            save_filename)
