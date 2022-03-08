#____________________________________________________________ CS003 ________________________________________________________________

import dash
from dash import dcc
from dash import html
from dash import dash_table
import plotly.express as px
import pandas as pd
import numpy as np

from datetime import date
from datetime import timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots

import os
import sys
import elasticsearch
from elasticsearch import Elasticsearch

es= Elasticsearch([{'host': '10.10.6.90','port': 9200}])

es.ping()


'''
__________________________________________________

For yesterday's date
__________________________________________________
'''
today = date.today()
yesterday = today - timedelta(days = 20)
today=str(today)

yesterday = yesterday.strftime('%Y-%m-%dT%H:%M:%SZ')
print("DATA ONLY ACQUIRED TILL DATE: - \t",yesterday)

#for Slide placement to get thickness info
res = es.search(index="slide_locking", doc_type="", body={"_source":{
    "includes":["data.load_identifier","data.time_stamp","data.scanner_name","data.cluster_name"]},
    "query":{"range": {"data.time_stamp":{"time_zone": "+01:00","gte": yesterday,"lte": "now"}}},}, size=1000000,)
print("slide_locking ACQUIRED SUCCESSFULLY")
slide_locking = pd.json_normalize(res['hits']['hits'])

'''
__________________________________________________

Adding date as an columns from time stamp
__________________________________________________
'''

slide_locking['date'] = pd.to_datetime(slide_locking['_source.data.time_stamp']).dt.date
slide_locking['date'] = pd.to_datetime(slide_locking['date'])

slide_locking['dropdown'] = slide_locking['date'].astype(str)+"("+slide_locking['_source.data.load_identifier']+")"

Station_1 = "H01JBA21P"
Station_2 = "H01JBA15R"
Station_3 = "H01JBA11R"
Station_4 = "H01JBA14R"



external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

colors = {
    'background': '#111111',
    'text': '#44bd32'
}


#tab style
tabs_styles = {
    'height': '70px'
}
tab_style = {
    'borderBottom': '1px solid #d6d6d6',
    'padding': '25px',
    'fontWeight': 'bold'
}

tab_selected_style = {
    'borderTop': '1px solid #d6d6d6',
    'borderBottom': '1px solid #d6d6d6',
    'backgroundColor': '#119DFF',
    'color': 'white',
    'padding': '10px'
}
##tab style ends here

category1 = []
for opt in sorted(slide_locking[slide_locking['_source.data.scanner_name']==Station_1]['dropdown'].unique())[::-1]:
    category1.append({'label' : opt, 'value' : opt})

category2 = []
for opt in sorted(slide_locking[slide_locking['_source.data.scanner_name']==Station_2]['dropdown'].unique())[::-1]:
    category2.append({'label' : opt, 'value' : opt})

category3 = []
for opt in sorted(slide_locking[slide_locking['_source.data.scanner_name']==Station_3]['dropdown'].unique())[::-1]:
    category3.append({'label' : opt, 'value' : opt})

category4 = []
for opt in sorted(slide_locking[slide_locking['_source.data.scanner_name']==Station_4]['dropdown'].unique())[::-1]:
    category4.append({'label' : opt, 'value' : opt})



app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

server = app.server

