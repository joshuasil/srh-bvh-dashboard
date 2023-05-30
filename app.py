import pandas as pd
import numpy as np
import statistics as stat
from datetime import datetime, date

## Plotly and Dash Imports
import dash
import dash_bootstrap_components as dbc
from dash import dcc, Dash
from dash import html, callback_context
from dash.dependencies import Input, Output, State, ClientsideFunction
import plotly.express as px
from dash.exceptions import PreventUpdate
from PIL import Image

## SQL Imports
from flask import Flask
import psycopg2
from sqlalchemy import create_engine
from dash_bootstrap_templates import ThemeChangerAIO, template_from_url
from sqlalchemy import text
from dotenv import load_dotenv

import os
load_dotenv()
## Postgres username, password, and database name
POSTGRES_ADDRESS = os.getenv('POSTGRES_ADDRESS') ## INSERT YOUR DB ADDRESS IF IT'S NOT ON PANOPLY
POSTGRES_PORT = os.getenv('POSTGRES_PORT')
POSTGRES_USERNAME = os.getenv('POSTGRES_USERNAME') ## CHANGE THIS TO YOUR PANOPLY/POSTGRES USERNAME
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD') ## CHANGE THIS TO YOUR PANOPLY/POSTGRES PASSWORD
POSTGRES_DBNAME = os.getenv('POSTGRES_DBNAME') ## CHANGE THIS TO YOUR DATABASE NAME

## A long string that contains the necessary Postgres login information
postgres_str = ('postgresql://{username}:{password}@{ipaddress}:{port}/{dbname}'
.format(username=POSTGRES_USERNAME,
password=POSTGRES_PASSWORD,
ipaddress=POSTGRES_ADDRESS,
port=POSTGRES_PORT,
dbname=POSTGRES_DBNAME))


## Create the Connection
engine = create_engine(postgres_str, echo=False)
conn = engine.connect()
sql_select_query = text('''SELECT * FROM public.srh_bvh_logs;''')
sqlresult = conn.execute(sql_select_query)
df_comp = pd.DataFrame(sqlresult.fetchall())
df_comp.columns = sqlresult.keys()
df_comp["request_timestamp"] = df_comp["request_timestamp"].dt.tz_localize('UTC').dt.tz_convert(None)
df_comp.sort_values(by=["request_timestamp"], inplace=True, ascending=False)
conn.commit()
conn.close()

df_user_statistics = df_comp['conversation_id'].value_counts().rename_axis('users').reset_index(name='counts')
unique_users = df_comp['conversation_id'].nunique()

tot_questions = df_comp.shape[0]
avg_mess_per_user = round(df_user_statistics['counts'].mean(),2)
minimum_mess_per_user = df_user_statistics['counts'].min()
maximum_mess_per_user = df_user_statistics['counts'].max()
df_comp['request_date'] = df_comp['request_timestamp'].dt.date
df_count_by_date =df_comp['request_date'].value_counts().sort_index().rename_axis('dates').reset_index(name='counts')
df_count_by_date['cum_total'] = df_count_by_date['counts'].cumsum()

# pandas group by and apply function
df_confidence = df_comp.groupby(['request_date'])['confidence'].mean().reset_index(name='avg_confidence')
df_confidence['avg_confidence'] = (df_confidence['avg_confidence']*100).apply(lambda x: round(x, 2))
df_comp['browser_os_context'].fillna('unknown',inplace=True)

avg_accuracy = round(df_comp['confidence'].mean()*100,2)
avg_accuracy = str(avg_accuracy) + '%'
colors = {
    'background': '#FEFFFF',
    'graph background': '#CDD0D0',
    'title text': '#012337',
    'intent': 'oranges', # Will use continuous color sequence
    'source': '#EF8B69', # Will use discrete color sequence
    'browser': '#F1E091', # Will use discrete color sequence
    'hour': 'greens', # Will use continuous color sequence
    'subtitle text': '#012337',
    'label text': '#012337',
    'line color': '#056B7D'
}

covid_logo = Image.open('COVID_chatbot_logo.png')
sph_logo = Image.open('coloradosph_stacked_schools.jpg')


df_confidence = df_comp.groupby(['request_date'])['confidence'].mean().reset_index(name='avg_confidence')
df_confidence['avg_confidence'] = (df_confidence['avg_confidence']*100).apply(lambda x: round(x, 2))
fig_acc_time = px.line(df_confidence, x='request_date', y='avg_confidence', title='Average Confidence by Time',
                       labels = {'index': 'Date', 'value':'Percentage'}, render_mode='webg1')
fig_acc_time.update_layout(title_x=0.5)
fig_acc_time.update_xaxes(rangeslider_visible=True)


