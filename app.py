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

Station_1 = "H01JBA21P"
Station_2 = "H01JBA15R"
Station_3 = "H01JBA11R"
Station_4 = "H01JBA14R"
# |----------------------------------------------------------------------------|
# SLot Empty 
# |----------------------------------------------------------------------------|
res = es.search(index="basket_data", doc_type="", body={"_source":{}}, size=1000000,)
print("basket_data ACQUIRED SUCCESSFULLY")
basket_data = pd.json_normalize(res['hits']['hits'])
basket_data['date'] = pd.to_datetime(basket_data['_source.data.time_stamp']).dt.date
basket_data['date'] = pd.to_datetime(basket_data['date'])
basket_data = basket_data.dropna(subset=['_source.data.row_index','_source.data.col_index'])
basket_data['_source.data.row_index'] = basket_data['_source.data.row_index'].astype(int)
basket_data['_source.data.col_index'] = basket_data['_source.data.col_index'].astype(int)
basket_data['dropdown'] = basket_data['date'].astype(str)+"("+basket_data['_source.data.load_identifier']+")"
basket_data['row_col'] = (basket_data['_source.data.row_index']+1).astype(str)+"_"+(basket_data['_source.data.col_index']+1).astype(str)
basket_data = basket_data.sort_values(["_source.data.row_index","_source.data.col_index"], ascending = (True, True))


def slots_plot(output,input):
    @app.callback(Output(output, 'figure'),
                [Input(input, 'value')])
    def figure_inten1(input_1):
        x1 = basket_data[basket_data['dropdown']==input_1]

        fig = px.scatter(x=x1['row_col'],y=x1['_source.data.slide_thickness'])
        # fig.add_hline(y=0.2,line_color="red")
        fig.add_scatter(x=x1[x1['_source.data.slide_thickness']<0.2]['row_col'],
                        y=x1[x1['_source.data.slide_thickness']<0.2]['_source.data.slide_thickness'],
                    marker=dict(color="red",size=12),mode="markers")
        fig.update_layout(hovermode="x unified",width=1200,showlegend=False)
        fig.update_xaxes(title="Slot Position",tickangle=45)
        fig.update_yaxes(dtick=1,range=[-0.8,3],title="Slide Thickness (mm)")
        # fig.update_xaxes(categoryorder='category ascending')
        
        return fig
# @app.callback(
#     Output("download-dataframe-csv", "data"),
#     Input("btn_csv", "n_clicks"),
#     prevent_initial_call=True,
# )
# def func(n_clicks):
#     return dcc.send_data_frame(df.to_csv, "mydf.csv")
for i in range(4):
    slots_plot("graphslots{}".format((i+1)),"slots{}".format((i+1)))


# |----------------------------------------------------------------------------|
# Multiple Indexes from Elastic Getting Merged as one Dataframe
# |----------------------------------------------------------------------------|

# #for Slide placement to get thickness info
res = es.search(index="slide_placement", doc_type="", body={"_source":{}}, size=1000000,)
print("slide_placement ACQUIRED SUCCESSFULLY")
slide_placement = pd.json_normalize(res['hits']['hits'])

#for Slide placement to get thickness info
res = es.search(index="inline_corrections", doc_type="", body={"_source":{}}, size=1000000,)
print("inline_corrections ACQUIRED SUCCESSFULLY")
inline_corrections = pd.json_normalize(res['hits']['hits'])

res = es.search(index="slide_locking", doc_type="", body={"_source":{}}, size=1000000,)
print("slide_locking ACQUIRED SUCCESSFULLY")
slide_locking = pd.json_normalize(res['hits']['hits'])

both = pd.merge(slide_placement,inline_corrections,on=["_source.data.slide_id","_source.data.scanner_name",
                      "_source.data.load_identifier","_source.data.row_index","_source.data.col_index",
                      "_source.data.cluster_name"])
both = pd.merge(slide_locking,both,on=["_source.data.slide_id","_source.data.scanner_name",
                      "_source.data.load_identifier","_source.data.row_index","_source.data.col_index",
                      "_source.data.cluster_name"])
both = both.drop_duplicates(subset="_source.data.slide_id",keep="last")

both['row_col'] = (both['_source.data.row_index']+1).astype(str)+"_"+(both['_source.data.col_index']+1).astype(str)
both = both.sort_values(["_source.data.row_index","_source.data.col_index"], ascending = (True, True))
both['date'] = pd.to_datetime(both['_source.data.time_stamp_x']).dt.date
both['date'] = pd.to_datetime(both['date'])
both['dropdown'] = both['date'].astype(str)+"("+both['_source.data.load_identifier']+")"
both['computed_angle'] = both['_source.data.computed_angle']*(180/3.14)
both['slide_height'] = both['_source.data.slide_height_um']/1000

