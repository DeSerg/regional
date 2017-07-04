import sys
import json
import operator
import matplotlib.pyplot as plt
sys.path.insert(0, '..')

import location_utils.location_helper as lh
import standart_locations.region_database as reg_db
import corpus.corpus_helper as ch


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


def stat_certain(class_corp, locations_filename, min_texts_len=ch.MinTextLen):

    regions, countries = lh.parse_classification_locations(locations_filename)

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


def countries_only_stat(class_corp):
    countries = {}
    for author, data in class_corp.items():
        if not lh.CityKey in data and not lh.RegionKey in data and lh.CountryKey in data:
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


def regions_for_country(class_corp, country_targ):
    regions = {}

    for author, data in class_corp.items():
        if not lh.RegionKey in data or not lh.CountryKey in data:
            continue

        country = data[lh.CountryKey]
        if country != country_targ:
            continue

        region = data[lh.RegionKey]
        pos_text_flag = 0
        if data[lh.PositiveTextsKey]:
            pos_text_flag = 1

        if region in regions:
            regions[region][0] += 1
            regions[region][1] += pos_text_flag
        else:
            regions[region] = [1, pos_text_flag]

    regions_list = [(region, data[0], data[1]) for region, data in regions.items()]
    regions_list.sort(key=lambda x: x[1], reverse=True)

    region_ids = []
    authors_nums = []
    reg_authors_nums = []

    for region_id, (region, authors_num, reg_authors_num) in enumerate(regions_list, 1):
        # print('%s: %d, %d' % (region, authors_num, reg_authors_num))
        print('%s:' % (region))
        region_ids.append(region_id)
        authors_nums.append(authors_num)
        reg_authors_nums.append(reg_authors_num)

    # print('Total authors num: %d' % sum(authors_nums))
    # print('Total authors with regional texts num: %d' % sum(reg_authors_nums))

    #start = 1
    #plt.plot(region_ids[start:], authors_nums[start:], 'bo', region_ids[start:], reg_authors_nums[start:], 'r^')
    # plt.plot(region_ids[start:], reg_authors_nums[start:], 'g^')
    #plt.show()


def general_stat(class_corp):

    total_authors_num = len(class_corp)
    total_texts_num = 0
    total_texts_len = 0

    city_region_country_num = 0
    region_country_num = 0
    country_num = 0

    text_len_border = [20, 300, 500, 1000, 3000, 5000]
    author_num_for_border = {}
    for text_len in text_len_border:
        author_num_for_border[text_len] = 0

    for author, data in class_corp.items():
        city, region, country = '', '', ''
        if lh.CityKey in data:
            city = data[lh.CityKey]
        if lh.RegionKey in data:
            region = data[lh.RegionKey]
        if lh.CountryKey in data:
            country = data[lh.CountryKey]
        if city and region and country:
            city_region_country_num += 1
        elif region and country:
            region_country_num += 1
        elif country:
            country_num += 1

        text_len = data[lh.TextsLenKey]
        total_texts_len += text_len

        total_texts_num += len(data[lh.PositiveTextsKey]) + data[lh.NegativeTextsNumKey]

        for text_len_border, value in author_num_for_border.items():
            if text_len > text_len_border:
                author_num_for_border[text_len_border] = value + 1

    print('General LJ corpus stat')
    print()
    print('Total authors num: %d' % total_authors_num)
    print('Total_texts_num: %d' % total_texts_num)
    print('Average texts len: %f' % (total_texts_len / total_texts_num))
    print()
    print('Authors with city, region, country: %d' % city_region_country_num)
    print('Authors with region, country: %d' % region_country_num)
    print('Authors with country: %d' % country_num)
    print()
    for text_len_border, authors_num in author_num_for_border.items():
        print('Border: %d, authors: %d' % (text_len_border, authors_num))

# for corpus with texts lengths
def general_stat_for_locs(class_corp, locations_filename, min_texts_len=ch.MinTextLen):

    regions, countries = lh.parse_classification_locations(locations_filename)

    total_authors_num = 0
    total_texts_num = 0
    total_texts_len = 0

    locations_data = {}

    for author, data in class_corp.items():
        region, country = '', ''
        if lh.RegionKey in data:
            region = data[lh.RegionKey]
        if lh.CountryKey in data:
            country = data[lh.CountryKey]

        location = ''
        if region in regions:
            location = region
        elif country in countries:
            location = country
        else:
            continue

        total_authors_num += 1
        
        texts_len = data[lh.TextsLenKey]
        total_texts_len += texts_len

        texts_num = len(data[lh.PositiveTextsKey]) + data[lh.NegativeTextsNumKey]
        total_texts_num += texts_num

        if location in locations_data:
            locations_data[location][0] += 1 # authors_num
            locations_data[location][1] += texts_num # texts_num
            locations_data[location][2] += texts_len # texts_len
        else:
            locations_data[location] = [1, texts_num, texts_len]

    locations_data_list = [(location, data[0], data[1], data[2]) for location, data in locations_data.items()]
    locations_data_list.sort(key=lambda x: x[1])

    print('Total authors num: %d' % total_authors_num)
    print('Total_texts_num: %d' % total_texts_num)
    print('Average texts len: %f' % (total_texts_len / total_texts_num))
    print()

    print('Location: Authors_num, texts_num, avg_texts_len')
    for location, authors_num, texts_num, texts_len in locations_data_list:
        print('%s: %d, %d, %f' % (location, authors_num, texts_num, texts_len / texts_num))

def general_stat_no_locs_corpus(class_corp):

    total_authors_num = len(class_corp)
    total_texts_num = 0
    total_texts_len = 0

    text_len_border = [20, 300, 500, 1000, 3000, 5000]
    author_num_for_border = {}
    for text_len in text_len_border:
        author_num_for_border[text_len] = 0

    for author, data in class_corp.items():

        text_len = data[lh.TextsLenKey]
        total_texts_len += text_len

        total_texts_num += len(data[lh.PositiveTextsKey]) + data[lh.NegativeTextsNumKey]

        for text_len_border, value in author_num_for_border.items():
            if text_len > text_len_border:
                author_num_for_border[text_len_border] = value + 1

    print('General LJ corpus stat')
    print()
    print('Total authors num: %d' % total_authors_num)
    print('Total_texts_num: %d' % total_texts_num)
    print('Average texts len: %f' % (total_texts_len / total_texts_num))
    print()
    for text_len_border, authors_num in author_num_for_border.items():
        print('Border: %d, authors: %d' % (text_len_border, authors_num))

def main(argv):
    json_filename = argv[0]
    locations_filename = argv[1]

    class_corp = {}
    with open(json_filename) as json_file:
        class_corp = json.load(json_file)

    # countries_only_stat(class_corp)
    # general_stat_for_locs(class_corp, locations_filename, min_texts_len=ch.MinTextLen)
    regions_for_country(class_corp, 'Ukraine')
    regions_for_country(class_corp, lh.RussiaName)
    # general_stat_no_locs_corpus(class_corp)


if __name__ == "__main__":
    main(sys.argv[1:])
