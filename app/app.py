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


class App(dash.Dash):
    def __init__(self):
        super().__init__(__name__, external_stylesheets=['https://codepen.io/chriddyp/pen/bWLwgP.css'])
        self.title = 'COVID-19 Dash Map'
        self.data = pd.DataFrame()
        self.choropleth = None
        self.density = None
        self.difference = None
        self.updated = datetime.now()
        self.not_updating = threading.Event()
        self.not_updating.set()
        self.current_layout = None
        self.layout = self.update_layout

    def update_data(self):
        df = pd.read_excel('https://fingertips.phe.org.uk/documents/Historic%20COVID-19%20Dashboard%20Data.xlsx',
                           header=7,
                           sheet_name='UTLAs',
                           ).rename(columns={'Area Code': 'code'}).drop(columns=['Area Name'])
        df = df.melt(id_vars=['code'], var_name='date', value_name='cases')
        date = df.date.max()
        df = df[df.date == date].drop('date', axis=1)

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
        scotland_date = scotland_html[scotland_html.find('Scottish COVID-19 test numbers:'):]
        scotland_date = pd.to_datetime(scotland_date[:scotland_date.find('</h3>')].split(':')[1])

        if scotland_date == date:
            scotland = pd.read_html(scotland_html, header=0)[0].rename(columns={'Total confirmed cases to date': 'cases'})
            scotland['Health board'] = scotland['Health board'].str.replace(u'\xa0', u' ')
            scotland = scotland.replace(download.scotland_codes).rename(columns={'Health board': 'code'})
            scotland['cases'] = scotland.cases.astype(str).str.replace('*', '5').astype(int)
            df = df.append(scotland[['code', 'cases']])

        update_count = mongo.insert(df.set_index('code').cases.to_dict(), date.timestamp())

        if update_count == 0 and len(self.data) > 0:
            return

        df = mongo.get_all_documents()

        df = pd.merge(df, population)

        df['cases_by_pop'] = (df.cases / df.population * 10000).round(1)

        df = pd.merge(df, centroids)

        df['new_cases_by_pop'] = (df.groupby('code')['cases'].diff() / df.population * 10000).round(1)

        self.data = df

        self.choropleth = self.create_figure('choropleth')
        self.density = self.create_figure('density')
        self.difference = self.create_figure('difference')

    def create_figure(self, mode='choropleth'):

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

            fig = px.density_mapbox(self.data, lat='lat', lon='lon', z='cases',
                                    animation_frame=animation_frame,
                                    animation_group=animation_group,
                                    mapbox_style='carto-positron',
                                    hover_name=hover_name,
                                    hover_data=hover_data,
                                    color_continuous_scale=color_continuous_scale,
                                    labels=labels,
                                    zoom=zoom,
                                    center=center,
                                    range_color=(0, self.data.cases.max()),
                                    radius=40)

        elif mode == 'choropleth':

            fig = px.choropleth_mapbox(self.data, geojson=geojson,
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
                                       range_color=(0, self.data.cases_by_pop.max())
                                       )

            fig.update_traces(marker={'line': {'width': 0.5}})

        elif mode == 'difference':

            fig = px.choropleth_mapbox(self.data.dropna(), geojson=geojson,
                                       locations='code',
                                       color='new_cases_by_pop',
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
                                       range_color=(0, self.data.new_cases_by_pop.max())
                                       )

            fig.update_traces(marker={'line': {'width': 0.5}})

        else:
            raise Exception('mode "{}" is not supported'.format(mode))

        slider = fig['layout']['sliders'][0]
        slider['active'] = len(slider.steps) - 1
        slider['pad']['t'] = 0
        slider['currentvalue'] = {'visible': False}

        buttons = fig.layout.updatemenus[0]
        buttons.x = 0
        buttons.y = 0
        buttons.xanchor = 'left'
        buttons.yanchor = 'bottom'
        buttons.pad = {'r': 0, 't': 0, 'l': 50, 'b': 10}
        buttons.buttons[0].args[1]["frame"]["duration"] = 1000
        fig.update_layout(
            margin={"r": 0, "t": 0, "l": 0, "b": 0},
            hoverlabel=dict(font=dict(size=20)),
            coloraxis={'colorbar': {'title': {'text': '/10<sup>4</sup>' if mode != 'density' else ''},
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
                    text='<b>{}</b>'.format({
                        'choropleth': 'Cases per 10,000 People',
                        'density': 'Number of Cases',
                        'difference': 'New Cases per 10,000 People'
                    }[mode]),
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

    def update_layout(self):
        self.not_updating.wait()
        if not self.current_layout or (datetime.now() - self.updated) > timedelta(minutes=1):
            self.not_updating.clear()
            self.create_layout()
            self.updated = datetime.now()
            self.not_updating.set()

        return self.current_layout

    def create_layout(self):

        self.update_data()

        class_name = 'map'

        choropleth = dcc.Graph(
            id='choropleth',
            figure=self.choropleth,
            config={'displayModeBar': False},
            className=class_name
        )

        density = dcc.Graph(
            id='density',
            figure=self.density,
            config={'displayModeBar': False},
            className=class_name
        )

        difference = dcc.Graph(
            id='difference',
            figure=self.difference,
            config={'displayModeBar': False},
            className=class_name
        )

        graph = dcc.Graph(
            id='graph',
            figure={'layout': graph_layout},
            config={'displayModeBar': False})

        self.current_layout = html.Div(children=[
            dcc.Tabs([
                dcc.Tab(label='Choropleth', children=[choropleth]),
                dcc.Tab(label='Density', children=[density]),
                dcc.Tab(label='Difference', children=[difference])],
                id='tabs'),
            graph
        ],
            className="main")


app = App()
server = app.server

if os.path.exists('data/population.csv'):
    population = pd.read_csv('data/population.csv')
else:
    population = download.population()

if os.path.exists('data/boundaries.geojson'):
    with open('data/boundaries.geojson') as f:
        geojson = json.load(f)
else:
    geojson = download.boundaries()

centroids = pd.read_csv('data/centroids.csv')

date_format = '%d/%m'


graph_layout = {
    'margin': {"r": 30, "t": 10, "l": 30, "b": 15},
    'title': {'text': 'Click on a region to view time series', 'y': 0.95}}


@app.callback(
    dash.dependencies.Output('graph', 'figure'),
    [dash.dependencies.Input('choropleth', 'clickData'),
     dash.dependencies.Input('density', 'clickData'),
     dash.dependencies.Input('difference', 'clickData')],
    [dash.dependencies.State('tabs', 'value')]
)
def display_click_data(click_data, density_clickdata, difference_clickdata, tabs_value):
    if click_data is None and density_clickdata is None and difference_clickdata is None:
        raise PreventUpdate
    data = {'tab-1': click_data, 'tab-2': density_clickdata, 'tab-3': difference_clickdata}[tabs_value]
    point = data['points'][0]
    cases = app.data[app.data.code == point['id']]
    x = cases.date.values
    if tabs_value == 'tab-1':
        y = cases.cases_by_pop.values
    elif tabs_value == 'tab-2':
        y = cases.cases.values
    else:
        x = x[1:]
        y = cases.new_cases_by_pop.values[1:]
    return {'data': [{'x': x, 'y': y}],
            'layout': {**graph_layout, 'title': {'text': point['hovertext'],
                                                 'y': 0.8, 'x': 0.1
                                                 }}}


if __name__ == '__main__':
    app.run_server(port=os.environ['PORT'], host='0.0.0.0', debug=True)
