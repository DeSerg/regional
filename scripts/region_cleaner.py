# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:        standard_regions_cleaner.py
#-------------------------------------------------------------------------------

import sys
import pandas as pd
import numpy as np

LOC_COL = 'регион'

if __name__ == '__main__':
    args = sys.argv[1:]
    if len(args) != 4:
        sys.exit("Pass toponyms file, intermediate mapping file, "
                 "city mapping file and output file")
    infile, map_file, city_map_file, outfile = args
    data = pd.read_csv(infile, sep='\t')
    first_map = dict()
    for _, row in data.iterrows():
        loc, first_loc = row[0], row[3]
        if isinstance(first_loc, str) and np.isnan(row[4]):
            first_map[loc] = first_loc
    intermediate_data = pd.read_csv(map_file, sep=',')
    second_map = dict()
    for _, row in intermediate_data.iterrows():
        first, second = row[u'Регион'], row[u'Стандартный регион']
        if isinstance(second, float) and np.isnan(second):
            second = first
        second_map[first] = second
        second_map[second] = second
    city_map = dict()
    city_data = pd.read_csv(city_map_file, sep='\t')
    for _, row in city_data.iterrows():
        city, region = row['Город'], row['Регион']
        city_map[city] = region
    final_map = dict()
    for loc, first_loc in first_map.items():
        if first_loc in second_map:
            final_map[loc] = second_map[first_loc]
    for loc, region in city_map.items():
        final_map[loc] = region

    regions, standard = map(list, zip(*sorted(final_map.items(), key=(lambda x: x[0]))))
    regions_data = pd.DataFrame(data={'Локация': regions, "Стандартный регион": standard})
    regions_data.to_csv(outfile, sep="\t")