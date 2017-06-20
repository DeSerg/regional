'''
Модуль для вывода статистики.

Пока что сырой
'''

import pandas as pd
import numpy as np
import sys
import math
import csv
from itertools import chain, filterfalse, zip_longest
from collections import OrderedDict
from bisect import bisect, bisect_left, insort

import regional_dict.regional_search as rs
import regional_dict.regional_json_statistics as rjs
from locations import save_to_file


class RegionalStatsDemonstrator:

    def __init__(self, dict_filename, add_locs_filename, cross_table_filename, loc_table_filename):
        self.dict_filename = dict_filename
        self.add_locs_filename = add_locs_filename
        self.cross_table = pd.DataFrame.from_csv(cross_table_filename, sep='\t')
        self.loc_table = pd.DataFrame.from_csv(loc_table_filename, sep='\t')

        self.lemmatizer = rs.RegionalWords(dict_filename)
        self.locs_keys = self.lemmatizer.locs_list()
        self.admissible_locs =\
            rjs._make_admissible_locations(self.locs_keys, self.add_locs_filename)
        self.lemma_stats, self.loc_stats = OrderedDict(), {}

    def read_tables(self):
        self._read_cross_table()
        self._read_loc_table()

    def output_detailed(self, save_filename, top_lemmas_number, min_occs_number):
        ABSOLUTE_TOP_LENGTH, RELATIVE_TOP_LENGTH = 10, 20
        header_format_string = "{0:<12}{1:<24}{2:<6}{3:<14}{1:<24}{2:<6}{3:<14}\n"
        fillvalue = (None, None, None)
        if top_lemmas_number == -1:
            top_lemmas_number = len(self.lemma_stats)
        with open(save_filename, "w") as fout:
            for i, (lemma, stats) in zip(range(top_lemmas_number), self.lemma_stats.items()):
                expected_locs, other_locs = self._group_locs_for_lemma(lemma)
                expected_stats = dict(filter(lambda x: x[0] in expected_locs,
                                             stats['locs'].items()))
                other_stats = dict(filter(lambda x: x[0] in other_locs and x[1][0] > 0,
                                          stats['locs'].items()))

                # sorted by occurrences number
                fout.write(header_format_string.format(lemma, "Регион", "Вхожд", "Процент"))
                expected_output = sorted(
                    ((loc, val[0], (val[0] * 100 / stats['total']['count']) if val[0] > 0 else 0.0)
                     for loc, val in expected_stats.items()),
                    key=(lambda x: x[2]), reverse=True)
                min_value =\
                    max(1, 0.9 * (expected_output[-1][2] if len(expected_output) > 0 else 0))
                other_output = sorted(
                    ((loc, val[0], (val[0] * 100 / stats['total']['count']) if val[0] > 0 else 0.0)
                     for loc, val in other_stats.items() if val[0] >= min_value),
                    key=(lambda x: x[2]), reverse=True)
                for j, ((first_key, first_x, first_y), (second_key, second_x, second_y)) in\
                    zip(range(ABSOLUTE_TOP_LENGTH),
                        zip_longest(expected_output, other_output, fillvalue = fillvalue)):
                    fout.write("{0:<12}".format("") +
                               self._table_record_formatter(first_key, first_x, first_y) +
                               self._table_record_formatter(second_key, second_x, second_y) + "\n")
                fout.write("\n")

                # sorted by authors number
                fout.write(header_format_string.format("", "Регион", "Авт", "Процент"))
                expected_output = sorted(
                    ((loc, val[1],
                      (val[1] * 100 / stats['total']['authors count']) if val[1] > 0 else 0.0)
                     for loc, val in expected_stats.items()),
                    key=(lambda x: x[2]), reverse=True)
                min_value =\
                    max(1, 0.9 * (expected_output[-1][2] if len(expected_output) > 0 else 0))
                other_output = sorted(
                    ((loc, val[1],
                      (val[1] * 100 / stats['total']['authors count']) if val[1] > 0 else 0.0)
                     for loc, val in other_stats.items() if val[1] >= min_value),
                    key=(lambda x: x[2]), reverse=True)
                for j, ((first_key, first_x, first_y), (second_key, second_x, second_y)) in\
                    zip(range(ABSOLUTE_TOP_LENGTH),
                        zip_longest(expected_output, other_output, fillvalue = fillvalue)):
                    fout.write("{0:<12}".format("") +
                               self._table_record_formatter(first_key, first_x, first_y) +
                               self._table_record_formatter(second_key, second_x, second_y) + "\n")
                fout.write("\n")

                # sorted by occurrences percentage in case there are enough occurrences
                fout.write(header_format_string.format("", "Регион", "Вхожд", "Вхожд/100000"))
                unit_value = 100000
                expected_output = sorted(
                    ((loc, val[0],
                      (val[0] * unit_value / self.loc_stats[loc]['words']) if val[0] > 0 else 0.0)
                     for loc, val in expected_stats.items() if val[0] >= min_occs_number),
                    key=(lambda x: x[2]), reverse=True)
                min_value =\
                    max(0.0001, 0.9 * (expected_output[-1][2] if len(expected_output) > 0 else 0))
                other_output = sorted(
                    ((loc, val[0],
                      (val[0] * unit_value / self.loc_stats[loc]['words']) if val[0] > 0 else 0.0)
                     for loc, val in other_stats.items() if val[0] >= min_occs_number),
                    key=(lambda x: x[2]), reverse=True)
                if len(other_output) > 0:
                    index = bisect_left([elem[2] for elem in other_output][::-1], min_value)
                    other_output = other_output[:max(len(other_output) - index, 1)]
                for j, ((first_key, first_x, first_y), (second_key, second_x, second_y)) in\
                    zip(range(RELATIVE_TOP_LENGTH),
                        zip_longest(expected_output, other_output, fillvalue = fillvalue)):
                    fout.write("{0:<12}".format("") +
                               self._table_record_formatter(first_key, first_x, first_y) +
                               self._table_record_formatter(second_key, second_x, second_y) + "\n")
                fout.write("\n")

                # sorted by authors percentage in case there are enough authors
                fout.write(header_format_string.format("", "Регион", "Авт", "Авт/100"))
                unit_value = 100
                expected_output = sorted(
                    ((loc, val[1],
                      (val[1] * unit_value / self.loc_stats[loc]['authors']) if val[1] > 0 else 0.0)
                     for loc, val in expected_stats.items() if val[1] >= min_occs_number),
                    key=(lambda x: x[2]), reverse=True)
                min_value =\
                    max(0.0001, 0.9 * (expected_output[-1][2] if len(expected_output) > 0 else 0))
                other_output = sorted(
                    ((loc, val[1],
                      (val[1] * unit_value / self.loc_stats[loc]['authors']) if val[1] > 0 else 0.0)
                     for loc, val in other_stats.items() if val[1] >= min_occs_number),
                    key=(lambda x: x[2]), reverse=True)
                if len(other_output) > 0:
                    index = bisect_left([elem[2] for elem in other_output][::-1], min_value)
                    other_output = other_output[:max(len(other_output) - index, 1)]
                for j, ((first_key, first_x, first_y), (second_key, second_x, second_y)) in\
                    zip(range(RELATIVE_TOP_LENGTH),
                        zip_longest(expected_output, other_output, fillvalue = fillvalue)):
                    fout.write("{0:<12}".format("") +
                               self._table_record_formatter(first_key, first_x, first_y) +
                               self._table_record_formatter(second_key, second_x, second_y) + "\n")
                fout.write("\n\n")

    def output_separation(self, type, save_filename, top_lemmas_number, min_occs_number):
        if type not in ['words', 'authors']:
            raise ValueError("type should be 'words' or 'authors'")

        if type == 'words':
            index = 0
            unit_value = 100000
            header_string = u"{0:<24}{1:<6}{2:<14}".format("Регион", "Вхожд", "Процент")
        elif type == 'authors':
            index = 1
            unit_value = 100
            header_string = u"{0:<24}{1:<6}{2:<14}".format("Регион", "Авт", "Процент")

        if top_lemmas_number == -1:
            top_lemmas_number = len(self.lemma_stats)
        fillvalue = (None, None, None)

        with open(save_filename, "w") as fout:
            for i, (lemma, stats) in zip(range(top_lemmas_number), self.lemma_stats.items()):
                expected_locs, other_locs = self._group_locs_for_lemma(lemma)
                lemma_percentage = dict()
                for loc, counts in stats['locs'].items():
                    if loc not in expected_locs and loc not in other_locs:
                        continue
                    count = counts[index]
                    if count >= min_occs_number:
                        percentage = count * unit_value / self.loc_stats[loc][type]
                        lemma_percentage[loc] = percentage
                true_positives, false_positives, false_negatives = [], [], []
                if len(lemma_percentage) > 0:
                    threshold = _define_separation_threshold(lemma_percentage, expected_locs)
                    for loc, value in lemma_percentage.items():
                        if value >= threshold:
                            if loc in expected_locs:
                                true_positives.append((loc, value))
                            elif loc in other_locs:
                                false_positives.append((loc, value))
                        elif loc in expected_locs:
                            false_negatives.append((loc, value))
                tpc, fpc = len(true_positives), len(false_positives),
                fnc, tnc = len(false_negatives), len(other_locs) - len(false_negatives)
                # print (lemma, tpc, fpc, fnc, tnc)
                fout.write(u"{0:<12}{1:<4} {2:<4} {3:<4} {4:<4}\n".format(
                        lemma, tpc, fpc, fnc, tnc))
                if len(lemma_percentage) > 0:
                    fout.write("{0:<12}{1:<44}{2:<44}\n".format("", "True positives", "False positives"))
                    fout.write("{0:<12}{1}{1}\n".format("", header_string))
                    expected_output =\
                        [(loc, stats['locs'][loc][index], value)
                         for loc, value in sorted(true_positives, key = lambda x: x[1], reverse=True)]
                    other_output =\
                        [(loc, stats['locs'][loc][index], value)
                         for loc, value in sorted(false_positives, key = lambda x: x[1], reverse=True)]
                    for (first_key, first_x, first_y), (second_key, second_x, second_y) in\
                            zip_longest(expected_output, other_output, fillvalue = fillvalue):
                        fout.write("{0:<12}".format("") +
                                   self._table_record_formatter(first_key, first_x, first_y) +
                                   self._table_record_formatter(second_key, second_x, second_y) + "\n")
                    fout.write("{0:<12}{1:<44}\n".format("", "False negatives"))
                    fout.write("{0:<12}{1}\n".format("", header_string))
                    expected_output =\
                        [(loc, stats['locs'][loc][index], value)
                         for loc, value in sorted(false_negatives, key = lambda x: x[1], reverse=True)]
                    for (first_key, first_x, first_y) in expected_output:
                        fout.write("{0:<12}".format("") +
                                   self._table_record_formatter(first_key, first_x, first_y) + "\n")
                fout.write("\n\n")

    def output_extract(self, type, save_filename, top_lemmas_number, min_occs_number):
        if type not in ['words', 'authors']:
            raise ValueError("type should be 'words' or 'authors'")
        if top_lemmas_number == -1:
            top_lemmas_number = len(self.lemma_stats)
        if type == 'words':
            index = 0
            positive = 'positive'
            negative = 'negative'
            not_positive = 'not positive'
            mult = 100000
        elif type == 'authors':
            index = 1
            positive = 'positive authors'
            negative = 'negative authors'
            not_positive = 'not positive authors'
            mult = 100
        extraction_stats = dict()
        for i, (lemma, stats) in zip(range(top_lemmas_number), self.lemma_stats.items()):
            if stats['total']['positive'] == 0 and stats['total']['negative'] == 0:
                continue
            expected_locs, other_locs = self._group_locs_for_lemma(lemma)
            expected_stats = dict(filter(lambda x: x[0] in expected_locs,
                                         stats['locs'].items()))
            other_stats = dict(filter(lambda x: x[0] in other_locs and x[1][0] > 0,
                                      stats['locs'].items()))
            current_stats = dict()
            # initializing total counts
            current_stats['positive'] = [stats['total'][positive], stats['total'][positive]]
            current_stats['negative'] = [stats['total'][negative], stats['total'][negative]]
            current_stats['not positive'] = [stats['total'][not_positive]]
            # subtracting counts for regions with small number of authors
            for loc, counts in expected_stats.items():
                if not self._has_enough_authors(loc):
                    current_stats['positive'][1] -= stats['locs'][loc][index]
            for loc, counts in other_stats.items():
                if not self._has_enough_authors(loc):
                    current_stats['negative'][1] -= stats['locs'][loc][index]
            # positive fraction
            total = [current_stats['positive'][0] + current_stats['negative'][0],
                     current_stats['positive'][1] + current_stats['negative'][1]]
            current_stats['pos fraction'] =\
                [100 * current_stats['positive'][0] / total[0] if total[0] > 0 else 0.0,
                 100 * current_stats['positive'][1] / total[1] if total[1] > 0 else 0.0]
            # positive fraction without Moscow
            first = [current_stats['positive'][0], current_stats['positive'][1]]
            moscow = stats['locs']['Москва'][index] if 'Москва' in stats['locs'] else 0
            if u'Москва' in expected_locs:
                first[0] -= moscow
                first[1] -= moscow
            current_stats['pos fraction without Moscow'] =\
                [100 * first[0] / (total[0] - moscow) if first[0] > 0.0 else 0.0,
                 100 * first[1] / (total[1] - moscow) if first[1] > 0.0 else 0.0]
            # lemma percentage
            lemma_percentage = {loc: (stats['locs'][loc][index] / self.loc_stats[loc][type])
                                for loc in stats['locs']}
            # чтобы не было дублирования
            def _form_percentages(locs):
                return [dict(filter(lambda x: x[0] in locs, lemma_percentage.items())),
                        dict(filter(lambda x:(x[0] in locs and self._has_enough_authors(x[0]) and
                                    stats['locs'][x[0]][index] >= min_occs_number),
                             lemma_percentage.items()))]
            expected_locs_percentage = _form_percentages(expected_locs)
            other_locs_percentage = _form_percentages(other_locs)
            # extracting top other locs
            expected_locs_count = [len(elem) for elem in expected_locs_percentage]
            other_locs_percentage =\
                [dict(sorted(elem.items(),
                             key=(lambda x: x[1]), reverse=True)[:(count if count > 0 else 1)])
                 for elem, count in zip(other_locs_percentage, expected_locs_count)]
            # comparing positive and negative percentage
            # mult is used to come from fractions to counts per mult
            current_stats['mean pos percentage'] =\
                [(mult * np.mean(list(elem.values())) if len(elem) > 0 else 0.0)
                 for elem in expected_locs_percentage]
            # на случай, если элемент other_locs_percentage
            # оказался короче элемента в expected_locs_percentage
            negative_values = [list(elem.values()) + [0.0] * (max(count - len(elem), 0))
                               for elem, count in zip(other_locs_percentage, expected_locs_count)]
            current_stats['mean neg percentage'] =\
                [((mult * np.mean(elem)) if len(elem) > 0 else 0.0) for elem in negative_values]
            current_stats['pos neg ratio'] =\
                [(first / second if second > 0.0 else (np.inf if first > 0.0 else 0.0))
                 for first, second in zip(current_stats['mean pos percentage'],
                                          current_stats['mean neg percentage'])]
            top_locs_percentage =\
                [sorted(chain(first.items(), second.items()), key=(lambda x: x[1]), reverse=True)
                 for first, second, count
                 in zip(expected_locs_percentage, other_locs_percentage, expected_locs_count)]
            top_locs_average_percentage =\
                [mult * (np.mean(list(x[1] for x in elem)[:count] if max(count, len(elem)) > 0
                         else 0.0))
                 for count, elem in zip(expected_locs_count, top_locs_percentage)]
            current_stats['percentage defect'] =\
                [((second - first) / second if second > 0.0 else 0.0)
                 for first, second in zip(current_stats['mean pos percentage'],
                                          top_locs_average_percentage)]
            current_stats['rank defect'] =\
                [((np.mean([[elem[0] for elem in second].index(loc) for loc in first]) -
                   (count - 1) / 2) / count) if count > 0 else 1.0
                 for first, second, count in zip(expected_locs_percentage,
                                                 top_locs_percentage, expected_locs_count)]
            extraction_stats[lemma] = current_stats

        # outputting counts
        order = ['positive', 'negative', 'not positive', 'pos fraction',
                 'pos fraction without Moscow', 'mean pos percentage',
                 'mean neg percentage', 'pos neg ratio', 'percentage defect', 'rank defect']
        header = [u'Лемма'] + list(chain.from_iterable([elem, ""] for elem in order[:2])) +\
                 [order[2]] + list(chain.from_iterable([elem, ""] for elem in order[3:]))
        rows = [([lemma] +
                 list(map(number_formatter, chain.from_iterable(stats[key] for key in order))))
                for lemma, stats in sorted(extraction_stats.items(),
                                           key=(lambda x: np.min(x[1]['pos neg ratio'])),
                                           reverse=True)]
        save_to_file(save_filename, [header] + rows)

    def _read_cross_table(self):
        first_column = 8
        last_column = self.cross_table.columns.get_loc('Other Locs')
        for i, (lemma, row) in enumerate(self.cross_table.iterrows()):
            current_loc_stats = dict([(self.cross_table.columns[j], (row[j], row[j+1]))
                                      for j in range(first_column, last_column, 2)
                                      if row[j] > 0 or row[j+1] > 0])
            self.lemma_stats[lemma] = {
                'total': {loc.lower(): value for loc, value
                          in list(zip(self.cross_table.columns, row))[:first_column]},
                'locs': current_loc_stats}

    def _read_loc_table(self):
        authors_count_ind, words_count_ind = 0, 1
        for loc, row in self.loc_table.iterrows():
            for adm_loc in self.admissible_locs.get(loc, []):
                if adm_loc not in self.locs_keys:
                    continue
                if adm_loc not in self.loc_stats:
                    self.loc_stats[adm_loc] = {'authors': 0, 'words': 0}
                self.loc_stats[adm_loc]['authors'] += row[authors_count_ind]
                self.loc_stats[adm_loc]['words'] += row[words_count_ind]

    @staticmethod
    def _table_record_formatter(key, x, y):
        return("{0:<24}{1:<6}".format(key if key else "", x if x else "") +
               ("{0:<14.4f}".format(y) if y else "{0:<14}".format("")))

    def _is_maximal_admissible_loc(self, loc, lemma):
        lemma_locs = self.lemmatizer.lemma_locs(lemma)
        if loc not in lemma_locs:
            return False
        for adm_loc in self.admissible_locs[loc]:
            if adm_loc in lemma_locs and loc != adm_loc:
                return False
        return True

    def _group_locs_for_lemma(self, lemma):
        expected_locs = [loc for loc in self.lemmatizer.lemma_locs(lemma)
                         if self._is_maximal_admissible_loc(loc, lemma)]
        possible_locs =\
            set(chain.from_iterable(self.admissible_locs[loc] for loc in expected_locs))
        other_locs = [loc for loc in self.locs_keys
                      if (loc not in possible_locs and all((elem not in expected_locs)
                                                           for elem in self.admissible_locs[loc]))]
        return expected_locs, other_locs

    def _has_enough_authors(self, loc, MINIMAL_AUTHORS_NUMBER = 50):
        return self.loc_stats[loc]['authors'] >= MINIMAL_AUTHORS_NUMBER


