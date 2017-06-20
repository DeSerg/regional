'''
Подготовка json-файла, поступающего на вход региональному классификатору
'''

import sys
import json

sys.path.insert(0, '/Users/deserg/Google Drive/MIPT/Regional/classification/scripts')
import regional_dict.regional_search as rs
import regional_dict.regional_json_statistics as rjs

class RegionalClassifierJsonPreprocessor:

    def __init__(self, dict_filename, add_locs_filename, minimal_words_number):
        self.lemmatizer = rs.RegionalWords(dict_filename)
        self.locs_keys = self.lemmatizer.locs_list()
        self.admissible_locs =\
            rjs._make_admissible_locations(self.locs_keys, add_locs_filename)
        self.minimal_words_number = minimal_words_number
        self.UNKNOWN_LENGTH = -1

    def process(self, source_filename, author_filename, output_filename):
        json_data = json.load(open(source_filename, 'r'))
        author_data = json.load(open(author_filename, 'r'))
        output_data = dict()
        has_regional_words = dict()
        for m, (id, elem) in enumerate(json_data.items(), 1):
            if m % 100000 == 0:
                print (m)
            if not elem:
                continue
            loc = rjs.extract_loc(elem.get('loc', 'NA'), self.admissible_locs)
            city, words = elem.get('city', 'NA'), elem['regional_words']
            author = elem.get('author', None)
            length = elem.get('length', self.UNKNOWN_LENGTH)
            if loc in self.locs_keys and author is not None:
                if author_data[author]['count'] < self.minimal_words_number:
                    continue
                try:
                    current_author_data = output_data[author]
                except KeyError:
                    output_data[author] = {'loc': loc, 'texts' : []}
                    current_author_data = output_data[author]
                if len(words) > 0:
                    current_author_data['texts'].append(words)
        for author, elem in author_data.items():
            loc = rjs.extract_loc(elem.get('loc', 'NA'), self.admissible_locs)
            text_count, count = elem.get('text count'), elem.get('count')
            if loc not in self.locs_keys or count < self.minimal_words_number:
                continue
            try:
                current_author_data = output_data[author]
            except KeyError:
                output_data[author] = {'loc': loc, 'texts' : []}
                current_author_data = output_data[author]
            current_author_data['texts without regional'] =\
                text_count - len(current_author_data['texts'])
        with open(output_filename, "w") as outfile:
            json.dump(output_data, outfile, ensure_ascii=False)


def run(args):
    if len(args) != 6:
        sys.exit("Pass dict_file, additional_dict_file,\
                  minimal_words_number, source_json file, author_json_file and output_json_file")
    dict_filename, add_locs_filename, minimal_words_number, source, authors, output = args
    minimal_words_number = int(minimal_words_number)

    rsjp = RegionalClassifierJsonPreprocessor(dict_filename, add_locs_filename, minimal_words_number)
    rsjp.process(source, authors, output)

