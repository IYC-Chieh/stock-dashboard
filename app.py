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
# 提示使用者可以輸入中文備註，程式會自動處理
ticker_input = st.sidebar.text_input("輸入股票代號 (例如: 2330.TW 或 AAPL 蘋果)", value="2330.TW")
days = st.sidebar.slider("回顧天數", 30, 365, 180)

# --- 防呆機制 1：自動清洗代號 ---
# 使用 split() 取出第一個空格前的代號，避免後面的中文導致錯誤
# 例如 "AAPL (蘋果)" 會變成 "AAPL"
if not ticker_input:
    ticker = "2330.TW" # 預設值
else:
    ticker = ticker_input.split().strip().upper()

# 核心功能：抓取資料
def get_data(symbol, n_days):
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=n_days)
        # 嘗試下載資料
        df = yf.download(symbol, start=start_date, end=end_date)
        
        # 如果下載回來的資料是空的，回傳 None
        if df.empty:
            return None
            
        # --- 防呆機制 2：處理多層索引 (MultiIndex) ---
        # yfinance 新版本有時會回傳多層欄位 (Price, Ticker)，這裡統一扁平化
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.droplevel(1)
            
        return df
    except Exception as e:
        print(f"錯誤: {e}")
        return None

# 執行抓取
df = get_data(ticker, days)

if df is not None and not df.empty:
    # 計算簡單策略：20日均線 (月線)
    df['MA20'] = df['Close'].rolling(window=20).mean()
    
    # --- 防呆機制 3：確保數值格式正確 ---
    try:
        latest_close = df['Close'].iloc[-1]
        latest_ma20 = df['MA20'].iloc[-1]
        
        # 強制轉型為浮點數 (float)，避免因為是 Series 而報錯
        if isinstance(latest_close, pd.Series):
            latest_close = latest_close.item()
        if isinstance(latest_ma20, pd.Series):
            latest_ma20 = latest_ma20.item()
            
        latest_close = float(latest_close)
        latest_ma20 = float(latest_ma20)
        
    except Exception as e:
        st.error(f"數據格式處理錯誤: {e}")
        st.stop()

    # 顯示關鍵數據
    col1, col2, col3 = st.columns(3)
    col1.metric("目前股價", f"{latest_close:.2f}")
    col2.metric("20日均線 (月線)", f"{latest_ma20:.2f}")
    
    # 簡單決策訊號
    signal = "觀望 😐"
    if latest_close > latest_ma20:
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
    st.error(f"找不到 {ticker} 的資料。請確認代號是否正確 (例如台積電是 2330.TW，美股 AAPL)")

st.markdown("---")
st.caption("資料來源：Yahoo Finance | 自動化更新系統")
