import sys
import json
from pprint import pprint

def main(argv):
    if len(argv) < 1:
        print('Usage: locations_filename.txt')

    locations_filename = argv[0]


    locations_map = {}
    # string -> {city: string, region: string, country: string}
    CityKey     = 'city'
    RegionKey   = 'region'
    CountryKey  = 'country'
    with open(locations_filename) as locations_file:
        for line in locations_file:
            line_split = line.split('\t\t')
            if len(line_split) != 2:
                print('Bad line:\n %s\n' % line)
            origin_loc = line_split[0]
            stand_loc_split = line_split[1].split(';')
            stand_loc_split = [loc.split(':') for loc in stand_loc_split]

            stand_loc_map = {}
            for loc_split in stand_loc_split:
                if len(loc_split) != 2:
                    print('Bad location: %s' % origin_loc)
                    continue
                stand_loc_map[loc_split[0].strip()] = loc_split[1].strip()

            locations_map[origin_loc] = stand_loc_map

    regions_set = set()

    for origin_loc, stand_loc in locations_map.items():
        if RegionKey in stand_loc:
            regions_set.add(stand_loc[RegionKey])

    print('Total loc number : %d' % len(locations_map))
    print('Unique regions   : %d' % len(regions_set))

    with open('../../data/lj/locations_map.json', 'w') as loc_map_json:
        json.dump(locations_map, loc_map_json, ensure_ascii=False)


if __name__ == "__main__":

    main(sys.argv[1:])
