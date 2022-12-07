import plotly.express as px
import pandas as pd
from dash import Dash, dcc, html, Input, Output
import dash_bootstrap_components as dbc
import base64
import dash
import os
import flask
import sample_lines
from datetime import datetime as dt
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer


### Enter your own filepath to the project
image_directory = '/Users/angel/DS3500/group6_ds3500-main/Drake_Clouds'
list_of_images = os.listdir(image_directory)
static_image_route = '/static/'

def process_scores(df):
    '''
    Calculates a % of scores that are positive from the pos/neg scores
    '''
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
    '''
    Reads in our dataframe, naming the columns we want and calling the process_scores function
    '''
    df = pd.read_csv(filename)
    df.columns = ['idx', 'date', 'pos_scores', "neg_scores"]
    df['scores'] = process_scores(df)
    return df

# Grabs the twitter sentiment time series for Drake and makes a df from it
drake_df = read_df('drake_tsd_15')
# Creates the computer generated Drake lyrics
ts_fake, drake_fake = sample_lines.ml()


def extract_local_network(df, numobs, timeframe = [drake_df.idx.min(), drake_df.idx.max()]):
    '''
    For use in app callbacks, grabs a filtered version of the dataframe based on user inputs
    '''
    df = match_idx()
    df = df[df.idx.between(timeframe[0],timeframe[1])]
    df['roll_avg'] = df.scores.rolling(numobs).mean()
    return df

def clean_label(i):
    '''
    Returns a cleaned version of the album name, for use in our dashboard's album dropdown
    '''
    df = pd.read_csv("drake.csv")
    in_disc = False
    for k in df["Album Name"]:
        if k in i:
            in_disc = True
            return k
    if in_disc == False:
        return " "

def match_idx():
    '''
    Combines our datasets on drake, matching the datetime objects of his twitter sentiment
    with when his albums were released.
    '''
    album_col = []
    name_col = []
    # Reading in album release dates
    df = pd.read_csv("drake.csv")
    for k in range(0, len(drake_df)-1):
        # Getting the time frame of the twitter scores
        lower = dt.strptime(drake_df["date"][k], '%Y-%m-%d %H:%M:%S')
        upper = dt.strptime(drake_df["date"][k+1], '%Y-%m-%d %H:%M:%S')
        in_range = False
        for i in range(0, len(df)):
            # For each album release, give a arbitrary value to that datetime index
            formatted = dt.strptime(df["Release Date"][i], '%Y-%m-%d')
            if formatted >= lower and  formatted <= upper:
                in_range = True
                album_col.append(100)
                name_col.append(df["Album Name"][i])
                print("TEST")
        # For all other values, leave at 0
        if in_range == False:
            album_col.append(0)
            name_col.append(" ")
    album_col.append(0)
    name_col.append(" ")
    print(len(album_col))
    drake_df["album_col"] = album_col
    drake_df["name_col"] = name_col
    return(drake_df)

def buttons(csv):
    '''
    Reads in our Drake csv and grabs the names of albums to use as options in the dashboard
    '''
    df = pd.read_csv(csv)
    return df['Album Name']

def make_marks(tick_len):
    '''
    Create x axis tick marks from the dataframe based on the length of
    the data and size of the timeframe
    '''
    i = 0
    mark_dict = {}
    jump = int(len(drake_df)/tick_len)
    while i < len(drake_df):
        mark_dict[i] = str(drake_df['date'][i])
        i += jump
    return mark_dict


def b64_image(image_filename):
    '''
    Reads in a b64 image at the given filepath,
    used to display our premade wordclouds in the dashbaord
    '''
    print('ran')
    with open(image_filename, 'rb') as f:
        image = f.read()
    return 'data:image/jpg;base64,' + base64.b64encode(image).decode('utf-8')

def match_url(selection):
    '''
    Takes an album name and reformats it to make the structure of the
    corresponding image filepath
    '''
    df = pd.read_csv('drake.csv')
    for i in range(0, len(df['Album Name'])):
        if df['Album Name'][i] == selection:
            print(df['Album Name'][i]+"wordcloud.jpg")
            return(df['Album Name'][i]+"wordcloud.jpg")

# Build an App using external style sheets to place graphs next to each other and add theme
external_stylesheets = [dbc.themes.SUPERHERO]
app = Dash(__name__, external_stylesheets=external_stylesheets)
# Features to list as options in the spotify chart dropdowns
graph_columns = ['danceability', 'energy', 'key', 'loudness', 'mode', 'speechiness',
                 'acousticness', 'instrumentalness', 'liveness', 'valence', 'tempo',
                 'track_name']

