import re
from dash import dcc
from dash import html
from dash import dash_table
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
import pandas as pd
from datetime import date
from datetime import timedelta
# must add this line in order for the app to be deployed successfully on Heroku
from index import server
from index import app
# import all pages in the app
from apps import home,cs003,cs004
import numpy as np
import plotly.express as px
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import elasticsearch
from elasticsearch import Elasticsearch


es= Elasticsearch([{'host': '10.10.6.90','port': 9200}])

es.ping()

# building the navigation bar
# https://github.com/facultyai/dash-bootstrap-components/blob/master/examples/advanced-component-usage/Navbars.py
dropdown = dbc.DropdownMenu(
    children=[
        dbc.DropdownMenuItem("Home", href="/home"),
        dbc.DropdownMenuItem("CS003", href="/cs003"),
    ],
    nav = True,
    in_navbar = True,
    label = "Explore",
)

navbar = dbc.Navbar(
    dbc.Container(
        [
            html.A(
                # Use row and col to control vertical alignment of logo / brand
                dbc.Row(
                    [
                        dbc.Col(html.Img(src=app.get_asset_url('spec3.png'), height="30px")),
                        dbc.Col(dbc.NavbarBrand("Report DASH", className="ml-2")),
                    ],
                    align="center",

                ),
                href="/home",
            ),
            dbc.NavbarToggler(id="navbar-toggler2"),
            dbc.Collapse(
                dbc.Nav(
                    # right align dropdown menu with ml-auto className
                    [dropdown], className="ml-auto", navbar=True
                ),
                id="navbar-collapse2",
                navbar=True,
            ),
        ]
    ),
    color="dark",
    dark=True,
    className="mb-4",
)

def toggle_navbar_collapse(n, is_open):
    if n:
        return not is_open
    return is_open

for i in [2]:
    app.callback(
        Output(f"navbar-collapse{i}", "is_open"),
        [Input(f"navbar-toggler{i}", "n_clicks")],
        [State(f"navbar-collapse{i}", "is_open")],
    )(toggle_navbar_collapse)

# embedding the navigation bar
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    navbar,
    html.Div(id='page-content')
])

@app.callback(Output('page-content', 'children'),
              [Input('url', 'pathname')])
def display_page(pathname):
    if pathname == '/home':
        return home.app.layout
    elif pathname == '/cs003':
        return cs003.app.layout
    elif pathname == '/cs004':
        return cs004.app.layout
    else:
        return home.app.layout

# |----------------------------------------------------------------------------|
# Time Delta for reference
# |----------------------------------------------------------------------------|
today = date.today()
yesterday = today - timedelta(days = 1)
today=str(today)
yesterday=str(yesterday)

Station_1 = "H01BBB23P"
Station_2 = "H01BBB25P"
Station_3 = "H01BBB19P"
Station_4 = "H01BBB24P"
# |----------------------------------------------------------------------------|
# SLot Empty 
# |----------------------------------------------------------------------------|


def dataframes_additions(df):
    df['date'] = pd.to_datetime(df['_source.data.time_stamp']).dt.date
    df['date'] = pd.to_datetime(df['date'])
    df = df.dropna(subset=['_source.data.row_index','_source.data.col_index'])
    df['_source.data.row_index'] = df['_source.data.row_index'].astype(int)
    df['_source.data.col_index'] = df['_source.data.col_index'].astype(int)
    df['dropdown'] = df['date'].astype(str)+"("+df['_source.data.load_identifier']+")"
    df['row_col'] = (df['_source.data.row_index']+1).astype(str)+"_"+(df['_source.data.col_index']+1).astype(str)
    df = df.sort_values(["_source.data.row_index","_source.data.col_index"], ascending = (True, True))

    return df


def slots_plot(output,input):
    @app.callback(Output(output, 'figure'),
                [Input(input, 'value')])
    def figure_inten1(input_1):

        res = es.search(index="basket_data", doc_type="", body={"_source":{},'query': {'match_phrase':\
            {"data.load_identifier": input_1.split("(")[-1].split(')')[0]}}}, size=1000000)

        x1 = dataframes_additions(pd.json_normalize(res['hits']['hits']))

        fig = px.scatter(x1, y='row_col',x="_source.data.slide_thickness",color="_source.data.scanner_name",marginal_x="histogram")
        # fig.add_hline(y=0.2,line_color="red")
        # fig.add_scatter(x=x1[x1['_source.data.slide_thickness']<0.2]['row_col'],
        #                 y=x1[x1['_source.data.slide_thickness']<0.2]['_source.data.slide_thickness'],
        #             marker=dict(color="red",size=12),mode="markers")
        fig.update_layout(height=1200,showlegend=False)
        fig.update_xaxes(title="Slide Thickness (mm)",tickangle=45,range=[0,3])
        fig.update_yaxes(showticklabels=True)
        fig.update_yaxes(title='',showticklabels=False)
        fig.update_layout(yaxis1=dict(title="Slot Position",showticklabels=True))

        return fig

