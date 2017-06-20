# -*- coding: utf8 -*-
'''
Cбор статистики по словам и регионам в .csv-файл
'''
import sys
import os
import pandas as pd
import json as json
import numpy as np

HEADER = ["Регион", "Тексты", "Авторы", "Слова", "Длинные тексты", "Авторы длинных текстов",
          "Слова в длинных текстах", "Слова в первых текстах"]

KEYS = ["texts", "authors", "words", "long_texts", "long_texts_authors",
        "long_texts_words",  "first_text_words"]

def read_words_data(infile, regions, keys):
    columns = ['Слово'] + regions + ['Всего']
    data_frames = {key: pd.DataFrame(columns=columns) for key in keys}
    with open(infile, "r") as fin:
        for i, line in enumerate(fin):
            if i % 500 == 0:
                print(i)
            if line.count(":") == 0:
                continue
            pos = line.find(':')
            word, word_data = line[:pos], line[(pos+1):]
            word_data = word_data.strip().strip(',')
            word_data = json.loads(word_data)
            current_rows = dict()
            current_data = [word] + [0] * (len(regions) + 1)
            for key in keys:
                current_rows[key] = pd.Series(data=current_data, index=columns)
            for region, word_data_for_region in word_data.items():
                for key, count in word_data_for_region.items():
                    current_rows[key][region] = count
            for key in keys:
                row = current_rows[key]
                row['Всего'] = np.sum(row[1:-1])
                data_frames[key] = data_frames[key].append(row, ignore_index=True)
    return data_frames


if __name__ == "__main__":
    args = sys.argv[1:]
    if len(args) != 3:
        sys.exit("Pass .json input file, .csv file for regions "
                 "and output directory for .csv files")
    infile, csv_file, outdir = args
    if not os.path.exists(outdir):
        os.makedirs(outdir)
    # keep_default_na = False to prevent NA to be considered as 'non available'
    data = pd.read_csv(csv_file, sep="\t",keep_default_na=False)
    columns = data.columns
    regions = list(data['Регион'])
    data_frames = read_words_data(infile, regions, KEYS)
    for key, data_frame in data_frames.items():
        outfile = os.path.join(outdir, "{0}.csv".format(key))
        data_frame.to_csv(outfile, sep="\t", float_format='%0.0f')