# Define the dashboard layout
app.layout = html.Div([
    dbc.Row(dbc.Col(dbc.Col(html.H2('Interactive Artist Dashboard: Drake'), className='text-center', width=12))),
    dcc.Dropdown(id='image-dropdown', options=[{'label': clean_label(i), 'value': i} for i in list_of_images],
                     value=list_of_images[0]),
    dbc.Row([dbc.Col(dcc.Graph(id="graph", style={'width':'45vw', 'height':'45vh'},
                                responsive = True)),
            html.Img(id='image', style={'width':'45vw', 'height':'45vh'}),
            html.H4("Time range you want to view"),
            dcc.RangeSlider(drake_df.idx.min(), drake_df.idx.max(), 6,
                            value=[drake_df.idx.min(), drake_df.idx.max()], id='timeframe', marks=make_marks(6)),
            # user input for how many obersvations should be taken for the rolling average
            html.H4("how many months do you want to observe on average?"),
            dcc.Slider(1, 10, 1, value=5, id='numobs'),
            html.Br(),
            html.H3("Machine Learning of Drake's albums"),
            html.H6(drake_fake),
            dcc.Graph(id='pie'),
            dcc.Graph(id='graph_spotify'),
            html.H6('Select X and Y Features'),
            dcc.Dropdown(id='xfeat-dropdown', options=graph_columns, value='acousticness'),
            dcc.Dropdown(id='yfeat-dropdown', options=graph_columns, value='danceability')
            ])
    ])


@app.callback(
    dash.dependencies.Output('image', 'src'),
    [dash.dependencies.Input('image-dropdown', 'value')])
def update_image_src(value):
    '''
    Grabs the word cloud for the selected album and shows it on the left of the dashboard
    '''
    return static_image_route + value

# Add a static image route that serves images from desktop
# Be *very* careful here - you don't want to serve arbitrary files
# from your computer or server
@app.server.route('{}<image_path>.jpg'.format(static_image_route))
def serve_image(image_path):
    '''
    Formats the string of for the filepath of the wordcloud image being displayed
    '''
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
    '''
    Creates the twitter sentiment time series plot to show on the left of the dashbaord
    '''
    #modify dataframe
    local = extract_local_network(drake_df, numobs, timeframe)
    #makes the sunspots over time figure
    fig = px.line(local, x='idx', y=['scores', 'roll_avg'],
                  title="Twitter Sentiment of Drake Over Time", hover_data=["name_col", "date"],
                  color_discrete_sequence=px.colors.sequential.RdBu)
    sub_local = local[local['album_col'] > 0].index
    for idx in sub_local:
        fig.add_vline(x=idx, line_width=1, line_dash="dash", line_color="green")

    fig.update_layout(hovermode='x unified', xaxis_title='Date',
                      yaxis_title='Percent Positive Language')
    fig.update_layout({'paper_bgcolor': 'rgba(0,0,0,0)', 'plot_bgcolor': 'rgba(0,0,0,0)'})
    return fig


@app.callback(
    Output("pie","figure"),
    Input('image-dropdown','value')
)
def update_pie(value):
    """
    Creates a sentiment pie plot for machine learning generated lyrics for user selected album.
    """
    sentiment = SentimentIntensityAnalyzer()
    neg = 0
    neu = 0
    pos = 0
    for l in drake_fake:
        sent = sentiment.polarity_scores(l)
        neg += sent['neg']
        neu += sent['neu']
        pos += sent['pos']
    df = pd.DataFrame.from_dict({'neg':neg,'neu':neu,'pos':pos},orient='index',columns=['value'])
    fig = px.pie(df, values ='value', names=['negative','neutral','positive'], title="Sentiment Analysis of Machine Learning Lyrics",
                 color_discrete_sequence=px.colors.sequential.RdBu)
    fig.update_layout({'paper_bgcolor': 'rgba(0,0,0,0)', 'plot_bgcolor': 'rgba(0,0,0,0)'})
    return fig



spotify_df = pd.read_csv('drake_spotify.csv')
@app.callback(
    dash.dependencies.Output('graph_spotify', 'figure'),
    [dash.dependencies.Input('image-dropdown', 'value')],
    Input('xfeat-dropdown', 'value'),
    Input('yfeat-dropdown', 'value')
)
def spotify_plot(album, xfeat='acousticness', yfeat='danceability'):
    '''
    Creates the scatter plot of Spotify song features at the bottom of the dashbaord
    Takes in dash inputs for which album to show songs from and which features to compare
    '''
    # Filters data
    dataframe = spotify_df
    album = clean_label(album)
    sub_df = dataframe[dataframe['album_name'] == album]

    # Creates and returns scatter plot
    fig = px.scatter(sub_df, x=xfeat, y=yfeat, color="track_name",
                     size='duration_ms', hover_data=['track_name'], title="Feature Comparison of Songs from {}".format(album),
                     color_discrete_sequence=px.colors.sequential.RdBu)
    fig.update_layout(showlegend=False)
    fig.update_layout({'paper_bgcolor': 'rgba(0,0,0,0)','plot_bgcolor':'rgba(0,0,0,0)'})
    fig.update_layout(yaxis_range=[0, 1], xaxis_range=[0, 1])
    return fig

if __name__ == '__main__':
    app.run_server(debug=True)
