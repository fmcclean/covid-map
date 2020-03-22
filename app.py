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
import mongo

try:
    import chromedriver_binary
except:
    pass

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.title = 'COVID-19 Dash Map'
server = app.server

app.dates = mongo.get_available_dates()


def create_figure():

    df = pd.read_csv('https://www.arcgis.com/sharing/rest/content/items/b684319181f94875a6879bbc833ca3a6/data')

    updated = download.updated()
    timestamp = pd.to_datetime(updated[8:]).timestamp()

    mongo.insert(df.set_index('GSS_CD')['TotalCases'].to_dict(), timestamp)

    app.dates = mongo.get_available_dates()

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
                                       'cases_by_pop': 'Cases per 10,000 people'},
                               )

    fig.update_layout(
        margin={"r": 0, "t": 0, "l": 0, "b": 20},
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
            )],
        uirevision=True
    )

    return fig


def set_date(timestamp):
    print(mongo.get_date(app.dates[-1].timestamp()))


def create_layout(figure):
    return html.Div(
        id='div',
        children=[
            dcc.Graph(
                id='graph',
                figure=figure,
                style={"height": "90%"},
                config={'displayModeBar': False},
            ),
            dcc.Slider(
                id='date',
                min=min(app.dates).timestamp(),
                max=max(app.dates).timestamp(),
                step=None,
                marks={int(date.timestamp()): date.strftime("%d/%m") for date in app.dates}
            ),
        ], className="main")

print({date.timestamp(): str(date) for date in app.dates})
app.layout = create_layout(create_figure())


@app.callback(dash.dependencies.Output('graph', 'figure'),
              [dash.dependencies.Input('div', 'id')])
def update_figure(div_id):
    figure = create_figure()
    app.layout = create_layout(figure)
    return figure


if __name__ == '__main__':
    app.run_server(port=os.environ['PORT'], host='0.0.0.0', debug=True)
