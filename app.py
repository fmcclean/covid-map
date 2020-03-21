# -*- coding: utf-8 -*-
import dash
import dash_core_components as dcc
import dash_html_components as html
import argparse
import plotly.express as px
import json
import pandas as pd

parser = argparse.ArgumentParser()

parser.add_argument('-p')
parser.add_argument('-m', default='develop')

args = parser.parse_args()
port = args.p
mode = args.m

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

df = pd.read_csv('https://www.arcgis.com/sharing/rest/content/items/b684319181f94875a6879bbc833ca3a6/data')

with open('la-boundaries-simple.geojson') as f:
    geojson = json.load(f)

fig = px.choropleth_mapbox(df, geojson=geojson,
                           locations='GSS_CD',
                           color='TotalCases',
                           hover_name='GSS_NM',
                           hover_data=['TotalCases'],
                           color_continuous_scale="Viridis",
                           featureidkey='properties.ctyua17cd',
                           mapbox_style="carto-positron",
                           zoom=6,
                           center={"lat": 53, "lon": -1},
                           opacity=0.5,
                           labels={'TotalCases': 'Total Cases', 'GSS_CD': 'Area Code'})

fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0},
                  font=dict(size=18),
                  hoverlabel=dict(font=dict(size=18)))

app.layout = html.Div(children=[
    dcc.Graph(
        id='example-graph',
        figure=fig,
        style={"height": "95vh"}
    )
])

if __name__ == '__main__':
    app.run_server(port=port, host='0.0.0.0', debug=mode == 'develop')
