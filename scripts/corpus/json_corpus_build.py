import sys
import json
import re
from xml.etree import cElementTree as ET

sys.path.insert(0, '..')

import regional_dict.regional_collect as rc
import location_utils.location_helper as lh
import corpus.corpus_helper as ch


def parse_line(line_num, line, locations_map, regional_dict, corpus_for_classification):

    line_split = line.split(' ', 1)
    if len(line_split) != 2:
        print('Line without author?\n%s\n' % line)
        return
    author_login, data = line_split[0], line_split[1]

    # Location
    locations = lh.corpus_loc_re.findall(data)
    locations = [lh.extract_location(loc) for loc in locations]

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


    author_data = {}

    if not max_loc in locations_map:
        return
    author_location = locations_map[max_loc]
    if not lh.RegionKey in author_location and not lh.CountryKey in author_location:
        return
    if lh.RegionKey in author_location:
        author_data[lh.RegionKey] = author_location[lh.RegionKey]
    if lh.CountryKey in author_location:
        author_data[lh.CountryKey] = author_location[lh.CountryKey]

    # Text
    texts = lh.corpus_text_re.findall(line)
    texts = [re.sub(lh.xml_re, '', text) for text in texts]
    if sum([len(text) for text in texts]) < ch.MinTextLen:
        return

    author_data[lh.NegativeTextsNumKey], author_data[lh.PositiveTextsKey] = ch.count_regional_words(texts, regional_dict)

    corpus_for_classification[author_login] = author_data


def main(argv):
    if len(argv) < 4:
        print('Usage: %s locations_map.json regional_dictionary.xlsx out_corpus_for_classification.json' % argv[0])

    with open(argv[1]) as locations_map_f:
        locations_map = json.load(locations_map_f)

    rw = rc.RegionalWords(argv[2])
    regional_dict = rw.word_forms()

    out_data_filename = argv[3]

    corpus_for_classification = {}
    for corpus_filename, total_num_lines in ch.CorpusFiles:
        with open(corpus_filename) as corpus_f:
            for line_num, line in enumerate(corpus_f):
                parse_line(line_num, line, locations_map, regional_dict, corpus_for_classification)
                ch.print_progress(line_num, total_num_lines, corpus_filename)

    with open(out_data_filename, 'w') as out_data_f:
        json.dump(corpus_for_classification, out_data_f, ensure_ascii=False, indent=0)




if __name__ == "__main__":
    main(sys.argv)
