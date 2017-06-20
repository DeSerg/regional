# -*- coding: utf8 -*-
"""
Модуль для поиска по .xml корпусу по словоформам из словаря Руслана.

#NOTE: Содержит в себе вспомогательный класс RegionalWords и публичный метод
       normalize, которыe стоит вынести в отдельный файл.
"""

import pandas as pd
import numpy as np
import re
import sys
import statprof
# import ujson as json
# json._toggle_speedups(True)
from copy import deepcopy
from collections import defaultdict
from itertools import chain

import utility.huge_file_processor as hfp
import regional_dict.regional_dict_helper as dh



class RegionalCollectJson:
    def __init__(self, filename, minimal_words_number = -1):
        self.filename = filename
        self.minimal_words_number = minimal_words_number
        hfp.process_data = self.process_data
        self.errors_data = []
        self.debug = True
        self.has_started_dumping = False
        self.current_author = None

    def collect(self, word_forms, chunk_size, text_save_filename, author_save_filename):
        self._make_word_forms_dict(word_forms)
        self.ftext = open(text_save_filename, "w")
        self.fauth = open(author_save_filename, "w")
        hfp.process_hugefile(self.filename, chunk_size)
        if self.has_started_dumping:
            self._dump_author()
            self.ftext.write("\n]")
            self.fauth.write("\n}")
        self.ftext.close()
        self.fauth.close()


    def save(self, text_save_filename, author_save_filename):
        with open(text_save_filename, 'w') as outfile:
            json.dump(self.text_data, outfile, ensure_ascii=False)


    def process_data(self, lines_piece, **kwargs):
        try:
            self.process(lines_piece)
        except:
            e = sys.exc_info()[0]
            self.errors_data.append(e)
            if self.debug is True:
                raise

    def process(self, lines_piece):
        for ind, line in enumerate(lines_piece):
            line = line.strip()
            if line.startswith('<text'):
                self.current_header = line
                if extract_field(line, "source", "NA") == "lj":
                    current_author = extract_field(line, "author", "NA")
                else:  # vkontakte
                    current_author = extract_field(line, "id", "NA")
                self.current_loc = extract_field(line, "loc", "NA")
                if current_author != self.current_author:
                    if self.current_author is not None:
                        self._dump_author()
                    self._initialize_author_data()
                    self.current_author = current_author
                self.current_regional_words = defaultdict(int)
                self.current_words = defaultdict(int)
                self.current_words_count = 0
                self.current_regional_words_count = 0
            elif line.startswith('</text>'):
                # dumping current text
                current_data = {'header': self.current_header, 'words': self.current_words,
                                'regional_words': self.current_regional_words, 'length': self.current_words_count,
                                'regional_words_count': self.current_regional_words_count}
                # self.ftext.write("," if self.has_started_dumping else "[")
                # self.ftext.write(json.dumps(current_data, ensure_ascii=False))
                # self.has_started_dumping = True
                self.text_data.append(current_data)
                self.current_author_data['words_count'] += self.current_words_count
                self.current_author_data['regional_words_count'] += self.current_regional_words_count
                self.current_author_data['texts_count'] += 1
                for word, count in self.current_words.items():
                    self.current_author_data['words'][word] += count
                for word, count in self.current_regional_words.items():
                    self.current_author_data['regional_words'][word] += count
            elif line.startswith("<"):
                continue
            splitted_line = line.split('\t')
            if len(splitted_line) < 2:
                continue
            word, _, lemma = splitted_line[:3]
            word = dh.standartize(word)
            normalized = dh.normalize(word)
            if dh.CyrillicPattern.match(normalized):
                if word in self.word_forms_dict:
                    lemma = self.word_forms_dict[word]
                    self.current_regional_words_count += 1
                    self.current_regional_words[lemma] += 1
                elif normalized in self.word_forms_dict:
                    lemma = self.word_forms_dict[normalized]
                    self.current_regional_words_count += 1
                    self.current_regional_words[lemma] += 1
                self.current_words_count += 1
                self.current_words[lemma] += 1

    def _make_word_forms_dict(self, word_forms):
        self.word_forms_dict = word_forms

    def _initialize_author_data(self):
        self.current_author_data = {'loc': self.current_loc,
                                    'words': defaultdict(int), 'regional_words': defaultdict(int),
                                    'words_count': 0, 'texts_count': 0, 'regional_words_count': 0}
        self.text_data = []

    def _dump_author(self):
        if self.current_author_data['words_count'] >= self.minimal_words_number:
            self.fauth.write(", " if self.has_started_dumping else "{\n")
            self.fauth.write('"{0}": {1},\n'.format(self.current_author,
                                                 json.dumps(self.current_author_data, ensure_ascii=False)))
            self.ftext.write(",\n" if self.has_started_dumping else "[\n")
            self.ftext.write(",\n".join(json.dumps(elem, ensure_ascii=False) for elem in self.text_data))
            self.has_started_dumping = True

def extract_field(line, field, default=None):
    found = re.search('{0}="(.*?)"'.format(field), line)
    if found:
        return found.groups(1)[0]
    else:
        return default


def run(args):
    if len(args) not in [5, 6]:
        sys.exit("Pass filename, dict_filename, save_filename for texts,"
                 "save_filename for authors, chunk size"
                 "[and minimal number of words for an author]")
    filename, dict_filename, text_save_filename, author_save_filename, chunk_size = args[:5]
    minimal_words_number = int(args[5]) if len(args) == 6 else -1
    chunk_size = float(chunk_size)

    rw = dh.RegionalWords(dict_filename)
    rcj = RegionalCollectJson(filename, minimal_words_number)
    rcj.collect(rw.word_forms(), chunk_size, text_save_filename, author_save_filename)
