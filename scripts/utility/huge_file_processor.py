# -*- coding: utf-8 -*-
"""
Модуль для обработки больших файлов
"""

import re
import collections
import csv
import sys
import os
from functools import partial


def process_data(piece, **kwargs):
    pass


# http://stackoverflow.com/questions/519633/lazy-method-for-reading-big-file-in-python
# http://stupidpythonideas.blogspot.ru/2013/06/readlines-considered-silly.html
def process_by_readline(filename, mb_size):
    with open(filename, 'r') as f:
        file_size = os.fstat(f.fileno()).st_size // (1024*1024)
        progress = 0
        step = int(1024 * 1024 * mb_size)
        for piece in iter(partial(f.readlines, step), []):
            process_data(piece)
            progress += mb_size
            print("Processed {0:.2f}/{1}".format(progress, file_size))


def process_hugefile(filename, mb_size):
    process_by_readline(filename, mb_size)


def run():
    if len(sys.argv[1:]) < 2:
        print("Pass filename and size")
        return

    filename = sys.argv[1]
    size = sys.argv[2]
    process_hugefile(filename, float(size))
