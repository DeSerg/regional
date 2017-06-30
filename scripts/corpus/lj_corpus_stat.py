import sys
import json
import re
import pandas as pd
from xml.etree import cElementTree as ET

sys.path.insert(0, '..')

import regional_dict.regional_dict_helper as rdh
import location_utils.location_helper as lh
import corpus.corpus_helper as ch


def mapped_locations_toponims_utf8_stat(toponims_utf8_filename):
    df = pd.read_csv(toponims_utf8_filename, '\t')

    locs_map = set()
    for _, record in df.iterrows():
        # author_loc = record[['author_name']].to_string(index=False, header=False, na_rep='') for pandas 0.18
        author_loc = record[['author_name']].str
        locs_map.add(author_loc)

    print(len(locs_map))
    print(locs_map[:40])

    authors_mapped = 0
    for filename_num, (corpus_filename, total_num_lines) in enumerate(ch.CorpusFiles):
        with open(corpus_filename) as corpus_f:
            for line_num, line in enumerate(corpus_f):

                success, locs_set = ch.extract_raw_locs_from_line(line)
                if not success:
                    continue

                found = False
                for loc in locs_set:
                    loc_split = loc.split(lh.ToponimSeparator)
                    for toponim in loc_split:
                        if toponim in locs_map:
                            found = True

                if found:
                    authors_mapped += 1

                ch.print_progress(line_num, total_num_lines, corpus_filename, filename_num)

    print('\n\nAuthors with toponmis-utf8 mapped location: %d\n\n' % authors_mapped)


# number of authors with location which was successfully mapped by standartificator
def mapped_locations_stat(locations_map):

    authors_mapped = 0
    for filename_num, (corpus_filename, total_num_lines) in enumerate(ch.CorpusFiles):
        with open(corpus_filename) as corpus_f:
            for line_num, line in enumerate(corpus_f):
                success, login, location, texts = ch.extract_data_from_line(line, locations_map)
                if not success:
                    continue

                authors_mapped += 1

                ch.print_progress(line_num, total_num_lines, corpus_filename, filename_num)

    print('Authors with mapped location: %d' % authors_mapped)


def mapped_locations_stat_country_only(locations_map, regions_filename):
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


def mapped_locations_stat_certain(locations_map_filename, regions, countries):

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
        json.dump(locs_map_out, out_f, ensure_ascii=False)


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

    print('\n\nNumber of authors with location: %d\n\n' % authors_with_region)


# number of authors, texts, texts with regional words in countries
def mapped_country_region_stat_regional(locations_map, regional_dict, out_filename):

    countries = {} # authors_num, regional_texts_num

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
            regional_texts_num = country_stat[1]
            out_f.write('%s: %s, %f\n' % (country, authors_num, regional_texts_num / authors_num))

    with open(out_filename, 'w') as out_f:
        countries_list = [(country, value) for country, value in countries.items()]
        countries_list.sort(key=lambda x: x[1][0], reverse=True)
        for country, country_stat in countries_list:
            authors_num = country_stat[0]
            regional_texts_num = country_stat[1]
            out_f.write('%s: %s, %f\n' % (country, authors_num, regional_texts_num / authors_num))


# number of authors in locations with countries only
def mapped_country_only_stat(locations_map):

    countries = {} # authors_num, regional_words_num
    authors_mapped = 0

    for filename_num, (corpus_filename, total_num_lines) in enumerate(ch.CorpusFiles):
        with open(corpus_filename) as corpus_f:
            for line_num, line in enumerate(corpus_f):
                success, login, location, texts = ch.extract_data_from_line(line, locations_map)
                if not success:
                    continue
                if (lh.CityKey not in location) and (lh.RegionKey not in location) and (lh.CountryKey in location):
                    country = location[lh.CountryKey]
                    if not country in countries:
                        countries[country] = 1
                    else:
                        countries[country] += 1

                    authors_mapped += 1

                ch.print_progress(line_num, total_num_lines, corpus_filename, filename_num)

    check_sum = 0
    for country, num in countries.items():
        check_sum += num

    if check_sum != authors_mapped:
        print('fail: authors_mapped = %d, check_sum = %d' % (authors_mapped, check_sum))

    print('Authors with mapped location (only country): %d' % authors_mapped)
    for country, num in countries.items():
        print('%s: %d' % (country, num))


def main(argv):
    if len(argv) < 1:
        print('Usage: script.py stat_method locations_map.json regional_dict.xlsx locations_file.txt out_file')
        return

    stat_method = argv[0]

    if stat_method == 'mapped_locs_toponims_utf8':
        if len(argv) < 2:
            print('Usage: script.py mapped_locations_stat toponims-utf8.txt')
            return

        mapped_locations_toponims_utf8_stat(argv[1])

    elif stat_method == 'mapped_locs':
        if len(argv) < 2:
            print('Usage: script.py mapped_locations_stat locations_map.json')
            return

        location_map_filename = argv[1]
        locations_map = lh.load_locations_map(location_map_filename)

        mapped_locations_stat(locations_map)

    # location_map_filename = argv[0]
    # locations_map = lh.load_locations_map(location_map_filename)
    #
    # regional_dict_filename = argv[1]
    # rw = rdh.RegionalWords(regional_dict_filename)
    # regional_dict = rw.word_forms()
    #
    # locations_filename = argv[2]
    # regions, countries = lh.parse_classification_locations(locations_filename)
    #
    # out_filename = argv[3]
    #
    # mapped_country_only_stat(locations_map)
    # mapped_region_stat_regional(locations_map, regional_dict, regions, countries, out_filename)


if __name__ == "__main__":
    main(sys.argv[1:])
