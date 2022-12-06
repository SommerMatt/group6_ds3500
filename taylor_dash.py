import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from dash import Dash, dcc, html, Input, Output
import dash_bootstrap_components as dbc
import dash
import os
import flask
import sample_lines
from datetime import datetime as dt

### Enter your own filepath to the project
image_directory = '/Users/mattsommer/Downloads/Project/taylor_wordclouds'
list_of_images = os.listdir(image_directory)
static_image_route = '/static/'

def process_scores(df):
    pct_pos=[]
    for i in range(0, len(df)):
        if df['pos_scores'][i]+df['neg_scores'][i] == 0:
            den = 1
        else:
            den = df['pos_scores'][i]+df['neg_scores'][i]
        pct = (df['pos_scores'][i]/den) * 100
        pct_pos.append(pct)
    return pct_pos


def read_df(filename):
    df = pd.read_csv(filename)
    df.columns = ['idx', 'date', 'pos_scores', "neg_scores"]
    df['scores'] = process_scores(df)
    return df

main_df = read_df('taylor_swift_tsd_15')
taylor_fake, d_fake = sample_lines.ml()


def extract_local_network(df, numobs, timeframe = [main_df.idx.min(), main_df.idx.max()]):
    df = match_idx()
    df = df[df.idx.between(timeframe[0], timeframe[1])]
    df['roll_avg'] = df.scores.rolling(numobs).mean()
    return df

def buttons(csv):
    df = pd.read_csv(csv)
    return df['Album Name']

def make_marks(tick_len):
    i = 0
    mark_dict = {}
    jump = int(len(main_df)/tick_len)
    while i < len(main_df):
        mark_dict[i] = str(main_df['date'][i])
        i += jump
    return mark_dict



# Build an App using external style sheets to place graphs next to each other and add theme
app = Dash(__name__, external_stylesheets=[dbc.themes.MINTY])

def clean_label(i):
    df = pd.read_csv("taylor.csv")
    in_disc = False
    for k in df["Album Name"]:
        if k in i:
            in_disc = True
            return k
    if in_disc == False:
        return " "

def match_idx():
    album_col = []
    name_col = []
    df = pd.read_csv("taylor.csv")
    for k in range(0, len(main_df)-1):
        lower = dt.strptime(main_df["date"][k], '%Y-%m-%d %H:%M:%S')
        upper = dt.strptime(main_df["date"][k+1], '%Y-%m-%d %H:%M:%S')
        in_range = False
        for i in range(0, len(df)):
            formatted = dt.strptime(df["Release Date"][i], '%Y-%m-%d')
            if formatted >= lower and  formatted <= upper:
                in_range = True
                album_col.append(75)
                name_col.append(df["Album Name"][i])
        if in_range == False:
            album_col.append(0)
            name_col.append(" ")
    album_col.append(0)
    name_col.append(" ")
    main_df["album_col"] = album_col
    main_df["name_col"] = name_col
    return(main_df)

graph_columns = ['danceability', 'energy', 'key', 'loudness', 'mode', 'speechiness',
                 'acousticness', 'instrumentalness', 'liveness', 'valence', 'tempo', 'duration_ms',
                 'track_name', 'age']

# Define the dashboard layout
app.layout = html.Div([
    dbc.Row(dbc.Col(dbc.Col(html.H2('Interactive Artist Dashboard Taylor'), className='text-center', width=12))),
    dcc.Dropdown(id='image-dropdown', options=[{'label': clean_label(i), 'value': i} for i in list_of_images],
                     value=list_of_images[0]),
    dbc.Row([dbc.Col(dcc.Graph(id="graph",style={'width':'45vw', 'height':'45vh'},
                                responsive = True)),
            html.Img(id='image', style={'width':'45vw', 'height':'45vh'}),
            html.H4("Time range you want to view"),
            dcc.RangeSlider(main_df.idx.min(), main_df.idx.max(), 6,
                            value=[main_df.idx.min(), main_df.idx.max()], id='timeframe', marks=make_marks(6)),
            # user input for how many obersvations should be taken for the rolling average
            html.H4("How many months do you want to observe on average?"),
            dcc.Slider(1, 10, 1, value=5, id='numobs'),
            html.H3("Machine Learning of Taylor Swift's albums"),
            html.H6(id = 'lyrics'),
            dcc.Graph(id='graph_spotify'),
            html.H6('Select X and Y Features'),
            dcc.Dropdown(id='xfeat-dropdown', options=graph_columns, value='acousticness'),
            dcc.Dropdown(id='yfeat-dropdown', options=graph_columns, value='danceability')
            ])
    ])
@app.callback(
    dash.dependencies.Output('lyrics', 'children'),
    [dash.dependencies.Input('image-dropdown', 'value')])
def update_lyrics(value):
    for k in taylor_fake.keys():
        comp_str = k+'wordcloud.jpg'
        if comp_str == value:
            return taylor_fake[k]

@app.callback(
    dash.dependencies.Output('image', 'src'),
    [dash.dependencies.Input('image-dropdown', 'value')])
def update_image_src(value):
    return static_image_route + value

# Add a static image route that serves images from desktop
@app.server.route('{}<image_path>.jpg'.format(static_image_route))
def serve_image(image_path):
    image_name = '{}.jpg'.format(image_path)
    if image_name not in list_of_images:
        raise Exception('"{}" is excluded from the allowed static files'.format(image_path))
    return flask.send_from_directory(image_directory, image_name)

@app.callback(
    Output("graph", "figure"),
    Input("timeframe", "value"),
    Input("numobs", "value"),
)
def display_plot(timeframe, numobs):
    #modify dataframe
    local = extract_local_network(main_df, numobs, timeframe)
    #makes the sunspots over time figure
    fig = px.line(local, x='idx', y=['scores', 'roll_avg', "album_col"],
                  title="Twitter Sentiment of Taylor Swift Over Time", hover_data=["name_col", "date"])
    fig.update_layout(hovermode='x unified', xaxis_title='Date',
                  yaxis_title='Percent Positive Language')
    fig.update_layout({'paper_bgcolor': 'rgba(0,0,0,0)','plot_bgcolor':'rgba(0,0,0,0)'})
    return fig

taylor_df = pd.read_csv('taylor_spotify.csv')
@app.callback(
    dash.dependencies.Output('graph_spotify', 'figure'),
    [dash.dependencies.Input('image-dropdown', 'value')],
    Input('xfeat-dropdown', 'value'),
    Input('yfeat-dropdown', 'value')
)
def spotify_plot(album='1989', xfeat='acousticness', yfeat='danceability'):

    dataframe = taylor_df
    album= clean_label(album)
    sub_df = dataframe[dataframe['album_name'] == album]

    fig = px.scatter(sub_df, x=xfeat, y=yfeat, color="track_name",
                     size='duration_ms', hover_data=['track_name'],
                     title="Feature Comparison of Songs from {}".format(album), )
    fig.update_layout(showlegend=False)
    fig.update_layout({'paper_bgcolor': 'rgba(0,0,0,0)','plot_bgcolor':'rgba(0,0,0,0)'})
    fig.update_layout(yaxis_range=[0,1], xaxis_range=[0,1])
    return fig

app.run_server(debug=True)

