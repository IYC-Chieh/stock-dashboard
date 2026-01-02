import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

# 設定頁面標題
st.set_page_config(page_title="股市決策戰情室", layout="wide")
st.title("📈 全球與台股投資決策儀表板")

# 側邊欄：使用者輸入
st.sidebar.header("設定參數")
ticker = st.sidebar.text_input("輸入股票代號 (台股請加.TW)", value="2330.TW")
days = st.sidebar.slider("回顧天數", 30, 365, 180)

# 核心功能：抓取資料
def get_data(symbol, n_days):
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=n_days)
        df = yf.download(symbol, start=start_date, end=end_date)
        return df
    except Exception as e:
        return None

# 執行抓取
df = get_data(ticker, days)

if df is not None and not df.empty:
    # 計算簡單策略：20日均線 (月線)
    df['MA20'] = df['Close'].rolling(window=20).mean()
    latest_price = df['Close'].iloc[-1]
    latest_ma20 = df['MA20'].iloc[-1]

    # 顯示關鍵數據
    col1, col2, col3 = st.columns(3)
    col1.metric("目前股價", f"{latest_price:.2f}")
    col2.metric("20日均線 (月線)", f"{latest_ma20:.2f}")

    # 簡單決策訊號
    signal = "觀望 😐"
    if latest_price > latest_ma20:
        signal = "多頭趨勢 🐂 (股價在月線上)"
        col3.success(signal)
    else:
        signal = "空頭警示 🐻 (股價在月線下)"
        col3.error(signal)

    # 繪製 K 線圖
    fig = go.Figure(data=[go.Candlestick(x=df.index,
                    open=df['Open'],
                    high=df['High'],
                    low=df['Low'],
                    close=df['Close'],
                    name='K線'),
                    go.Scatter(x=df.index, y=df['MA20'], line=dict(color='orange', width=1), name='月線')])

    fig.update_layout(title=f"{ticker} 股價走勢圖", xaxis_title="日期", yaxis_title="價格")
    st.plotly_chart(fig, use_container_width=True)

    # 顯示原始數據
    with st.expander("查看詳細歷史數據"):
        st.dataframe(df.sort_index(ascending=False))

else:
    st.error("找不到股票資料，請確認代號是否正確 (例如台積電是 2330.TW，蘋果是 AAPL)")

st.markdown("---")
st.caption("資料來源：Yahoo Finance | 自動化更新系統")
