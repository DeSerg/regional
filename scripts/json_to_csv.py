# -*- coding: utf8 -*-
import sys
import json
import pandas as pd

header = ["Регион", "Тексты", "Авторы", "Слова", "Длинные тексты", "Авторы длинных текстов",
          "Слова в длинных текстах", "Первые тексты", "Авторы первых текстов",
          "Слова в первых текстах"]
keys = ["texts", "authors", "words", "long_texts", "long_texts_authors",
        "long_texts_words", "long_texts_authors", "long_texts_authors",
        "first_text_words"]

if __name__ == "__main__":
    args = sys.argv[1:]
    if len(args) != 2:
        sys.exit("Pass input .json file and output .csv")
    infile, outfile = args
    with open(infile, "r") as fin:
        data = json.load(fin)
    data_frame = pd.DataFrame(columns=header, dtype=int)
    for region, region_data in data.items():
        row = [[region] + [region_data[key] for key in keys]]
        data_frame = data_frame.append(pd.DataFrame(row, columns=header, dtype=int))
    data_frame = data_frame.sort("Авторы", ascending=False)
    data_frame.to_csv(outfile, sep="\t", encoding="utf8", index=False, float_format='%0.0f')