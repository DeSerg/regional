import sys
import json
import re
from xml.etree import cElementTree as ET

sys.path.insert(0, '..')

import regional_dict.regional_collect as rc
import locations.location_helper as lh

loc_files = [
    #('body.txt', 90)
    ('/data/kaa/compose/m.lj.compact/groups.txt', 146425),
    ('/data/kaa/compose/m.lj.compact5/groups.txt', 585704),
    ('/data/kaa/compose/m.lj.compactR/groups.txt', 732129)
]

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
    all_texts = '\n'.join(texts)
    if len(all_texts) < MinTextLen:
        return

    author_data[lh.NegativeTextsNumKey], author_data[lh.PositiveTextsKey] = analyze_texts(texts, regional_dict)

    corpus_for_classification[author_login] = author_data

def main(argv):
    if len(argv) < 4:
        print('Usage: %s locations_map.json regional_dictionary.xlsx out_corpus_for_classification.json' % argv[0])

    with open(argv[1]) as locations_map_f:
        locations_map = json.load(locations_map_f)

    rw = rc.RegionalWords(argv[2])
    regional_dict = rw.word_forms()

    out_data_filename = argv[3]


    global loc_files
    if len(argv) >= 5:
        loc_files = ([argv[4]], 1000)

    corpus_for_classification = {}
    for corpus_filename, total_num_lines in loc_files:
        with open(corpus_filename) as corpus_f:
            for line_num, line in enumerate(corpus_f):
                parse_line(line_num, line, locations_map, regional_dict, corpus_for_classification)

                progress = line_num / total_num_lines * 100
                sys.stderr.write("%s: %d%%   \r" % (corpus_filename, progress))
                sys.stderr.flush()

    with open(out_data_filename, 'w') as out_data_f:
        json.dump(corpus_for_classification, out_data_f, ensure_ascii=False, indent=0)




if __name__ == "__main__":
    main(sys.argv)