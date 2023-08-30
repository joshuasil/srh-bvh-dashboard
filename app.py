# usage python app.py
import pandas as pd
import numpy as np
import statistics as stat
from datetime import datetime, date, timedelta
from dateutil import parser
from get_postgres_str import get_postgres_str
from components import *

## Plotly and Dash Imports
import dash
import dash_bootstrap_components as dbc
from dash import dcc, Dash, html, callback_context
from dash.dependencies import Input, Output, State, ClientsideFunction
from dash_bootstrap_templates import ThemeChangerAIO, template_from_url
import plotly.express as px
from dash.exceptions import PreventUpdate
from PIL import Image

## SQL Imports
from flask import Flask
import psycopg2
from sqlalchemy import create_engine, text


## Postgres username, password, and database name
postgres_str = get_postgres_str()


## Create the Connection
engine = create_engine(postgres_str, echo=False)
conn = engine.connect()
sql_select_query = text('''SELECT * FROM public.srh_bvh_logs;''')
sqlresult = conn.execute(sql_select_query)
df_comp = pd.DataFrame(sqlresult.fetchall())
df_comp.columns = sqlresult.keys()
conn.commit()
conn.close()

# processing main dataframe
df_comp = df_comp[df_comp['input'].notna()]
df_comp["request_timestamp"] = df_comp["request_timestamp"].dt.tz_localize('America/Denver')
df_comp.sort_values(by=["request_timestamp"], inplace=True, ascending=False)
df_comp['request_timestamp'] = pd.to_datetime(df_comp['request_timestamp'])
df_comp['request_date'] = df_comp['request_timestamp'].dt.date
df_comp['confidence'] = df_comp['confidence'].astype(float)
df_comp['browser_os_context'].fillna('unknown',inplace=True)

print(df_comp.shape)

unique_users, tot_questions, avg_mess_per_user, minimum_mess_per_user, maximum_mess_per_user, avg_accuracy, book_apt_count = get_metrics(df_comp)


covid_logo = Image.open('COVID_chatbot_logo.png')
clinic_logo = Image.open('logo.png')
clinic_logo = clinic_logo.convert('RGB')

fig_acc_time = get_fig_acc_time(df_comp)
fig_cum_total_by_date = get_fig_cum_total_by_date(df_comp)
fig_intent = get_count_by_intent(df_comp)
fig_browser = get_count_by_browser(df_comp)



dbc_css = (
    "https://cdn.jsdelivr.net/gh/AnnMarieW/dash-bootstrap-templates@V1.0.1/dbc.min.css"
)
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP, dbc_css],
           meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1"}
    ])
server = app.server

modal_desc = html.Div([html.H2('Beginning and End Dates'),html.P(dates_text),html.H2('Total Unique Users'),html.P(total_unique_users_text),
                       html.H2('Total Questions'),html.P(total_questions_text),html.H2('Avg No. of Messages'),html.P(avg_messages_text),
                       html.H2('Min No. of Messages'),html.P(min_messages_text),html.H2('Max No. of Messages'),html.P(max_messages_text),
                       html.H2('Average Confidence'),html.P(avg_accuracy_text),html.H2('Book Appointment Count'),html.P(book_apt_count_text), 
                       html.H2('Average Confidence by Time'),html.P(avg_condifence_by_time_text),
                       html.H2('Cumulative Total by Day'),html.P(cum_tot_by_day_text),html.H2('Top Intents'),html.P(top_intents_text),
                       html.H2('Browser Percentages'),html.P(browser_percentages_text),])

modal = html.Div([dbc.Button("Info", id="open", n_clicks=0),
        dbc.Modal([dbc.ModalHeader(dbc.ModalTitle("Dashboard Info")),
                dbc.ModalBody(modal_desc),
                dbc.ModalFooter(dbc.Button("Close", id="close", className="ms-auto", n_clicks=0)),],
            id="modal",scrollable=True,is_open=False,size='xl' ,),])


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
                                            start_date = df_comp['request_date'].min(),end_date = datetime.now())],className="form-check")),
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
                dbc.Col(dbc.Card([html.P("Book Appointment Count"),html.H6(book_apt_count,id='book_apt_count'),],
                                     body=True,color="primary",inverse=True,style={'textAlign': 'center'},className="mx-1"),),
            dbc.Col(modal),
            ],style={'textAlign': 'center'}
        ),
    ]

# theme changer: dbc.Row(ThemeChangerAIO(aio_id="theme", radio_props={"value":dbc.themes.FLATLY}))
navbar = dbc.NavbarSimple(
    children=[html.Img(src=clinic_logo,height='40px'),
    ],
    brand="Clinic Chat - Boulder Valley Health - Sexual Reproductive Health Chatbot Dashboard",
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
    end_date = parser.parse(end_date)
    end_date = end_date + timedelta(seconds=86399)
    updated_df = df_comp.copy()
    updated_df['request_timestamp'] = pd.to_datetime(updated_df['request_timestamp']).dt.tz_localize(None)
    updated_df = updated_df[(updated_df['request_timestamp'] >= begin_date) & (updated_df['request_timestamp'] <= end_date)]
    unique_users, tot_questions, avg_mess_per_user, minimum_mess_per_user, maximum_mess_per_user, avg_accuracy, book_apt_count = get_metrics(updated_df)

    fig_acc_time = get_fig_acc_time(updated_df)
    fig_cum_total_by_date = get_fig_cum_total_by_date(updated_df)
    fig_intent = get_count_by_intent(updated_df)
    fig_browser = get_count_by_browser(updated_df)

    print(df_comp.shape)

    return [unique_users, tot_questions, avg_mess_per_user, minimum_mess_per_user, maximum_mess_per_user, avg_accuracy, fig_acc_time, fig_cum_total_by_date, fig_intent, fig_browser]

if __name__ == '__main__':
    app.run_server(host="localhost", port=8080,debug=False)