import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from pymongo import MongoClient
import os

# Connect to MongoDB
MONGO_URL = os.environ.get("MONGO_URL")
client = MongoClient(MONGO_URL)
db = client["TrademanUserProfile"]
clients_collection = db["Clients"]

def load_data_from_mongodb(email):
    client_data = clients_collection.find_one({"email": email})
    if client_data and "performance_data" in client_data:
        return pd.DataFrame(client_data["performance_data"])
    else:
        return None

def show_performance_dashboard(email):
    st.header("Performance Dashboard")

    # Strategy selection
    strategy = st.selectbox(
        'Select Strategy',
        ('SMACrossover', 'GoldenRatio')
    )

    # Account selection
    account = st.selectbox(
        'Select Account',
        ('Signals', 'YY0222', 'BY1424')
    )

    # Load data from MongoDB based on the user's email
    data = load_data_from_mongodb(email)

    if data is not None:
        # Filter data based on strategy and account
        filtered_data = data[(data['Strategy'] == strategy) & (data['Account'] == account)]

        # Display the data
        st.dataframe(filtered_data)

        # Convert 'Date' to datetime
        filtered_data['Date'] = pd.to_datetime(filtered_data['Date'], format='%d-%b')

        # Line plot for 'NetPnL' over time
        st.line_chart(filtered_data.set_index('Date')['NetPnL'])

        # Calculate running total of 'NetPnL'
        filtered_data['Cumulative NetPnL'] = filtered_data['NetPnL'].cumsum()

        # Calculate underwater curve (drawdown)
        filtered_data['Underwater'] = filtered_data['Cumulative NetPnL'].cummax() - filtered_data['Cumulative NetPnL']

        # Underwater plot using Plotly
        fig = go.Figure(data=[
            go.Scatter(name='Underwater', x=filtered_data['Date'], y=filtered_data['Underwater'], fill='tonexty', line_color='indianred'),
            go.Scatter(name='NetPnL', x=filtered_data['Date'], y=filtered_data['Cumulative NetPnL'], line_color='deepskyblue'),
        ])
        fig.update_layout(title='Underwater Plot', xaxis_title='Date', yaxis_title='Value')
        st.plotly_chart(fig)

        # Calculate statistics
        stats = calculate_stats(filtered_data)

        # Display statistics in Streamlit
        st.subheader("Performance Statistics")
        for key, value in stats.items():
            st.markdown(f"**{key}:** {value:,.2f}")

def calculate_stats(data):
    # Calculate statistics
    allocated_capital = 1000000  # As per your requirement
    num_trading_days = len(data['Date'].unique())
    num_trades = len(data)
    gross_profit = data['Gross PnL'].sum()
    charges = data['Taxes'].abs().sum()  # Assuming taxes are the charges
    net_profit = data['NetPnL'].sum()
    returns = (net_profit / allocated_capital) * 100
    annualized_returns = (1 + net_profit / allocated_capital) ** (252/num_trading_days) - 1
    max_profit = data['NetPnL'].max()
    max_loss = data['NetPnL'].min()

    # Calculating win and loss days
    daily_pnl = data.groupby('Date')['NetPnL'].sum()
    num_win_days = len(daily_pnl[daily_pnl > 0])
    num_loss_days = len(daily_pnl[daily_pnl < 0])

    # Calculate max drawdown
    cumulative_pnl = daily_pnl.cumsum()
    running_max = np.maximum.accumulate(cumulative_pnl)
    drawdown = (running_max - cumulative_pnl) / running_max
    max_drawdown = drawdown.max() * 100

    # Calculate winning accuracy
    num_winning_trades = len(data[data['NetPnL'] > 0])
    winning_accuracy = (num_winning_trades / num_trades) * 100

    # Create stats dictionary
    stats = {
        "Allocated Capital": allocated_capital,
        "Number of trading days": num_trading_days,
        "Number of trades": num_trades,
        "Number of win days": num_win_days,
        "Number of loss days": num_loss_days,
        "Gross Profit": gross_profit,
        "Charges": charges,
        "Net Profit": net_profit,
        "Returns (%)": returns,
        "Annualized (%)": annualized_returns * 100,
        "Max Profit": max_profit,
        "Max Loss": max_loss,
        "Max Drawdown from Peak (%)": max_drawdown,
        "Winning Accuracy(%)": winning_accuracy,
    }
    
    return stats
