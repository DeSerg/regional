from __future__ import print_function
def eprint(*args, **kwargs):
    print(*args, file=sys.stdout, **kwargs)
from pandas import read_csv
import pandas as pd
import transliterate as tr
import sys
import re
import psycopg2

import warnings
warnings.filterwarnings("ignore", 'This pattern has match groups')

# some initializations
CountriesSupported = ['RU', 'UA', 'BY', 'KZ']

LocationCodes = ['PCL', 'ADM', 'PPL']
CityCode = LocationCodes[2]
RegionCode = LocationCodes[1]
CountryCode = LocationCodes[0]

#Levels = ['город', 'регион', 'страна']
#City, Region, Country = Levels[0], Levels[1], Levels[2]

Levels = ['cn', 'rn', 'ppl']
LevelsOrigin = ['country', 'region', 'ppl']
CityLevel = 2
RegionLevel = 1
CountryLevel = 0
LavelNames = ['country', 'region', 'city']


MaxDist = 0.55
MinFine = 9
FineValues = [10, 10, 10, 10]
FineMessages = [
    'Location region not equal to the region',
    'Location country not equal to region country',
    'Region country not equal to country',
    'Location country not equal to country'
]

p = re.compile("<Location><o>(.*?)</o></Location>")

LocationPrefix = '<Location><o>'
LocationSuffix = '</o></Location>'
LocationNA = '<Location><o> NA </o></Location>'


def char_range(c1, c2):
    """Generates the characters from `c1` to `c2`, inclusive."""
    for c in range(ord(c1), ord(c2)+1):
        yield chr(c)

RussianLetters = set(list(char_range('а', 'я')) + list(char_range('А', 'Я')))

database_path = '../../data/standart_locations/database/'


