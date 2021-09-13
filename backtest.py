# -*- coding: utf-8 -*-
"""
Created on Tue Jun  8 15:02:02 2021

@author: Calven
"""


# =============================================================================
# Backtesting Strategy I
#KC Breakout Strategy Paired with OBV and MACD

# =============================================================================

import numpy as np
import pandas as pd
from alpha_vantage.timeseries import TimeSeries
import statsmodels.api as sm
import copy
import time
import matplotlib.pyplot as plt


def ATR(DF,n):
    "function to calculate True Range and Average True Range"
    df = DF.copy()
    df['H-L']=abs(df['High']-df['Low'])
    df['H-PC']=abs(df['High']-df['Close'].shift(1))
    df['L-PC']=abs(df['Low']-df['Close'].shift(1))
    df['TR']=df[['H-L','H-PC','L-PC']].max(axis=1,skipna=False)
    df['ATR'] = df['TR'].rolling(n).mean()
    #df['ATR'] = df['TR'].ewm(span=n,adjust=False,min_periods=n).mean()
    df2 = df.drop(['H-L','H-PC','L-PC'],axis=1)
    return df2['ATR']


'''Uses of OBV
- Buy Signal:5 day OBV slope greater than 30 degrees
- Sell Signal:5 day OBV slope less than -30 degrees
Extremely useful as an entry filter when a stock is testing a major support or resistance.
If OBV hits new high at resistance, there is a high chance it will breakout.
If OBV hits new low at support, there is a high chance it will breakdown.
'''
def OBV(DF):
    """function to calculate On Balance Volume"""
    df = DF.copy()
    df['daily_ret'] = df['Close'].pct_change()
    df['direction'] = np.where(df['daily_ret']>=0,1,-1)
    df['direction'][0] = 0
    df['vol_adj'] = df['Volume'] * df['direction']
    df['obv'] = df['vol_adj'].cumsum()
    return df['obv']

def slope(ser,n):
    "function to calculate the slope of n consecutive points on a plot"
    slopes = [i*0 for i in range(n-1)]
    for i in range(n,len(ser)+1):
        y = ser[i-n:i]
        x = np.array(range(n))
        y_scaled = (y - y.min())/(y.max() - y.min())
        x_scaled = (x - x.min())/(x.max() - x.min())
        x_scaled = sm.add_constant(x_scaled)
        model = sm.OLS(y_scaled,x_scaled)
        results = model.fit()
        slopes.append(results.params[-1])
    slope_angle = (np.rad2deg(np.arctan(np.array(slopes))))
    return np.array(slope_angle)


def MACD(DF, slow, fast, smooth):
    exp1 = DF["Close"].ewm(span = fast, adjust = False).mean()
    exp2 = DF["Close"].ewm(span = slow, adjust = False).mean()
    macd = exp1-exp2
    signal = macd.ewm(span = smooth, adjust = False).mean()
    hist = macd - signal
    DF["MACD"] = macd
    DF["signal"] = signal
    DF["hist"] = hist
    return (DF["MACD"],DF["signal"],DF["hist"])

def plot_macd(prices, macd, signal, hist):
    ax1 = plt.subplot2grid((8,1), (0,0), rowspan = 5, colspan = 1)
    ax2 = plt.subplot2grid((8,1), (5,0), rowspan = 3, colspan = 1)

    ax1.plot(prices)
    ax2.plot(macd, color = 'grey', linewidth = 1.5, label = 'MACD')
    ax2.plot(signal, color = 'skyblue', linewidth = 1.5, label = 'SIGNAL')

    for i in range(len(prices)):
        if str(hist[i])[0] == '-':
            ax2.bar(prices.index[i], hist[i], color = '#ef5350')
        else:
            ax2.bar(prices.index[i], hist[i], color = '#26a69a')

    plt.legend(loc = 'lower right')


def trade_signal(df, i, ticker):
    "function to generate signal"
    signal = ""
    global last_transaction

    if df[ticker]["keltner_signal"][i] == "BREAKOUT BUY" and \
    df[ticker]["obv"][i] > df[ticker]["obv_ema"][i] and \
    tickers_transaction[ticker] != "BUY":
        signal = "BUY"
        tickers_transaction[ticker] = signal
        last_transaction = signal
        
    #Sell if price retreats to Middle band of Keltner Channel aka EMA
    elif df[ticker]["keltner_signal"][i] == "CLOSE TRADE" and \
    df[ticker]["obv"][i] < df[ticker]["obv_ema"][i] and \
    (tickers_transaction[ticker] == "BUY"):
        signal = "SELL"
        tickers_transaction[ticker] = signal
        last_transaction = signal
    
    else:
        signal = "NO SIGNAL"
    
    print(signal + ' at ' + str(df[ticker].index[i]))
    df[ticker]["g_signal"][i] = signal
    return df

