"""
Модуль для извлечения текстовых данных из xml корпуса (слово, синтаксис, лемма)
"""

import numpy as np
import re
import sys
import json
import os

import utility.huge_file_processor as hfp
import utility.helpers as helper


class ContentExtractor:
    CACHE_CLEAR_COUNT = 3

    def __init__(self, ids_data, basic_filename):
        self.ids_data = ids_data
        hfp.process_data = self.process_data
        self.content_data = {'errors': []}
        self.id_regexp = re.compile('id="(.*?)"')
        self.basic_filename = basic_filename

        self.cache_counter = 0
        self.filenames = []

    def extract(self, filename, chunk_size):
        hfp.process_hugefile(filename, chunk_size)
        self.filenames.append(self._cache_filename())
        self.save(self._cache_filename())

    def process_data(self, lines_piece, **kwargs):
        self.process(lines_piece)
        self.cache_counter += 1
        self._save_and_clear_cache()

    def process(self, lines_piece):
        for ind, line in enumerate(lines_piece):
            try:
                if line[0:5] == '<text':
                    id = self.id_regexp.search(line).groups()[0]
                    if id in self.ids_data:
                        end_ind = self._find_close_text_tag(lines_piece, ind)
                        content = lines_piece[ind+1:end_ind-1]
                        self.content_data[id] = content
            except Exception as e:
                self.content_data['errors'].append([str(e), line])

    def save(self, save_filename):
        helper.json_save(save_filename, self.content_data)

    def _save_and_clear_cache(self):
        if self.cache_counter > 0 and self.cache_counter % self.CACHE_CLEAR_COUNT == 0:
            self.filenames.append(self._cache_filename())
            self.save(self._cache_filename())
            self.content_data = {'errors': []}

    def _cache_filename(self):
        return "{0}.{1}".format(self.basic_filename, self.cache_counter)

    def _find_close_text_tag(self, lines_piece, ind):
        end_ind = None
        delta = len(lines_piece) - ind
        for j in range(1, delta):
            end_ind = ind + j
            if lines_piece[end_ind][0:7] == '</text>':
                return end_ind
        return None


def run(args):
    if len(args) < 4:
        sys.exit("pass json data with keys, corpora xml, chunk size \
                  and save filename")
    ids_data_filename = args[0]
    corpora_filename = args[1]
    chunk_size = int(args[2])
    save_filename = args[3]

    ids_data = set(json.load(open(ids_data_filename, 'r')).keys())

    content_extractor = ContentExtractor(ids_data, save_filename)
    content_extractor.extract(corpora_filename, chunk_size)

    print(len(content_extractor.content_data['errors']), len(content_extractor.content_data))

    unioned_jsons = helper.union_jsons(content_extractor.filenames)
    helper.json_save(save_filename, unioned_jsons)

    for filename in content_extractor.filenames:
        os.remove(filename)
