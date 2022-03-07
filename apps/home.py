import dash_html_components as html
import dash
import dash_bootstrap_components as dbc

# needed only if running this as a single page app
external_stylesheets = [dbc.themes.LUX]

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

# change to app.layout if running as single page app instead
app.layout = html.Div([
    dbc.Container([
        dbc.Row([
            dbc.Col(html.H1("CLUSTER PERFORMANCE MANAGEMENT DASHBOARD", className="text-center")
                    , className="mb-5 mt-5")
        ]),        
        dbc.Col(html.Img(src=app.get_asset_url('spec.png'),style={'verticalAlign': 'middle','margin-left': '50px'})
                , className="mb-5 mt-5"),


        dbc.Col(dbc.Card(children=[html.H3(children='Clusters',
                                            className="text-center"),
                                                
                                    dbc.Row([dbc.Col(dbc.Button("CS003", href="/cs003",
                                                                color="primary"),
                                                    className="mt-3")], justify="center")
                                    ],
                            body=True, color="dark", outline=True,style={'verticalAlign': 'middle','margin-left': '50px'})
                , width=4, className="mb-4")

    ])

])

# needed only if running this as a single page app
# if __name__ == '__main__':
#     app.run_server(host='127.0.0.1', debug=True)
