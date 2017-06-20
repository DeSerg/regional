"""
Модуль для подсчета статистики по локациям (loc и city) в xml корпусе.
"""

import re
import collections
import csv
import sys


loc_freqs = dict()
city_freqs = dict()
loc_city_freqs = dict()

loc_regexp = re.compile('loc="(.*?)"')
city_regexp = re.compile('city="(.*?)"')


def process_data(piece):
    locs = loc_regexp.findall(piece)
    cities = city_regexp.findall(piece)

    write_freqs(locs, cities)


def write_freqs(locs, cities):
    locs_counter = collections.Counter(locs)
    cities_counter = collections.Counter(cities)

    loc_cities = zip(locs, cities)
    loc_city_counter = collections.Counter(loc_cities)

    update_freqs(loc_freqs, locs_counter)
    update_freqs(city_freqs, cities_counter)
    update_freqs(loc_city_freqs, loc_city_counter)


def update_freqs(freqs, counter):
    for k in counter:
        if k not in freqs:
            freqs[k] = counter[k]
        else:
            freqs[k] += counter[k]


def process_hugefile(filename):
    progress = 0

    f = open(filename)

    def read512mb():
        return f.read(1024 * 1024 * 512)  # 512Mb

    for piece in iter(read512mb, ''):
        process_data(piece)

        progress += 1
        print("Processed " + str(progress * 512))


def save_freqs_to_file():
    loc_city_freqs_ = [[loc, city, loc_city_freqs[(loc, city)]]
                       for loc, city in loc_city_freqs]

    loc_city_freqs_ = sorted(loc_city_freqs_, reverse=True, key=lambda x: x[2])
    city_freqs_ = sorted(city_freqs.items(), reverse=True, key=lambda x: x[1])
    loc_freqs_ = sorted(loc_freqs.items(), reverse=True, key=lambda x: x[1])

    save_to_file('loc_city_freqs.csv', loc_city_freqs_)
    save_to_file('city_freqs.csv', city_freqs_)
    save_to_file('loc_freqs.csv', loc_freqs_)


def save_to_file(filename, arr):
    with open(filename, 'w') as f:
        writer = csv.writer(f, delimiter='\t')
        writer.writerows(arr)


def run():
    if len(sys.argv[1:]) == 0:
        print("Pass filename to count frequency of loc and city")
        return

    filename = sys.argv[1]
    process_hugefile(filename)
    save_freqs_to_file()
