import sys
import json
from pprint import pprint

sys.path.insert(0, '..')

import location_utils.location_helper as lh


def main(argv):
    if len(argv) < 1:
        print('Usage: locations_filename.json')

    loc_map_filename = argv[0]

    with open(loc_map_filename) as loc_map_f:
        loc_map = json.load(loc_map_f)

    city_region_country_num = 0
    region_country_num = 0
    country_num = 0

    for origin_loc, result_loc in loc_map.items():
        city = ''
        region = ''
        country = ''
        if lh.CityKey in result_loc:
            city = result_loc[lh.CityKey]
        if lh.RegionKey in result_loc:
            region = result_loc[lh.RegionKey]
        if lh.CountryKey in result_loc:
            country = result_loc[lh.CountryKey]

        if city and region and country:
            city_region_country_num += 1
        elif region and country:
            region_country_num += 1
        elif country:
            country_num += 1


    print('City, region and country number: %d' % city_region_country_num)
    print('Region and country number: %d' % region_country_num)
    print('Country number: %d' % country_num)


if __name__ == "__main__":

    main(sys.argv[1:])