for i in range(4):
    slots_plot("graphslots{}".format((i+1)),"slots{}".format((i+1)))


# |----------------------------------------------------------------------------|
# RZ plots
# |----------------------------------------------------------------------------|

def rz_plot(output,input):
    @app.callback(Output(output, 'figure'),
                [Input(input, 'value')])
    def figure_inten1(input_1):
        res = es.search(index="slide_placement", doc_type="", body={"_source":{},'query': {'match_phrase':\
            {"data.load_identifier": input_1.split("(")[-1].split(')')[0]}}}, size=1000000)
        slide_placement = dataframes_additions(pd.json_normalize(res['hits']['hits']))

        res = es.search(index="inline_corrections", doc_type="", body={"_source":{},'query': {'match_phrase':\
            {"data.load_identifier": input_1.split("(")[-1].split(')')[0]}}}, size=1000000)

        inline_corrections = dataframes_additions(pd.json_normalize(res['hits']['hits']))

        both = pd.merge(slide_placement,inline_corrections,on=["_source.data.slide_id","_source.data.scanner_name",
                      "_source.data.load_identifier","_source.data.row_index","_source.data.col_index","row_col",
                      "_source.data.cluster_name"])
        
        both = both.drop_duplicates(subset="_source.data.slide_id",keep="last")
        both['computed_angle'] = both['_source.data.computed_angle']*(180/3.14)
        both['angle_difference'] = round(both['_source.data.actual_angle'] - both['computed_angle'],2)



        fig = make_subplots(
            rows=1, cols=4,
            subplot_titles=("<b>Row : 1 ","<b>Row : 2 ","<b>Row : 3 ","<b>Row : 4 "))
        for i in range(4):
            fig.add_trace(go.Scatter(x=round(both[both['_source.data.row_index']==i]['_source.data.actual_angle'],2),y=both[both['_source.data.row_index']==i]['row_col'],
                                    name="Actual Angle",showlegend=False,mode="markers",marker=dict(color="MediumPurple")),row=1,col=(i+1))
            fig.add_trace(go.Scatter(x=round(both[both['_source.data.row_index']==i]['computed_angle'],2),y=both[both['_source.data.row_index']==i]['row_col'],
                                    name="Computed Angle",showlegend=False,mode="markers",marker=dict(color="salmon")),row=1,col=(i+1))
            fig.add_annotation(y=-3,text="<b>Postive Adjustments : "+str(len(both[(both['_source.data.row_index']==i)&(both['angle_difference']>0)]))+\
                        "<br>Negative Adjustments : "+str(len(both[(both['_source.data.row_index']==i)&(both['angle_difference']<0)]))+\
                            "<br>μ Postive Adjustments : "+str(round(np.mean(both[(both['_source.data.row_index']==i)&(both['angle_difference']>0)]['angle_difference']),2))+\
                            "<br>μ Negative Adjustments : "+str(round(np.mean(both[(both['_source.data.row_index']==i)&(both['angle_difference']<0)]['angle_difference']),2)),
                            showarrow=False,row=1,col=(i+1))

        fig.add_trace(go.Scatter(x=round(both[both['_source.data.row_index']==0]['computed_angle'],2),y=both[both['_source.data.row_index']==0]['row_col'],
                                name="Incoming Angle",mode="markers",marker=dict(color="salmon")),row=1,col=1)
        fig.add_trace(go.Scatter(x=round(both[both['_source.data.row_index']==0]['_source.data.actual_angle'],2),y=both[both['_source.data.row_index']==0]['row_col'],
                                name="Corrected Angle",mode="markers",marker=dict(color="MediumPurple")),row=1,col=1)
        fig.update_layout(title="<b>Angle Adjustment Plot",height=800,width=1400,hovermode="y unified")
        fig.update_yaxes(autorange="reversed")
        fig.update_yaxes(title="Slot Position",row=1,col=1)
        fig.update_xaxes(title="Slide Angle")
        fig.update_xaxes(range=[-4.3,4.3])
        fig.add_vline(x=-4, line_width=3, line_dash="dash", line_color="red")
        fig.add_vline(x=4, line_width=3, line_dash="dash", line_color="red")
        fig.add_annotation(x=1.165,y=0.9,xref="paper",yref="paper",
                text="<br><b>Basket Level Details <br>"+"<b>+ve Adjustments : "+str(len(both[both['angle_difference']>0]))+\
                        "<br>-ve Adjustments : "+str(len(both[both['angle_difference']<0]))+\
                            "<br>μ +ve Adjustments : "+str(round(np.mean(both[both['angle_difference']>0]['angle_difference']),2))+\
                            "<br>μ -ve Adjustments :"+str(round(np.mean(both[both['angle_difference']<0]['angle_difference']),2)),
                showarrow=False,font=dict(family="Courier New, monospace",size=10,color="black"),align="center",
                bordercolor="#c7c7c7",
                borderwidth=2,
                borderpad=4,
                bgcolor="white",
                opacity=0.8
                )
        
        return fig

