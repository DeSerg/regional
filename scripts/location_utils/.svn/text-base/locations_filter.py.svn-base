"""
Модуль для получения автоматического отображения локация между словарем Руслана
и toponyms-utf8.
"""

import pandas as pd
import numpy as np
import re
import sys


class LocationsFilter(object):
    def __init__(self, filename):
        self.filename = filename

    def filtered_dict(self):
        sheet = self.excel_sheet()
        locations = self.filtered_locations(sheet)

        sheet['filtered_locations'] = locations
        sheet.to_excel('files/dictionary_20_11_2014.xlsx', index=False)

    def filter_and_save_locations(self):
        locations_set_ = self.locations_set()

        pd_locations = pd.Series(sorted(locations_set_)).to_frame(name='location')
        pd_locations.to_excel('files/dict_locations_20_11_2014.xlsx', index=False)
        pd_locations.to_csv(
            'files/dict_locations_20_11_2014.csv', index=False, sep='\t')

    def locations_set(self):
        locations = self.filtered_locations(self.excel_sheet())
        splitted_locations = [loc.split(', ') for loc in locations]
        flatten_locations = sum(splitted_locations, [])
        return set(flatten_locations)

    def excel_sheet(self):
        xlsx = pd.ExcelFile(self.filename)
        return xlsx.parse(u'Словарь')

    def filtered_locations(self, sheet):
        locations_strs = sheet[u'РЕГИОН']

        locations = []
        for location_str in locations_strs:
            filtered_str = self.filter_string(location_str)
            splitted_str = [self.filter_string(str) for str in filtered_str.split(', ')]
            locations.append(', '.join(splitted_str))
        return locations

    # Replace in the str: а) б) в) (кроме ...) I II () (без реже
    def filter_string(self, str):
        if self.is_nan(str):
            return ""

        bez_regexp = re.compile('(\(без .*?\))')
        krome_regexp = re.compile('(\(кроме .*?\))')

        filtered_str = str

        filtered_str = re.sub(bez_regexp, '', filtered_str)
        filtered_str = re.sub(krome_regexp, '', filtered_str)
        filtered_str = filtered_str.replace('а)', '')
        filtered_str = filtered_str.replace('б)', ', ')
        filtered_str = filtered_str.replace('в)', ', ')
        filtered_str = filtered_str.replace('II', ', ')
        filtered_str = filtered_str.replace('I', '')
        filtered_str = filtered_str.replace('(', ', ')
        filtered_str = filtered_str.replace(')', '')
        filtered_str = filtered_str.replace('реже', '')

        filtered_str = filtered_str.strip()

        if filtered_str[0] == ',':
            filtered_str = filtered_str[2:]

        return filtered_str

    def is_nan(self, str):
        return(not str == str)


def run():
    if len(sys.argv[1:]) == 0:
        print("Pass only_locations or filtered_dict to get what you want \
              and filename as a second param")
        return

    lf = LocationsFilter(sys.argv[2])

    if sys.argv[1] == 'only_locations':
        lf.filter_and_save_locations()
    elif sys.argv[1] == 'filtered_dict':
        lf.filtered_dict()
