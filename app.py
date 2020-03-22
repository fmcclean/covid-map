# -*- coding: utf-8 -*-
import dash
import dash_core_components as dcc
import dash_html_components as html
import os
import plotly.express as px
import json
import pandas as pd
import urllib.request

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.title = 'COVID-19 Dash Map'
server = app.server

df = pd.read_csv('https://www.arcgis.com/sharing/rest/content/items/b684319181f94875a6879bbc833ca3a6/data')

with urllib.request.urlopen("https://opendata.arcgis.com/datasets/56ae7efaabc841b4939385e2178437a3_0.geojson") as url:
    geojson = json.loads(url.read().decode())

fig = px.choropleth_mapbox(df, geojson=geojson,
                           locations='GSS_CD',
                           color='TotalCases',
                           hover_name='GSS_NM',
                           hover_data=['TotalCases'],
                           color_continuous_scale="Viridis",
                           featureidkey='properties.ctyua19cd',
                           mapbox_style="carto-positron",
                           zoom=6,
                           center={"lat": 53, "lon": -1},
                           opacity=0.5,
                           labels={'TotalCases': 'Total Cases', 'GSS_CD': 'Area Code'})

fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0},
                  font=dict(size=20),
                  hoverlabel=dict(font=dict(size=20)),
                  coloraxis={'colorbar':{'title':{'text':''}, 'tickangle': -90}})

app.layout = html.Div(children=[
    dcc.Graph(
        id='graph',
        figure=fig,
        style={"height": "100%"},
        config={'displayModeBar': False},
    )
], className="main")

if __name__ == '__main__':
    app.run_server(port=os.environ['PORT'], host='0.0.0.0')