for i in range(4):
    rz_plot("graphrz{}".format((i+1)),"rz{}".format((i+1)))

# |----------------------------------------------------------------------------|
# Slide Placement Plots -- X Offset
# |----------------------------------------------------------------------------|


def x_offset(output,input,option):
    @app.callback(Output(output, 'figure'),
                [Input(input, 'value'),Input(option,"value")])
    def figure_inten1(input_1,option):

        res = es.search(index="slide_placement", doc_type="", body={"_source":{},'query': {'match_phrase':\
            {"data.load_identifier": input_1.split("(")[-1].split(')')[0]}}}, size=1000000)
        slide_placement = dataframes_additions(pd.json_normalize(res['hits']['hits']))

        if option == 'B':

            fig = make_subplots(
                rows=1, cols=4,
                subplot_titles=("<b>Row : 1 ","<b>Row : 2 ","<b>Row : 3 ","<b>Row : 4 "))
            for i in range(4):
                fig.add_trace(go.Scatter(x=slide_placement[slide_placement['_source.data.row_index']==i]['_source.data.offset_pos_x_um'],y=slide_placement[slide_placement['_source.data.row_index']==i]['row_col'],
                                        name="X-Offset",showlegend=False,mode="markers",marker=dict(color="MediumPurple")),row=1,col=(i+1))
                
                fig.add_annotation(y=-3,text="<b>Postive Adjustments : "+str(len(slide_placement[(slide_placement['_source.data.row_index']==i)&(slide_placement['_source.data.offset_pos_x_um']>0)]))+\
                            "<br>Negative Adjustments : "+str(len(slide_placement[(slide_placement['_source.data.row_index']==i)&(slide_placement['_source.data.offset_pos_x_um']<0)]))+\
                                "<br>μ Postive Adjustments : "+str(round(np.mean(slide_placement[(slide_placement['_source.data.row_index']==i)&(slide_placement['_source.data.offset_pos_x_um']>0)]['_source.data.offset_pos_x_um']),2))+\
                                "<br>μ Negative Adjustments : "+str(round(np.mean(slide_placement[(slide_placement['_source.data.row_index']==i)&(slide_placement['_source.data.offset_pos_x_um']<0)]['_source.data.offset_pos_x_um']),2)),
                                showarrow=False,row=1,col=(i+1))

            fig.add_trace(go.Scatter(x=slide_placement[slide_placement['_source.data.row_index']==0]['_source.data.offset_pos_x_um'],y=slide_placement[slide_placement['_source.data.row_index']==0]['row_col'],
                                    name="X-Offset                      ",mode="markers",marker=dict(color="MediumPurple")),row=1,col=1)
                
            fig.update_layout(title="<b>X-Offset Plot",height=800,width=1400)
            fig.update_yaxes(autorange="reversed")
            fig.update_yaxes(title="Slot Position",row=1,col=1)
            fig.update_xaxes(title="X-Offset(um)",range=[-3550,3550])
            fig.add_vline(x=-3500, line_width=3, line_dash="dash", line_color="red")
            fig.add_vline(x=3500, line_width=3, line_dash="dash", line_color="red")
            fig.add_annotation(x=1.158,y=0.9,xref="paper",yref="paper",
                    text="<br><b>Basket Level Details <br>"+"<b>+ve Adjustments : "+str(len(slide_placement[slide_placement['_source.data.offset_pos_x_um']>0]))+\
                            "<br>-ve Adjustments : "+str(len(slide_placement[slide_placement['_source.data.offset_pos_x_um']<0]))+\
                                "<br>μ +ve Adjustments : "+str(round(np.mean(slide_placement[slide_placement['_source.data.offset_pos_x_um']>0]['_source.data.offset_pos_x_um']),2))+\
                                "<br>μ -ve Adjustments :"+str(round(np.mean(slide_placement[slide_placement['_source.data.offset_pos_x_um']<0]['_source.data.offset_pos_x_um']),2)),
                    showarrow=False,font=dict(family="Courier New, monospace",size=10,color="black"),align="center",
                    bordercolor="#c7c7c7",
                    borderwidth=2,
                    borderpad=4,
                    bgcolor="white",
                    opacity=0.8)
            return fig
        else:
            fig = px.scatter(x=slide_placement["_source.data.offset_pos_x_um"],y=slide_placement['row_col'])
            fig.update_layout(title="<b>X-Offset Plot",height=800,width=1400)
            fig.update_yaxes(autorange="reversed")
            fig.update_yaxes(title="Slot Position")
            fig.update_xaxes(title="X-Offset(um)",range=[-3550,3550])
            fig.add_vline(x=-3500, line_width=3, line_dash="dash", line_color="red")
            fig.add_vline(x=3500, line_width=3, line_dash="dash", line_color="red")
            fig.add_annotation(x=3500,y=1,xref="x",yref="y",
                    text="<br><b>Basket Level Details <br>"+"<b>+ve Adjustments : "+str(len(slide_placement[slide_placement['_source.data.offset_pos_x_um']>0]))+\
                            "<br>-ve Adjustments : "+str(len(slide_placement[slide_placement['_source.data.offset_pos_x_um']<0]))+\
                                "<br>μ +ve Adjustments : "+str(round(np.mean(slide_placement[slide_placement['_source.data.offset_pos_x_um']>0]['_source.data.offset_pos_x_um']),2))+\
                                "<br>μ -ve Adjustments :"+str(round(np.mean(slide_placement[slide_placement['_source.data.offset_pos_x_um']<0]['_source.data.offset_pos_x_um']),2)),
                    showarrow=False,font=dict(family="Courier New, monospace",size=10,color="black"),align="center",
                    bordercolor="#c7c7c7",
                    borderwidth=2,
                    borderpad=4,
                    bgcolor="white",
                    opacity=0.8)
            return fig



