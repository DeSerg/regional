import re
import json

CityKey = 'city'
RegionKey = 'region'
CountryKey = 'country'

NegativeTextsNumKey = 'negative texts num'
PositiveTextsKey = 'positive texts'

RussiaName = 'Russian Federation'

corpus_loc_re = re.compile('attr_\d+_Location="(.*?)"')
corpus_text_re = re.compile('<text>(.*?)</text>')
xml_re = re.compile('(<\w+>)|(</\w+>)|(<\w+/>)')

# " city , region  ,  country" => "city,region,country"
def extract_location(location):
    loc = location.split(',')

    if not loc:
        return ''

    loc = [s.strip() for s in loc]
    return ';'.join(loc)


def parse_classification_locations(locations_filename):
    regions = []
    countries = []
    with open(locations_filename) as locations_f:
        for line in locations_f:
            line = line.strip()
            if not line:
                continue
            line_split = line.split(': ')
            if len(line_split) != 2:
                print('bad loc: %s' % line)

            location = line_split[1]
            if not location:
                print('bad loc: %s' % location)
                continue

            if line_split[0] == RegionKey:
                regions.append(location)
            else:
                countries.append(location)

    return regions, countries


def load_locations_map(locations_map_filename):
    loc_map = {}
    with open(locations_map_filename) as loc_map_f:
        loc_map = json.load(loc_map_f)
    return loc_map