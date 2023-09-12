import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from scipy.stats import norm

            
# Function to calculate additional columns
def calculate_columns(df, start_capital):
    Margin_utilized = []
    Lots = []
    Qty = []
    PnL = []
    Taxes = []
    NetPnL = []
    Capital = [start_capital]
    margin_per_lot = 80000  # 80k margin per lot
    lot_size = 50
    for i in range(len(df)):
        Margin_utilized.append(0.6 * Capital[-1])
        Lots.append(Margin_utilized[-1] // margin_per_lot)
        Qty.append(int(Lots[-1] * lot_size))
        PnL.append(Qty[-1] * df.loc[i, 'NetTradePoints'])
        
        # Calculate taxes and charges
        premium = df.loc[i, 'TradeEntryPrice'] * Qty[-1]
        brokerage = 40  # Rs. 40 per executed order
        transaction_charges = 0.00053 * premium
        gst = 0.18 * (brokerage + transaction_charges)
        sebi_charges = 5 * (premium / 10000000)  # Rs. 5 per crore
        stamp_charges = 100 * (premium / 10000000)  # Rs. 100 per crore, varies by state
        total_charges = brokerage + transaction_charges + gst + sebi_charges + stamp_charges
        
        Taxes.append(total_charges)
        NetPnL.append(PnL[-1] - Taxes[-1])
        if i < len(df) - 1:  # Avoids IndexError on the last row
            Capital.append(Capital[-1] + NetPnL[-1])
    return Margin_utilized, Lots, Qty, PnL, Taxes, NetPnL, Capital


def load_data():
    df = pd.read_csv(r'C:\Users\user\Desktop\GroundUp_Trading\NiftyStrategy\Strategies\OvernightNF\backtest_results.csv')
    df['Datetime'] = pd.to_datetime(df['Date'] + ' ' + df['TradeEntryTime'])
    df.sort_values(by=['Datetime'], inplace=True)
    df.reset_index(drop=True, inplace=True)
    df['Trade_No'] = df.index + 1
    return df

#st.title('AmiPy_Backtest')
start_capital = st.sidebar.number_input('Enter Starting Capital', value=1800000)
df = load_data()

# Select the date range using the sidebar
selected_dates = st.sidebar.date_input('Select Date Range', [df['Datetime'].min().date(), df['Datetime'].max().date()])

# Filter data according to selected_dates
df = df.loc[(df['Datetime'] >= pd.Timestamp(selected_dates[0])) & (df['Datetime'] <= pd.Timestamp(selected_dates[1]))]

# drop unnamed column from display_df and make Trade_No the index
# df.drop(columns=['Unnamed: 0'], inplace=True)
#df.set_index('Trade_No', inplace=True)

Margin_utilized, Lots, Qty, PnL, Taxes, NetPnL, Capital = calculate_columns(df, start_capital)
df['Margin_utilized'] = Margin_utilized
df['Lots'] = Lots
df['Qty'] = Qty
df['PnL'] = PnL
df['Taxes'] = Taxes
df['NetPnL'] = NetPnL
df['Capital'] = Capital

df.to_csv('amiNF_trd_sig_backtest_mod.csv', index=True)

# Additional statistics
net_profit = Capital[-1] - start_capital
net_profit_percentage = ((Capital[-1] / start_capital) - 1) * 100  # in percentage
avg_profit_loss = df['PnL'].mean()
largest_win = df['PnL'].max()
largest_loss = df['PnL'].min()
largest_win_trade_no = df['PnL'].idxmax() + 1  # trade numbers start at 1
largest_loss_trade_no = df['PnL'].idxmin() + 1
max_consecutive_wins = (df['PnL'] > 0).astype(int).groupby(df['PnL'].astype(bool).cumsum()).count().max()
max_consecutive_losses = (df['PnL'] < 0).astype(int).groupby(df['PnL'].astype(bool).cumsum()).count().max()
# Calculate drawdowns and max drawdown
drawdowns = pd.Series(Capital) - pd.Series(Capital).cummax()
max_drawdown = -drawdowns.min()
max_percent_drawdown = (max_drawdown / pd.Series(Capital).loc[drawdowns.idxmin()]) * 100  # in percentage

recovery_factor = df['NetPnL'].sum() / max_drawdown
risk_reward_ratio = abs(df['PnL'][df['PnL'] > 0].mean() / df['PnL'][df['PnL'] < 0].mean())
sharpe_ratio = df['NetPnL'].mean() / df['NetPnL'].std() * np.sqrt(len(df))  # assume risk-free rate = 0


fig = go.Figure()
fig.add_trace(go.Scatter(x=df['Datetime'], y=df['NetPnL'].cumsum(), mode='lines+markers', name='NetPnL'))
fig.update_layout(title='Net Profit and Loss Over Time', xaxis_title='Date', yaxis_title='Net PnL',
                  autosize=False, width=1000, height=500)
st.plotly_chart(fig)

stats = {
    "Starting Capital": "{:.2f}".format(start_capital),    
    "Net Profit": "{:.2f}".format(net_profit),
    "Net Profit (%)": "{:.2f}".format(net_profit_percentage),
    "Average Profit/Loss": "{:.2f}".format(avg_profit_loss),
    "Largest Win": "{:.2f}".format(largest_win),
    "Largest Win Trade No": largest_win_trade_no,
    "Largest Loss": "{:.2f}".format(largest_loss),
    "Largest Loss Trade No": largest_loss_trade_no,
    "Max Consecutive Wins": max_consecutive_wins,
    "Max Consecutive Losses": max_consecutive_losses,
    "Max Drawdown": "{:.2f}".format(max_drawdown),
    "Max % Drawdown": "{:.2f}".format(max_percent_drawdown),
    "Recovery Factor": "{:.2f}".format(recovery_factor),
    "Risk/Reward Ratio": "{:.2f}".format(risk_reward_ratio),
    "Sharpe Ratio": "{:.2f}".format(sharpe_ratio),
}

# Display stats in a table
st.table(pd.DataFrame.from_dict(stats, orient='index', columns=['Value']))

st.dataframe(df)


