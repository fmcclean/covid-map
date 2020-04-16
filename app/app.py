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
import asyncio
from pyppeteer import launch
import os


async def download_uk_data():
    browser = await launch({'headless': True, 'args': ['--no-sandbox']})
    page = await browser.newPage()

    cdp = await page.target.createCDPSession()
    await cdp.send(
        "Page.setDownloadBehavior",
        {"behavior": "allow", "downloadPath": os.getcwd()},
    )
    xpath = "//a[contains(text(), 'Download cases data as CSV')]"
    await page.goto('https://coronavirus.data.gov.uk/#')
    await page.waitForXPath(xpath)
    elements = await page.xpath(xpath)
    await elements[0].click()
    await page.waitFor(500)
    await browser.close()


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

        asyncio.get_event_loop().run_until_complete(download_uk_data())

        df = pd.read_csv('coronavirus-cases.csv', header=0,
                         parse_dates=['Specimen date']).rename(
            columns={
                'Area code': 'code',
                'Cumulative lab-confirmed cases': 'cases',
                'Specimen date': 'date'
            })[['code', 'cases', 'date']].sort_values('date')

        scotland = pd.read_html('https://en.wikipedia.org/wiki/2020_coronavirus_pandemic_in_Scotland',
                                header=1,
                                match='A&A',
                                index_col='Date')[0].iloc[:-3, :14].dropna()

        scotland = scotland.rename(columns={
            'A&A': 'S08000015',
            'BOR': 'S08000016',
            'D&G': 'S08000017',
            'FIF': 'S08000029',
            'FV': 'S08000019',
            'GRA': 'S08000020',
            'GGC': 'S08000031',
            'HLD': 'S08000022',
            'LAN': 'S08000032',
            'LOT': 'S08000024',
            'ORK': 'S08000025',
            'SHE': 'S08000026',
            'TAY': 'S08000030',
            'WES': 'S08000028'}).transpose().reset_index().rename(columns={'index': 'code', 'Date': 'date'})

        scotland = scotland.melt(id_vars=['code'], var_name='date', value_name='cases')

        scotland['date'] = pd.to_datetime(scotland.date)
        scotland['cases'] = scotland['cases'].astype(str).str.extract(r'([\d.]+)').astype(float)

        scotland = scotland.sort_values('date')

        scotland['cases'] = scotland.groupby('code')['cases'].cumsum()

        df = df.append(scotland)

        df = df.sort_values('date')

        df = df[
            (df.date >= datetime(2020, 4, 1)) &
            (df.date < df[df.code == 'E06000001'].date.max()) &
            (df.code != 'S92000003')]

        df = pd.merge(df, population)

        df['date_string'] = df.date.dt.strftime('%d/%m')

        df['date'] = df.date.apply(lambda d: d.isoformat())

        df['cases_by_pop'] = (df.cases / df.population * 10000).round(1)

        df = pd.merge(df, centroids)

        df['new_cases_by_pop'] = (df.groupby('code')['cases'].diff() / df.population * 10000).round(1)

        self.data = df

        self.choropleth = self.create_figure('choropleth')
        self.density = self.create_figure('density')
        self.difference = self.create_figure('difference')

    def create_figure(self, mode='choropleth'):

        animation_frame = 'date_string'
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