def y_offset(output,input,option):
    @app.callback(Output(output, 'figure'),
                [Input(input, 'value'),Input(option,"value")])
    def figure_inten1(input_1,option):

        res = es.search(index="slide_placement", doc_type="", body={"_source":{},'query': {'match_phrase':\
            {"data.load_identifier": input_1.split("(")[-1].split(')')[0]}}}, size=1000000)
        slide_placement = dataframes_additions(pd.json_normalize(res['hits']['hits']))

        if option == 'B':
            fig = make_subplots(
                        rows=4, cols=1,
                        subplot_titles=("<b>Row : 1 ","<b>Row : 2 ","<b>Row : 3 ","<b>Row : 4 "))
            for i in range(4):
                fig.add_trace(go.Scatter(y=slide_placement[slide_placement['_source.data.row_index']==i]['_source.data.offset_pos_y_um'],x=slide_placement[slide_placement['_source.data.row_index']==i]['row_col'],
                                        name="X-Offset",showlegend=False,mode="markers",marker=dict(color="MediumPurple")),row=(i+1),col=1)
                
                fig.add_annotation(x=-4,xref="x",yref="y",text="<b>Postive Adjustments : "+str(len(slide_placement[(slide_placement['_source.data.row_index']==i)&(slide_placement['_source.data.offset_pos_y_um']>0)]))+\
                                "<br>μ Postive Adjustments : "+str(round(np.mean(slide_placement[(slide_placement['_source.data.row_index']==i)&(slide_placement['_source.data.offset_pos_y_um']>0)]['_source.data.offset_pos_y_um']),2)),
                                showarrow=False,row=(i+1),col=1)

            fig.add_trace(go.Scatter(y=slide_placement[slide_placement['_source.data.row_index']==0]['_source.data.offset_pos_y_um'],x=slide_placement[slide_placement['_source.data.row_index']==0]['row_col'],
                                    name="Y-Offset                ",mode="markers",marker=dict(color="MediumPurple")),row=1,col=1)
                
            fig.update_layout(title="<b>Y-Offset Plot",height=800,width=1400)
            # fig.update_xaxes(autorange="reversed")
            fig.update_xaxes(tickangle=55)
            fig.update_xaxes(title="Slot Position",row=4,col=1)
            fig.update_yaxes(title="Y-Offset(um)",range=[0,5050])
            fig.add_hline(y=0, line_width=3, line_dash="dash", line_color="red")
            fig.add_hline(y=5000, line_width=3, line_dash="dash", line_color="red")
            fig.add_annotation(x=1.158,y=0.9,xref="paper",yref="paper",
                    text="<br><b>Basket Level Details <br>"+"<b>+ve Adjustments : "+str(len(slide_placement[slide_placement['_source.data.offset_pos_y_um']>0]))+\
                                "<br>μ +ve Adjustments : "+str(round(np.mean(slide_placement[slide_placement['_source.data.offset_pos_y_um']>0]['_source.data.offset_pos_y_um']),2)),
                    showarrow=False,font=dict(family="Courier New, monospace",size=10,color="black"),align="center",
                    bordercolor="#c7c7c7",
                    borderwidth=2,
                    borderpad=4,
                    bgcolor="white",
                    opacity=0.8)
            return fig
        else:
            fig = px.scatter(y=slide_placement["_source.data.offset_pos_y_um"],x=slide_placement['row_col'])
            fig.update_layout(title="<b>Y-Offset Plot",height=800,width=1400)
            # fig.update_xaxes(autorange="reversed")
            fig.update_xaxes(tickangle=55)
            fig.update_xaxes(title="Slot Position",row=4,col=1)
            fig.update_yaxes(title="Y-Offset(um)",range=[0,5050])
            fig.add_hline(y=0, line_width=3, line_dash="dash", line_color="red")
            fig.add_hline(y=5000, line_width=3, line_dash="dash", line_color="red")
            fig.add_annotation(y=5000,xref="x",yref="y",
                    text="<br><b>Basket Level Details <br>"+"<b>+ve Adjustments : "+str(len(slide_placement[slide_placement['_source.data.offset_pos_y_um']>0]))+\
                                "<br>μ +ve Adjustments : "+str(round(np.mean(slide_placement[slide_placement['_source.data.offset_pos_y_um']>0]['_source.data.offset_pos_y_um']),2)),
                    showarrow=False,font=dict(family="Courier New, monospace",size=10,color="black"),align="center",
                    bordercolor="#c7c7c7",
                    borderwidth=2,
                    borderpad=4,
                    bgcolor="white",
                    opacity=0.8)
            return fig


