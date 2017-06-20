import geonames as geo
import pandas as pd



#db = geo.Database()
# read data
geonames_ppl = pd.read_csv('database/all_ppls.csv', '\t', dtype = {'acode1': object})
geonames_region = pd.read_csv('database/all_regions.csv', '\t', dtype = {'acode1': object})
geonames_country = pd.read_csv('database/all_countries.csv', '\t', dtype = {'acode1': object})

def csv():

    geonames = pd.read_csv('../geonames/geonames_all.csv', '\t',
                           dtype={'altnames': object, 'cc2': object, 'acode1': object, 'acode2': object,
                                  'acode3': object, 'acode4': object})
    geonames_ = geonames[['geonameid', 'name', 'altnames', 'fclass', 'fcode', 'ccode', 'acode1', 'pop']]

    # csv: ppl
    print('csv: ppl')
    CountriesSupported = ['RU', 'UA', 'BY', 'KZ']
    ppls_sng = geonames_.ix[(bool(geonames_.fcode.notnull)) & (geonames_.fcode.str.startswith('PPL')) & (
    geonames_['ccode'].isin(CountriesSupported))]

    ppls_1000 = pd.read_csv('../geonames/cities1000.txt', '\t',
                            dtype={'altnames': object, 'cc2': object, 'acode1': object, 'acode2': object, 'acode3': object, 'acode4': object})
    ppls_1000_ = ppls_1000[['geonameid', 'name', 'altnames', 'fclass', 'fcode', 'ccode', 'acode1', 'pop']]

    ppls = ppls_1000_
    ppls_no_sng = ppls.ix[~(ppls['ccode'].isin(CountriesSupported))]

    ppls_all = ppls_sng.append(ppls_no_sng)

    print(ppls.shape, ppls_no_sng.shape)
    print(ppls_sng.shape, ppls_all.shape)

    ppls_all.to_csv('../geonames/all_ppls.csv', sep='\t', index=False)

    # csv: region
    print('csv: region')
    geonames_region = geonames_.ix[(bool(geonames_.fcode.notnull)) & (geonames_.fcode.str.startswith('ADM'))]
    geonames_region.to_csv('../geonames/all_regions.csv', sep='\t', index=False)

    # csv: country
    print('csv: country')
    geonames_country = geonames_.ix[(bool(geonames_.fcode.notnull)) & (geonames_.fcode.str.startswith('PCL'))]
    geonames_country.to_csv('../geonames/all_countries.csv', sep='\t', index=False)


def geo():
    geo_cn = geonames_country[['geonameid', 'fclass', 'fcode', 'ccode', 'acode1', 'pop']]
    geo_cn.to_csv('database/geo_cn.csv', sep='\t', index=False, columns=['geonameid', 'fclass', 'fcode', 'ccode', 'acode1', 'pop'])

    print(geonames_region.columns)
    geo_rn = geonames_region[['geonameid', 'fclass', 'fcode', 'ccode', 'acode1', 'pop']]
    geo_rn.to_csv('database/geo_rn.csv', sep='\t', index=False, columns=['geonameid', 'fclass', 'fcode', 'ccode', 'acode1', 'pop'])

    geo_ppl = geonames_ppl[['geonameid', 'fclass', 'fcode', 'ccode', 'acode1', 'pop']]
    geo_ppl.to_csv('database/geo_ppl.csv', sep='\t', index=False, columns=['geonameid', 'fclass', 'fcode', 'ccode', 'acode1', 'pop'])

def geo_names():
    # countries
    print('countries')
    print(geonames_country.shape)

    d = []
    for _, record in geonames_country.iterrows():
        names = [record['name']]
        names += record['altnames'].split(',')
        for i in range(len(names)):
            d.append({'geonameid': record['geonameid'], 'recordid': i, 'name': names[i], 'lower_name': names[i].lower()})

    geonames_country_names = pd.DataFrame(d)
    print(geonames_country_names.shape)
    print(geonames_country_names[:10])
    geonames_country_names.to_csv('database/geo_cn_names.csv', sep='\t', index=False, columns=['geonameid', 'recordid', 'name', 'lower_name'])

    # regions
    print('regions')
    print(geonames_region.shape)

    d = []
    for _, record in geonames_region.iterrows():
        if pd.notnull(record['name']):
            names = [record['name']]
        else:
            names = []
        if pd.notnull(record['altnames']):
            names += record['altnames'].split(',')
        for i in range(len(names)):
            d.append({'geonameid': record['geonameid'], 'recordid': i, 'name': names[i], 'lower_name': names[i].lower()})

    geonames_region_names = pd.DataFrame(d)
    print(geonames_region_names.shape)
    print(geonames_region_names[:10])
    geonames_region_names.to_csv('database/geo_rn_names.csv', sep='\t', index=False, columns=['geonameid', 'recordid', 'name', 'lower_name'])


    # ppls
    print('ppls')
    print(geonames_ppl.shape)

    d = []
    for _, record in geonames_ppl.iterrows():
        if pd.notnull(record['name']):
            names = [record['name']]
        else:
            names = []
        if pd.notnull(record['altnames']):
            names += record['altnames'].split(',')
        for i in range(len(names)):
            d.append({'geonameid': record['geonameid'], 'recordid': i, 'name': names[i], 'lower_name': names[i].lower()})

    geonames_ppl_names = pd.DataFrame(d)
    print(geonames_ppl_names.shape)
    print(geonames_ppl_names[:10])
    geonames_ppl_names.to_csv('database/geo_ppl_names.csv', sep='\t', index=False, columns=['geonameid', 'recordid', 'name', 'lower_name'])

# csv()
geo()
# geo_names()