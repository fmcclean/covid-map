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

port = parser.parse_args().p

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

df = pd.read_csv('CountyUAs_cases_table.csv', index_col='GSS_CD')

with open('la-boundaries-simple.geojson') as f:
    geojson = json.parse(f.read())

fig = px.choropleth_mapbox(df, geojson=geojson, locations='lad19cd', color='TotalCases',
                           color_continuous_scale="Viridis",
                           # range_color=(0, 12),
                           mapbox_style="carto-positron",
                           zoom=3,
                           center={"lat": 55, "lon": -1},
                           opacity=0.5,
                           labels={'TotalCases': 'Total Cases'}
                          )
fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
fig.show()

app.layout = html.Div(children=[
    html.H1(children='Hello Dash'),

    html.Div(children='''
        Dash: A web application framework for Python.
    '''),

    dcc.Graph(
        id='example-graph',
        figure=fig
    )
])

if __name__ == '__main__':
    app.run_server(port=port, host='0.0.0.0')