class Database:
    MaxEditDistance = 1
    RegionsMap = {}

    conn = psycopg2.connect("dbname=geonames user=deserg")
    cursor = conn.cursor()

    #    geonames = pd.DataFrame
    geonames_ppl = pd.DataFrame()
    geonames_region = pd.DataFrame()
    geonames_country = pd.DataFrame()

    def __init__(self):
        #self.cursor.execute('select set_limit(0.55);')
        # self.__load()
        self.__parse_region_map()

    # Loading
    # def __load(self):
        # pandas database is deprecated
        # self.geonames_ppl = read_csv(database_path + 'all_ppls.csv',  sep='\t', dtype = {'acode1': object})
        # self.geonames_region = read_csv(database_path + 'all_regions.csv', sep='\t', dtype = {'acode1': object})
        # self.geonames_country = read_csv(database_path + 'all_countries.csv', sep='\t', dtype = {'acode1': object})

    def __parse_region_map(self):
        countries_db = pd.read_csv(database_path + 'countryInfo.txt', sep='\t')

        for _, record in countries_db.iterrows():
            iso = record['ISO']
            geonameid = record['geonameid']
            if iso not in self.RegionsMap.keys():
                self.RegionsMap[iso] = {}
            self.RegionsMap[iso]['00'] = self.sql_find_by_id(geonameid, CountryLevel)

        regions_db = pd.read_csv(database_path + 'admin1Codes.txt', sep='\t')
        for _, record in regions_db.iterrows():
            iso_code = record['iso_code']
            geonameid = record['geonameid']
            iso, code = iso_code.split('.', 1)
            if iso not in self.RegionsMap.keys():
                self.RegionsMap[iso] = {}
            self.RegionsMap[iso][code] = self.sql_find_by_id(geonameid, RegionLevel)

    # Unloading
    def unload(self):
        self.conn.commit()

    # SQL
    find_precisely_command = """select distinct on (a.geonameid) *, b.name from geo_{0} a inner join geo_{0}_names b
        on a.geonameid = b.geonameid
        where b.lower_name = $${1}$$;"""

    find_id_precisely_command = """select * from geo_{0} where geonameid = {1};"""

    find_with_errs_command = """
        select distinct on (geonameid) * from 
        (select a.geonameid, a.fclass, a.fcode, a.ccode, a.acode, a.pop, b.lower_name <-> $${1}$$ AS dist
        from geo_{0} a
        inner join geo_{0}_names b
        on a.geonameid = b.geonameid
        order by dist
        limit 5) as res;"""

    find_orig_names_command = """select name from geonames_{0} where geonameid = {1};"""
    find_names_command = """select name from geo_{0}_names where geonameid = {1};"""

    # Place: 'geonameid', 'name', 'class', 'code', 'country', 'region'
    def sql_place_from_sql_record(self, record):

        place = {}
        geonameid = record[0]
        code = record[2]

        place['geonameid'] = geonameid
        place['class'] = record[1]
        place['code'] = code
        place['country'] = record[3]
        place['region'] = record[4]
        place['pop'] = record[5]
        if len(record) > 8:
            place['name'] = record[8]
        else:
            if code.startswith('PCL'):
                place['name'] = self.sql_find_orig_name(geonameid, CountryLevel)
            elif code.startswith('ADM'):
                place['name'] = self.sql_find_orig_name(geonameid, RegionLevel)
            elif code.startswith('PPL'):
                place['name'] = self.sql_find_orig_name(geonameid, CityLevel)
        return place

    def sql_place_from_pd_record(self, record):
        place = {}
        place['geonameid'] = record[['geonameid']].to_string(index=False, header=False, na_rep='')
        place['class'] = record[['fclass']].to_string(index=False, header=False, na_rep='')
        place['code'] = record[['fcode']].to_string(index=False, header=False, na_rep='')
        place['country'] = record[['ccode']].to_string(index=False, header=False, na_rep='')
        place['region'] = record[['acode1']].to_string(index=False, header=False, na_rep='')
        place['name'] = record[['name']].to_string(index=False, header=False, na_rep='')
        return place

    def sql_find_by_id(self, geonameid, level_ind):
        if level_ind < 0 or level_ind >= len(Levels):
            return []
        try:
            self.cursor.execute(self.find_id_precisely_command.format(Levels[level_ind], geonameid))
        except Exception as ex:
            eprint(ex)
            self.conn.rollback()
            return []
        self.conn.commit()
        tup = self.cursor.fetchone()
        if tup:
            return self.sql_place_from_sql_record(tup)
        else:
            return {}

    def sql_find_records_precisely(self, location, level_ind):
        if level_ind < 0 or level_ind >= len(Levels):
            return []
        try:
            self.cursor.execute(self.find_precisely_command.format(Levels[level_ind], location))
        except Exception as ex:
            eprint(ex)
            self.conn.rollback()
            return []
        list_tup = self.cursor.fetchall()
        self.conn.commit()
        max_pop = 0
        places = []
        for tup in list_tup:
            place = self.sql_place_from_sql_record(tup)
            places.append(place)
            if place['pop'] > max_pop:
                max_pop = place['pop']

        results = []
        for place in places:
            results.append((place, 0.0, location, max_pop))

        return results

    def sql_find_records_precisely_for_arr(self, locations, level_ind):
        for location in locations:
            records = self.sql_find_records_precisely(location, level_ind)
            if records:
                return records
        return []

    def sql_find_records_with_errs(self, location, level_ind):
        if level_ind < 0 or level_ind >= len(Levels):
            return []

        try:
            self.cursor.execute(self.find_with_errs_command.format(Levels[level_ind], location))
        except Exception as ex:
            eprint(ex)
            self.conn.rollback()
            return []

        list_tup = self.cursor.fetchall()
        self.conn.commit()

        max_pop = 0
        for tup in list_tup:
            if tup[5] > max_pop:
                max_pop = tup[5]

        results = []
        for tup in list_tup:
            if tup[6] < MaxDist:
                results.append((self.sql_place_from_sql_record(tup), tup[6], location, max_pop))

        return results

    def sql_find_records_with_errs_for_arr(self, locations, level_ind):
        for location in locations:
            records = self.sql_find_records_with_errs(location, level_ind)
            if records:
                return records
        return []

    def sql_find_orig_name(self, geonameid, level_ind):
        try:
            self.cursor.execute(self.find_orig_names_command.format(LevelsOrigin[level_ind], geonameid))
        except Exception as ex:
            eprint(ex)
            self.conn.rollback()
            return ''
        tup = self.cursor.fetchone()
        if tup:
            return tup[0]
        else:
            return ''

    def sql_find_names(self, geonameid, level_ind):
        if level_ind < 0 or level_ind >= len(Levels):
            return []

        results = []
        try:
            self.cursor.execute(self.find_orig_names_command.format(LevelsOrigin[level_ind], geonameid))
        except Exception as ex:
            eprint(ex)
            self.conn.rollback()
            return []
        tup = self.cursor.fetchone()
        if tup:
            results.append(tup[0])
        else:
            return []

        try:
            self.cursor.execute(self.find_names_command.format(Levels[level_ind], geonameid))
        except Exception as ex:
            eprint(ex)
            self.conn.rollback()
            return []

        list_tup = self.cursor.fetchall()
        for tup in list_tup:
            results.append(tup[0])
        return results

    def sql_get_region_id(self, geonameid):
        rows = self.sql_find_by_id(geonameid, self.CityLevel)
        ans = []
        for row in rows:
            country_ = row['country']
            region_ = row['region']
            try:
                rec_ = self.RegionsMap[country_][region_]
                ans.append(rec_[['geonameid']])
            except Exception:
                continue



    # Pandas
    def get_ppl_by_id(self, id, message = True):
        records = self.geonames_ppl.ix[self.geonames_ppl['geonameid'] == id]
        if records.empty:
            if message:
                eprint('Failed to find ppl with id', id)
            return default_dataframe()
        else:
            return records.iloc[0]

    def get_region_by_id(self, id, message = True):
        records = self.geonames_region.ix[self.geonames_region['geonameid'] == id]
        if records.empty:
            if message:
                eprint('Failed to find region with id', id)
            return default_dataframe()
        else:
            return records.iloc[0]

    def get_country_by_id(self, id, message = True):
        records = self.geonames_country.ix[self.geonames_country['geonameid'] == id]
        if records.empty:
            if message:
                eprint('Failed to find country with id', id)
            return default_dataframe()
        else:
            return records.iloc[0]

    def get_record_by_id(self, id, message = True):
        rec = self.get_country_by_id(id, False)
        if not rec.empty:
            return rec
        rec = self.get_region_by_id(id, False)
        if not rec.empty:
            return rec
        rec = self.get_ppl_by_id(id, False)
        if not rec.empty:
            return rec
        if message:
            eprint('Failed to find record with id', id)
        return default_dataframe()

    def get_records_for_code(self, location, fcode_start):
        records_for_fcode = self.geonames.ix[(bool(self.geonames.fcode.notnull)) & (self.geonames.fcode.str.startswith(fcode_start))]
        return get_records_for_location(records_for_fcode, location)

    def get_records_for_code_with_errs(self, location, fcode_start, max_edit_distance=MaxEditDistance):
        records_for_fcode = self.geonames.ix[(bool(self.geonames.fcode.notnull)) & (self.geonames.fcode.str.startswith(fcode_start))]
        return get_records_for_location_with_errs(records_for_fcode, location, max_edit_distance)

    def get_records_for_class(self, location, fclass):
        records_for_fclass = self.geonames.ix[self.geonames.fclass == fclass]
        return get_records_for_location(records_for_fclass, location)

    def get_records_for_class_with_errs(self, location, fclass, max_edit_distance = MaxEditDistance):
        records_for_fclass = self.geonames.ix[self.geonames.fclass == fclass]
        return get_records_for_location_with_errs(records_for_fclass, location, max_edit_distance)

    # Populated places
    def get_ppls(self, name):
        return get_records_for_location(self.geonames_ppl, name)

    def get_ppls_with_errs(self, names, max_edit_distance=MaxEditDistance):
        return get_records_for_location_with_errs(self.geonames_ppl, names, max_edit_distance)

    # Regions
    def get_regions(self, name):
        return get_records_for_location(self.geonames_region, name)

    def get_regions_with_errs(self, names, max_edit_distance=MaxEditDistance):
        return get_records_for_location_with_errs(self.geonames_region, names, max_edit_distance)

    # Countries
    def get_countries(self, name):
        return get_records_for_location(self.geonames_country, name)

    def get_countries_with_errs(self, names, max_edit_distance=MaxEditDistance):
        return get_records_for_location_with_errs(self.geonames_country, names, max_edit_distance)

    # Switcher between PANDAS functions by code:
    def get_records(self, name, code):
        if code == CityCode:
            return self.get_ppls(name)
        elif code == RegionCode:
            return self.get_regions(name)
        else:
            return self.get_countries(name)

    def get_records_from_arr(self, names, code):
        for name in names:
            records = self.get_records(name, code)
            if not records.empty:
                return records, name
        return default_dataframe(), ''

    def get_records_with_errs(self, names, code, max_edit_distance=MaxEditDistance):
        if code == CityCode:
            return self.get_ppls_with_errs(names, max_edit_distance)
        elif code == RegionCode:
            return self.get_regions_with_errs(names, max_edit_distance)
        else:
            return self.get_countries_with_errs(names, max_edit_distance)

    # Toponim helpers
    def get_regions_for_ppl(self, populated_place):
        ppls = self.get_ppls(populated_place)
        regions = pd.DataFrame()
        for row_id, row in ppls.iterrows():
            names = [row['name']] + row['altnames'].split(',')
            if populated_place in names:
                country = row['ccode']
                try:
                    region_num = int(row['acode1'])
                except ValueError:
                    eprint('get_regions(', populated_place, '): bad region num in record for', names[0])
                    continue
                region = self.RegionsMap[country][region_num]
                regions.append(region)
        regions = regions[~regions.geonameid.duplicated(keep='first')]
        return [region for _, region in regions.iterrows()]

    def get_countries_for_region(self, region):
        regions = self.get_regions(region)
        countires = pd.DataFrame()
        for _, record in regions.iterrows():
            country_alias = record.ccode
            countires.append(self.RegionsMap[country_alias]['00'])
        countries = countires[~countires.geonameid.duplicated(keep='first')]
        return [country for _, country in countires.iterrows()]

    def get_region_for_record(self, record):
        try:
            country = record.ccode
            region_num = int(record.acode1)
            region = self.RegionsMap[country][region_num]
            return True, region
        except Exception:
            eprint('get_region_for_record(', record.name, '): bad region num: ', record.acode1, sep='')
            return False, pd.DataFrame()

    def get_country_for_record(self, record):
        country_alias = record.ccode
        if country_alias in self.RegionsMap:
            country = self.RegionsMap[country_alias]['00']
            return True, country
        else:
            return False, pd.Series()

    def get_info_for_record(self, record):
        try:
            country = record.ccode
            region_num = record.acode1
            region = self.RegionsMap[country][region_num]
            country = self.RegionsMap[country]['00']
            return True, region, country
        except Exception:
            eprint('get_info_for_record(', record.name, '): bad region num: ', record.acode1, sep='')
            return False, pd.DataFrame(), pd.DataFrame()

    def get_info_for_ppl(self, ppl):
        regions = self.get_regions_for_ppl(ppl)
        info = []
        for _, region in regions:
            country = self.get_country_for_record(region)
            info.append((region, country))
        return info

    def get_country_for_sql_record(self, record):
        country_alias = record['country']
        if country_alias in self.RegionsMap:
            country = self.RegionsMap[country_alias]['00']
            if country:
                return True, country
            else:
                return False, {}
        else:
            return False, {}

    def get_info_for_sql_record(self, record):
        try:
            country = record['country']
            region_num = record['region']
            region = self.RegionsMap[country][region_num]
            country = self.RegionsMap[country]['00']
            if region and country:
                return True, region, country
            else:
                return False, {}, {}
        except Exception as ex:
            eprint(ex, '\nget_info_for_record(', record['name'], '): bad region num: ', record['region'], sep='')
            return False, {}, {}


    # Find location in database
    def location_variations(self, location):
        possible_chars = ["'", "`", "-"]

        location_filtered = ''
        for ch in location:
            if ch.isalpha() or ch.isspace() or ch in possible_chars:
                location_filtered += ch.lower()
        location_filtered = location_filtered.strip()

        if not location_filtered:
            return []

        locations = [tr.translit(location_filtered, 'ru', reversed=True), location_filtered, tr.translit(location_filtered, 'ru')]
        fin_locations = list(set(locations))
        return sorted(fin_locations)

    def prepare_similar(self, records, edit_distances, location):
        similar = []
        i = 0
        for _, record in records.iterrows():
            similar.append((record, location, edit_distances[i]))
            i += 1
        return similar

    def get_similar_locations(self, locations, code):
        # TODO - find in topoims.utf8.txt if records are empty
        records, fit_location = self.get_records_from_arr(locations, code)
        if records.empty:
            return []

        edit_distances = [0 for i in range(len(records))]
        return self.prepare_similar(records, edit_distances, fit_location)

    def get_similar_locations_with_errs(self, locations, code, max_edit_distance=MaxEditDistance):
        records, edit_distances, fit_location = self.get_records_with_errs(locations, code, max_edit_distance)
        if records.empty:
            return []
        return self.prepare_similar(records, edit_distances, fit_location)

    # Methods for getting similar locations using other types of locations
    def get_similar_ppls_with_hints(self, locations, similar_regions, similar_countries, max_edit_distance=MaxEditDistance):
        region_codes = []
        for region, _, _ in similar_regions:
            region_codes.append(region['acode1'])

        if similar_regions:
            hinted_records_raw = self.geonames_ppl.ix[(self.geonames_ppl['acode1'].isin(region_codes))]
            hinted_records, edit_distances, fit_location = get_records_for_location_with_errs(hinted_records_raw, locations, max_edit_distance)
            if not hinted_records.empty:
                return self.prepare_similar(hinted_records, edit_distances, fit_location)

        country_codes = []
        for country, _, _ in similar_countries:
            country_codes.append(country['ccode'])
        if similar_countries:
            hinted_records_raw = self.geonames_ppl.ix[(self.geonames_ppl['ccode'].isin(country_codes)) & ~(self.geonames_ppl['acode1'].isin(region_codes))]
            hinted_records, edit_distances, fit_location = get_records_for_location_with_errs(hinted_records_raw, locations, max_edit_distance)
            if not hinted_records.empty:
                return self.prepare_similar(hinted_records, edit_distances, fit_location)

        hinted_records_raw = self.geonames_ppl.ix[~(self.geonames_ppl['ccode'].isin(country_codes)) & ~(self.geonames_ppl['acode1'].isin(region_codes))]
        hinted_records, edit_distances, fit_location = get_records_for_location_with_errs(hinted_records_raw, locations, max_edit_distance)
        return self.prepare_similar(hinted_records, edit_distances, fit_location)

    def get_similar_regions_with_hints(self, locations, similar_ppls, similar_countries, max_edit_distance=MaxEditDistance):
        df = pd.DataFrame()
        for ppl, _, _ in similar_ppls:
            succ, region = self.get_region_for_record(ppl)
            if not succ:
                continue
            df = df[0:0]
            df = df.append(region)
            hinted_records, edit_distances, fit_location = get_records_for_location_with_errs(df, locations, max_edit_distance)
            if not hinted_records.empty:
                return self.prepare_similar(hinted_records, edit_distances, fit_location)

        country_codes = []
        for country, _, _ in similar_countries:
            country_codes.append(country['ccode'])
        if similar_countries:
            hinted_records_raw = self.geonames_ppl.ix[self.geonames_ppl['ccode'].isin(country_codes)]
            hinted_records, edit_distances, fit_location = get_records_for_location_with_errs(hinted_records_raw, locations, max_edit_distance)
            if not hinted_records.empty:
                return self.prepare_similar(hinted_records, edit_distances, fit_location)

        hinted_records_raw = self.geonames_ppl.ix[~(self.geonames_ppl['ccode'].isin(country_codes))]
        hinted_records, edit_distances, fit_location = get_records_for_location_with_errs(hinted_records_raw, locations, max_edit_distance)
        return self.prepare_similar(hinted_records, edit_distances, fit_location)

    def get_similar_countries_with_hints(self, locations, similar_ppls, similar_regions, max_edit_distance=MaxEditDistance):
        df = pd.DataFrame()
        for region, _, _ in similar_regions:
            succ, country = self.get_country_for_record(region)
            if not succ:
                continue
            df = df[0:0]
            df = df.append(country)
            hinted_records, edit_distances, fit_location = get_records_for_location_with_errs(df, locations, max_edit_distance)
            if not hinted_records.empty:
                return self.prepare_similar(hinted_records, edit_distances, fit_location)

        for ppl, _, _ in similar_ppls:
            succ, country = self.get_country_for_record(ppl)
            if not succ:
                continue
            return (self.sql_place_from_pd_record(country), 0, )
            df = df[0:0]
            df = df.append(country)
            hinted_records, edit_distances, fit_location = get_records_for_location_with_errs(df, locations, max_edit_distance)
            if not hinted_records.empty:
                return self.prepare_similar(hinted_records, edit_distances, fit_location)

        return self.get_similar_locations_with_errs(locations, CountryCode, max_edit_distance)
