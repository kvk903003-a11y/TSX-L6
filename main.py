import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import ta
import time

st.set_page_config(page_title="TSX Institutional Quant Engine", layout="wide")
st.title("🇨🇦 Institutional Quant Portfolio Engine")

INITIAL_CAPITAL = 100000
TOP_N = 3

if "equity_curve" not in st.session_state:
    st.session_state.equity_curve = [INITIAL_CAPITAL]

if "capital" not in st.session_state:
    st.session_state.capital = INITIAL_CAPITAL

stocks = [
    "SHOP.TO","SU.TO","RY.TO","TD.TO","BNS.TO",
    "ENB.TO","CNQ.TO","CP.TO","CNR.TO","BAM.TO",
    "TRP.TO","MFC.TO","WCN.TO","ATD.TO","CM.TO"
]

def factor_score(df):

    score = 0

    df["EMA20"] = ta.trend.ema_indicator(df["Close"], 20)
    df["EMA50"] = ta.trend.ema_indicator(df["Close"], 50)
    df["RSI"] = ta.momentum.rsi(df["Close"], 14)
    df["ATR"] = ta.volatility.average_true_range(
        df["High"], df["Low"], df["Close"], 14
    )

    last = df.iloc[-1]

    # Trend Factor
    if last["EMA20"] > last["EMA50"]:
        score += 30

    # Momentum Factor
    if 55 < last["RSI"] < 75:
        score += 25

    # Volatility Quality
    if last["ATR"] < df["ATR"].rolling(20).mean().iloc[-1]:
        score += 20

    # Price Strength
    if last["Close"] > df["Close"].rolling(50).mean().iloc[-1]:
        score += 25

    return score

results = []

for ticker in stocks:

    df = yf.download(ticker, period="6mo", interval="1d")

    if df.empty:
        continue

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    score = factor_score(df)

    last_price = float(df["Close"].iloc[-1])

    results.append({
        "Stock": ticker,
        "Score": score,
        "Price": round(last_price,2)
    })

if len(results) > 0:

    df_rank = pd.DataFrame(results).sort_values(by="Score", ascending=False)

    top_stocks = df_rank.head(TOP_N)

    allocation = st.session_state.capital / TOP_N

    st.subheader("🏆 Top Portfolio Selections")
    st.dataframe(top_stocks)

    st.write(f"Equal Allocation per Stock: ${round(allocation,2)}")

    # Simulated portfolio move
    if st.button("Simulate +1% Portfolio Gain"):
        st.session_state.capital *= 1.01
        st.session_state.equity_curve.append(st.session_state.capital)

    if st.button("Simulate -1% Portfolio Loss"):
        st.session_state.capital *= 0.99
        st.session_state.equity_curve.append(st.session_state.capital)

    st.subheader("📈 Portfolio Equity Curve")
    st.line_chart(st.session_state.equity_curve)

    # Risk metrics
    equity_array = np.array(st.session_state.equity_curve)
    returns = pd.Series(equity_array).pct_change().dropna()

    if len(returns) > 0:
        sharpe = np.sqrt(252) * returns.mean() / returns.std() if returns.std()!=0 else 0
        drawdown = (equity_array / np.maximum.accumulate(equity_array) - 1).min()

        st.write(f"Sharpe Ratio: {round(sharpe,2)}")
        st.write(f"Max Drawdown: {round(drawdown*100,2)}%")

else:
    st.warning("No stocks scored.")
    
time.sleep(60)
st.rerun()