def keltner_signal(df, i, ticker):
    "function to detect trend-pullback and breakouts using keltner channels"
    "identifying the trend of the stock"
    if df[ticker]["Close"][i] > df[ticker]["upper_band"][i]:
        tickers_trend[ticker] = "Uptrend"
    elif df[ticker]["Close"][i] < df[ticker]["lower_band"][i]:
        tickers_trend[ticker] = "Downtrend"
    
    "detecting pull-backs on uptrending stocks"
    #if df[ticker]["Close"][i] <= df[ticker]["EMA"][i] and \
    #tickers_trend[ticker] == "Uptrend":
    #    df[ticker]["keltner_signal"][i] = "UPTREND BUY"
    #else:
    #    df[ticker]["keltner_signal"][i] = "NO SIGNAL"
    "detecting break-outs"
    #More accurate during first 30 minutes of market open
    if df[ticker]["Close"][i] > df[ticker]["upper_band"][i]:
        df[ticker]["keltner_signal"][i] = "BREAKOUT BUY"
    elif df[ticker]["Close"][i] < df[ticker]["EMA"][i]:
        df[ticker]["keltner_signal"][i] = "CLOSE TRADE"
    else:
        df[ticker]["keltner_signal"][i] = "NO SIGNAL"
        

def calculate_returns(df, i, ticker):
    "function to calculate returns"
    signal = df["g_signal"][i]
    close_price = df["Close"][i]
    global avg_price
    if signal == "BUY":
        avg_price = close_price
    elif signal == "SELL":
        tickers_ret[ticker].append((close_price/avg_price)-1)
        avg_price = 0
    
                
    
tickers = ["IRNT","ATER","SPRT","BBIG"]

key_path = "C:\\Users\\Calven\\Documents\\projects\\alphavantagekey.txt"


ohlc_intraday = {} # directory with ohlc value for each stock   
api_call_count = 1
ts = TimeSeries(key=open(key_path,'r').read(), output_format='pandas')
start_time = time.time()
for ticker in tickers:
    data = ts.get_intraday(symbol=ticker,interval='5min', outputsize='full')[0]
    api_call_count+=1
    data.columns = ["Open","High","Low","Close","Volume"]
    data = data.iloc[::-1]
    data = data.between_time('09:35', '16:00') #remove data outside regular trading hours
    #data = data.between_time('04:05', '20:00') #to include premarket and postmarket, first candle starts 5mins after 
    ohlc_intraday[ticker] = data
    if api_call_count==5:
        api_call_count = 1
        time.sleep(60 - ((time.time() - start_time) % 60.0))

tickers = ohlc_intraday.keys()

ohlc_dict = copy.deepcopy(ohlc_intraday)
tickers_trend = {}
tickers_ret = {}
tickers_transaction = {}
for ticker in tickers:
    print("calculating technical indicators for ",ticker)
    ohlc_dict[ticker]["EMA"] = ohlc_dict[ticker]["Close"].ewm(span=20, min_periods=20).mean()
    ohlc_dict[ticker]["ATR"] = ATR(ohlc_dict[ticker],20)
    ohlc_dict[ticker]["macd"]= MACD(ohlc_dict[ticker],26,12,9)[0]
    ohlc_dict[ticker]["macd_sig"]= MACD(ohlc_dict[ticker],26,12,9)[1]
    ohlc_dict[ticker]["obv"]= OBV(ohlc_dict[ticker])
    ohlc_dict[ticker]["obv_slope"]= slope(ohlc_dict[ticker]["obv"],5)
    ohlc_dict[ticker]["obv_ema"] = ohlc_dict[ticker]["obv"].ewm(com=20).mean()
    ohlc_dict[ticker]["upper_band"] = ohlc_dict[ticker]["EMA"] + (ohlc_dict[ticker]["ATR"]*1)
    ohlc_dict[ticker]["lower_band"] = ohlc_dict[ticker]["EMA"] - (ohlc_dict[ticker]["ATR"]*1)
    ohlc_dict[ticker]["g_signal"] = "" #General Signal
    ohlc_dict[ticker]["keltner_signal"] = ""
    ohlc_dict[ticker].dropna(inplace=True)
    tickers_trend[ticker] = ""
    tickers_transaction[ticker] = ""
    tickers_ret[ticker] = [0]
    
last_transaction = ""
for ticker in tickers:
    for i in range(0, len(ohlc_dict[ticker])):
        keltner_signal(ohlc_dict, i, ticker)
        trade_signal(ohlc_dict, i, ticker)
    
avg_price = 0
#Visualizing buy and sell points
for ticker in tickers:
    stock = ohlc_dict[ticker]
    print("Visualizing for " + ticker)
    transactions = stock[stock['g_signal']!="NO SIGNAL"]
    print(transactions[['Close','g_signal']])
    for i in range(0, len(transactions)):
        calculate_returns(transactions, i, ticker)
    
#Calculating overall strategy's KPI

total_ret = 0
for ticker in tickers:
    total_ret += sum(tickers_ret[ticker])
    
#Individual stock performance
print({k:sum(v) for k,v in tickers_ret.items()}) 

#If i invested $100, what are my returns + principal amount
value = (total_ret*100)+100
returns_per = ((value-100)/100)*100

print("Total Returns is " + str(round(returns_per,2)) + "%")

n = len(stock)
CAGR = (value/1000)**(1/n)-1
