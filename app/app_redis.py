import base64
import io

import dash
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go

import pandas as pd

import redis

R = redis.Redis()

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


def make_graph(data):
    '''
    Create the graph

    Args:
        data (pandas.DataFrame): data
    '''

    layout = go.Layout(
        title='Plot',
        showlegend=True,
        template='ggplot2',
    )

    graph = dcc.Graph(
        id='plot{}'.format(data.columns[1]),
        figure=go.Figure(
            data=[
                go.Scattergl(
                    x=data.iloc[:, 0],
                    y=data.iloc[:, 1],
                    mode='lines',
                )
            ],
            layout=layout,
        )
    )

    return graph


def parse_contents(contents, filename):
    content_type, content_string = contents.split(',')

    decoded = base64.b64decode(content_string)
    try:
        if 'csv' in filename:
            # Assume that the user uploaded a CSV file
            df = pd.read_csv(
                io.StringIO(decoded.decode('utf-8')))
        elif 'xls' in filename:
            # Assume that the user uploaded an excel file
            df = pd.read_excel(io.BytesIO(decoded))
    except Exception as e:
        print(e)
        return html.Div([
            'There was an error processing this file.'
        ])

    return R.set(filename, df.to_json())


def populate_content():

    children = []

    for filename in R.keys():
        df = pd.read_json(R.get(filename).decode('utf-8'))
        children.append(
            html.Div([
                html.H5(filename.decode('utf-8')),

                html.Div(
                    make_graph(df)
                ),

                html.Hr(),  # horizontal line

                # For debugging, display the raw contents provided by the web browser
                html.Div(', '.join([k.decode('utf-8') for k in R.keys()])),
                html.Div('Raw Content'),
                # html.Pre(contents[0:200] + '...', style={
                #     'whiteSpace': 'pre-wrap',
                #     'wordBreak': 'break-all'
                # })
            ])
        )
    return children


@app.callback(Output('output-data-upload', 'children'),
              [Input('upload-data', 'contents')],
              [State('upload-data', 'filename')])
def update_output(list_of_contents, list_of_names):

    if list_of_contents:
        for c, n in zip(list_of_contents, list_of_names):
            parse_contents(c, n)

    children = populate_content()
    return children
