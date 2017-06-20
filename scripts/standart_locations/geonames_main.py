import editdistance as ee
import time
import pandas as pd
import sys

from region_database import *


def default_dataframe():
    return pd.DataFrame(columns=['geonameid', 'name', 'altnames', 'fclass', 'fcode', 'ccode', 'acode1'])


def get_records_for_location(records, location):
    records = records.ix[(records['name'] == location) | ((records['altnames'].notnull()) & (records['altnames'].str.contains(location)))]
    result = pd.DataFrame(columns=list(records))
    for _, record in records.iterrows():
        names = []
        if not pd.isnull(record['name']):
            names.append(record['name'])
        if not pd.isnull(record['altnames']):
            names += record['altnames'].split(',')
        if location in names:
            # print(names)
            result = result.append(record)
    # print(len(result))
    return result


def get_records_for_location_with_errs(records, locations, max_edit_distance):
    result = pd.DataFrame(columns=list(records))
    edit_distances = []
    min_pair = ('', '')
    for _, record in records.iterrows():
        names = []
        if not pd.isnull(record['name']):
            names.append(record['name'])
        if not pd.isnull(record['altnames']):
            names += record['altnames'].split(',')
        # print(names)

        min_dist = max_edit_distance + 1
        for location in locations:
            for name in names:
                dist = ee.eval(location, name)
                if dist < min_dist:
                    min_dist = dist
                    min_pair = (location, name)
        if min_dist <= max_edit_distance:
            # print(names[min_dist_index], min_dist)
            result = result.append(record)
            edit_distances.append(min_dist)

    # print(len(result))
    return result, edit_distances, min_pair[0]


def prepare_combinations_1(database, full_location, result):
    if len(full_location) != 1:
        return

    location_variants = database.location_variations(full_location[0])
    for code in LocationCodes:
        #similar = database.get_similar_locations(location_variants, code)
        similar = database.sql_find_records_precisely()
        if not similar:
            continue
        result += [{code: similar_item} for similar_item in similar]
        return

    return
    # for code in LocationCodes:
    #     similar = database.get_similar_locations_with_errs(location_variants, code)
    #     if not similar:
    #         continue
    #     result += [{code: similar_item} for similar_item in similar]
    #     return


def prepare_combinations_2(database, full_location, result):
    if len(full_location) != 2:
        return

    code_combinations = [(CityCode, CountryCode), (CityCode, RegionCode), (RegionCode, CountryCode)]
    variants0 = database.location_variations(full_location[0])
    variants1 = database.location_variations(full_location[1])

    for code0, code1 in code_combinations:
        similar0 = database.get_similar_locations(variants0, code0)
        if not similar0:
            continue
        similar1 = database.get_similar_locations(variants1, code1)
        if not similar1:
            continue
        for item0 in similar0:
            for item1 in similar1:
                result.append({code0: item0, code1: item1})
                return

    return
    # for code0, code1 in code_combinations:
    #     similar0 = database.get_similar_locations_with_errs(variants0, code0)
    #     if not similar0:
    #         continue
    #     similar1 = database.get_similar_locations_with_errs(variants1, code1)
    #     if not similar1:
    #         continue
    #     for item0 in similar0:
    #         for item1 in similar1:
    #             result.append({code0: item0, code1: item1})
    #             return


def prepare_combinations_3(database, full_location, result):
    if len(full_location) != 3:
        return
    location_variations = []
    for loc in full_location:
        location_variations.append(database.location_variations(loc))
    ppl_similar = database.get_similar_locations(location_variations[0], CityCode)
    region_similar = database.get_similar_locations(location_variations[1], RegionCode)
    country_similar = database.get_similar_locations(location_variations[2], CountryCode)

    if not ppl_similar or not region_similar or not country_similar:
        return
    if not country_similar:
         country_similar = database.get_similar_countries_with_hints(location_variations[2], ppl_similar, region_similar)
    if not region_similar:
         region_similar = database.get_similar_regions_with_hints(location_variations[1], ppl_similar, country_similar)
    if not ppl_similar:
         ppl_similar = database.get_similar_ppls_with_hints(location_variations[0], region_similar, country_similar)

    for ppl_item in ppl_similar:
        for region_item in region_similar:
            for country_item in country_similar:
                result.append({CityCode: ppl_item, RegionCode: region_item, CountryCode: country_item})