for i in range(4):
    x_offset("graphxoffset{}".format((i+1)),"place{}".format((i+1)),"button_place{}".format((i+1)))
    y_offset("graphyoffset{}".format((i+1)),"place{}".format((i+1)),"button_place{}".format((i+1)))


# |----------------------------------------------------------------------------|
# Dynamic Slide Locking 
# |----------------------------------------------------------------------------|

def current_plot(output,input,o_input):
    @app.callback(Output(output, 'figure'),
                [Input(input, 'value'),Input(o_input,"value")])
    def figure_locking(input_1,o_input):

        res = es.search(index="slide_locking", doc_type="", body={"_source":{},'query': {'match_phrase':\
            {"data.load_identifier": input_1.split("(")[-1].split(')')[0]}}}, size=1000000)
        slide_locking = dataframes_additions(pd.json_normalize(res['hits']['hits']))

        res = es.search(index="slide_placement", doc_type="", body={"_source":{},'query': {'match_phrase':\
            {"data.load_identifier": input_1.split("(")[-1].split(')')[0]}}}, size=1000000)
        slide_placement = dataframes_additions(pd.json_normalize(res['hits']['hits']))

        x1 = pd.merge(slide_locking,slide_placement,on=["_source.data.slide_id","_source.data.scanner_name",
                      "_source.data.load_identifier","_source.data.row_index","_source.data.col_index",
                      "_source.data.cluster_name","row_col"])
        
        x1['slide_height'] = x1['_source.data.slide_height_um']/1000

        if o_input == 'A':
            if len(x1[x1['_source.data.second_status']==True]) > 0:
                fig = make_subplots(
                    rows=1, cols=2,subplot_titles=("First Locking Attempt","Second Locking Attempt"))
                
                fig.add_trace(go.Scatter(x=x1['row_col'],y=x1['_source.data.first_current_diff'],name="First Current Difference",mode="lines+markers",
                            marker=dict(color="green"),showlegend=False),
                                row=1, col=1)
                fig.add_trace(go.Scatter(x=x1[x1['_source.data.first_current_diff']<=50]['row_col'],
                                        y=x1[x1['_source.data.first_current_diff']<=50]['_source.data.first_current_diff'],
                                        name="Failed to Lock",mode="markers",
                            marker=dict(color="red",size=12)),
                                row=1, col=1)
                
                fig.add_trace(go.Scatter(x=x1['row_col'],y=x1['_source.data.second_current_diff'],name="Second Current Difference",mode="lines+markers",
                            marker=dict(color="red"),showlegend=False),
                            row=1, col=2)
                fig.add_trace(go.Scatter(x=x1[x1['_source.data.second_current_diff']>=50]['row_col'],name="Locked",
                                y=x1[x1['_source.data.second_current_diff']>=50]['_source.data.second_current_diff']
                            ,mode="markers",marker=dict(size=12,color="green")),
                            row=1, col=2)
                
                fig.add_hline(y=50, line_dash="dot", line_color="#000000", line_width=2)
                fig.update_layout(width=1800,hovermode="x unified")
                fig.update_yaxes(title="Current Difference(mA)")
                fig.update_xaxes(title="Slot Position")
            else:
                fig = go.Figure()
                fig.add_scatter(x=x1['row_col'],y=x1['_source.data.first_current_diff'],name="Difference",mode="lines+markers",
                            marker=dict(color="green"))
                fig.add_scatter(x=x1[x1['_source.data.first_current_diff']<=50]['row_col'],name="Failed to Lock",
                                y=x1[x1['_source.data.first_current_diff']<=50]['_source.data.first_current_diff']
                            ,mode="markers",marker=dict(size=12,color="red"))
                fig.add_hline(y=50, line_dash="dot", line_color="#000000", line_width=2)
                fig.update_layout(width=1800,hovermode="x unified")
                fig.update_yaxes(title="Current Difference(mA)")
                fig.update_xaxes(title="Slot Position")

            return fig
        else:

            fig = make_subplots(specs=[[{"secondary_y": True}]])

            fig.add_trace(
                go.Scatter(x=x1['row_col'],y=x1['slide_height'], mode="lines+markers",name="Slide Height"),
                secondary_y=True,
            )

            fig.add_trace(
                go.Bar(x=x1['row_col'], y=x1['_source.data.first_current_diff'], marker=dict(color="salmon"),name="First Current Difference"),
                secondary_y=False,
            )
            fig.add_trace(
                go.Bar(x=x1['row_col'], y=x1['_source.data.second_current_diff'], marker=dict(color="red"),name="Second Current Difference"),
                secondary_y=False,
            )

            fig.update_layout(barmode="stack",hovermode='x unified',
                title_text="Slide Height Vs Current Difference"
            )

            fig.update_xaxes(tickangle=55,title_text="Row_Col")

            fig.update_yaxes(range=[0,max(x1['_source.data.first_current_diff'])+20],title_text="<b>Current(mA)</b>", secondary_y=False)
            fig.update_yaxes(range=[70,77],title_text="<b>Height(mm)</b>", secondary_y=True)
            return fig
                