app.layout = html.Div([
    dcc.Tabs([
        dcc.Tab(label='Scanner Health',style=tab_style, selected_style=tab_selected_style, children=[
            html.Br(),
            html.Br(),
            html.Br(),
            html.Br(),
            html.Br(),
            html.Br(),
            html.Br(),
            html.Br(),
            html.Br(),
            html.Br(),
            html.Br(),
            html.Br(),
            #html.Img(src=app.get_asset_url('/spec2.png'),style={'maxWidth': '100%','maxHeight': '100%','marginLeft': 'auto','marginRight': 'auto'}),
            html.Br(),
            html.Br(),
            html.H1(children='Components status',style={
            'textAlign': 'center',
            'color': colors['text']}),
            html.H1(children='\t\t- Last updated for :'+str(date.today()- timedelta(days = 1)),style={
            'textAlign': 'center',
            'color': colors['text']})

        ]),
        # |----------------------------------------------------------------------------|
        # STATION - 1
        # |----------------------------------------------------------------------------|
        dcc.Tab(label=Station_1,style=tab_style, selected_style=tab_selected_style, children=[
        html.Br(),
        html.H1(children='Slot Status'),
        html.Label("Choose date"),
            dcc.Dropdown(id = 'slots1', options = category1,value=sorted(slide_locking[slide_locking['_source.data.scanner_name']==Station_1]['dropdown'].unique())[-1]),
            dcc.Graph(id='graphslots1',style={'verticalAlign': 'middle','margin-left': '550px'}),
        html.Br(),
        html.H1(children='RZ Status'),
        html.Label("Choose date"),
            dcc.Dropdown(id = 'rz1', options = category1,value=sorted(slide_locking[slide_locking['_source.data.scanner_name']==Station_1]['dropdown'].unique())[-1]),
            dcc.Graph(id='graphrz1',style={'verticalAlign': 'middle','margin-left': '550px'}),
        html.Br(),
        html.H1(children='Slide Placement Status'),
        html.Label("Choose date"),
            dcc.Dropdown(id = 'place1', options = category1,value=sorted(slide_locking[slide_locking['_source.data.scanner_name']==Station_1]['dropdown'].unique())[-1]),
            dcc.Graph(id='graphplace1',style={'verticalAlign': 'middle','margin-left': '550px'}),
        html.Br(),
        html.H1(children='Slide Locking Status'),
        html.Label("Choose date"),
            dcc.Dropdown(id = 'current1', options = category1,value=sorted(slide_locking[slide_locking['_source.data.scanner_name']==Station_1]['dropdown'].unique())[-1]),
            html.Br(),
            dcc.RadioItems(id = 's1_rbutton',options = [dict(label = 'Current Info', value = 'A'),
                                                 dict(label = 'Correlate with Slide Height', value = 'B')],value = 'A'),
            dcc.Graph(id='graphcurrent1',style={'verticalAlign': 'middle','margin-left': '550px'}), 
        ]),
        # |----------------------------------------------------------------------------|
        # STATION - 2
        # |----------------------------------------------------------------------------|
        dcc.Tab(label=Station_2,style=tab_style, selected_style=tab_selected_style, children=[
        html.Br(),
        html.H1(children='Slot Status'),
        html.Label("Choose date"),
                dcc.Dropdown(id = 'slots2', options = category2,value=sorted(slide_locking[slide_locking['_source.data.scanner_name']==Station_2]['dropdown'].unique())[-1]),
                dcc.Graph(id='graphslots2',style={'verticalAlign': 'middle','margin-left': '550px'}),
        html.Br(),
        html.H1(children='RZ Status'),
        html.Label("Choose date"),
            dcc.Dropdown(id = 'rz2', options = category2,value=sorted(slide_locking[slide_locking['_source.data.scanner_name']==Station_2]['dropdown'].unique())[-1]),
            dcc.Graph(id='graphrz2',style={'verticalAlign': 'middle','margin-left': '550px'}),
        html.Br(),
        html.H1(children='Slide Placement Status'),
        html.Label("Choose date"),
            dcc.Dropdown(id = 'place2', options = category2,value=sorted(slide_locking[slide_locking['_source.data.scanner_name']==Station_2]['dropdown'].unique())[-1]),
            dcc.Graph(id='graphplace2',style={'verticalAlign': 'middle','margin-left': '550px'}),    
        html.Br(),
        html.H1(children='Slide Locking Status'),
        html.Label("Choose date"),
            dcc.Dropdown(id = 'current2', options = category2,value=sorted(slide_locking[slide_locking['_source.data.scanner_name']==Station_2]['dropdown'].unique())[-1]),
            html.Br(),
            dcc.RadioItems(id = 's2_rbutton',options = [dict(label = 'Current Info', value = 'A'),
                        dict(label = 'Correlate with Slide Height', value = 'B')],value = 'A'),
            dcc.Graph(id='graphcurrent2',style={'verticalAlign': 'middle','margin-left': '550px'}),     
        ]),
        # |----------------------------------------------------------------------------|
        # STATION - 3
        # |----------------------------------------------------------------------------|
        dcc.Tab(label=Station_3,style=tab_style, selected_style=tab_selected_style, children=[
        html.Br(),
        html.H1(children='Slot Status'),
        html.Label("Choose date"),
                dcc.Dropdown(id = 'slots3', options = category3,value=sorted(slide_locking[slide_locking['_source.data.scanner_name']==Station_3]['dropdown'].unique())[-1]),
                dcc.Graph(id='graphslots3',style={'verticalAlign': 'middle','margin-left': '550px'}),
        html.Br(),
        html.H1(children='RZ Status'),
        html.Label("Choose date"),
            dcc.Dropdown(id = 'rz3', options = category3,value=sorted(slide_locking[slide_locking['_source.data.scanner_name']==Station_3]['dropdown'].unique())[-1]),
            dcc.Graph(id='graphrz3',style={'verticalAlign': 'middle','margin-left': '550px'}),
        html.Br(),
        html.H1(children='Slide Placement Status'),
        html.Label("Choose date"),
            dcc.Dropdown(id = 'place3', options = category3,value=sorted(slide_locking[slide_locking['_source.data.scanner_name']==Station_3]['dropdown'].unique())[-1]),
            dcc.Graph(id='graphplace3',style={'verticalAlign': 'middle','margin-left': '550px'}),
        html.Br(),
        html.H1(children='Slide Locking Status'),
        html.Label("Choose date"),
            dcc.Dropdown(id = 'current3', options = category3,value=sorted(slide_locking[slide_locking['_source.data.scanner_name']==Station_3]['dropdown'].unique())[-1]),
            html.Br(),
            dcc.RadioItems(id = 's3_rbutton',options = [dict(label = 'Current Info', value = 'A'),
                                                 dict(label = 'Correlate with Slide Height', value = 'B')],value = 'A'),
            dcc.Graph(id='graphcurrent3',style={'verticalAlign': 'middle','margin-left': '550px'}), 
        ]),
        # |----------------------------------------------------------------------------|
        # STATION - 4
        # |----------------------------------------------------------------------------|
        dcc.Tab(label=Station_4,style=tab_style, selected_style=tab_selected_style, children=[
        html.Br(),
        html.H1(children='Slot Status'),
        html.Label("Choose date"),
                dcc.Dropdown(id = 'slots4', options = category4,value=sorted(slide_locking[slide_locking['_source.data.scanner_name']==Station_4]['dropdown'].unique())[-1]),
                dcc.Graph(id='graphslots4',style={'verticalAlign': 'middle','margin-left': '550px'}),
        html.Br(),
        html.H1(children='RZ Status'),
        html.Label("Choose date"),
            dcc.Dropdown(id = 'rz4', options = category4,value=sorted(slide_locking[slide_locking['_source.data.scanner_name']==Station_4]['dropdown'].unique())[-1]),
            dcc.Graph(id='graphrz4',style={'verticalAlign': 'middle','margin-left': '550px'}),
        html.Br(),
        html.H1(children='Slide Placement Status'),
        html.Label("Choose date"),
            dcc.Dropdown(id = 'place4', options = category4,value=sorted(slide_locking[slide_locking['_source.data.scanner_name']==Station_4]['dropdown'].unique())[-1]),
            dcc.Graph(id='graphplace4',style={'verticalAlign': 'middle','margin-left': '550px'}),
        html.Br(),
        html.H1(children='Slide Locking Status'),
        html.Label("Choose date"),
            dcc.Dropdown(id = 'current4', options = category4,value=sorted(slide_locking[slide_locking['_source.data.scanner_name']==Station_4]['dropdown'].unique())[-1]),
            html.Br(),
            dcc.RadioItems(id = 's4_rbutton',options = [dict(label = 'Current Info', value = 'A'),
                                                 dict(label = 'Correlate with Slide Height', value = 'B')],value = 'A'),
            dcc.Graph(id='graphcurrent4',style={'verticalAlign': 'middle','margin-left': '550px'}), 
        ])

]) 
])


'''
if __name__ == '__main__':
    app.run_server(debug=True,port=8700)
'''
