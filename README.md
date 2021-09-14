# Intraday Breakout Strategy in Python: Template Project

This base project uses Keltner Channels and OBV on 5 min ticks to generate trading signals according to direction of the stock. This strategy focuses on small-cap/mid-cap stocks.

## Introduction
This project implements Keltner Channels on python to detect breakouts of a particular asset. It is supported by other technical indicators such as obv.  

## Overview

The overall workflow for this project:
### Backtesting for 1 month 5-min ticks
1. Acquire the stock price data - using alphavantage.
2. Populate Technical Indicators into OHLC dictionary.
3. Populate Buy and Sell signals.
4. Calculate returns, CAGR, and Max Drawdown

### Strategy Overview
**Long-only**  
Entry:  
If the asset closes above the upper channel, obv is higher than obv_ema, a buy signal is generated.  
Exit:  
If the asset closes below the middle channel (20 EMA), obv is lower than obv_ema, a sell signal is generated. 

### Evaluation
During the period (2021-08-16 to 2021-09-10) of high retail interest in tickers ["IRNT","ATER","SPRT","BBIG"]  
The portfolio had a 492.97%  returns.  
Individual stock performance in % {'IRNT': 0.38, 'ATER': 0.97, 'SPRT': 1.51, 'BBIG': 2.07}


# Work still in progress...
1. Working on screening tickers for the strategy (currently uses high volatile stocks frequently mentioned by retail traders)
2. Reducing whipsaws in strategy

*As a disclaimer, this is a purely a self-initiated educational project. Any backtested results do not guarantee performance in live trading. Do live trading at your own risk.*