def sql_prepare_combinations_1(database, full_location, result):
    if len(full_location) != 1:
        return

    location_variants = database.location_variations(full_location[0])
    for level_ind in range(3):
        similar = database.sql_find_records_precisely_for_arr(location_variants, level_ind)
        if not similar:
            continue
        result += [{level_ind: similar_item} for similar_item in similar]
        return

    for level_ind in range(3):
        similar = database.sql_find_records_with_errs_for_arr(location_variants, level_ind)
        if not similar:
            continue
        result += [{level_ind: similar_item} for similar_item in similar]


def sql_prepare_combinations_2(database, full_location, result):
    if len(full_location) != 2:
        return

    level_combinations = [(CityLevel, CountryLevel), (CityLevel, RegionLevel), (RegionLevel, CountryLevel)]
    #, (RegionLevel, CityLevel),
    #(CountryLevel, RegionLevel), (CountryLevel, CityLevel)]

    variants0 = database.location_variations(full_location[0])
    variants1 = database.location_variations(full_location[1])

    for level0, level1 in level_combinations:
        similar0 = database.sql_find_records_precisely_for_arr(variants0, level0)
        if not similar0:
            continue
        similar1 = database.sql_find_records_precisely_for_arr(variants1, level1)
        if not similar1:
            continue
        for item0 in similar0:
            for item1 in similar1:
                result.append({level0: item0, level1: item1})
        return

    for level0, level1 in level_combinations:
        similar0 = database.sql_find_records_precisely_for_arr(variants0, level0)
        similar1 = database.sql_find_records_precisely_for_arr(variants1, level1)

        if not similar0:
            similar0 = database.sql_find_records_with_errs_for_arr(variants0, level0)
        if not similar1:
            similar1 = database.sql_find_records_with_errs_for_arr(variants1, level1)

        if similar0 and similar1:
            for item0 in similar0:
                for item1 in similar1:
                    result.append({level0: item0, level1: item1})
            return result


def append_2(result, items0, level0, items1, level1):
    for item0 in items0:
        for item1 in items1:
            result.append({level0: item0, level1: item1})


def append_1(result, items, level):
    for item in items:
        result.append({level: item})


def sql_prepare_combinations_3(database, full_location, result):
    if len(full_location) != 3:
        return
    location_variations = []
    for loc in full_location:
        location_variations.append(database.location_variations(loc))
    ppl_similar = database.sql_find_records_precisely_for_arr(location_variations[0], CityLevel)
    region_similar = database.sql_find_records_precisely_for_arr(location_variations[1], RegionLevel)
    country_similar = database.sql_find_records_precisely_for_arr(location_variations[2], CountryLevel)

    # wrong = 0
    # if not ppl_similar:
    #     wrong += 1
    # if not region_similar:
    #     wrong += 1
    # if not country_similar:
    #     wrong += 1
    # if wrong > 1:
    #     return

    if not ppl_similar:
        ppl_similar = database.sql_find_records_with_errs_for_arr(location_variations[0], CityLevel)
    if not region_similar:
        region_similar = database.sql_find_records_with_errs_for_arr(location_variations[1], RegionLevel)
    if not country_similar:
        country_similar = database.sql_find_records_with_errs_for_arr(location_variations[2], CountryLevel)

    if ppl_similar and region_similar and country_similar:
        for ppl_item in ppl_similar:
            for region_item in region_similar:
                for country_item in country_similar:
                    result.append({CityLevel: ppl_item, RegionLevel: region_item, CountryLevel: country_item})
    elif ppl_similar and region_similar:
        append_2(result, ppl_similar, CityLevel, region_similar, RegionLevel)
    elif ppl_similar and country_similar:
        append_2(result, ppl_similar, CityLevel, country_similar, CountryLevel)
    elif region_similar and country_similar:
        append_2(result, region_similar, RegionLevel, country_similar, CountryLevel)
    elif ppl_similar:
        append_1(result, ppl_similar, CityLevel)
    elif region_similar:
        append_1(result, region_similar, RegionLevel)
    elif country_similar:
        append_1(result, country_similar, CountryLevel)

