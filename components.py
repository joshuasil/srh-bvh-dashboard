import pandas as pd
import plotly.express as px

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

def get_metrics(df):
    df_user_statistics = df['conversation_id'].value_counts().rename_axis('users').reset_index(name='counts')
    unique_users = df['conversation_id'].nunique()

    tot_questions = df.shape[0]
    avg_mess_per_user = round(df_user_statistics['counts'].mean(),2)
    minimum_mess_per_user = df_user_statistics['counts'].min()
    maximum_mess_per_user = df_user_statistics['counts'].max()
    df_confidence = df.groupby(['request_date'])['confidence'].mean().reset_index(name='avg_confidence')
    df_confidence['avg_confidence'] = (df_confidence['avg_confidence']*100).apply(lambda x: round(x, 2))
    avg_accuracy = round(df['confidence'].mean()*100,2)
    avg_accuracy = str(avg_accuracy) + '%'
    book_apt_count = df[df['intent_bot']=='schedule_an_appointment'].shape[0]
    return unique_users, tot_questions, avg_mess_per_user, minimum_mess_per_user, maximum_mess_per_user, avg_accuracy, book_apt_count

def get_fig_acc_time(df):
    df_confidence = df.groupby(['request_date'])['confidence'].mean().reset_index(name='avg_confidence')
    df_confidence['avg_confidence'] = (df_confidence['avg_confidence']*100).apply(lambda x: round(x, 2))
    df_confidence['cumulative_avg_confidence'] = df_confidence['avg_confidence'].expanding().mean()
    fig_acc_time = px.line(df_confidence, x='request_date', y='cumulative_avg_confidence', title='Cumulative Average Confidence by Time',
                        labels = {'request_date': 'Drag here to adjust dates', 'cumulative_avg_confidence':'Cumulative Average confidence Percentage'}, render_mode='webgl')
    fig_acc_time.update_layout(title_x=0.5)
    fig_acc_time.update_layout(
                xaxis=dict(rangeslider=dict(visible=True,bgcolor="#636EFA",thickness=0.04),
                        type="date"))
    return fig_acc_time


def get_fig_cum_total_by_date(df):
    df_count_by_date =df['request_date'].value_counts().sort_index().rename_axis('dates').reset_index(name='counts')
    df_count_by_date['cum_total'] = df_count_by_date['counts'].cumsum()
    fig_cum_total_by_date = px.line(df_count_by_date, x='dates', y=['cum_total', 'counts'], title = 'Cumulative Total by Day',
                              labels = {'dates': 'Drage here to adjust dates', 'cum_total': 'Cumulative Sum', 'counts':'Counts'}, render_mode='webg1')
    fig_cum_total_by_date.update_layout(title_x=0.5)
    fig_cum_total_by_date.update_layout(
                xaxis=dict(rangeslider=dict(visible=True,bgcolor="#636EFA",thickness=0.04),
                        type="date"))
    return fig_cum_total_by_date

def get_count_by_intent(df):
    count_by_intent = df[df['intent_bot'].notna()]['intent_bot'].value_counts().rename_axis('intent').reset_index(name='counts')[:15]
    fig_intent = px.bar(count_by_intent, y='intent', x="counts", orientation='h', title = 'Top Intents', color = 'counts',
    labels = {'intent': 'Intent', 'counts': 'Count'}, color_continuous_scale = colors['intent'])
    fig_intent.update_layout(title_x=0.5,yaxis=dict(autorange="reversed"))
    return fig_intent

def get_count_by_browser(df):
    count_by_browser = df['browser_os_context'].value_counts(normalize=True).rename_axis('browser').reset_index(name='counts')
    fig_browser =px.pie(count_by_browser, values='counts', names='browser', title='Browser Percentages',
    labels = {'counts': 'count', 'hour': 'Hour'}, color_discrete_sequence=[colors['browser']])
    fig_browser.update_layout(title_x=0.5)
    return fig_browser


avg_condifence_by_time_text = 'This figure gives us the average confidence with which the chatbot executed the intent. The confidence is a value between 0 and 1, with 1 being the highest confidence. The average confidence is calculated by taking the average of all the confidence values for each day.'
cum_tot_by_day_text = 'This figure gives us the cumulative count of the number of questions asked by users. The cumulative count is calculated by taking the sum of the number of questions asked by users for each day.'
top_intents_text = 'This figure gives us the top 15 intents that were executed by the chatbot. The intents are the actions that the chatbot executes in response to a user question. The count is the number of times the intent was executed.'
browser_percentages_text = 'This figure gives us the percentage of users that used each browser to access the chatbot. The percentage is the percentage of users that used each browser.'
total_unique_users_text = 'This is the total number of unique users that have accessed the chatbot.'
total_questions_text = 'This is the total number of questions that have been asked by users.'
avg_messages_text = 'This is the total number of messages received by the system divided by the number of conversations.'
min_messages_text = 'This is the minimum number of messages received by the system for a conversation.'
max_messages_text = 'This is the maximum number of messages received by the system for a conversation.'
avg_accuracy_text = 'This is the average confidence with which the chatbot executed the intent. The confidence is a value between 0 and 1, with 1 being the highest confidence.'
dates_text = 'This is the date range for which the data is being displayed. The start and end date can be adjusted by picking on the calendar icon and selecting the desired dates.'
book_apt_count_text = 'This is the total number of times users asked the chatbot to book an appointment.'