import pandas as pd
import numpy as np
from copy import deepcopy
from itertools import chain
import re
import subprocess as sp

CyrillicPattern = re.compile(u"^[а-я]+([-][а-я]+)?$", re.I)

LEMMA_COLUMN = u'ЛЕММА'
WORDS_COLUMN = u'Список словоформ'
REGIONS_COLUMN = 'Standartized locations'
DB_REGIONS_COLUMN = 'Standartized db regions'
DB_COUNTRIES_COLUMN = 'Standartized db countries'

class RegionalWords:

    def __init__(self, filename):
        self.filename = filename
        self.excel_sheet = self._excel_sheet()

        self._word_forms_dict = {}
        self._lemma_locations = {}
        self._lemma_regions = {}
        self._lemma_countries = {}

        self._locs_list = []
        self._regions_list = []
        self._countries_list = []

    def word_forms(self):
        if not self._word_forms_dict:
            self._make_lemmatizer()
        return deepcopy(self._word_forms_dict)

    def locs_list(self):
        if not self._locs_list:
            self._locs_list = list(set(chain.from_iterable(self._make_lemma_locations().values())))
        return self._locs_list

    def regions_list(self):
        if not self._regions_list:
            self._regions_list = list(set(chain.from_iterable(self._make_lemma_regions().values())))
        return self._regions_list

    def countries_list(self):
        if not self._countries_list:
            self._countries_list = list(set(chain.from_iterable(self._make_lemma_countries().values())))
        return self._countries_list

    def lemma_locs(self, lemma):
        if not self._lemma_locations:
            self._make_lemma_locations()
        return deepcopy(self._lemma_locations.get(lemma, set()))

    def lemma_regions(self, lemma):
        if not self._lemma_regions:
            self._make_lemma_regions()
        return deepcopy(self._lemma_regions.get(lemma, set()))

    def lemma_countries(self, lemma):
        if not self._lemma_countries:
            self._make_lemma_countries()
        return deepcopy(self._lemma_countries.get(lemma, set()))

    def lemmatize(self, word):
        if not self._word_forms_dict:
            self._make_lemmatizer()
        return self._word_forms_dict.get(word, None)

    def _make_lemmatizer(self):
        self._word_forms_dict = dict(chain.from_iterable(
            [(standartize(word), lemma) for word in words.split(", ")]
            for lemma, words in zip(self.excel_sheet[LEMMA_COLUMN],
                                    self.excel_sheet[WORDS_COLUMN])
            if words is not np.nan))  # распознавание пустой ячейки

    def _make_lemma_locations(self):
        if not self._lemma_locations:
            self._lemma_locations = \
                dict((lemma, set(loc_str.split(', ')))
                     for lemma, loc_str in zip(self.excel_sheet[LEMMA_COLUMN],
                                               self.excel_sheet[REGIONS_COLUMN]))
        return self._lemma_locations

    def _make_lemma_regions(self):
        if not self._lemma_regions:
            self._lemma_regions = \
                dict((lemma, set(loc_str.split(';')))
                     for lemma, loc_str in zip(self.excel_sheet[LEMMA_COLUMN],
                                               self.excel_sheet[DB_REGIONS_COLUMN]))
        return self._lemma_regions

    def _make_lemma_countries(self):
        if not self._lemma_countries:
            self._lemma_countries = \
                dict((lemma, set(loc_str.split(';')))
                     for lemma, loc_str in zip(self.excel_sheet[LEMMA_COLUMN],
                                               self.excel_sheet[DB_COUNTRIES_COLUMN]))
        return self._lemma_countries

    def _excel_sheet(self):
        xlsx = pd.ExcelFile(self.filename)
        return xlsx.parse('Sheet1')

# RegionalWords from regional_search.py
#
#
# class RegionalWords:
#     LEMMA_COLUMN = u'ЛЕММА'
#     WORDS_COLUMN = u'Список словоформ'
#
#     def __init__(self, filename):
#         self.filename = filename
#         self.excel_sheet = self._excel_sheet()
#
#         self._word_forms_dict = {}
#         self._lemma_locations = {}
#         self._locs_list = []
#
#     def word_forms(self):
#         if not self._word_forms_dict:
#             self._make_lemmatizer()
#         return deepcopy(self._word_forms_dict)
#
#     def locs_list(self):
#         if not self._locs_list:
#             self._locs_list = set(chain.from_iterable(self._make_lemma_locations().values()))
#         return list(self._locs_list)
#
#     def lemma_locs(self, lemma):
#         if not self._lemma_locations:
#             self._make_lemma_locations()
#         return deepcopy(self._lemma_locations.get(lemma, set()))
#
#     def lemmatize(self, word):
#         if not self._word_forms_dict:
#             self._make_lemmatizer()
#         return self._word_forms_dict.get(word, None)
#
#     def _make_lemmatizer(self):
#         self._word_forms_dict = dict(chain.from_iterable(
#             [(normalize(standartize(word)), lemma) for word in words.split(", ")]
#             for lemma, words in zip(self.excel_sheet[RegionalWords.LEMMA_COLUMN],
#                                     self.excel_sheet[RegionalWords.WORDS_COLUMN])
#             if words is not np.nan)) # распознавание пустой ячейки
#
#     def _make_lemma_locations(self):
#         if not self._lemma_locations:
#             locations_column = 'Standartized locations'
#             self._lemma_locations =\
#                 dict((lemma, set(loc_str.split(', ')))
#                      for lemma, loc_str in zip(self.excel_sheet[RegionalWords.LEMMA_COLUMN],
#                                                self.excel_sheet[locations_column]))
#         return self._lemma_locations
#
#     def _excel_sheet(self):
#         xlsx = pd.ExcelFile(self.filename)
#         return xlsx.parse('Sheet1')


def standartize(word):
    return word.replace(u"ё", u"е")


def normalize(word):
    return word.lower()


def lemma(word):
    try:
        process = sp.Popen('echo "%s" | tnt-russian-nopipe-ext' % word, stdout=sp.PIPE, stderr=sp.PIPE, shell=True)
        out_byte, _ = process.communicate()
        # out_byte = sp.check_output('echo "%s" | tnt-russian-nopipe-ext' % word, shell=True)
        out = out_byte.decode("utf-8")
        for line in out.split('\n'):
            if line.startswith(word):
                line_split = line.split('\t')
                if len(line_split) > 2:
                    return True, line_split[2]
        return False, 'bad output'
    except Exception as ex:
        return False, str(ex)