def get_possible_combinations(database, full_location):
    combinations = []
    if (not full_location) or (len(full_location) > 3):
        eprint('Size of combination is bad:')
        return combinations

    if len(full_location) == 1:
        sql_prepare_combinations_1(database, full_location, combinations)
    elif len(full_location) == 2:
        sql_prepare_combinations_2(database, full_location, combinations)
    else:
        sql_prepare_combinations_3(database, full_location, combinations)
    # print(combinations)
    return combinations


def check_fine(num, location1, location2, fine, fine_message):
    if not location1 or not location2:
        fine += FineValues[num]
        fine_message += 'Location not found!'
    if 'geonameid' in location1 and 'geonameid' in location2 and location1['geonameid'] != location2['geonameid']:
        fine += FineValues[num]
        fine_message += FineMessages[num] + ': ' + location1['name'] + ', ' + location2['name'] + ' => fine + ' + str(FineValues[num])
    return fine, fine_message

def pop_fine(pop, max_pop):
    if max_pop == 0:
        return 0
    return 1 - pop / max_pop

def eval_fine(database, combination):
    location_exists = CityLevel in combination.keys()
    region_exists = RegionLevel in combination.keys()
    country_exists = CountryLevel in combination.keys()

    # print(location_exists, region_exists, country_exists)
    short_fine_message = 'fine for: '

    if location_exists:
        ppl, ppl_dist, ppl_origin, ppl_max_pop = combination[CityLevel]
        short_fine_message += ppl_origin + ', '
    if region_exists:
        region, region_dist, region_origin, region_max_pop = combination[RegionLevel]
        short_fine_message += region_origin + ', '
    if country_exists:
        country, country_dist, country_origin, country_max_pop = combination[CountryLevel]
        short_fine_message += country_origin + ', '

    total_fine_val = 0
    total_fine_messages = []
    short_fine_message += 'is: '

    pop_fine_val = 0
    pop_fine_messages = []
    if location_exists:
        fine = pop_fine(ppl['pop'], ppl_max_pop)
        pop_fine_val += fine
        if fine > 0:
            pop_fine_messages.append('Location: ' + ppl['name'] + ': ' + str(fine))
    if region_exists:
        fine = pop_fine(region['pop'], region_max_pop)
        pop_fine_val += fine
        if fine > 0:
            pop_fine_messages.append('Region: ' + region['name'] + ': ' + str(fine))
    if country_exists:
        fine = pop_fine(country['pop'], country_max_pop)
        pop_fine_val += fine
        if fine > 0:
            pop_fine_messages.append('Country: ' + country['name'] + ': ' + str(fine))

    total_fine_val += pop_fine_val
    total_fine_messages.append('Population fine:\n\t' + '\n\t'.join(pop_fine_messages))


    edit_distance_fine_val = 0
    edit_distance_fine_messages = []
    if location_exists and ppl_dist > 0:
        edit_distance_fine_val += ppl_dist
        edit_distance_fine_messages.append('Location: ' + ppl['name'] + ' - ' + ppl_origin + ': ' + str(
            ppl_dist) + '\n')
        short_fine_message += 'Mistake in city => +' + str(ppl_dist) + ', '
    if region_exists and region_dist > 0:
        edit_distance_fine_val += region_dist
        edit_distance_fine_messages.append('Region: ' + region['name'] + ' - ' + region_origin + ': ' + str(
            region_dist) + '\n')
        short_fine_message += 'Mistake in region => +' + str(region_dist) + ', '
    if country_exists and country_dist > 0:
        edit_distance_fine_val += country_dist
        edit_distance_fine_messages.append('Country: ' + country['name'] + ' - ' + country_origin + ': ' + str(
            country_dist) + '\n')
        short_fine_message += 'Mistake in country => +' + str(country_dist) + ', '
    if edit_distance_fine_messages:
        total_fine_val += edit_distance_fine_val
        total_fine_messages.append('Edit distance fine: \n\t' + '\n\t'.join(edit_distance_fine_messages))

    if location_exists:
        _, location_region, location_country = database.get_info_for_sql_record(ppl)
    if region_exists:
        _, region_country = database.get_country_for_sql_record(region)

    disc_fine_val = 0
    disc_fine_message = ''

    if location_exists and region_exists and country_exists:
        disc_fine_val, disc_fine_message = check_fine(0, location_region, region, disc_fine_val, disc_fine_message)
        disc_fine_val, disc_fine_message = check_fine(1, location_country, region_country, disc_fine_val, disc_fine_message)
        disc_fine_val, disc_fine_message = check_fine(2, region_country, country, disc_fine_val, disc_fine_message)
        disc_fine_val, disc_fine_message = check_fine(3, location_country, country, disc_fine_val, disc_fine_message)
    elif location_exists and region_exists:
        disc_fine_val, disc_fine_message = check_fine(0, location_region, region, disc_fine_val, disc_fine_message)
        disc_fine_val, disc_fine_message = check_fine(1, location_country, region_country, disc_fine_val, disc_fine_message)
    elif location_exists and country_exists:
        disc_fine_val, disc_fine_message = check_fine(3, location_country, country, disc_fine_val, disc_fine_message)
        if disc_fine_val < disc_fine_val:
            disc_fine_val = disc_fine_val
            disc_fine_message = disc_fine_message
    elif region_exists and country_exists:
        disc_fine_val, disc_fine_message = check_fine(2, region_country, country, disc_fine_val, disc_fine_message)
        if disc_fine_val < disc_fine_val:
            disc_fine_val = disc_fine_val
            disc_fine_message = disc_fine_message

    if disc_fine_message:
        short_fine_message += disc_fine_message
        disc_fine_message = 'Discrepancy fine: \n' + disc_fine_message
        total_fine_val += disc_fine_val
        total_fine_messages.append(disc_fine_message)

    #if total_fine_val > 0:
    #   eprint(short_fine_message)
    return total_fine_val, '\n'.join(total_fine_messages)


