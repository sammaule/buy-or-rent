import dash
from dash import dcc, html, dash_table
import dash_bootstrap_components as dbc
import pandas as pd
from dash.dependencies import Input, Output
import plotly.graph_objs as go
import numpy as np
import numpy_financial as npf

# Choose a Bootstrap theme
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Define marks for sliders for better readability
sale_price_marks = {i: f"£{i//1000}k" for i in range(300_000, 610_000, 100_000)}
buying_price_marks = {i: f"£{i//1000}k" for i in range(0, 1_010_000, 200_000)}
rent_pcm_marks = {i: f"£{i}" for i in range(0, 4100, 1000)}
house_price_growth_markers = {i: f"{i}%" for i in range(0, 11)}
saving_return_markers = {i: f"{i}%" for i in range(0, 11)}

app.layout = dbc.Container(
    [
        dcc.Store(id="net_proceeds"),
        html.H1("Buy or Rent", className="mb-4"),
        dbc.Row(
            [
                dbc.Col(
                    dbc.Card(
                        [
                            dbc.CardHeader(html.H3("Sale Information")),
                            dbc.CardBody(
                                [
                                    dbc.Label("Expected Sale Price (£)"),
                                    dcc.Slider(
                                        id="sale_price_slider",
                                        min=300_000,
                                        max=600_000,
                                        step=10_000,
                                        value=500_000,
                                        marks=sale_price_marks,
                                    ),
                                    dbc.CardGroup(
                                        [
                                            dbc.Label("Estate Agent Fee (£)"),
                                            dbc.Input(
                                                id="estate_agent_fee",
                                                type="number",
                                                value=5000,
                                            ),
                                        ]
                                    ),
                                    dbc.CardGroup(
                                        [
                                            dbc.Label("Movers Fees (£)"),
                                            dbc.Input(
                                                id="movers_fees",
                                                type="number",
                                                value=2000,
                                            ),
                                        ]
                                    ),
                                    dbc.CardGroup(
                                        [
                                            dbc.Label("Solicitors Fees (£)"),
                                            dbc.Input(
                                                id="solicitors_fees",
                                                type="number",
                                                value=2000,
                                            ),
                                        ]
                                    ),
                                    dbc.CardGroup(
                                        [
                                            dbc.Label("Storage (£)"),
                                            dbc.Input(
                                                id="storage", type="number", value=0
                                            ),
                                        ]
                                    ),
                                ]
                            ),
                        ]
                    ),
                    width=12,
                    lg=6,
                ),
                dbc.Col(
                    dbc.Card(
                        [
                            dbc.CardHeader(html.H3("Buying vs Renting")),
                            dbc.CardBody(
                                [
                                    dbc.Label("Buying Price (£)"),
                                    dcc.Slider(
                                        id="buying_price_slider",
                                        min=0,
                                        max=1000000,
                                        step=10000,
                                        value=500000,
                                        marks=buying_price_marks,
                                    ),
                                    dbc.Label("Maintenance per Year (£)"),
                                    dbc.Input(
                                        id="maintenance_per_year",
                                        type="number",
                                        value=5000,
                                    ),
                                    dbc.Label("Building Insurance per Year (£)"),
                                    dbc.Input(
                                        id="building_insurance_per_year",
                                        type="number",
                                        value=500,
                                    ),
                                    dbc.Label("Rent per Month (£)"),
                                    dcc.Slider(
                                        id="rent_pcm_slider",
                                        min=0,
                                        max=4000,
                                        step=100,
                                        value=1500,
                                        marks=rent_pcm_marks,
                                    ),
                                    dbc.Label("House Price Growth p.a. (%)"),
                                    dcc.Slider(
                                        id="house_price_growth",
                                        min=0,
                                        max=10,
                                        step=0.1,
                                        value=2,
                                        marks=house_price_growth_markers,
                                    ),
                                    dbc.Label("Savings Returns p.a. (%)"),
                                    dcc.Slider(
                                        id="savings_returns",
                                        min=0,
                                        max=10,
                                        step=0.1,
                                        value=2,
                                        marks=saving_return_markers,
                                    ),
                                ]
                            ),
                        ]
                    ),
                    width=12,
                    lg=6,
                ),
            ],
            className="mb-4",
        ),
        dbc.Row(
            [
                dbc.Col(html.Div(id="sale_output"), width=12),
                dbc.Col(html.Div(id="stamp_duty_due"), width=12),
                dbc.Col(dcc.Graph(id="wealth_comparison_chart"), width=12),
            ]
        ),
        dbc.Row(
            dash_table.DataTable(
                id="financial_comparison_table",
                columns=[
                    {"name": "Year", "id": "Year"},
                    {"name": "Buying Income", "id": "Buying Income"},
                    {
                        "name": "Buying Total Expenditure",
                        "id": "Buying Total Expenditure",
                    },
                    {"name": "Buying Total Wealth", "id": "Buying Total Wealth"},
                    {"name": "Renting Income", "id": "Renting Income"},
                    {"name": "Renting Expenditure", "id": "Renting Expenditure"},
                    {"name": "Renting Total Wealth", "id": "Renting Total Wealth"},
                ],
                style_table={"overflowX": "auto"},
                fill_width=False,
            )
        ),
    ],
    fluid=True,
)


