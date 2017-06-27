import sys
import json
import re
from xml.etree import cElementTree as ET
import matplotlib.pyplot as plt

sys.path.insert(0, '..')

import regional_dict.regional_dict_helper as rdh
import location_utils.location_helper as lh
import corpus.corpus_helper as ch

loc_files = [
    #('body.txt', 90)
    ('/data/kaa/compose/m.lj.compact/groups.txt', 146425),
    ('/data/kaa/compose/m.lj.compact5/groups.txt', 585704),
    ('/data/kaa/compose/m.lj.compactR/groups.txt', 732129)
]



def parse_line(line, locations_map, regions, countries, locs_map_out):

    line_split = line.split(' ', 1)
    if len(line_split) != 2:
        print('Line without author?\n%s\n' % line)
        return 0
    author_login, data = line_split[0], line_split[1]

    # Location
    locations = lh.corpus_loc_re.findall(data)
    locations = [lh.extract_location(loc) for loc in locations]

    if not locations:
        return 0
    loc_set = set(locations)
    max_loc = locations[0]
    max_count = locations.count(locations[0])
    for location in loc_set:
        count = locations.count(location)
        if count > max_count:
            max_loc = location
            max_count = count


    author_data = {}

    if not max_loc in locations_map:
        return 0
    author_location = locations_map[max_loc]
    if not lh.RegionKey in author_location and not lh.CountryKey in author_location:
        return 0

    if lh.RegionKey in author_location:
        region = author_location[lh.RegionKey]
        if region in regions:
            if region in locs_map_out:
                locs_map_out[region] += 1
            else:
                locs_map_out[region] = 1

    if lh.CountryKey in author_location:
        country = author_location[lh.CountryKey]
        if country in countries:
            if country in locs_map_out:
                locs_map_out[country] += 1
            else:
                locs_map_out[country] = 1

    return 1


# number of authors with location which was successfully mapped by standartificator
def mapped_region_stat(locations_map_filename, regions_filename):
    with open(locations_map_filename) as locations_map_f:
        locations_map = json.load(locations_map_f)
    regions, countries = lh.parse_classification_locations(regions_filename)

    authors_mapped = 0
    locs_map_out = {}
    for filename_num, (corpus_filename, total_num_lines) in enumerate(ch.CorpusFiles):
        with open(corpus_filename) as corpus_f:
            for line_num, line in enumerate(corpus_f):
                success, login, location, texts = ch.extract_data_from_line(line, locations_map)
                if not success:
                    continue

                if lh.RegionKey in location:
                    region = location[lh.RegionKey]
                    if region in regions:
                        if region in locs_map_out:
                            locs_map_out[region] += 1
                        else:
                            locs_map_out[region] = 1

                if lh.CountryKey in location:
                    country = location[lh.CountryKey]
                    if country in countries:
                        if country in locs_map_out:
                            locs_map_out[country] += 1
                        else:
                            locs_map_out[country] = 1

                authors_mapped += 1

                ch.print_progress(line_num, total_num_lines, corpus_filename, filename_num)

    print('Authors with region: %d' % authors_mapped)
    for loc, num in locs_map_out.items():
        print('%s: %d' % (loc, num))


