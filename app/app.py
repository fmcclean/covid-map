# -*- coding: utf-8 -*-
import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.express as px
import json
import pandas as pd
from plotly import graph_objs as go
import download
from datetime import datetime, timedelta
from dash.exceptions import PreventUpdate
import threading
import os
from uk_covid19 import Cov19API


class App(dash.Dash):
    def __init__(self):
        super().__init__(__name__, external_stylesheets=['https://codepen.io/chriddyp/pen/bWLwgP.css'])
        self.title = 'COVID-19 Dash Map'
        self.data = pd.DataFrame()
        self.difference = None
        self.updated = datetime.now()
        self.not_updating = threading.Event()
        self.not_updating.set()
        self.current_layout = None
        self.layout = self.update_layout

    def update_data(self):

        df = []
        for area_type in ['utla', 'nation']:
            print(area_type)
            new_cases = "newCasesByPublishDate"
            df.extend(Cov19API(filters=[f'areaType={area_type}'], structure={
                "date": "date",
                "areaCode": "areaCode",
                new_cases: new_cases,
            }, latest_by=new_cases).get_json()['data'])

        df = pd.DataFrame(df).rename(columns={new_cases: 'new_cases', 'areaCode': 'code'})
        df['date'] = pd.to_datetime(df.date)

        df = df.sort_values('date')

        df = pd.merge(df, population)

        df['date_string'] = df.date.dt.strftime('%d/%m')

        df['date'] = df.date.apply(lambda d: d.isoformat())

        df['cases_by_pop'] = (df.new_cases / df.population * 10000).round(1).cumsum()

        df['new_cases_by_pop'] = (df.new_cases / df.population * 10000).round(1)

        self.data = df

        self.difference = self.create_figure()

    def create_figure(self):

        hover_name = 'name'
        hover_data = ['new_cases', 'population']
        color_continuous_scale = px.colors.sequential.Viridis[::-1]
        zoom = 6
        center = {"lat": 54, "lon": -3}
        labels = {'new_cases': 'New Cases', 'code': 'Area Code',
                  'population': 'Total Population',
                  'cases_by_pop': 'Cases per 10,000 people'},

        df = self.data

        fig = px.choropleth_mapbox(df.dropna(), geojson=geojson,
                                   locations='code',
                                   color='new_cases_by_pop',
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

        fig.update_layout(
            margin={"r": 0, "t": 0, "l": 0, "b": 0},
            hoverlabel=dict(font=dict(size=20)),
            coloraxis={'colorbar': {'title': {'text': '/10<sup>4</sup>'},
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
                    text='<b>{}</b>'.format('New Cases per 10,000 People'),
                    showarrow=False,
                    x=0.5,
                    y=0.9,
                    bgcolor="#ffffff",
                    align='left',
                    font={'size': 25}
                )
            ],
            uirevision=True,
        )

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

        self.current_layout = html.Div(children=[difference,
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

date_format = '%d/%m'


graph_layout = {
    'margin': {"r": 30, "t": 10, "l": 30, "b": 15},
    'title': {'text': 'Click on a region to view time series', 'y': 0.95},
    'hovermode': 'closest'
}


@app.callback(
    dash.dependencies.Output('graph', 'figure'),
    [
     dash.dependencies.Input('difference', 'clickData')]
)
def display_click_data(difference_clickdata):
    if difference_clickdata is None:
        raise PreventUpdate
    data = difference_clickdata
    point = data['points'][0]
    area_name = point['location']
    if area_name[0] in ['E', 'W']:
        area_type = 'utla'
    else:
        area_type = 'nation'
    name = "newCasesBySpecimenDate"

    cases = pd.DataFrame(Cov19API(filters=[f'areaType={area_type};areaCode={area_name}'], structure={
        "date": "date",
        "code": "areaCode",
        "cases": name,
    }).get_json()['data'])
    cases['date'] = pd.to_datetime(cases.date).apply(lambda d: d.isoformat())

    x = cases.date.values
    y = cases.cases.values
    return {'data': [{'x': x, 'y': y}],
            'layout': {**graph_layout, 'title': {'text': point['hovertext'],
                                                 'y': 0.8, 'x': 0.1
                                                 }}}


if __name__ == '__main__':
    app.run_server(port=os.environ['PORT'], host='0.0.0.0', debug=True)