# Callback for dynamically adjusting the estate agent fee
@app.callback(
    Output("estate_agent_fee", "value"), [Input("sale_price_slider", "value")]
)
def update_estate_agent_fee(sale_price):
    estate_agent_fee = sale_price * 0.01
    return estate_agent_fee


# Callback for dynamically adjusting the maintenance fee
@app.callback(
    Output("maintenance_per_year", "value"), [Input("buying_price_slider", "value")]
)
def update_maintenance_fee(buying_price):
    maintenance_fee = buying_price * 0.01
    return maintenance_fee


# Callback for dynamically updating the stamp duty due
@app.callback(
    Output("stamp_duty_due", "children"), [Input("buying_price_slider", "value")]
)
def update_stamp_duty_due(buying_price):
    stamp_duty = calculate_stamp_duty(buying_price)
    return f"Stamp Duty Due: £{stamp_duty:,.2f}"


# Callback for updating the sale output
@app.callback(
    [Output("sale_output", "children"),
     Output("net_proceeds", "data")],
    [
        Input("sale_price_slider", "value"),
        Input("estate_agent_fee", "value"),
        Input("movers_fees", "value"),
        Input("solicitors_fees", "value"),
        Input("storage", "value"),
    ],
)
def update_sale_output(
    sale_price, estate_agent_fee, movers_fees, solicitors_fees, storage
):
    total_selling_costs = estate_agent_fee + movers_fees + solicitors_fees + storage
    net_proceeds = sale_price - total_selling_costs
    return f"Net proceeds from sale: £{net_proceeds:,.2f}", net_proceeds


# Callback for updating the wealth comparison chart and DataTable with annual figures
@app.callback(
    [Output('wealth_comparison_chart', 'figure'),
     Output('financial_comparison_table', 'data')],
    [Input('buying_price_slider', 'value'),
     Input('maintenance_per_year', 'value'),
     Input('building_insurance_per_year', 'value'),
     Input('rent_pcm_slider', 'value'),
     Input('house_price_growth', 'value'),
     Input('savings_returns', 'value'),
     Input('net_proceeds', 'data')
     ]
)
def update_outputs(buying_price, maintenance, insurance, rent_pcm, house_growth, savings_return, net_proceeds):
    years = np.arange(1, 31)  # 30 years

    # Stamp Duty Calculation - Simplified version
    stamp_duty = calculate_stamp_duty(buying_price)  # Reuse the previously defined function

    # Buying calculations (annual figures)
    annual_growth_rate = 1 + house_growth / 100
    house_value_initial = buying_price
    buying_income_annual = np.array([(house_value_initial * (annual_growth_rate ** year)) - house_value_initial for year in years]).round()
    buying_expenditure_annual = np.array([maintenance + insurance if year > 1 else maintenance + insurance + stamp_duty for year in years]).round()
    buying_wealth_annual = npf.fv(rate=house_growth/100, nper=years, pmt=buying_expenditure_annual + insurance, pv=-house_value_initial).round()

    # Renting calculations (annual figures)
    
    renting_income_annual = np.array([net_proceeds * (1 + savings_return / 100) ** year - net_proceeds for year in years]).round()
    renting_expenditure_annual = np.array([rent_pcm * 12 for _ in years]).round()
    renting_wealth_annual = npf.fv(rate=savings_return/100, nper=years, pmt=rent_pcm * 12, pv=-net_proceeds).round()

    # Prepare data for the DataTable
    data = {
        'Year': years,
        'Buying Income': buying_income_annual,
        'Buying Total Expenditure': buying_expenditure_annual,
        'Buying Total Wealth': buying_wealth_annual,  # Cumulative wealth from buying
        'Renting Income': renting_income_annual,
        'Renting Expenditure': renting_expenditure_annual,
        'Renting Total Wealth': renting_wealth_annual,  # Cumulative wealth from renting
    }
    df = pd.DataFrame(data)

    # Create the chart
    figure = {
        'data': [
            go.Scatter(x=years, y=buying_wealth_annual, mode='lines', name='Wealth from Buying'),
            go.Scatter(x=years, y=renting_wealth_annual, mode='lines', name='Wealth from Renting')
        ],
        'layout': go.Layout(title='Wealth Comparison: Buying vs Renting', xaxis={'title': 'Years'}, yaxis={'title': 'Wealth (£)'})
    }

    # Return chart and data for DataTable
    table_data = df.to_dict('records')
    return figure, table_data


# Stamp Duty Calculation - Simplified version
def calculate_stamp_duty(price):
    if price <= 125000:
        return 0
    elif price <= 250000:
        return (price - 125000) * 0.02
    elif price <= 925000:
        return ((price - 250000) * 0.05) + (125000 * 0.02)
    elif price <= 1500000:
        return ((price - 925000) * 0.1) + (675000 * 0.05) + (125000 * 0.02)
    else:
        return (
            ((price - 1500000) * 0.12)
            + (575000 * 0.1)
            + (675000 * 0.05)
            + (125000 * 0.02)
        )

# Run the app
if __name__ == "__main__":
    app.run_server(debug=True)
