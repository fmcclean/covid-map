import urllib.request
import json
import pandas as pd
from io import BytesIO

def boundaries():
    with urllib.request.urlopen(
            "https://opendata.arcgis.com/datasets/b216b4c8a4e74f6fb692a1785255d777_0.geojson") as url:
        geojson = json.loads(url.read().decode())

    for feature in geojson['features']:
        feature['properties'] = {'code': feature['properties']['ctyua19cd']}

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
        stream = BytesIO(url.read())
        df = pd.read_excel(stream,
                           sheet_name='MYE2-All',
                           header=4, engine='xlrd')
        df = df.rename(
            columns={'Code': 'code',
                     'Name': 'name',
                     'All ages': 'population'})[['code', 'name', 'population']].iloc[:-3]

    df = df.groupby(['code', 'name'])['population'].sum().reset_index()

    df.to_csv('population.csv', index=False)

    return df


def scotland_html():
    with urllib.request.urlopen('https://www.gov.scot/publications/coronavirus-covid-19-tests-and-cases-in-scotland/') as url:
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