def extract_location(line):
    loc = p.search(line).group(1)
    loc = loc.split(',')
    loc = [s.strip() for s in loc]
    return loc


# main func
def obtain_location(database, full_location):
    combinations = get_possible_combinations(database, full_location)
    eprint('== Getting possible combinations done, total:', len(combinations), '==')

    fined_combinations = []
    for combination in combinations:
        fine, message = eval_fine(database, combination)
        fined_combinations.append((combination, fine, message))
    sorted_combinations = sorted(fined_combinations, key=lambda tup: tup[1])
    eprint('== Fine evaluating and sorting done ==')

    return sorted_combinations


def get_region_name(database, geonameid):
    names = database.sql_find_names(geonameid, RegionLevel)
    if not names:
        return ''
    # region_signs = ['область', "oblast'", 'region']
    # for name in names:
    #     if region_signs[0] in name:
    #         return name
    # for name in names:
    #     if any(sign in name for sign in region_signs):
    #         return name
    return names[0]

isascii = lambda s: len(s) == len(s.encode())

def get_country_name(database, geonameid):
    names = database.sql_find_names(geonameid, CountryLevel)
    if not names:
        return ''
    return names[0]
    # min_len = len(names[0])
    # min_name = names[0]
    # for name in names:
    #     if len(name) < min_len and isascii(name):
    #         min_len = len(name)
    #         min_name = name
    # return min_name

