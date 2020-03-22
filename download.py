import urllib
import json
import pandas as pd
from zipfile import ZipFile
from io import BytesIO


def boundaries():
    with urllib.request.urlopen(
            "https://opendata.arcgis.com/datasets/56ae7efaabc841b4939385e2178437a3_0.geojson") as url:
        geojson = json.loads(url.read().decode())

    geojson['features'] = [feature for feature in geojson['features']
                           if feature['properties']['ctyua19cd'].startswith('E')]

    for feature in geojson['features']:
        feature['properties'] = {key: feature['properties'][key] for key in ['ctyua19cd']}

    with open('boundaries.geojson', 'w') as f:
        json.dump(geojson, f)

    return geojson


def population():
    req = urllib.request.Request(
        "https://www.ons.gov.uk/file?uri=%2fpeoplepopulationandcommunity%2fpopulationandmigration%2fpopulationestimates%2fdatasets%2flowersuperoutputareamidyearpopulationestimatesnationalstatistics%2fmid2018sape21dt12a/sape21dt12amid20182019lalsoabroadagegrpsestformatted.zip",
        headers={
            'User-Agent': 'Chrome/23.0.1271.64',
            'Accept': 'zip/zip',
            'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
            'Accept-Encoding': 'none',
            'Accept-Language': 'en-US,en;q=0.8',
            'Connection': 'keep-alive'}
        )

    with urllib.request.urlopen(req) as url:
        zip_file = ZipFile(BytesIO(url.read()))

    with zip_file.open(zip_file.namelist()[0]) as f:
        population = pd.read_excel(f, sheet_name='Mid-2018 Persons', header=4, index_col='Area Codes')

    lookup = pd.read_csv('https://opendata.arcgis.com/datasets/4c6f3314565e43c5ac7885fd71347548_0.csv')

    df = pd.merge(population, lookup, left_on='Area Codes', right_on='LSOA11CD')

    df[['All Ages', 'UTLA19CD']].to_csv('population.csv', index=False)

    return df
