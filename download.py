import urllib.request
import json
import pandas as pd
from zipfile import ZipFile
from io import BytesIO
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.common.by import By


def boundaries():
    with urllib.request.urlopen(
            "https://opendata.arcgis.com/datasets/56ae7efaabc841b4939385e2178437a3_0.geojson") as url:
        geojson = json.loads(url.read().decode())

    with urllib.request.urlopen(
            "https://opendata.arcgis.com/datasets/629c303e07ee4ad09a4dfd0bfea499ec_0.geojson") as url:
        countries = json.loads(url.read().decode())

    geojson['features'] = [feature for feature in geojson['features']
                           if feature['properties']['ctyua19cd'].startswith('E')]

    countries['features'] = [feature for feature in countries['features']
                             if not feature['properties']['ctry18cd'].startswith('E')]

    for feature in geojson['features']:
        feature['properties'] = {key: feature['properties'][key] for key in ['ctyua19cd']}

    for feature in countries['features']:
        feature['properties'] = {'ctyua19cd': feature['properties']['ctry18cd']}

    geojson['features'].extend(countries['features'])

    with open('boundaries.geojson', 'w') as f:
        json.dump(geojson, f)

    return geojson


def population():
    req = urllib.request.Request(
        'https://www.ons.gov.uk/file?uri=%2fpeoplepopulationandcommunity%2fpopulationandmigration%2fpopu'
                       'lationestimates%2fdatasets%2fpopulationestimatesforukenglandandwalesscotlandandnorthernireland%2fmid20182019laboun'
                       'daries/ukmidyearestimates20182019ladcodes.xls',
        headers={
            'User-Agent': 'Chrome/23.0.1271.64',
            'Accept': 'zip/zip',
            'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
            'Accept-Encoding': 'none',
            'Accept-Language': 'en-US,en;q=0.8',
            'Connection': 'keep-alive'}
        )

    with urllib.request.urlopen(req) as url:
        df = pd.read_excel(url.read(), sheet_name='MYE2-All', header=4).rename(columns={'Code': 'UTLA19CD',
                                                                                        'Name': 'UTLA19NM'})
    df = df.groupby(['UTLA19CD', 'UTLA19NM'])['All ages'].sum().reset_index()

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
    elem = WebDriverWait(browser, 5).until(
        expected_conditions.presence_of_element_located((By.ID, "dijit__TemplatedMixin_1")))
    html = elem.get_attribute('outerHTML')
    html = html[html.find('Updated:'):]
    html = html[:html.find('<')]
    browser.quit()
    return html