def get_cyrillic_name(database, level_ind, geonameid):
    if level_ind == RegionLevel:
        return get_region_name(database, geonameid)
    elif level_ind == CountryLevel:
        return get_country_name(database, geonameid)

    names = database.sql_find_names(geonameid, level_ind)
    if names:
        return names[0]
    else:
        return ''

    # orig_name_set = set(tr.translit(names[0], 'ru'))
    #
    # max_inters = 0
    # max_name = names[0]
    # for name in names:
    #     inters = 0
    #     for char in name:
    #         if char.isalpha():
    #             if char in orig_name_set:
    #                 inters += 1
    #             elif not char in RussianLetters:
    #                 max_inters = 0
    #                 break
    #     if inters > max_inters:
    #         max_inters = inters
    #         max_name = name
    # return max_name


def prepare_combination(database, combination):
    location, fine, message = combination[0], combination[1], combination[2]
    ppl_exists = CityLevel in location
    region_exists = RegionLevel in location
    country_exists = CountryLevel in location

    if ppl_exists and (not region_exists or not country_exists):
        success, region, country = database.get_info_for_sql_record(location[CityLevel][0])
        if success:
            if not region_exists:
                location[RegionLevel] = (region, 0, '')
            if not country_exists:
                location[CountryLevel] = (country, 0, '')
    elif region_exists and not country_exists:
        region = location[RegionLevel][0]
        country_code = region['country']
        if country_code in database.RegionsMap and '00' in database.RegionsMap[country_code]:
            country = database.RegionsMap[country_code]['00']
            if country:
                location[CountryLevel] = (country, 0, '')

    toponims = []
    for level in range(len(Levels) - 1, -1, -1):
        if level in location:
            entry = get_cyrillic_name(database, level, location[level][0]['geonameid'])
            toponims.append(LavelNames[level] + ': ' + entry)

    result = '; '.join(toponims)
    ready_combination = result

    result = '\n[[ ' + result + ' ]]'
    if fine > 0:
        commented_combination = result + '\nTotal fine: ' + str(fine) + '\nMessage:\n' + message
    else:
        commented_combination = result

    return ready_combination, commented_combination


def obtain_locations(database, input_file, output_file, output_bad_file):
    with open(output_file, 'w') as out:
        with open(output_bad_file, 'w') as out_bad:
            with open(input_file, 'r', encoding='UTF-8') as inp:
                total_loc_num = sum(1 for line in inp)
                inp.seek(0)
                for line_num, line in enumerate(inp):
                    old_loc = line
                    loc = [s.strip() for s in line.split(',')]

                    eprint('\n\n=== Obtaining ' + str(loc), '===')
                    start = time.time()

                    try:
                        sorted_comb = obtain_location(database, loc)
                        eprint('Time spent:', time.time() - start)

                        if sorted_comb:
                            ready, comm = prepare_combination(database, sorted_comb[0])
                            if sorted_comb[0][1] <= MinFine:
                                #new_loc = LocationPrefix + ready[0] + LocationSuffix
                                out.write(';'.join(loc) + '\t\t' + ready + '\n')
                            else:
                                new_loc = LocationNA
                                eprint('TOO HIGH FINE, SET TO NA')
                                out_bad.write(old_loc)

                            eprint(comm)
                        else:
                            out_bad.write(old_loc)
                            eprint("Location set to NA: it's components don't look like toponims\n")
                            new_loc = LocationNA
                    except Exception as ex:
                        out_bad.write(old_loc)
                        eprint("An exception occured: %s\n" % ex)

                    sys.stderr.write("At location %d out of %d: %d%%\r" % (line_num, total_loc_num, line_num / total_loc_num * 100))
                    sys.stderr.flush()
                    #line = line.replace(old_loc, new_loc)
                    #out.write(line)