fig_cum_total_by_date = px.line(df_count_by_date, x='dates', y=['cum_total', 'counts'], title = 'Cumulative Count by Day',
                              labels = {'dates': 'Date', 'cum_total': 'Cumulative Sum', 'counts':'Counts'}, render_mode='webg1')
fig_cum_total_by_date.update_layout(title_x=0.5)
fig_cum_total_by_date.update_xaxes(rangeslider_visible=True)



count_by_intent = df_comp[df_comp['intent_bot'].notna()]['intent_bot'].value_counts().rename_axis('intent').reset_index(name='counts')[:15]
fig_intent = px.bar(count_by_intent, y='intent', x="counts", orientation='h', title = 'Top Intents', color = 'counts',
labels = {'intent': 'Intent', 'counts': 'Count'}, color_continuous_scale = colors['intent'])
fig_intent.update_layout(title_x=0.5,yaxis=dict(autorange="reversed"))




count_by_browser = df_comp['browser_os_context'].value_counts(normalize=True).rename_axis('browser').reset_index(name='counts')
fig_browser =px.pie(count_by_browser, values='counts', names='browser', title='Browser Percentages',
labels = {'counts': 'count', 'hour': 'Hour'}, color_discrete_sequence=[colors['browser']])
fig_browser.update_layout(title_x=0.5)

dbc_css = (
    "https://cdn.jsdelivr.net/gh/AnnMarieW/dash-bootstrap-templates@V1.0.1/dbc.min.css"
)
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP, dbc_css],
           meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1"}
    ])
server = app.server


modal = html.Div(
    [
        dbc.Button("Info", id="open", n_clicks=0),
        dbc.Modal(
            [
                dbc.ModalHeader(dbc.ModalTitle("Dashboard Info")),
                dbc.ModalBody("Write new information about the dashboard here."),
                dbc.ModalFooter(
                    dbc.Button(
                        "Close", id="close", className="ms-auto", n_clicks=0
                    )
                ),
            ],
            id="modal",
            is_open=False,
        ),
    ]
)


