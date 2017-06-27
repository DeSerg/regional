import sys
import json
import matplotlib.pyplot as plt
import numpy as np
import plotly.plotly as py
import plotly.figure_factory as ff
from matplotlib.ticker import NullFormatter

sys.path.insert(0, '..')

import location_utils.location_helper as lh
import standart_locations.region_database as reg_db

def plot(x, y):
    plt.plot(x, y, 'ro')
    # plt.axis([0, 6, 0, 20])
    plt.xticks(np.arange(1, len(x), 2))
    axes = plt.gca()
    # axes.set_ylim([0, 1000])
    # axes.set_xlim([25, 90])

    plt.show()

# def table(index_table):
#     table = ff.create_table(index_table)
#     py.iplot(table, filename='locations')


def authors_distribution(class_corp, regions, countries):

    locations = {}
    for author, data in class_corp.items():
        region = ''
        country = ''
        if lh.RegionKey in data:
            region = data[lh.RegionKey]
        if lh.CountryKey in data:
            country = data[lh.CountryKey]

        if country in countries:
            if country in locations:
                locations[country] += 1
            else:
                locations[country] = 1

        if region in regions:
            if region in locations:
                locations[region] += 1
            else:
                locations[region] = 1

    x = []
    y = []
    index_table = {}
    for ind, (location, authors) in enumerate(locations.items()):
        ind += 1
        x.append(ind)
        y.append(authors)
        index_table[ind] = location

    x_sorted = []
    y_sorted = []
    locations_sorted = sorted(zip(x, y), key=lambda x: x[1], reverse=True)
    for new_ind, (ind, authors) in enumerate(locations_sorted):
        new_ind += 1
        print('%d: %s: %d' % (new_ind, index_table[ind], authors))
        x_sorted.append(new_ind)
        y_sorted.append(authors)

    plot(x_sorted, y_sorted)

    less_100 = 0
    less_500 = 0
    less_1000 = 0
    for location, authors in locations.items():
        if authors < 100:
            less_100 += 1
        if authors < 500:
            less_500 += 1
        if authors < 1000:
            less_1000 += 1
    print('Less than 100 authors : %d' % less_100)
    print('Less than 500 authors : %d' % less_500)
    print('Less than 1000 authors: %d' % less_1000)

def avg_regional(class_corp, regions, countries):
    locations_map = {}
    for author, data in class_corp.items():
        region = ''
        country = ''
        if lh.RegionKey in data:
            region = data[lh.RegionKey]
        if lh.CountryKey in data:
            country = data[lh.CountryKey]

        assert(lh.PositiveTextsKey in data)
        positive_texts = data[lh.PositiveTextsKey]
        if not positive_texts:
            continue

        if country in countries:
            if country in locations_map:
                locations_map[country][0] += 1
                locations_map[country][1] += len(positive_texts)
            else:
                locations_map[country] = [1, len(positive_texts)]

        if region in regions:
            if region in locations_map:
                locations_map[region][0] += 1
                locations_map[region][1] += len(positive_texts)
            else:
                locations_map[region] = [1, len(positive_texts)]

    distrib = []
    index_table = {}
    for ind, (location, (authors_num, positive_texts_num)) in enumerate(locations_map.items()):
        ind += 1
        positive_texts_avg = positive_texts_num / authors_num
        distrib.append((ind, authors_num, positive_texts_avg))
        index_table[ind] = location


    distrib.sort(key=lambda x: x[1], reverse=True)
    x = []
    y = []
    for ind_new, (ind, authors_num, positive_texts_avg) in enumerate(distrib):
        x.append(ind_new)
        y.append(positive_texts_avg)
        print('%d: %s:\t%4d,\t%f' % (ind_new, index_table[ind], authors_num, positive_texts_avg))

    # plot(x, y)

def main(argv):
    json_filename = argv[0]
    class_corp = {}
    with open(json_filename) as json_file:
        class_corp = json.load(json_file)

    locations_filename = argv[1]
    regions, countries = lh.parse_classification_locations(locations_filename)

    # authors_distribution(class_corp, regions, countries)
    avg_regional(class_corp, regions, countries)


if __name__ == "__main__":
    main(sys.argv[1:])