for i in range(4):
    current_plot("graphcurrent{}".format((i+1)),"current{}".format((i+1)),"s{}_rbutton".format((i+1)))


def post_plots(output,input):
    @app.callback(Output(output, 'figure'),
                [Input(input, 'value')])
    def figure_post(input_1):
        
        res = es.search(index="post", doc_type="", body={"_source":{
            "includes":["data.scanner_name","data.time_stamp","data.cluster_name","data.centering_info"]},
            "query": {"bool": {"must": [{"match": { "data.time_stamp": input_1 }}]}}}, size=1000000,)
        post1 = pd.json_normalize(res['hits']['hits'])
        post = pd.json_normalize(post1['_source.data.centering_info'][0])

        fig2 = make_subplots(rows=1, cols=2,subplot_titles=("<b>Centring","<b>Illuminaion"))
        fig2.add_trace(go.Scatter(x=post['centring_coordinate_x'],y=post['centring_coordinate_y'],
                                mode='markers',
                                name='Dispersion',
                                ),row=1,col=1)
        fig2.update_yaxes(title="Stage Y",range=[1216,0],row=1,col=1,ticks="outside", tickwidth=2, tickcolor='crimson')
        fig2.update_xaxes(title="Stage X",range=[0,1936],row=1,col=1,ticks="outside", tickwidth=2, tickcolor='crimson')
        fig2.add_shape(type="rect",
            xref="x", yref="y",
            x0=768, y0=408, x1=1168, y1=808,
            line_color="red",row=1,col=1
        )
        fig2.add_vline(x=968,line=dict(color="red"),opacity=0.3,row=1,col=1)
        fig2.add_hline(y=608,line=dict(color="red"),opacity=0.3,row=1,col=1)
        fig2.add_annotation(text="<b>Number of Steps : <b>"+str(len(post))+"<br><b>Average X-Shift : "+\
                        str(round(np.mean(post['centring_x_difference']),2))+"\t Average Y-Shift : <b>"+\
            str(round(np.mean(post['centring_y_difference']),2))+"</b><br>Max X-Shift : <b>"+str(round(max(post['centring_x_difference']),2))+\
                    "</b>\t Max Y-Shift : <b>"+str(round(max(post['centring_y_difference']),2))+\
                    "</b><br>Min X-Shift : <b>"+str(round(min(post['centring_x_difference']),2))+\
                    "</b>\t Min Y-Shift : <b>"+str(round(min(post['centring_y_difference']),2))
                    ,showarrow=False,font=dict(family="Courier New, monospace",size=12,color="black"),row=1,col=1,
                xref="paper", yref="paper",x=1800, y=5,bordercolor="#c7c7c7",borderwidth=2,borderpad=4,bgcolor="#ffffff",opacity=0.8)
        ##adding illumination
        fig2.add_trace(go.Scatter(y=post['mean_red_intensity'],mode='lines',name='Mean Red',
                                line=dict(color='red')),row=1,col=2)
        fig2.add_trace(go.Scatter(y=post['mean_blue_intensity'],mode='lines',name='Mean Blue',
                                line=dict(color='blue')),row=1,col=2)
        fig2.add_trace(go.Scatter(y=post['mean_green_intensity'],mode='lines', name='Mean Green',
                                line=dict(color='green')),row=1,col=2)
        fig2.update_yaxes(title="Intensity",range=[150, 260],row=1,col=2)
        fig2.update_xaxes(title="Z Steps",row=1,col=2)

        fig2.update_layout(showlegend=False,font=dict(family="Courier New, monospace",size=16,color="Black"),width=1800,height=800)
        fig2.add_annotation(text="<b>Calibration Data for <b>: "+str(input_1),xref="paper", yref="paper",showarrow=False,x=0, y=1.08,font=dict(family="Courier New, monospace",
                size=24,color="RebeccaPurple"))
        fig2.add_annotation(text="<b>Number of Steps : <b>"+str(len(post))+"<br><b>Min μ Red : "+\
                    str(round(min(post['mean_red_intensity']),2))+"\t | Max μ Red : <b>"+\
        str(round(max(post['mean_red_intensity']),2))+"</b><br> Min μ Green : <b>"+str(round(min(post['mean_green_intensity']),2))+\
                "</b>\t | Min μ Green : <b>"+str(round(min(post['mean_green_intensity']),2))+\
                "</b><br> Min μ Blue : <b>"+str(round(min(post['mean_blue_intensity']),2))+\
                "</b>\t | Min μ Blue : <b>"+str(round(min(post['mean_blue_intensity']),2))
                ,showarrow=False,font=dict(family="Courier New, monospace",size=12,color="black"),row=1,col=2,
                    x=60, y=254,bordercolor="#c7c7c7",borderwidth=2,borderpad=4,bgcolor="#ffffff",opacity=0.8)
        
        return fig2

for i in range(4):
    post_plots("post{}".format((i+1)),"post_id{}".format((i+1)))


if __name__ == '__main__':
    app.run_server(port=8030,debug=True,threaded=True,dev_tools_hot_reload_interval=50000)
