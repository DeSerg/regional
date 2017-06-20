import sys
import json
import operator
sys.path.insert(0, '..')

import location_utils.location_helper as lh
import standart_locations.region_database as reg_db

def stat_old(json_filename):
    class_corp = {}
    with open(json_filename) as json_file:
        class_corp = json.load(json_file)

    authors_num = len(class_corp)
    total_texts_num = 0
    pos_texts_num = 0

    locations_set = set()

    for author, data in class_corp.items():
        loc = data['loc']
        locations_set.add(loc)

        num_neg_texts = data['texts without regional']
        pos_texts = data['texts']

        pos_texts_num += len(pos_texts)
        total_texts_num += num_neg_texts + len(pos_texts)

    print('Authors                      : %d' % authors_num)
    print('All texts                    : %d' % total_texts_num)
    print('Texts with regional words    : %d' % pos_texts_num)
    print('Texts without regional words : %d' % (total_texts_num - pos_texts_num))
    print('Unique locations             : %d' % len(locations_set))


def stat_reg_country(json_filename):
    class_corp = {}
    with open(json_filename) as json_file:
        class_corp = json.load(json_file)

    authors_num = len(class_corp)
    total_texts_num = 0
    pos_texts_num = 0

    region_country_num = 0
    only_region_num = 0
    only_country_num = 0
    regions_set = set()
    countries_set = set()


    for author, data in class_corp.items():
        if lh.RegionKey in data:
            regions_set.add(data[lh.RegionKey])
            if lh.CountryKey in data:
                countries_set.add(data[lh.CountryKey])
                region_country_num += 1
            else:
                print('Damn it! %s' % author)
                print(data[lh.RegionKey])
                only_region_num += 1
        elif lh.CountryKey in data:
            countries_set.add(data[lh.CountryKey])
            only_country_num += 1

        num_neg_texts = data[lh.NegativeTextsNumKey]
        pos_texts = data[lh.PositiveTextsKey]

        pos_texts_num += len(pos_texts)
        total_texts_num += num_neg_texts + len(pos_texts)

    print('Authors                      : %d' % authors_num)
    print('All texts                    : %d' % total_texts_num)
    print('Texts with regional words    : %d' % pos_texts_num)
    print('Texts without regional words : %d' % (total_texts_num - pos_texts_num))
    print('Unique regions num           : %d' % len(regions_set))
    print('Unique countries num         : %d' % len(countries_set))
    print('Region and country tot num   : %d' % region_country_num)
    print('Only region tot num          : %d' % only_region_num)
    print('Only country tot num         : %d' % only_country_num)


def stat_certain_old(class_corp, locs_filename):

    locations = ['Москва']
    # with open(locs_filename) as locs_f:
    #     for line in locs_f:
    #         line = line.strip()
    #         if line:
    #             locations.append(line)

    author_num = 0
    total_texts_num = 0
    pos_texts_num = 0

    for author, data in class_corp.items():
        loc = data['loc']
        if not loc in locations:
            continue

        author_num += 1
        num_neg_texts = data['texts without regional']
        pos_texts = data['texts']

        pos_texts_num += len(pos_texts)
        total_texts_num += num_neg_texts + len(pos_texts)

    print('Author number                : %d' % author_num)
    print('All texts                    : %d' % total_texts_num)
    print('Texts with regional words    : %d' % pos_texts_num)
    print('Texts without regional words : %d' % (total_texts_num - pos_texts_num))

def stat_certain(class_corp, locs_filename):

    regions = ['Moscow Oblast']
    countries = []
    # with open(locs_filename) as locs_f:
    #     for line in locs_f:
    #         line_split = line.strip().split(': ')
    #         if len(line_split) != 2:
    #             print('damn')
    #             continue
    #         if line_split[0] == lh.RegionKey:
    #             regions.append(line_split[1])
    #         else:
    #             countries.append(line_split[1])

    author_num = 0
    total_texts_num = 0
    pos_texts_num = 0

    for author, data in class_corp.items():
        region = ''
        country = ''
        if lh.RegionKey in data:
            region = data[lh.RegionKey]
        if lh.CountryKey in data:
            country = data[lh.CountryKey]

        if (region and region in regions) or (country and country in countries):
            num_neg_texts = data[lh.NegativeTextsNumKey]
            pos_texts = data[lh.PositiveTextsKey]

            author_num += 1
            pos_texts_num += len(pos_texts)
            total_texts_num += num_neg_texts + len(pos_texts)

    print('Author number                : %d' % author_num)
    print('All texts                    : %d' % total_texts_num)
    print('Texts with regional words    : %d' % pos_texts_num)
    print('Texts without regional words : %d' % (total_texts_num - pos_texts_num))


def regions_rus_stat(json_filename):
    class_corp = {}
    with open(json_filename) as json_file:
        class_corp = json.load(json_file)

    regions = {}
    for author, data in class_corp.items():
        region = ''
        country = ''
        if lh.RegionKey in data:
            region = data[lh.RegionKey]
        if lh.CountryKey in data:
            country = data[lh.CountryKey]

        if country == lh.RussiaName:
            if region in regions:
                regions[region] += 1
            else:
                regions[region] = 1

    for region, authors in regions.items():
        print('%s: %d' % (region, authors))

def countries_num(class_corp):
    countries = {}
    for author, data in class_corp.items():
        if not lh.RegionKey in data and lh.CountryKey in data:
            country = data[lh.CountryKey]
            if country in countries:
                countries[country] += 1
            else:
                countries[country] = 1

    total = 0
    for country, num in sorted(countries.items(), key=operator.itemgetter(1), reverse=True):
        print('%s: %d' % (country, num))
        total += num
    print('\ntotal: %d' % total)

def main(argv):
    json_filename = argv[0]
    regions_filename = argv[1]
    # stat_certain_old(json_filename, regions_filename)
    # stat_certain(json_filename, regions_filename)
    # stat_certain(json_filename, regions_filename)
    # stat_reg_country(json_filename)

    # regions_rus_stat(json_filename)

    class_corp = {}
    with open(json_filename) as json_file:
        class_corp = json.load(json_file)

    countries_num(class_corp)
    # stat_certain(class_corp, '')




if __name__ == "__main__":
    main(sys.argv[1:])