def number_formatter(x):
    if isinstance(x, int):
        formatter = "{0:d}"
    elif isinstance(x, float):
        formatter = "{0:.2f}"
    return formatter.format(x)

def _define_separation_threshold(scores, expected,
                                 min_fraction=0.5, min_count=1, switch=5):
    expected_keys_values = []
    for elem in expected:
        value = scores.get(elem, None)
        if value is not None:
            insort(expected_keys_values, value)
    if len(expected_keys_values) == 0:
        min_threshold = max(scores.values())
    else:
        min_threshold = _find_min_threshold(expected_keys_values, min_fraction, min_count, switch)
    values = sorted(scores.values())
    threshold = otsu(values)
    while threshold > min_threshold:
        values = values[:-1]
        threshold = otsu(values)
    return threshold

def _find_min_threshold(values, min_fraction, min_count, switch):
    '''
    accepts an ascending array of values
    and finds minimal threshold t such that
    1) at least "min_count" elements in "values" are not less then t in case
       len(values) < switch
    2) at least max(min_fraction * len(values), min_count) of elements in "values"
       are not less than t if len(values) >= switch
    switch=-1 means min_fraction strategy is always applied
    switch=None means min_count strategy is always applied
    '''
    values = np.fromiter(values, dtype=np.float64)
    length = values.shape[0]
    if switch is None:
        switch = length + 1
    if length >= switch:
        min_count = max(min_count, math.ceil(min_fraction * length))
    if length <= min_count:
        answer = values[0]
    else:
        answer = (values[-min_count-1] + values[-min_count]) / 2
    return answer




