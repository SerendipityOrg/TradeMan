import dash
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
from dash import html, dcc
import plotly.graph_objs as go
from datetime import datetime,timedelta
import pandas as pd


def plotly_plot(resultdf):
    # global trade_state_df
    # Define the custom shapes (background color) for each day
    shapes = []
    colors = ["white", "#C23B22", "#5F9EA0", "#F5DEB3", "black"]
    holidayz = [datetime.strptime(date_str, '%Y-%m-%d').date() for date_str in ['2023-05-01', '2023-06-16','2023-06-29']]

    if datetime.today().weekday() == 1:
        resultdf = resultdf.iloc[-370:]
    else:
        resultdf = resultdf.iloc[-288*2:]
    # print datatypes of resultdf columns including index
    for i, date in enumerate(resultdf.index):
        if date.hour == 9 and date.minute == 15:
            weekday = date.weekday()
            if weekday < 5:  # Only for Monday to Friday
                if date.date() not in holidayz:  # Check if the date is not a holiday
                    shape = {
                        "type": "rect",
                        "xref": "x",
                        "yref": "paper",
                        "x0": date,
                        "x1": date + pd.Timedelta(hours=6, minutes=15),
                        "y0": 0,
                        "y1": 1,
                        "fillcolor": colors[weekday],
                        "opacity": 0.3,
                        "line": {"width": 0},
                        "layer": "below",
                    }
                    shapes.append(shape)
                    
    holiday_rangebreaks = [{"bounds": [holiday.strftime('%Y-%m-%d'), (holiday + pd.Timedelta(days=1)).strftime('%Y-%m-%d')], "pattern": ''} for holiday in holidayz]

    # Create a layout with custom styling, including background colors and shapes
    layout = go.Layout(
        title="AmiPy_NF",
        title_x=0.5,
        plot_bgcolor="black",
        height=800,
        xaxis=dict(
            gridcolor="rgba(128, 128, 128, 0.1)",
            showgrid=True,
            tickformat="%Y-%m-%d %H:%M",
            dtick="60 * 60 * 1000",  # 1 hour in milliseconds
            rangebreaks=[
                dict(bounds=["sat", "mon"]),
                dict(bounds=[0, 9.25], pattern="hour"),
                dict(bounds=[15.5, 24], pattern="hour"),
            ]+holiday_rangebreaks,
        ),
        yaxis=dict(
            gridcolor="rgba(128, 128, 128, 0.1)",
            showgrid=True,
            automargin=True,
            autorange=True,
        ),
        # Add the custom shapes to the layout
        shapes=shapes,
    )

    fig = go.Figure()

    fig.add_trace(go.Scatter(x=resultdf.index, y=resultdf['close'],
                            mode='lines', name='Closing Price', line=dict(color='skyblue', dash='dot')))
    
        # Filter the data for uptrends and downtrends
    uptrend_df = resultdf[resultdf['Trend'] == 1]
    downtrend_df = resultdf[resultdf['Trend'] == -1]

    # Plot the uptrend data with a green line
    for i in range(len(uptrend_df) - 1):
        if uptrend_df.index[i+1] - uptrend_df.index[i] == pd.Timedelta(minutes=1):
            fig.add_trace(go.Scatter(x=[uptrend_df.index[i], uptrend_df.index[i+1]], y=[uptrend_df.iloc[i]['TrendSL'], uptrend_df.iloc[i+1]['TrendSL']],
            mode='lines', name='SuperTrend Uptrend', line=dict(color='green'), showlegend=False if i != 0 else True))

    # Plot the downtrend data with a red line
    for i in range(len(downtrend_df) - 1):
        if downtrend_df.index[i+1] - downtrend_df.index[i] == pd.Timedelta(minutes=1):
            fig.add_trace(go.Scatter(x=[downtrend_df.index[i], downtrend_df.index[i+1]], y=[downtrend_df.iloc[i]['TrendSL'], downtrend_df.iloc[i+1]['TrendSL']],
            mode='lines', name='SuperTrend Downtrend', line=dict(color='red'), showlegend=False if i != 0 else True))

    # Add the custom shapes to the layout
    layout.shapes = shapes

    # Update x-axis tick format
    layout.xaxis.tickformat = "%Y-%m-%d %H:%M"
    layout.xaxis.hoverformat = "%Y-%m-%d %H:%M"

    fig.add_trace(go.Scatter(x=resultdf[resultdf['LongSignal'] == 1].index, y=resultdf[resultdf['LongSignal'] == 1]['close'], mode='markers', name='Long', marker=dict(color='green', symbol='triangle-up', size=15)))
    fig.add_trace(go.Scatter(x=resultdf[resultdf['LongCoverSignal'] == 1].index, y=resultdf[resultdf['LongCoverSignal'] == 1]['close'], mode='markers', name='Long Cover', marker=dict(color='green', symbol='star', size=15)))
    fig.add_trace(go.Scatter(x=resultdf[resultdf['ShortSignal'] == 1].index, y=resultdf[resultdf['ShortSignal'] == 1]['close'], mode='markers', name='Short Signal', marker=dict(color='red', symbol='triangle-down', size=15)))
    fig.add_trace(go.Scatter(x=resultdf[resultdf['ShortCoverSignal'] == 1].index, y=resultdf[resultdf['ShortCoverSignal'] == 1]['close'], mode='markers', name='Short Cover Signal', marker=dict(color='red', symbol='star', size=15)))

    fig.update_layout(layout)
    # pyo.plot(fig)
    
    return fig