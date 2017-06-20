# -*- coding: utf8 -*-
'''
Модуль, оставляющий только авторов с достаточно большим числом текстов
'''

import sys
import ujson as json

def run(args):
    if len(args) != 5:
        sys.exit("Pass authors json file, prettified texts json file, "
                 "minimal number of words for an author, output authors file and output texts file")
    authors_file, texts_file, nwords, output_authors_file, output_texts_file = args
    nwords = int(nwords)

    with open(authors_file, "r") as fin:
        authors_data = json.load(fin)
    authors_data = {author: elem for author, elem in authors_data.items()
                    if elem['words_count'] >= nwords}
    authors = set(authors_data.keys())
    with open(output_authors_file, "w") as fout:
        json.dump(authors_data, fout, ensure_ascii=False)
    with open(texts_file, "r") as fin:
        text_data = json.load(fin)
    text_data = {id: elem for id, elem in text_data.items()
                 if elem['author'] in authors}
    with open(output_texts_file, "w") as fout:
        json.dump(text_data, fout, ensure_ascii=False)