@app.callback(
    Output("modal", "is_open"),
    [Input("open", "n_clicks"), Input("close", "n_clicks")],
    [State("modal", "is_open")],
)
def toggle_modal(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open


cards_global = [
        dbc.Row(
            [   dbc.Col(dbc.DropdownMenu(label='Beginning and End Dates',
                                    children=[dcc.DatePickerRange(id='begin_date',
                                            min_date_allowed=df_comp['request_date'].min(),max_date_allowed=date.today(),
                                            start_date = df_comp['request_date'].min(),end_date = date.today())],className="form-check")),
                dbc.Col(dbc.Card([html.P("Total Unique Users"),html.H6(unique_users,id='unique_users'),],
                                    body=True,color="primary",inverse=True,style={'textAlign': 'center'},className="mx-1"),),
                dbc.Col(dbc.Card([html.P("Total Questions"),html.H6(tot_questions,id='tot_questions'),],
                                    body=True,color="primary",inverse=True,style={'textAlign': 'center'},className="mx-1"),),
                dbc.Col(dbc.Card([html.P("Avg No. of Messages"),html.H6(avg_mess_per_user,id='avg_mess_per_user'),],
                                    body=True,color="primary",inverse=True,style={'textAlign': 'center'},className="mx-1"),),
                dbc.Col(dbc.Card([html.P("Min No. of Messages"),html.H6(minimum_mess_per_user,id='minimum_mess_per_user'),],
                                    body=True,color="primary",inverse=True,style={'textAlign': 'center'},className="mx-1"),),
                dbc.Col(dbc.Card([html.P("Max No. of Messages"),html.H6(maximum_mess_per_user,id='maximum_mess_per_user'),],
                body=True,color="primary",inverse=True,style={'textAlign': 'center'},className="mx-1"),),
                dbc.Col(dbc.Card([html.P("Average Confidence"),html.H6(avg_accuracy,id='avg_accuracy'),],
        body=True,color="primary",inverse=True,style={'textAlign': 'center'},className="mx-1"),),
            dbc.Col(modal),
            ],style={'textAlign': 'center'}
        ),
    ]

# theme changer: dbc.Row(ThemeChangerAIO(aio_id="theme", radio_props={"value":dbc.themes.FLATLY}))
navbar = dbc.NavbarSimple(
    children=[html.Img(src=sph_logo,height='40px'),
    ],
    brand="Clini Chat - Boulder Valley Health - Sexual Repreductive Health Chatbot Dashboard",
    brand_href="#",
    color="primary",
    dark=True,
)


figures_div = html.Div([
    dbc.Row([dbc.Col(dcc.Graph(id='fig_acc_time',figure=fig_acc_time)),dbc.Col(dcc.Graph(id='fig_cum_total_by_date',figure=fig_cum_total_by_date))]),
    dbc.Row([dbc.Col(dcc.Graph(id='fig_browser',figure=fig_browser)),dbc.Col(dcc.Graph(id='fig_intent',figure=fig_intent))])
])





app.layout = html.Div(style={'padding':10, 'backgroundColor': colors['background']}, children =[html.Div(navbar),
    dbc.Col(
                    children=[dbc.Card(
                        [dbc.CardHeader("Cumulative User Statistics"),dbc.CardBody(cards_global)]
                    )]),
figures_div
    ])


@app.callback([
    dash.dependencies.Output('unique_users', 'children'),
    dash.dependencies.Output('tot_questions', 'children'),
    dash.dependencies.Output('avg_mess_per_user', 'children'),
    dash.dependencies.Output('minimum_mess_per_user', 'children'),
    dash.dependencies.Output('maximum_mess_per_user', 'children'),
    dash.dependencies.Output('avg_accuracy', 'children'),
    dash.dependencies.Output('fig_acc_time', 'figure'),
    dash.dependencies.Output('fig_cum_total_by_date', 'figure'),
    dash.dependencies.Output('fig_browser', 'figure'),
    dash.dependencies.Output('fig_intent', 'figure')],
    [dash.dependencies.Input('begin_date', 'start_date'),
    dash.dependencies.Input('begin_date', 'end_date')])
# Callback Function

def date_cum_count_media_type(begin_date, end_date):
    begin_date = datetime.strptime(begin_date,'%Y-%m-%d')
    end_date = datetime.strptime(end_date,'%Y-%m-%d')
    updated_df = df_comp.copy()
    updated_df['request_timestamp'] = pd.to_datetime(updated_df['request_timestamp'])
    updated_df = df_comp[(df_comp['request_timestamp'] >= begin_date) & (df_comp['request_timestamp'] <= end_date)]
    unique_users = updated_df['user_id'].nunique()
    tot_questions = updated_df['user_id'].count()
    avg_mess_per_user = round(updated_df.groupby('user_id')['user_id'].count().mean(),2)
    minimum_mess_per_user = updated_df.groupby('user_id')['user_id'].count().min()
    maximum_mess_per_user = updated_df.groupby('user_id')['user_id'].count().max()
    avg_accuracy = round(updated_df['confidence'].mean(),4) * 100
    avg_accuracy = str(avg_accuracy) + '%'

    df_confidence = df_comp.groupby(['request_date'])['confidence'].mean().reset_index(name='avg_confidence')
    df_confidence['avg_confidence'] = (df_confidence['avg_confidence']*100).apply(lambda x: round(x, 2))
    fig_acc_time = px.line(df_confidence, x='request_date', y='avg_confidence', title='Average Confidence by Time',
                        labels = {'index': 'Date', 'value':'Percentage'}, render_mode='webg1')
    fig_acc_time.update_layout(title_x=0.5)
    fig_acc_time.update_xaxes(rangeslider_visible=True)

    df_count_by_date_new =updated_df['request_date'].value_counts().sort_index().rename_axis('dates').reset_index(name='counts')
    df_count_by_date_new['cum_total'] = df_count_by_date_new['counts'].cumsum()
    fig_cum_total_by_date = px.line(df_count_by_date_new, x='dates', y=['cum_total', 'counts'], title = 'Cumulative Count by Day',
                                labels = {'dates': 'Date', 'cum_total': 'Cumulative Sum', 'counts':'Counts'}, render_mode='webg1')
    fig_cum_total_by_date.update_layout(title_x=0.5)
    fig_cum_total_by_date.update_xaxes(rangeslider_visible=True)

    count_by_intent = updated_df[updated_df['intent_bot'].notna()]['intent_bot'].value_counts().rename_axis('intent').reset_index(name='counts')[:15]
    fig_intent = px.bar(count_by_intent, y='intent', x="counts", orientation='h', title = 'Top Intents', color = 'counts',
    labels = {'intent': 'Intent', 'counts': 'Count'}, color_continuous_scale = colors['intent'])
    fig_intent.update_layout(title_x=0.5,yaxis=dict(autorange="reversed"))

    count_by_browser = updated_df['browser_os_context'].value_counts(normalize=True).rename_axis('browser').reset_index(name='counts')
    fig_browser =px.pie(count_by_browser, values='counts', names='browser', title='Browser Percentages',
    labels = {'counts': 'count', 'hour': 'Hour'}, color_discrete_sequence=[colors['browser']])
    fig_browser.update_layout(title_x=0.5)

    return [unique_users, tot_questions, avg_mess_per_user, minimum_mess_per_user, maximum_mess_per_user, avg_accuracy, fig_acc_time, fig_cum_total_by_date, fig_intent, fig_browser]

if __name__ == '__main__':
    app.run_server(host="localhost", port=8080,debug=False)