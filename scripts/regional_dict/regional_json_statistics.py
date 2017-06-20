# -*-: coding: utf8 -*-
"""
Модуль для подсчета статистик
"""


import ujson as json
import sys
import pandas as pd

from copy import deepcopy
from itertools import chain
from collections import defaultdict

import regional_dict.regional_collect as rc
import location_utils.locations_mapper_dict as lm

NA_locations = set()

class BasicStatistics:
    '''
    Базовый класс для статистики, собираемой по текстам и по авторам
    '''
    def __init__(self, dictfile, location_map_file):
        self.dictfile = dictfile
        self.location_map_file = location_map_file
        self.lemma_statistics = defaultdict(dict)
        self.regional_lemma_statistics = defaultdict(dict)
        self.region_statistics = dict()

    def preprocess(self):
        '''
        Инициализируем лемматизатор для региональных слов по словарю
        '''
        self.lemmatizer = rc.RegionalWords(self.dictfile)
        self._locs_keys = set(self.lemmatizer.locs_list())
        # инициализируем отображение локаций
        self.location_mapper = lm.LocationsMapper(self.location_map_file)
        self.location_mapper.initialize()
        return self

    def dump(self, words_outfile, regional_words_outfile, regions_outfile):
        dump_dict(words_outfile, self.lemma_statistics)
        dump_dict(regional_words_outfile, self.regional_lemma_statistics)
        with open(regions_outfile, "w") as fout:
            json.dump(self.region_statistics, fout, ensure_ascii=False)

    def _get_region(self, loc):
        region = self.location_mapper.get_region(loc)
        if region == "NA":
            for loc_segment in loc.split(","):
                region = self.location_mapper.get_region(loc_segment)
                if region != "NA":
                    break
        if region == "Россия":
            region = "NA"
        return region


class RegionalWordStatistics(BasicStatistics):
    def __init__(self, dictfile, location_map_file, minimal_words_count):
        BasicStatistics.__init__(self, dictfile, location_map_file)
        self.minimal_words_count = minimal_words_count

    DEFAULTDICT = {'texts': 0, 'authors': 0, 'words': 0,
                   'long_texts': 0, 'long_texts_authors': 0,
                   'long_texts_words': 0, 'first_text_words': 0}

    def process_file(self, infile, mode='line'):
        '''
        Аргументы:
        ----------
        infile --- входной файл в формате .json,
        mode --- режим чтения ('line' или 'all')
        '''
        if mode not in ['line', 'all']:
            sys.exit("Reading mode should be 'line' or 'all'")
        if mode == 'line':
            with open(infile, "r") as fin:
                last_author, had_long_texts_before, is_first_long_text = None, False, False
                for i, line in enumerate(fin):
                    if i % 500000 == 0:
                        print(i)
                    line = line.strip()
                    line = line.strip(",")
                    if '{' not in line:
                        continue
                    elem = json.loads(line)
                    # loc
                    loc = elem.get('loc', 'NA')
                    region = self._get_region(loc)
                    if region == "NA":
                        NA_locations.add(loc)
                    author = elem.get('author', None) # author
                    is_new_author = (author != last_author)
                    length = elem.get('length')
                    is_long_text = (length >= self.minimal_words_count)
                    lemma_counts = elem.get('words')
                    regional_lemma_counts = elem.get('regional_words')
                    # проверяем, является ли текст первым для данного автора
                    if is_new_author:
                        had_long_texts_before = False
                        current_author_words = set()
                        current_author_regional_words = set()
                        long_current_words = set()
                        long_current_regional_words = set()
                    if not had_long_texts_before and is_long_text:
                        is_first_long_text = True
                        had_long_texts_before = True
                    else:
                        is_first_long_text = False
                    # обновление статистики для региона
                    current_region_statistics = self.region_statistics.get(region, None)
                    if current_region_statistics is None:
                        self.region_statistics[region] = deepcopy(self.DEFAULTDICT)
                        current_region_statistics = self.region_statistics[region]
                    self._update_current_region_statistics(current_region_statistics, length, is_new_author,
                                                           is_long_text, is_first_long_text, is_first_long_text)
                    # обновление статистики по словам
                    self._update_word_statistics(
                            'lemma_statistics', region, lemma_counts,
                            current_author_words, long_current_words,
                            is_long_text, is_first_long_text)
                    self._update_word_statistics(
                            'regional_lemma_statistics', region,
                            regional_lemma_counts, current_author_regional_words,
                            long_current_regional_words, is_long_text, is_first_long_text)
                    last_author = author

    def _update_current_region_statistics(self, stats_dict, length, is_new_author,
                                          is_long_text, is_first_long_text,
                                          is_first_long_text_for_word):
        '''
        Обновление статистики для текущего региона
        '''
        stats_dict['texts'] += 1
        stats_dict['authors'] += int(is_new_author)
        stats_dict['words'] += length
        stats_dict['long_texts'] += int(is_long_text)
        stats_dict['long_texts_authors'] += int(is_first_long_text_for_word)
        if is_long_text:
            stats_dict['long_texts_words'] += length
        if is_first_long_text:
            stats_dict['first_text_words'] += length
        return

    def _update_word_statistics(self, key, region, counts, words_set, words_set_long,
                                is_long_text, is_first_long_text):
        '''
        Обновление статистики по словам
        '''
        stats = getattr(self, key)
        for word, count in counts.items():
            word_stats = stats[word]
            if region not in word_stats:
                word_stats[region] = deepcopy(self.DEFAULTDICT)
            if word in words_set:
                is_new_author = False
            else:
                is_new_author = True
                words_set.add(word)
            if word in words_set_long:
                is_new_author_long = False
            else:
                is_new_author_long = True
                words_set_long.add(word)
            self._update_current_region_statistics(
                    word_stats[region], count, is_new_author,
                    is_long_text, is_first_long_text, is_new_author_long)
        return

