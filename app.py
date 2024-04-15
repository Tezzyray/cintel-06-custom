import sqlite3
import dash
from dash import html, dcc, Input, Output
import plotly.express as px

# Create connection to SQLite database
conn = sqlite3.connect('tips.db')
cursor = conn.cursor()

# Create table if not exists
cursor.execute('''CREATE TABLE IF NOT EXISTS tips (
                    total_bill REAL,
                    tip REAL,
                    sex TEXT,
                    smoker TEXT,
                    day TEXT,
                    time TEXT,
                    size INTEGER
                )''')

# Load data into SQLite database
tips = px.data.tips()
tips.to_sql('tips', conn, if_exists='replace', index=False)

# Initialize Dash app
app = dash.Dash(__name__)

# Define layout
app.layout = html.Div([
    html.H1("Montoya's Restaurant Tips"),
    html.Div(id='main-content'),
    html.Div([
        dcc.RangeSlider(
            id='total-bill-slider',
            min=tips['total_bill'].min(),
            max=tips['total_bill'].max(),
            value=[tips['total_bill'].min(), tips['total_bill'].max()],
            marks={str(i): str(i) for i in range(int(tips['total_bill'].min()), int(tips['total_bill'].max())+1, 5)},
            step=0.01
        ),
        dcc.Checklist(
            id='time-selector',
            options=[{'label': i, 'value': i} for i in ['Lunch', 'Dinner']],
            value=['Lunch', 'Dinner']
        ),
        html.Button('Reset Filter', id='reset-button')
    ], style={'margin': '20px 0'}),
    html.Div(id='tip-stats'),
    html.Div(id='tip-scatterplot'),
    html.Div(id='tip-percentage-ridgeplot')
])

# Define callback to update data
@app.callback(
    [Output('main-content', 'children'),
     Output('tip-stats', 'children'),
     Output('tip-scatterplot', 'children'),
     Output('tip-percentage-ridgeplot', 'children')],
    [Input('total-bill-slider', 'value'),
     Input('time-selector', 'value'),
     Input('reset-button', 'n_clicks')]
)
def update_data(total_bill_range, selected_time, n_clicks):
    # Filter data
    cursor.execute('''
        SELECT * FROM tips 
        WHERE total_bill BETWEEN ? AND ?
        AND time IN ({seq})
    '''.format(seq=','.join(['?']*len(selected_time))),
                   total_bill_range[0], total_bill_range[1], *selected_time)
    filtered_tips = cursor.fetchall()
    
    # Calculate statistics
    total_tippers = len(filtered_tips)
    if total_tippers > 0:
        average_tip = sum(row[1] for row in filtered_tips) / total_tippers
        average_bill = sum(row[0] for row in filtered_tips) / total_tippers
    else:
        average_tip = 0
        average_bill = 0
    
    # Create scatterplot
    scatterplot = dcc.Graph(
        figure=px.scatter(filtered_tips, x='total_bill', y='tip', trendline='lowess', color='time')
    )
    
    # Create ridgeplot
    ridgeplot = dcc.Graph(
        figure=px.violin(filtered_tips, y='tip/total_bill', x='day', color='day')
    )
    
    return (html.Div([
                html.H2(f'Total tippers: {total_tippers}'),
                html.H2(f'Average tip: ${average_tip:.2f}'),
                html.H2(f'Average bill: ${average_bill:.2f}')
            ]), scatterplot, ridgeplot)

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)