def append_toponims(toponims, author_name, geonameid, level_ind):
    toponims.write(author_name + '\t' + str(geonameid) + '\t' + str(level_ind) + '\n')


def try_insert_city(database, toponims, cities_from_pl, regions_for_cities, regions_from_pl, author_name):
    for reg_id_ind in range(len(regions_for_cities)):
        for region in regions_from_pl:
            if regions_for_cities[reg_id_ind] == region['geonameid']:
                append_toponims(toponims, author_name, cities_from_pl[reg_id_ind]['geonameid'], CityLevel)
                return True

    return False

def obtain_toponims(database):
    df = pd.read_csv('toponims-utf8/toponims-utf8.txt', '\t')

    toponims_name = 'toponims-utf8/toponims_obtained.txt'
    failed_toponims = pd.DataFrame()

    with open(toponims_name, 'w') as toponims:
        for _, record in df.iterrows():
            author_name = record[['author_name']].to_string(index=False, header=False, na_rep='')
            place = record[['place']].to_string(index=False, header=False, na_rep='')
            region = record[['region']].to_string(index=False, header=False, na_rep='')

            cities_from_pl = database.sql_find_records_precisely(place, CityLevel)
            regions_for_cities = []
            if len(cities_from_pl) == 1:
                city_ = cities_from_pl[0]
                append_toponims(toponims, author_name, city_['geonameid'], CityLevel)
                continue
            elif cities_from_pl:
                for city in cities_from_pl:
                    regions_for_cities.append(database.sql_get_region_id(city['geonameid']))

            regions_from_pl = database.sql_find_records_precisely(place, RegionLevel)
            if regions_from_pl and not try_insert_city(database, toponims, cities_from_pl, regions_for_cities, regions_from_pl, author_name):
                region_ = regions_from_pl[0]
                append_toponims(toponims, author_name, region_['geonameid'], RegionLevel)
                continue

            regions_from_rg = database.sql_find_records_precisely(region, RegionLevel)
            if regions_from_rg and not try_insert_city(database, toponims, cities_from_pl, regions_for_cities, regions_from_rg, author_name):
                region_ = regions_from_rg[0]
                append_toponims(toponims, author_name, region_['geonameid'], RegionLevel)
                continue

            country_from_rg = database.sql_find_records_precisely(region, CountryLevel)
            if country_from_rg:
                country_ = country_from_rg[0]
                region_['geonameid'], RegionLevel
                append_toponims(toponims, author_name, country_['geonameid'], CountryLevel)
                continue

            print('failed with', author_name)
            failed_toponims.append(record)


def main(argv):
    if len(argv) != 3:
        eprint('Usage: script.py input output output_bad')
        return
    input_file = argv[0]
    output_file = argv[1]
    output_bad_file = argv[2]

    database = Database()
    eprint('==== Database loading done ====')

    #print(database.RegionsMap)
    #print(database.geonames_ppl.shape, database.geonames_region.shape, database.geonames_country.shape)

    #print(database.get_ppls('Isparta'))
    # s# print(records)
    #country_codes = ['RU']
    #region_codes = ['01', '02', '37']
    #recs = database.geonames_ppl.ix[(database.geonames_ppl['ccode'].isin(country_codes)) & ~(database.geonames_ppl['acode1'].isin(region_codes))]

    #recs_ = recs.ix[recs['acode1'].isin(region_codes)]
    #database.get_similar_ppls_with_hints()

    obtain_locations(database, input_file, output_file, output_bad_file)
    #obtain_toponims(database)

    eprint('==== Obtaining locations done ====')

    database.unload()


if __name__ == "__main__":
    main(sys.argv[1:])
