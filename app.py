# -*- coding: utf-8 -*-
import dash
import dash_core_components as dcc
import dash_html_components as html
import os
import plotly.express as px
import json
import pandas as pd
from plotly import graph_objs as go
import download

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.title = 'COVID-19 Dash Map'
server = app.server

df = pd.read_csv('https://www.arcgis.com/sharing/rest/content/items/b684319181f94875a6879bbc833ca3a6/data')

updated = download.updated()

if os.path.exists('population.csv'):
    population = pd.read_csv('population.csv')
else:
    population = download.population()

if os.path.exists('boundaries.geojson'):
    with open('boundaries.geojson') as f:
        geojson = json.load(f)
else:
    geojson = download.boundaries()

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

fig.update_layout(
    margin={"r": 0, "t": 0, "l": 0, "b": 0},
    font=dict(size=20),
    hoverlabel=dict(font=dict(size=20)),
    coloraxis={'colorbar': {'title': {'text': '/10<sup>4</sup>'}, 'tickangle': -90}},
    annotations=[
        go.layout.Annotation(
            text='{}<br><a href="http://www.github.com/fmcclean/covid-map/">See code on GitHub</a>'.format(updated),
            showarrow=False,
            x=0,
            y=0,
            bgcolor="#ffffff",
            opacity=0.8,
            align='left'
        )])

app.layout = html.Div(children=[
    dcc.Graph(
        id='graph',
        figure=fig,
        style={"height": "100%"},
        config={'displayModeBar': False},
    ),
], className="main")

if __name__ == '__main__':
    app.run_server(port=os.environ['PORT'], host='0.0.0.0', debug=True)
