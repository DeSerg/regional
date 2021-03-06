import re
import sys

sys.path.insert(0, '..')

import regional_dict.regional_dict_helper as rdh
import location_utils.location_helper as lh

CorpusFiles = [
    ('/data/kaa/compose/m.lj.compact/groups.txt', 146425),
    ('/data/kaa/compose/m.lj.compact5/groups.txt', 585704),
    ('/data/kaa/compose/m.lj.compactR/groups.txt', 732129)
]

MinTextLen = 5000


def extract_raw_locs_from_line(line):

    FailVal = (False, set())

    line_split = line.split(' ', 1)
    if len(line_split) != 2:
        print('Line without author?\n%s\n' % line)
        return FailVal

    author_login, data = line_split[0], line_split[1]

    # Location
    locations = lh.corpus_loc_re.findall(data)
    locations = [lh.extract_location(loc) for loc in locations]

    if not locations:
        return FailVal
    locs_set = set(locations)

    return True, locs_set


def extract_data_from_line(line, locations_map):

    FailVal = (False, '', '', '')

    line_split = line.split(' ', 1)
    if len(line_split) != 2:
        print('Line without author?\n%s\n' % line)
        return FailVal
    author_login, data = line_split[0], line_split[1]

    # Location
    locations = lh.corpus_loc_re.findall(data)
    locations = [lh.extract_location(loc) for loc in locations]

    if not locations:
        return FailVal
    loc_set = set(locations)
    loc_count_arr = [(loc, locations.count(loc)) for loc in locations]
    loc_count_arr.sort(key=lambda x: x[1], reverse=True)

    author_location = ''
    for loc, loc_count in loc_count_arr:
        if loc in locations_map:
            author_location = locations_map[loc]
            break

    if not author_location:
        return FailVal

    # Text
    texts = lh.corpus_text_re.findall(line)
    texts = [re.sub(lh.xml_re, '', text) for text in texts]

    return True, author_login, author_location, texts


# texts - list of texts written by author, regional_dict - mapping from regional words word forms to lemmas
def count_regional_words(texts, regional_dict):
    without_regional_words, regional_texts = 0, []
    for text in texts:
        text = text.strip()
        regional_list = []
        for word in text.split(' '):
            word = rdh.standartize(word)
            word = rdh.normalize(word)
            if word in regional_dict:
                regional_list.append(regional_dict[word])
        if regional_list:
            regional_texts.append(regional_list)
        else:
            without_regional_words += 1
    return without_regional_words, regional_texts


def print_progress(cur_line_num, total_line_num, cur_filename, filename_num=-1):
    progress = cur_line_num / total_line_num * 100
    if filename_num != -1:
        cur_filename = cur_filename + '(%d)' % (filename_num + 1)
    sys.stderr.write("%s: %d%%   \r" % (cur_filename, progress))
    sys.stderr.flush()