class RegionalAuthorsStatistics(BasicStatistics):
    '''
    Класс-обработчик для статистики по авторам
    '''
    def __init___(self, dictfile, location_map_file):
        BasicStatistics.__init__(self, dictfile, location_map_file)

    DEFAULTDICT = {'texts': 0, 'authors': 0, 'words': 0}

    def process_file(self, infile, mode='line'):
        '''
        Аргументы:
        ----------
        infile --- входной файл в формате .json,
        mode --- режим чтения ('line' или 'all')
        '''
        if mode not in ['line', 'all']:
            sys.exit("Reading mode should be 'line' or 'all'")
        if mode == 'line':
            with open(infile, "r") as fin:
                for i, line in enumerate(fin):
                    if i % 10000 == 0:
                        print(i)
                    line = line.strip()
                    line = line.strip(",")
                    if ':' not in line: #first or last line
                        continue
                    pos = line.find(':')
                    author, elem = line[:pos], line[pos+1:]
                    elem = json.loads(elem.strip())
                    # loc
                    loc = elem.get('loc', 'NA')
                    region = self._get_region(loc)
                    if region == "NA":
                        NA_locations.add(loc)
                    author = elem.get('author', None) # author
                    length = elem.get('words_count')
                    texts_count = elem.get('texts_count')
                    lemma_counts = elem.get('words')
                    regional_lemma_counts = elem.get('regional_words')
                    # проверяем, является ли текст первым для данного автора
                    # обновление статистики для региона
                    current_region_statistics = self.region_statistics.get(region, None)
                    if current_region_statistics is None:
                        self.region_statistics[region] = deepcopy(self.DEFAULTDICT)
                        current_region_statistics = self.region_statistics[region]
                    self._update_current_region_statistics(current_region_statistics, length, texts_count)
                    # обновление статистики по словам
                    self._update_word_statistics('lemma_statistics', region, lemma_counts)
                    self._update_word_statistics('regional_lemma_statistics', region,
                                                 regional_lemma_counts)

    def _update_current_region_statistics(self, stats_dict, length, texts_number):
        '''
        Обновление статистики для текущего региона
        '''
        stats_dict['texts'] += texts_number
        stats_dict['authors'] += 1
        stats_dict['words'] += length
        return

    def _update_word_statistics(self, key, region, counts):
        '''
        Обновление статистики по словам
        '''
        stats = getattr(self, key)
        for word, count in counts.items():
            word_stats = stats[word]
            if region not in word_stats:
                word_stats[region] = deepcopy(self.DEFAULTDICT)
            # в файле для авторов не сохраняется число текстов,
            # в которые входит данное слово
            self._update_current_region_statistics(word_stats[region], count, 0)
        return


def extract_loc(loc, admissible_locs):
    '''
    returns loc if loc is a standartized loc (Москва->Москва)
    returns standartized loc if loc contains standartized loc as in (Москва, Россия->Москва),
    returns loc, otherwise
    '''
    if loc in admissible_locs:
        return loc
    for loc_segment in loc.split(","):
        if loc_segment.strip() in admissible_locs:
            return loc_segment.strip()
    return loc

# используется в других модулях, поэтому вынесено из класса
def make_admissible_locations(standard_locs, add_locs_filename):
    admissible_locs = defaultdict(list)
    for key in standard_locs:
        admissible_locs[key] = [key]
    additional_locs_map = pd.read_csv(add_locs_filename, sep='\t', header=0)
    for loc, general_loc in zip(list(additional_locs_map['Подрегион']),
                                list(additional_locs_map['Регион'])):
        admissible_locs[loc].append(general_loc)
    return admissible_locs

def dump_dict(outfile, dictionary):
    with open(outfile, "w") as fout:
        fout.write("{\n")
        for word, elem in sorted(dictionary.items(),
                                 key=(lambda x: x[0])):
            fout.write("{0}: {1},\n".format(word, json.dumps(elem, ensure_ascii=False)))
        fout.write("}\n")
    return



def run(args):
    if len(args) == 0 or args[0] not in ['authors', 'texts']:
        sys.exit("Pass 'text' or 'authors' mode")
    mode, args = args[0], args[1:]
    if mode == 'texts':
        if len(args) != 7:
            sys.exit("Pass mode ('texts' or 'authors'), json file, dict filename, location map filename, "
                     "minimal number of words for an author, outfile "
                     "for words statistics, outfile for regional words statistics, "
                     "outfile for locs statistics")
        infile, dictfile, locsfile, minimal_words_count,\
                words_outfile, regional_words_outfile, locs_outfile = args
        minimal_words_count = int(minimal_words_count)

        rws = RegionalWordStatistics(dictfile, locsfile, minimal_words_count)

    elif mode == 'authors':
        if len(args) != 6:
            sys.exit("Pass mode ('texts' or 'authors'), json file, dict filename, "
                     "location map filename,  outfile for words statistics, "
                     "outfile for regional words statistics,  outfile for locs statistics")
        infile, dictfile, locsfile, words_outfile, regional_words_outfile, locs_outfile = args
        rws = RegionalAuthorsStatistics(dictfile, locsfile)
    rws.preprocess()
    rws.process_file(infile)
    rws.dump(words_outfile, regional_words_outfile, locs_outfile)
    print(sorted(NA_locations))



if __name__ == "__main__":
    run()