# |----------------------------------------------------------------------------|
# RZ plots
# |----------------------------------------------------------------------------|

def rz_plot(output,input):
    @app.callback(Output(output, 'figure'),
                [Input(input, 'value')])
    def figure_inten1(input_1):
        x1 = both[both['dropdown']==input_1]

        fig = go.Figure()
        fig.add_scatter(x=x1['_source.data.actual_angle'],y=x1['row_col'],mode="markers",name="Angle Before Placement",marker=dict(size=12))
        fig.add_scatter(x=x1['computed_angle'],y=x1['row_col'],mode="markers",name="Angle Slide Came With",marker=dict(size=12))
        for i in range(x1.shape[0]):
            fig.add_shape(
                type='line',
                x0=x1['computed_angle'].iloc[i], y0=x1['row_col'].iloc[i], 
                x1=x1['_source.data.actual_angle'].iloc[i], y1=x1['row_col'].iloc[i],
                line_color="#cccccc"
            )
        fig.update_layout(title="Computation of RZ",height=1500,hovermode="y unified")
        fig.update_yaxes(title="Row_Col Index")
        fig.update_xaxes(title="Slide Angle(Degree)")
        
        return fig
for i in range(4):
    rz_plot("graphrz{}".format((i+1)),"rz{}".format((i+1)))

# |----------------------------------------------------------------------------|
# Slide Placement Plots
# |----------------------------------------------------------------------------|

def placement_plot(output,input):
    @app.callback(Output(output, 'figure'),
                [Input(input, 'value')])
    def figure_inten1(input_1):
        x1 = both[both['dropdown']==input_1]

        fig = make_subplots(
            rows=2, cols=2,
            specs=[[{}, {}],
                [{"colspan": 2}, None]],row_width=[0.2, 0.4],
            subplot_titles=("X-Offset","Angle Permissible", "Y-Offset"))

        fig.add_trace(go.Scatter(y=x1["row_col"], x=x1["_source.data.offset_pos_x_um"],name="X-Offset(um)",mode="markers"),
                        row=1, col=1)


        fig.add_trace(go.Bar(x=x1["row_col"], y=x1["_source.data.permissible_angle"],marker_color='lightgreen'),
                        row=1, col=2)
        fig.add_trace(go.Bar(x=x1["row_col"], y=-1*(x1["_source.data.permissible_angle"]),marker_color='lightgreen'),
                        row=1, col=2)
        fig.add_trace(go.Bar(x=x1["row_col"], y=x1["_source.data.actual_angle"],name="Actual Anlge",marker_color='red'),
                        row=1, col=2)

        fig.add_trace(go.Scatter(x=x1["row_col"], y=x1["_source.data.offset_pos_y_um"],name="Y-Offset(um)",mode="markers"),
                        row=2, col=1)
        #system Specified range
        fig.add_vline(x=3500, line_dash="dot", row=1, col=1, line_color="red", line_width=2)
        fig.add_vline(x=-3500, line_dash="dot", row=1, col=1, line_color="red", line_width=2)
        fig.add_hline(y=0, line_dash="dot", row=2, col=1, line_color="red", line_width=2)
        fig.add_hline(y=5000, line_dash="dot", row=2, col=1, line_color="red", line_width=2)

        fig.update_layout(hovermode='x unified',barmode="overlay",height=1200,width=1500,showlegend=False)
        # fig.update_layout(hovermode="x unified",row=0,col=0)
        
        return fig
for i in range(4):
    placement_plot("graphplace{}".format((i+1)),"place{}".format((i+1)))

# |----------------------------------------------------------------------------|
# Dynamic Slide Locking 
# |----------------------------------------------------------------------------|

def current_plot(output,input,o_input):
    @app.callback(Output(output, 'figure'),
                [Input(input, 'value'),Input(o_input,"value")])
    def figure_locking(input_1,o_input):
        x1 = both[both['dropdown']==input_1]
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
                go.Bar(x=x1['row_col'], y=x1['_source.data.first_current_diff'], marker=dict(color="green"),name="First Current Difference"),
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

if __name__ == '__main__':
    app.run_server(port=8030,debug=True,threaded=True,dev_tools_hot_reload_interval=50000)
