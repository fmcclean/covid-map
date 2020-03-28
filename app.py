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
from datetime import datetime, timedelta
from dash.exceptions import PreventUpdate
import threading
import dash_daq as daq

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

centroids = pd.read_csv('centroids.csv')

date_format = '%d/%m'


def update_data():
    df = pd.read_csv('https://www.arcgis.com/sharing/rest/content/items/b684319181f94875a6879bbc833ca3a6/data',
                     ).rename(columns={'GSS_CD': 'code', 'TotalCases': 'cases'}).drop(columns=['GSS_NM'])
    date = pd.to_datetime(download.updated()[8:])

    indicators = pd.read_excel(
        'https://www.arcgis.com/sharing/rest/content/items/bc8ee90225644ef7a6f4dd1b13ea1d67/data')
    indicators_date = pd.to_datetime(indicators['DateVal'].values[0])
    indicators = indicators[['ScotlandCases', 'WalesCases', 'NICases']].rename(
        columns={'ScotlandCases': 'S92000003',
                 'WalesCases': 'W92000004',
                 'NICases': 'N92000002'}).transpose().reset_index().rename(
        columns={'index': 'code', 0: 'cases'})
    if indicators_date == date:
        df = df.append(indicators)

    scotland_html = download.scotland_html()
    scotland = pd.read_html(scotland_html)[0].rename(
        columns={'Positive cases': 'cases'}
    )
    scotland_date = scotland_html[scotland_html.find('Scottish test numbers:'):]
    scotland_date = pd.to_datetime(scotland_date[:scotland_date.find('</h3>')].split(':')[1])

    scotland['Health board'] = scotland['Health board'].str.replace(u'\xa0', u' ')

    scotland = scotland.replace(download.scotland_codes).rename(columns={'Health board': 'code'})

    if scotland_date == date:
        df = df.append(scotland)

    mongo.insert(df.set_index('code').cases.to_dict(), date.timestamp())

    df = mongo.get_all_documents()

    df = pd.merge(df, population)

    df['cases_by_pop'] = (df.cases / df.population * 10000).round(1)

    if df.equals(app.data):
        return

    app.data = df

    app.choropleth = create_figure('choropleth')
    app.density = create_figure('density')


def create_figure(mode='choropleth'):

    animation_frame = 'date'
    animation_group = 'code'
    hover_name = 'name'
    hover_data = ['cases', 'population']
    color_continuous_scale = px.colors.sequential.Viridis[::-1]
    zoom = 6
    center = {"lat": 54, "lon": -3}
    labels = {'cases': 'Total Cases', 'code': 'Area Code',
              'population': 'Total Population',
              'cases_by_pop': 'Cases per 10,000 people'},

    if mode == 'density':

        df = pd.merge(app.data, centroids)

        fig = px.density_mapbox(df, lat='lat', lon='lon', z='cases',
                                animation_frame=animation_frame,
                                animation_group=animation_group,
                                mapbox_style='carto-positron',
                                hover_name=hover_name,
                                hover_data=hover_data,
                                color_continuous_scale=color_continuous_scale,
                                labels=labels,
                                zoom=zoom,
                                center=center,
                                range_color=(0, df.cases.max())
                                )

    else:

        fig = px.choropleth_mapbox(app.data, geojson=geojson,
                                   locations='code',
                                   color='cases_by_pop',
                                   animation_frame=animation_frame,
                                   animation_group=animation_group,
                                   hover_name=hover_name,
                                   hover_data=hover_data,
                                   color_continuous_scale=color_continuous_scale,
                                   featureidkey='properties.code',
                                   mapbox_style="white-bg",
                                   zoom=zoom,
                                   center=center,
                                   labels=labels,
                                   range_color=(0, app.data.cases_by_pop.max())
                                   )

        fig.update_traces(marker={'line': {'width': 0.5}})

    slider = fig['layout']['sliders'][0]
    slider['active'] = len(slider.steps)-1
    slider['pad']['t'] = 0
    slider['currentvalue'] = {'visible': False}

    buttons = fig.layout.updatemenus[0]
    buttons.x = 0.2
    buttons.y = 1

    fig.update_layout(
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        hoverlabel=dict(font=dict(size=20)),
        coloraxis={'colorbar': {'title': {'text': '/10<sup>4</sup>' if mode == 'choropleth' else ''},
                                'tickangle': -90}},
        annotations=[
            go.layout.Annotation(
                text='<a href="http://www.github.com/fmcclean/covid-map/">View code on GitHub</a>',
                font={'size': 14},
                showarrow=False,
                x=0,
                y=1,
                bgcolor="#ffffff",
                align='left'
            ),

            go.layout.Annotation(
                text='<b>Cases per 10,000 People</b>' if mode == 'choropleth' else '<b>Number of Cases</b>',
                showarrow=False,
                x=0.5,
                y=0.9,
                bgcolor="#ffffff",
                align='left',
                font={'size': 25}
            )
        ],
        uirevision=True
    )

    fig.update_traces(fig.frames[-1].data[0])

    return fig


graph_layout = {
    'margin': {"r": 30, "t": 10, "l": 30, "b": 15},
    'title': {'text': 'Click on a region to view time series', 'y': 0.95}}

app.updated = datetime.now()
app.not_updating = threading.Event()
app.not_updating.set()
app.current_layout = None
app.density = None
app.choropleth = None
app.data = pd.DataFrame()


def update_layout():
    app.not_updating.wait()
    if not app.current_layout or (datetime.now() - app.updated) > timedelta(minutes=1):
        app.not_updating.clear()
        app.current_layout = create_layout()
        app.updated = datetime.now()
        app.not_updating.set()

    return app.current_layout


def create_layout():

    update_data()

    choropleth = dcc.Graph(
                id='choropleth',
                figure=app.choropleth,
                style={"height": "80%"},
                config={'displayModeBar': False})

    graph = dcc.Graph(
        id='graph',
        figure={'layout': graph_layout},
        style={"height": "20%"},
        config={'displayModeBar': False})

    dates = mongo.get_available_dates()

    toggle = daq.ToggleSwitch(
        id='toggle',
        value=False,
        vertical=True

    )

    return html.Div(children=[
        html.Div([html.P('Heatmap'),
                  html.Div(toggle, style={'padding': '20px'}),
                  html.P('Choropleth')],
                 style={'position': 'absolute', 'zIndex': 100, 'right': '100px', 'top': '30px',
                        'background': 'white', 'textAlign': 'center'}),
        choropleth,
        graph,
        html.Div(max(dates).timestamp(), id='previous_date', style={'display': 'none'})
    ],
        className="main")


app.layout = update_layout


@app.callback(
    dash.dependencies.Output('graph', 'figure'),
    [dash.dependencies.Input('choropleth', 'clickData')])
def display_click_data(click_data):
    if click_data is None:
        raise PreventUpdate
    point = click_data['points'][0]
    cases = app.data[app.data.code == point['id']]
    x = cases.date.values
    if 'lat' in point.keys():
        y = cases.cases.values
    else:
        y = cases.cases_by_pop.values
    return {'data': [{'x': x, 'y': y}],
            'layout': {**graph_layout, 'title': {'text': point['hovertext'],
                                                 'y': 0.8, 'x': 0.1
                                                 }}}


@app.callback(dash.dependencies.Output('choropleth', 'figure'),
              [dash.dependencies.Input('toggle', 'value')])
def update_figure_type(toggle_value):
    return app.density if toggle_value else app.choropleth


if __name__ == '__main__':
    app.run_server(port=os.environ['PORT'], host='0.0.0.0', debug=True)
