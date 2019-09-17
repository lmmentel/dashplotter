import base64
import io
import os
import re

import dash
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html

import plotly.graph_objs as go
from plotly.subplots import make_subplots

import pandas as pd
import peakutils


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div([
    dcc.Upload(
        id='upload-data',
        children=html.Div([
            'Drag and Drop or ',
            html.A('Select Files')
        ]),
        style={
            'width': '100%',
            'height': '60px',
            'lineHeight': '60px',
            'borderWidth': '1px',
            'borderStyle': 'dashed',
            'borderRadius': '5px',
            'textAlign': 'center',
            'margin': '10px'
        },
        # Allow multiple files to be uploaded
        multiple=True
    ),
    html.Div(id='output-data-upload'),
])


def parse_contents(contents, filename):
    '''
    Parse a file
    '''

    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    filebase, ext = os.path.splitext(filename)

    try:
        if ext.lower() == '.csv':
            df = pd.read_csv(
                io.StringIO(decoded.decode('utf-8')))
        elif ext.lower() == '.xls':
            df = pd.read_excel(io.BytesIO(decoded))
        elif ext.lower() == '.dat':
            df = pd.read_csv(io.StringIO(decoded.decode('utf-8')),
                             sep='\s+', engine='python')
    except Exception as e:
        print(e)
        return html.Div([
            'There was an error processing this file.'
        ])

    return filebase, df


def populate_subplots(dataframes, peak_indexes=None):
    '''
    Create scatter plots with shared x axis ffrom the dataframes in the
    `dataframes` dictionary.
    '''

    plot_height = 400
    show_all_tick_labels = False

    n_plots = len(dataframes)
    if n_plots == 0:
        return []

    fig = make_subplots(
        rows=n_plots, cols=1, shared_xaxes=True, vertical_spacing=0.02,
    )

    for i, (filebase, df) in enumerate(dataframes.items(), start=1):
        display_name = ' '.join(re.split(r'[_=.,\s]', filebase))
        fig.add_trace(go.Scatter(x=df.iloc[:, 0], y=df.iloc[:, 1],
                                 mode='lines', name=display_name),
                      row=i, col=1)
        if peak_indexes is not None:
            fig.add_trace(go.Scatter(x=df.iloc[peak_indexes[filebase], 0],
                                     y=df.iloc[peak_indexes[filebase], 1],
                                     mode='markers', name='peaks',
                                     marker=dict(size=7, symbol='star-diamond',
                                     color='Crimson')),
                          row=i, col=1)
        fig.update_yaxes(title_text=display_name, row=i, col=1)

    if show_all_tick_labels:
        for i in range(n_plots):
            xaxis_name = 'xaxis' if i == 0 else f'xaxis{i + 1}'
            getattr(fig.layout, xaxis_name).showticklabels = True

    for item in fig.layout['annotations']:
        item.xanchor = 'left'
        item.x = 0.0

    fig.update_layout(height=plot_height * n_plots, showlegend=False,
                      template='ggplot2',
                      margin=go.layout.Margin(
                          l=75,
                          r=50,
                          b=50,
                          t=50,
                          pad=4
                      )
    )
    fig.update_xaxes(autorange='reversed')
    graph = dcc.Graph(
        id='plots',
        figure=fig
    )

    return [graph]


def find_peaks(dataframes, thres=0.2, min_dist=10):
    '''
    Find indices of peak for each DataFrame
    '''

    peak_indexes = dict()
    for k, df in dataframes.items():

        peak_indexes[k] = peakutils.indexes(
            df.iloc[:, 1].values, thres=thres, min_dist=min_dist)

    return peak_indexes


@app.callback(Output('output-data-upload', 'children'),
              [Input('upload-data', 'contents')],
              [State('upload-data', 'filename')])
def update_output(list_of_contents, list_of_names):

    dataframes = {}

    if list_of_contents:
        for c, n in zip(list_of_contents, list_of_names):
            filebase, df = parse_contents(c, n)
            dataframes[filebase] = df

    peak_indexes = find_peaks(dataframes)
    children = populate_subplots(dataframes)

    return children
