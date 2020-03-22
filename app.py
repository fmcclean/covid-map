# -*- coding: utf-8 -*-
import dash
import dash_core_components as dcc
import dash_html_components as html
import os
import plotly.express as px
import json
import pandas as pd
import urllib.request
from zipfile import ZipFile
from io import BytesIO

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.title = 'COVID-19 Dash Map'
server = app.server

df = pd.read_csv('https://www.arcgis.com/sharing/rest/content/items/b684319181f94875a6879bbc833ca3a6/data')


with urllib.request.urlopen("https://opendata.arcgis.com/datasets/56ae7efaabc841b4939385e2178437a3_0.geojson") as url:
    geojson = json.loads(url.read().decode())

req = urllib.request.Request("https://www.ons.gov.uk/file?uri=%2fpeoplepopulationandcommunity%2fpopulationandmigration%2fpopulationestimates%2fdatasets%2flowersuperoutputareamidyearpopulationestimatesnationalstatistics%2fmid2018sape21dt12a/sape21dt12amid20182019lalsoabroadagegrpsestformatted.zip",
                             headers={
                                 'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
                                 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
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

population = pd.merge(population, lookup, left_on='Area Codes', right_on='LSOA11CD')

merged = pd.merge(df, population, left_on='GSS_CD', right_on='UTLA19CD')

df = pd.merge(df, merged.groupby('GSS_CD')['All Ages'].sum().reset_index())

df['cases_by_pop'] = (df['TotalCases'] / df['All Ages'] * 10000).round(1)

fig = px.choropleth_mapbox(df, geojson=geojson,
                           locations='GSS_CD',
                           color='cases_by_pop',
                           hover_name='GSS_NM',
                           hover_data=['TotalCases', 'All Ages'],
                           color_continuous_scale="Viridis",
                           featureidkey='properties.ctyua19cd',
                           mapbox_style="carto-positron",
                           zoom=6,
                           center={"lat": 53, "lon": -1},
                           opacity=0.5,
                           labels={'TotalCases': 'Total Cases', 'GSS_CD': 'Area Code',
                                   'All Ages': 'Total Population',
                                   'cases_by_pop': 'Cases per 10,000 people'})

fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0},
                  font=dict(size=20),
                  hoverlabel=dict(font=dict(size=20)),
                  coloraxis={'colorbar': {'title': {'text': '/10<sup>4</sup>'}, 'tickangle': -90}})

app.layout = html.Div(children=[
    dcc.Graph(
        id='graph',
        figure=fig,
        style={"height": "100%"},
        config={'displayModeBar': False},
    )
], className="main")

if __name__ == '__main__':
    app.run_server(port=os.environ['PORT'], host='0.0.0.0', debug=True)
