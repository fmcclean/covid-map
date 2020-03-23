import urllib
import json
import pandas as pd
from zipfile import ZipFile
from io import BytesIO
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

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

    df = df.groupby(['UTLA19CD', 'UTLA19NM'])['All Ages'].sum().reset_index()

    df.to_csv('population.csv', index=False)

    return df


def updated():
    url = 'https://www.arcgis.com/home/item.html?id=b684319181f94875a6879bbc833ca3a6'
    options = Options()
    options.headless = True

    options.add_argument('--no-sandbox')
    options.add_argument('--disable-gpu')
    browser = webdriver.Chrome(
        options=options)
    browser.get(url)
    elem = WebDriverWait(browser, 5).until(EC.presence_of_element_located((By.ID, "dijit__TemplatedMixin_1")))
    html = elem.get_attribute('outerHTML')
    html = html[html.find('Updated:'):]
    html = html[:html.find('<')]
    browser.quit()
    return html
