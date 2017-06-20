#-------------------------------------------------------------------------------
# Name:        dictionary_cleaner.py
# Purpose:     removes homonyms from the dictionary
#
# Author:      Алексей Сорокин
#
# Created:     29.01.2015
#-------------------------------------------------------------------------------

import sys
import pandas as pd
from itertools import chain, filterfalse
from pymystem3 import Mystem

class DictionaryCleaner:

    def __init__(self, dict_file):
        self.dict_file = dict_file
        self.mystemmer = Mystem(disambiguation=False, entire_input=False)

    def clean(self):
        LEMMA_COLUMN = u'ЛЕММА'
        WORDS_COLUMN = u'Список словоформ'
        self.sheet = pd.ExcelFile(self.dict_file).parse('Sheet1')
        new_word_forms = [", ".join(self._clean_ambigious_forms(lemma, words.split("; ")))
                          for lemma, words in zip(self.sheet[LEMMA_COLUMN],
                                                  self.sheet[WORDS_COLUMN])]
        self.sheet[WORDS_COLUMN] = new_word_forms

    def output(self, dict_outfile):
        self.sheet.to_excel(dict_outfile, index=False)

    def _clean_ambigious_forms(self, lemma, words):
        return list(filterfalse(lambda x: self._has_other_candidates(lemma, x), words))

    def _has_other_candidates(self, lemma, word):
        analysis = self.mystemmer.analyze(word)[0]['analysis']
        candidate_lemmas = set([variant['lex'] for variant in analysis
                                if variant.get('qual', 'NA') != 'bastard'])
        if len(candidate_lemmas) > 1:
            return True
        elif len(candidate_lemmas) == 0:
            return False
        # в выдаче mystem нет ё
        return (list(candidate_lemmas)[0] != normalize(lemma))

def normalize(word):
    return word.lower().replace(u"ё", u"е")


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit("Pass source dictionary file and destination dictionary file")
    (dict_file, dict_outfile) = sys.argv[1:]

    dc = DictionaryCleaner(dict_file)
    dc.clean()
    dc.output(dict_outfile)
