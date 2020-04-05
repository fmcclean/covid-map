import urllib.request
import json
import pandas as pd


def boundaries():
    with urllib.request.urlopen(
            "https://opendata.arcgis.com/datasets/d5dfaace0bbd4dea9255020b3c53284f_0.geojson") as url:
        geojson = json.loads(url.read().decode())

    with urllib.request.urlopen(
            "https://opendata.arcgis.com/datasets/629c303e07ee4ad09a4dfd0bfea499ec_0.geojson") as url:
        countries = json.loads(url.read().decode())

    with open('data/scotland.geojson') as f:
        scotland = json.load(f)

    geojson['features'] = [feature for feature in geojson['features']
                           if feature['properties']['ctyua19cd'].startswith('E')]

    countries['features'] = [feature for feature in countries['features']
                             if not feature['properties']['ctry18cd'][0].startswith('E')]

    for feature in geojson['features']:
        feature['properties'] = {'code': feature['properties']['ctyua19cd']}

    for feature in countries['features']:
        feature['properties'] = {'code': feature['properties']['ctry18cd']}

    for feature in scotland['features']:
        feature['properties'] = {'code': feature['properties']['HBCode']}

    geojson['features'].extend(countries['features'])
    geojson['features'].extend(scotland['features'])

    with open('data/boundaries.geojson', 'w') as f:
        json.dump(geojson, f)

    return geojson


def population():
    req = urllib.request.Request(
        'https://www.ons.gov.uk/file?uri=%2fpeoplepopulationandcommunity%2fpopulationandmigration%2fpopu'
        'lationestimates%2fdatasets%2fpopulationestimatesforukenglandandwalesscotlandandnorthernireland%'
        '2fmid20182019laboundaries/ukmidyearestimates20182019ladcodes.xls',
        headers={
            'User-Agent': 'Chrome/23.0.1271.64',
            'Accept': 'zip/zip',
            'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
            'Accept-Encoding': 'none',
            'Accept-Language': 'en-US,en;q=0.8',
            'Connection': 'keep-alive'}
        )

    with urllib.request.urlopen(req) as url:
        df = pd.read_excel(url.read(),
                           sheet_name='MYE2-All',
                           header=4).rename(
            columns={'Code': 'code',
                     'Name': 'name',
                     'All ages': 'population'})[['code', 'name', 'population']].iloc[:-3]

    scotland = pd.read_csv('https://www.opendata.nhs.scot/dataset/7f010430-6ce1-4813-b25c-f7f335bdc4dc/'
                           'resource/27a72cc8-d6d8-430c-8b4f-3109a9ceadb1/download/hb2014_pop_est_01072019.csv')
    scotland = scotland[scotland.Year == 2018].rename(
        columns={'HB2014': 'code', 'AllAges': 'population'})[['code', 'population']]

    scotland_names = pd.read_csv('https://www.opendata.nhs.scot/dataset/9f942fdb-e59e-44f5-b534-d6e17229cc7b'
                                 '/resource/944765d7-d0d9-46a0-b377-abb3de51d08e/download/geography_codes_an'
                                 'd_labels_hscp2016_01042019.csv')
    scotland_names = scotland_names.rename(columns={'HB2014': 'code', 'HB2014Name': 'name'})[['code', 'name']]
    scotland_names['name'] = scotland_names.name.str[4:]
    scotland = pd.merge(scotland, scotland_names.drop_duplicates())
    df = df.append(scotland)
    df = df.groupby(['code', 'name'])['population'].sum().reset_index()

    df.to_csv('population.csv', index=False)

    return df


def scotland_html():
    with urllib.request.urlopen('https://www.gov.scot/coronavirus-covid-19/') as url:
        return url.read().decode()


scotland_codes = {
    'Ayrshire and Arran': 'S08000015',
    'Borders': 'S08000016',
    'Dumfries and Galloway': 'S08000017',
    'Forth Valley': 'S08000019',
    'Grampian': 'S08000020',
    'Highland': 'S08000022',
    'Lothian': 'S08000024',
    'Orkney': 'S08000025',
    'Shetland': 'S08000026',
    'Western Isles': 'S08000028',
    'Fife': 'S08000029',
    'Tayside': 'S08000030',
    'Greater Glasgow and Clyde': 'S08000031',
    'Lanarkshire': 'S08000032'
}
