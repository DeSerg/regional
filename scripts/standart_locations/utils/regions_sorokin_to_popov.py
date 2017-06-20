import sys
import pandas as pd
import datetime
import os

sys.path.insert(0, '../..')

import location_utils.location_helper as lh
import standart_locations.region_database as rdb

def loc_convert(db, region, level_ind):
    region_variants = db.sql_find_records_precisely(region, level_ind)
    if not region_variants:
        region_variants_uns = db.sql_find_records_with_errs(region, level_ind)
        region_variants = sorted(region_variants_uns, key=lambda x: x[1])

    if not region_variants:
        return ''
    else:
        return region_variants[0][0]['name']

def dict_regions_convert(dict_filename, dict_filename_new):
    db = rdb.Database()
    REGIONS_COLUMN = 'Standartized locations'
    DB_REGIONS_COLUMN = 'Standartized db regions'
    DB_COUNTRIES_COLUMN = 'Standartized db countries'

    xlsx = pd.ExcelFile(dict_filename)
    sheet = xlsx.parse('Sheet1')

    sheet = pd.concat([sheet,
                       pd.DataFrame(columns=[DB_REGIONS_COLUMN]),
                       pd.DataFrame(columns=[DB_COUNTRIES_COLUMN])], axis=1)

    for i, row in sheet.iterrows():
        locs = row[REGIONS_COLUMN].split(', ')
        regions_new = []
        countries_new = []
        for loc in locs:
            region_new = loc_convert(db, loc, rdb.RegionLevel)
            if region_new:
                regions_new.append(region_new)
                continue
            country_new = loc_convert(db, loc, rdb.CountryLevel)
            if country_new:
                countries_new.append(country_new)
                continue
            print('Bad loc %s' % loc)
        sheet.set_value(i, DB_REGIONS_COLUMN, ';'.join(regions_new))
        sheet.set_value(i, DB_COUNTRIES_COLUMN, ';'.join(countries_new))
        print('Row %d obtained' % i)


    writer = pd.ExcelWriter(dict_filename_new)
    sheet.to_excel(writer)
    writer.save()

def file_regions_convert(filename, filename_new):
    db = rdb.Database()

    with open(filename_new, 'w') as f_new:
        with open(filename) as f:
            for line_num, line in enumerate(f):
                loc = line.strip()
                print('Loc: %s' % loc)
                region = loc_convert(db, loc, rdb.RegionLevel)
                if region:
                    f_new.write('%s: %s\n' % (lh.RegionKey, region))
                    continue
                country = loc_convert(db, loc, rdb.CountryLevel)
                if country:
                    f_new.write('%s: %s\n' % (lh.CountryKey, country))
                    continue
                print('BAD!!')


def test():
    db = rdb.Database()
    # print(loc_convert(db, 'Казахстан', rdb.CountryLevel))
    # print(loc_convert(db, 'Крымская область', rdb.RegionLevel))
    # print(loc_convert(db, 'Башкортостан', rdb.RegionLevel))

    print(db.RegionsMap['GB'])

def main(argv):
    if len(argv) < 1:
        print('Usage: mode (dict|list|test) ...')

    mode = argv[0]
    if mode == 'dict':
        dict_filename = argv[1]

        today_date = datetime.datetime.now().strftime('_%d_%m_%Y')
        dict_filename_new = argv[2] + today_date + '.xlsx'

        dict_regions_convert(dict_filename, dict_filename_new)
    elif mode == 'list':
        filename = argv[1]
        filename_new = argv[2]
        file_regions_convert(filename, filename_new)
    else:
        test()



if __name__ == '__main__':
    main(sys.argv[1:])