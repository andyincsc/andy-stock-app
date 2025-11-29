import streamlit as st
import yfinance as yf
import matplotlib.pyplot as plt
import pandas as pd

st.title("📈 雲端股市分析儀")
st.write("這是在雲端執行的 Python 程式！")

# 側邊欄設定
st.sidebar.header("參數設定")
stock_id = st.sidebar.text_input("股票代號", "2330.TW")
start_date = st.sidebar.date_input("開始日期", value=pd.to_datetime("2024-01-01"))

if st.sidebar.button("分析"):
    try:
        # 抓取資料
        stock = yf.Ticker(stock_id)
        df = stock.history(start=str(start_date))

        if df.empty:
            st.error("找不到資料，請確認代號是否正確 (台股要加 .TW)")
        else:
            # 計算均線
            df['5MA'] = df['Close'].rolling(window=5).mean()
            df['20MA'] = df['Close'].rolling(window=20).mean()
            df['60MA'] = df['Close'].rolling(window=60).mean()

            # 畫圖
            fig, ax = plt.subplots(figsize=(10, 5))
            ax.plot(df.index, df['Close'], label='收盤價', color='gray', alpha=0.5)
            ax.plot(df.index, df['5MA'], label='5MA (週)', color='orange')
            ax.plot(df.index, df['20MA'], label='20MA (月)', color='red')
            ax.plot(df.index, df['60MA'], label='60MA (季)', color='green')
            
            ax.set_title(f"{stock_id} Analysis")
            ax.grid(True)
            ax.legend()
            
            # 顯示結果
            st.pyplot(fig)
            st.metric("最新收盤價", f"{df['Close'].iloc[-1]:.2f}")

    except Exception as e:
        st.error(f"發生錯誤：{e}")
