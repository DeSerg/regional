"""
Модуль для поиска по .xml корпусу по словоформам из словаря Руслана.

#NOTE: Содержит в себе вспомогательный класс RegionalWords и публичный метод
       normalize, которыe стоит вынести в отдельный файл.
"""

import re
import sys
import json

import utility.huge_file_processor as hfp
import regional_dict.regional_dict_helper as dh


class RegionalSearch:
    def __init__(self, filename):
        self.filename = filename
        hfp.process_data = self.process_data
        self.text_data = {'errors': []}
        self.author_data = {}
        self.debug = True

    def search(self, word_forms, chunk_size):
        self._make_word_forms_dict(word_forms)
        hfp.process_hugefile(self.filename, chunk_size)

    def save(self, text_save_filename, author_save_filename):
        with open(text_save_filename, 'w') as outfile:
            json.dump(self.text_data, outfile, ensure_ascii=False)
        with open(author_save_filename, 'w') as outfile:
            json.dump(self.author_data, outfile, ensure_ascii=False)

    def process_data(self, lines_piece, **kwargs):
        try:
            self.process(lines_piece)
        except:
            e = sys.exc_info()[0]
            self.text_data['errors'].append(e)

            if self.debug is True:
                raise

    def process(self, lines_piece):
        for ind, line in enumerate(lines_piece):
            line = line.strip()
            if line.startswith('<text'):
                self.current_header = line
                if extract_field(line, "source", "NA") == "lj":
                    self.current_author = extract_field(line, "author", "NA")
                else:  # vkontakte
                    self.current_author = extract_field(line, "id", "NA")
                self.current_loc = extract_field(line, "loc", "NA")
                self.current_regional_words = []
                self.current_words_count = 0
            elif line.startswith('</text>'):
                if len(self.current_regional_words) > 0:
                    pass
                # assuming every header appears only once
                self.text_data[self.current_header] =\
                    {'regional_words': self.current_regional_words,
                     'length': self.current_words_count}
                if self.current_author not in self.author_data:
                    self.author_data[self.current_author] =\
                        {'count': 0, 'loc': self.current_loc, 'text count' : 0}
                self.author_data[self.current_author]['count'] += self.current_words_count
                self.author_data[self.current_author]['text count'] += 1
            word = dh.standartize(line.split('\t')[0])
            normalized = dh.normalize(word)
            if dh.CyrillicPattern.match(normalized):
                self.current_words_count += 1
                if word in self.word_forms_dict:
                    self.current_regional_words.append(word)
                elif normalized in self.word_forms_dict:
                    self.current_regional_words.append(normalized)

    def _make_word_forms_dict(self, word_forms):
        self.word_forms_dict = word_forms


def extract_field(line, field, default=None):
    found = re.search('{0}="(.*?)"'.format(field), line)
    if found:
        return found.groups(1)[0]
    else:
        return default

def run(args):
    if len(args) < 5:
        sys.exit("Pass filename, dict_filename, save_filename for texts,"
                 "save_filename for authors, chunk size")
    filename = args[0]
    dict_filename = args[1]
    text_save_filename = args[2]
    author_save_filename = args[3]
    chunk_size = float(args[4])

    rw = dh.RegionalWords(dict_filename)
    rs = RegionalSearch(filename)
    rs.search(rw.word_forms(), chunk_size)
    rs.save(text_save_filename, author_save_filename)
