import sys
import json
import re
from xml.etree import cElementTree as ET

sys.path.insert(0, '..')

import regional_dict.regional_dict_helper as rdh
import location_utils.location_helper as lh
import corpus.corpus_helper as ch


def parse_line(line_num, line, locations_map, regional_dict, corpus_for_classification, map_loc=True):

    line_split = line.split(' ', 1)
    if len(line_split) != 2:
        print('Line without author?\n%s\n' % line)
        return
    author_login, data = line_split[0], line_split[1]

    # Location
    locations = lh.corpus_loc_re.findall(data)
    locations = [lh.extract_location(loc) for loc in locations]

    author_data = {}

    if map_loc:
        if not locations:
            return

        loc_set = set(locations)
        max_loc = locations[0]
        max_count = locations.count(locations[0])
        for location in loc_set:
            count = locations.count(location)
            if count > max_count:
                max_loc = location
                max_count = count

        if not max_loc in locations_map:
            return

        author_location = locations_map[max_loc]

        if not lh.RegionKey in author_location and not lh.CountryKey in author_location:
            return
        if lh.CityKey in author_location:
            author_data[lh.CityKey] = author_location[lh.CityKey]
        if lh.RegionKey in author_location:
            author_data[lh.RegionKey] = author_location[lh.RegionKey]
        if lh.CountryKey in author_location:
            author_data[lh.CountryKey] = author_location[lh.CountryKey]


    # Text
    texts = lh.corpus_text_re.findall(line)
    texts = [re.sub(lh.xml_re, '', text) for text in texts]

    author_data[lh.TextsLenKey] = sum([len(text) for text in texts])
    author_data[lh.NegativeTextsNumKey], author_data[lh.PositiveTextsKey] = ch.count_regional_words(texts, regional_dict)

    corpus_for_classification[author_login] = author_data


def main(argv):
    if len(argv) < 4:
        print('Usage: %s locations_map.json regional_dictionary.xlsx out_corpus_for_classification.json [map_loc|no_map]' % argv[0])
        return

    with open(argv[1]) as locations_map_f:
        locations_map = json.load(locations_map_f)

    rw = rdh.RegionalWords(argv[2])
    regional_dict = rw.word_forms()

    out_data_filename = argv[3]

    map_loc = True
    if len(argv) > 4:
        map_loc_str = argv[4]
        if map_loc_str == 'no_map':
            map_loc = False

    corpus_for_classification = {}
    for file_num, (corpus_filename, total_num_lines) in enumerate(ch.CorpusFiles):
        with open(corpus_filename) as corpus_f:
            for line_num, line in enumerate(corpus_f):
                parse_line(line_num, line, locations_map, regional_dict, corpus_for_classification, map_loc)
                ch.print_progress(line_num, total_num_lines, corpus_filename, file_num)

    with open(out_data_filename, 'w') as out_data_f:
        json.dump(corpus_for_classification, out_data_f, ensure_ascii=False, indent=0)


if __name__ == "__main__":
    main(sys.argv)
