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
from datetime import datetime
from dash.exceptions import PreventUpdate

try:
    import chromedriver_binary
except ImportError:
    pass

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.title = 'COVID-19 Dash Map'
server = app.server

if os.path.exists('population.csv'):
    population = pd.read_csv('population.csv')
else:
    population = download.population()

if os.path.exists('boundaries.geojson'):
    with open('boundaries.geojson') as f:
        geojson = json.load(f)
else:
    geojson = download.boundaries()

date_format = '%d/%m'


def create_figure(timestamp=None):

    if not timestamp:  # creating for the first time

        df = pd.read_csv('https://www.arcgis.com/sharing/rest/content/items/b684319181f94875a6879bbc833ca3a6/data')
        date = pd.to_datetime(download.updated()[8:])

        indicators = pd.read_excel(
            'https://www.arcgis.com/sharing/rest/content/items/bc8ee90225644ef7a6f4dd1b13ea1d67/data')
        indicators_date = pd.to_datetime(indicators['DateVal'].values[0])
        indicators = indicators[['ScotlandCases', 'WalesCases', 'NICases']].rename(
            columns={'ScotlandCases': 'S92000003',
                     'WalesCases': 'W92000004',
                     'NICases': 'N92000002'}).transpose().reset_index().rename(
            columns={'index': 'GSS_CD', 0: 'TotalCases'})
        if indicators_date == date:
            df = df.append(indicators)

        mongo.insert(df.set_index('GSS_CD')['TotalCases'].to_dict(), date.timestamp())

    else:
        df = mongo.get_date(timestamp)

        date = datetime.fromtimestamp(timestamp)

    df = pd.merge(df, population, left_on='GSS_CD', right_on='UTLA19CD')

    df['cases_by_pop'] = (df['TotalCases'] / df['All ages'] * 10000).round(1)

    fig = px.choropleth_mapbox(df, geojson=geojson,
                               locations='GSS_CD',
                               color='cases_by_pop',
                               hover_name='UTLA19NM',
                               hover_data=['TotalCases', 'All ages'],
                               color_continuous_scale="Viridis",
                               featureidkey='properties.ctyua19cd',
                               mapbox_style="carto-positron",
                               zoom=6,
                               center={"lat": 53, "lon": -2},
                               opacity=0.5,
                               labels={'TotalCases': 'Total Cases', 'GSS_CD': 'Area Code',
                                       'All ages': 'Total Population',
                                       'cases_by_pop': 'Cases per 10,000 people'},
                               )

    fig.update_layout(
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        font=dict(size=20),
        hoverlabel=dict(font=dict(size=20)),
        coloraxis={'colorbar': {'title': {'text': '/10<sup>4</sup>'}, 'tickangle': -90}},
        annotations=[
            go.layout.Annotation(
                text='<a href="http://www.github.com/fmcclean/covid-map/">View code on GitHub</a>',
                font={'size': 12},
                showarrow=False,
                x=0,
                y=1,
                bgcolor="#ffffff",
                opacity=0.8,
                align='left'
            ),

            go.layout.Annotation(
                text='<b>Cases per 10,000 People ({})</b>'.format(date.strftime('%d/%m/%y')),
                showarrow=False,
                x=0.5,
                y=0.9,
                bgcolor="#ffffff",
                opacity=0.8,
                align='left',
                font={'size': 25}
            )
        ],
        uirevision=True
    )

    return fig


graph_layout = {'margin': {"r": 30, "t": 10, "l": 30, "b": 40},
                'title': {'text': 'Click on a region to view time series', 'y': 0.95}}


def create_layout():
    choropleth = dcc.Graph(
                id='choropleth',
                figure=create_figure(),
                style={"height": "70%"},
                config={'displayModeBar': False})

    graph = dcc.Graph(
        id='graph',
        figure={'layout': graph_layout},
        style={"height": "20%"},
        config={'displayModeBar': False})

    dates = mongo.get_available_dates()

    slider = dcc.Slider(
        id='slider',
        min=min(dates).timestamp(),
        max=max(dates).timestamp(),
        step=None,
        marks={int(date.timestamp()): {'label': date.strftime('%d/%m'), 'style': {'fontSize': 20}}
               for date in dates},
        value=max(dates).timestamp(),
        )

    return html.Div(children=[
        choropleth,
        graph,
        html.Div(slider, style={'marginLeft': '20px',
                                'marginRight': '20px',
                                'marginBottom': '5px',
                                'marginTop': '20px'}),
    ],
        className="main")


app.layout = create_layout


@app.callback(dash.dependencies.Output('choropleth', 'figure'),
              [dash.dependencies.Input('slider', 'value')])
def update_figure(slider_value):
    if slider_value is None:
        raise PreventUpdate
    return create_figure(timestamp=slider_value)


@app.callback(
    dash.dependencies.Output('graph', 'figure'),
    [dash.dependencies.Input('choropleth', 'clickData')])
def display_click_data(click_data):
    if click_data is None:
        raise PreventUpdate
    point = click_data['points'][0]
    cases = mongo.get_location(point['location'])
    x, y = list(zip(*cases))
    return {'data': [{'x': x, 'y': [total*10000/point['customdata'][1] for total in y]}],
            'layout': {**graph_layout, 'title': {'text': point['hovertext'], 'y': 0.8, 'x': 0.1}}}


if __name__ == '__main__':
    app.run_server(port=os.environ['PORT'], host='0.0.0.0', debug=True)
