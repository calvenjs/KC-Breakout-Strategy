# Intraday Breakout Strategy in Python: Template Project

This base project use Keltner Channels on 5 min ticks to generate trading signals according to direction of the stock.

## Overview

The overall workflow for this project:
###Backtesting
1. Acquire the stock price data - using alphavantage.
2. Populate Technical Indicators into OHLC dictionary.
3. Populate Buy and Sell signals.
4. Calculate returns and CAGR