# number of authors with regional texts and location which was successfully mapped by standartificator
def mapped_region_stat_regional(locations_map, regional_dict, regions, countries, out_filename):

    authors_mapped = 0
    locs_map_out = {}
    for filename_num, (corpus_filename, total_num_lines) in enumerate(ch.CorpusFiles):
        with open(corpus_filename) as corpus_f:
            for line_num, line in enumerate(corpus_f):
                success, login, location, texts = ch.extract_data_from_line(line, locations_map)
                if not success:
                    continue

                without_regional_words, regional_texts = ch.count_regional_words(texts, regional_dict)
                if not regional_texts:
                    continue

                if lh.RegionKey in location:
                    region = location[lh.RegionKey]
                    if region in regions:
                        if region in locs_map_out:
                            locs_map_out[region] += 1
                        else:
                            locs_map_out[region] = 1

                if lh.CountryKey in location:
                    country = location[lh.CountryKey]
                    if country in countries:
                        if country in locs_map_out:
                            locs_map_out[country] += 1
                        else:
                            locs_map_out[country] = 1

                authors_mapped += 1

                ch.print_progress(line_num, total_num_lines, corpus_filename, filename_num)

    print('Authors with location and regional text: %d' % authors_mapped)

    locs_map_list = [(location, loc_stat) for location, loc_stat in locs_map_out.items()]
    locs_map_list.sort(key=lambda x: x[1])

    with open(out_filename, 'w') as out_f:
        for loc_num, (loc, num) in enumerate(locs_map_list, 1):
            out_f.write('%d: %s: %d\n' % (loc_num, loc, num))

    with open(out_filename + '.json', 'w') as out_f:
        json.dump(locs_map_out, out_f)


# number of authors with location
def region_stat():
    authors_with_region = 0

    for filename_num, (corpus_filename, total_num_lines) in enumerate(ch.CorpusFiles):
        with open(corpus_filename) as corpus_f:
            for line_num, line in enumerate(corpus_f):
                line_split = line.split(' ', 1)
                if len(line_split) != 2:
                    print('Line without author?\n%s\n' % line)
                    return 0
                author_login, data = line_split[0], line_split[1]

                # Location
                locations = lh.corpus_loc_re.findall(data)
                if len(locations) > 0:
                    authors_with_region += 1

                ch.print_progress(line_num, total_num_lines, corpus_filename, filename_num)

    print('\n\n%d\n\n' % authors_with_region)


# number of authors, texts, texts with regional words in countries
def country_stat(locations_map, regional_dict, out_filename):

    countries = {} # authors_num, regional_words_num

    for filename_num, (corpus_filename, total_num_lines) in enumerate(ch.CorpusFiles):
        with open(corpus_filename) as corpus_f:
            for line_num, line in enumerate(corpus_f):
                success, login, location, texts = ch.extract_data_from_line(line, locations_map)
                if not success:
                    continue
                texts_joined = '\n'.join(texts)
                if (lh.RegionKey in location) and (lh.CountryKey in location) and (len(texts_joined) >= ch.MinTextLen):
                    country = location[lh.CountryKey]
                    without_regional_words, regional_texts = ch.count_regional_words(texts, regional_dict)
                    if not country in countries:
                        countries[country] = [1, len(regional_texts)]
                    else:
                        countries[country][0] += 1
                        countries[country][1] += len(regional_texts)

                ch.print_progress(line_num, total_num_lines, corpus_filename, filename_num)

    with open(out_filename + '_', 'w') as out_f:
        for country, country_stat in countries.items():
            authors_num = country_stat[0]
            regional_words_num = country_stat[1]
            out_f.write('%s: %s, %f\n' % (country, authors_num, regional_words_num / authors_num))

    with open(out_filename, 'w') as out_f:
        countries_list = [(country, value) for country, value in countries.items()]
        countries_list.sort(key=lambda x: x[1][0], reverse=True)
        for country, country_stat in countries_list:
            authors_num = country_stat[0]
            regional_words_num = country_stat[1]
            out_f.write('%s: %s, %f\n' % (country, authors_num, regional_words_num / authors_num))


def main(argv):
    if len(argv) < 4:
        print('Usage: script.py locations_map.json regional_dict.xlsx locations_file.txt out_file')
        return

    location_map_filename = argv[0]
    locations_map = lh.load_locations_map(location_map_filename)

    regional_dict_filename = argv[1]
    rw = rdh.RegionalWords(regional_dict_filename)
    regional_dict = rw.word_forms()

    locations_filename = argv[2]
    regions, countries = lh.parse_classification_locations(locations_filename)

    out_filename = argv[3]

    mapped_region_stat_regional(locations_map, regional_dict, regions, countries, out_filename)


if __name__ == "__main__":
    main(sys.argv[1:])