def otsu(a):
    '''
    Separates a bimodal distribution by an optimal threshold
    by Otsu method (en.wikipedia.org/wiki/Otsu%27s_method)
    '''
    a = np.atleast_1d(np.fromiter(a, dtype=np.float64))
    if a.ndim > 1:
        raise TypeError("a should be 1-dimensional")
    if a.shape[0] == 1:
        return a[0]
    a.sort()
    cumsums = np.cumsum(a)
    N, S = a.shape[0], cumsums[-1]
    b = [(((S - s) / (N - n) - s / n) ** 2) * (N - n) * n
         for n, s in enumerate(cumsums[:-1], 1)]
    i = np.argmax(b)
    return (a[i] + a[i+1]) / 2



def run(args):
    if len(args) != 8:
        sys.exit("Pass type(detail, extract_by_words or extract_by_authors),\
                  dict_filename, add_locs_filename, cross_table_filename, loc_table_filename,\
                  save_filename, top lemmas number, minimal number of occurences to output")
    (type, dict_filename, add_locs_filename, cross_table_filename,
     loc_table_filename, save_filename, top_lemmas_number, min_occs_number) = args
    top_lemmas_number, min_occs_number = int(top_lemmas_number), int(min_occs_number)

    rsd = RegionalStatsDemonstrator(dict_filename, add_locs_filename,
                                    cross_table_filename, loc_table_filename)
    rsd.read_tables()
    if type == 'detail':
        rsd.output_detailed(save_filename, top_lemmas_number, min_occs_number)
    elif type == 'extract_by_words':
        rsd.output_extract('words', save_filename, top_lemmas_number, min_occs_number)
    elif type == 'extract_by_authors':
        rsd.output_extract('authors', save_filename, top_lemmas_number, min_occs_number)
    elif type == 'separation_by_words':
        rsd.output_separation('words', save_filename, top_lemmas_number, min_occs_number)
    elif type == 'separation_by_authors':
        rsd.output_separation('authors', save_filename, top_lemmas_number, min_occs_number)
