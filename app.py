import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# --- 設定頁面 ---
st.set_page_config(page_title="台股智慧分析儀", layout="wide")
st.title("📊 台股智慧選股與追蹤系統")

# --- 初始化 Session State (用來記憶自選股) ---
if 'watchlist' not in st.session_state:
    st.session_state.watchlist = ['2330.TW', '2317.TW', '2454.TW'] # 預設給這三檔

# --- 定義樣本股票池 (為了雲端效能，這裡列出熱門股代表全市場) ---
# 實務上若要掃描全台股，建議連接資料庫，否則 yfinance 會抓很久
SAMPLE_STOCKS = [
    '2330.TW', '2317.TW', '2454.TW', '2308.TW', '2303.TW', '2603.TW', '2609.TW', '2615.TW',
    '2881.TW', '2882.TW', '1301.TW', '1303.TW', '2002.TW', '2382.TW', '3231.TW',
    '6669.TW', '3008.TW', '3037.TW', '2379.TW', '3034.TW', '3045.TW', '4938.TW',
    '2357.TW', '2344.TW', '3711.TW', '2412.TW', '2327.TW', '3017.TW', '6239.TW', '8069.TW'
]

# --- 核心函數：取得資料並計算指標 ---
@st.cache_data(ttl=300) # 設定快取 5 分鐘，避免一直重複抓
def get_stock_data(ticker_list):
    data_list = []
    
    # 為了計算指標，我們抓取過去 60 天的資料
    for ticker in ticker_list:
        try:
            stock = yf.Ticker(ticker)
            df = stock.history(period="3mo") # 抓3個月確保均線資料足夠
            
            if len(df) < 20: continue # 資料太少跳過

            # --- 計算技術指標 (六大條件基礎) ---
            # 1. 目前價格
            current_price = df['Close'].iloc[-1]
            prev_price = df['Close'].iloc[-2]
            change_pct = (current_price - prev_price) / prev_price * 100
            
            # 2. 均線 (MA)
            ma5 = df['Close'].rolling(5).mean().iloc[-1]
            ma10 = df['Close'].rolling(10).mean().iloc[-1]
            ma20 = df['Close'].rolling(20).mean().iloc[-1]
            ma60 = df['Close'].rolling(60).mean().iloc[-1]
            
            # 3. 成交量相關
            vol_current = df['Volume'].iloc[-1]
            vol_avg_10 = df['Volume'].rolling(10).mean().iloc[-1]
            vol_ratio = vol_current / vol_avg_10 if vol_avg_10 > 0 else 0
            
            # 4. RSI (相對強弱指標) - 簡單版 14日
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs)).iloc[-1]

            # --- 六大篩選條件判斷 (True/False) ---
            # 這裡定義您的「六大條件」，您可以根據需求修改
            # 條件1: 股價站上月線 (趨勢多頭)
            c1 = current_price > ma20
            # 條件2: 今日上漲 (動能)
            c2 = change_pct > 0
            # 條件3: 成交量大於 1000 張 (流動性)
            c3 = vol_current > 1000000 # yfinance 單位是股
            # 條件4: 量能放大 (今日量 > 10日均量 1.2倍)
            c4 = vol_ratio > 1.2
            # 條件5: RSI 強勢區 (大於 50 但小於 80 避免過熱)
            c5 = 50 < rsi < 80
            # 條件6: 均線多頭排列 (5MA > 10MA > 20MA)
            c6 = (ma5 > ma10) and (ma10 > ma20)

            # 計算符合幾個條件
            score = sum([c1, c2, c3, c4, c5, c6])

            data_list.append({
                '代號': ticker,
                '價格': round(current_price, 2),
                '漲跌幅(%)': round(change_pct, 2),
                '成交量(張)': int(vol_current / 1000),
                '量比(倍)': round(vol_ratio, 2),
                'RSI': round(rsi, 2),
                '站上月線': "✅" if c1 else "❌",
                '多頭排列': "✅" if c6 else "❌",
                '符合條件數': score,
                'Raw_Data': { # 藏一些原始數據供後續使用
                    'c1': c1, 'c2': c2, 'c3': c3, 'c4': c4, 'c5': c5, 'c6': c6
                }
            })
            
        except Exception as e:
            continue
            
    return pd.DataFrame(data_list)

# --- 介面佈局：分頁 ---
tab1, tab2 = st.tabs(["🔍 分析區 (智慧篩選)", "📋 自選區 (我的觀察名單)"])

# ==========================================
# 分頁 1: 分析區
# ==========================================
with tab1:
    st.header("六大條件智慧篩選")
    st.info("""
    **目前的六大篩選條件定義：**
    1. 股價站上月線 (20MA)
    2. 今日股價上漲
    3. 成交量 > 1,000 張
    4. 量能放大 (大於 10 日均量 1.2 倍)
    5. RSI 指標強勢 (50~80)
    6. 均線多頭排列 (5日 > 10日 > 20日)
    """)
    
    if st.button("🚀 開始篩選 (掃描熱門股)"):
        with st.spinner('正在分析市場數據，請稍候...'):
            # 1. 取得資料
            df_analysis = get_stock_data(SAMPLE_STOCKS)
            
            if not df_analysis.empty:
                # 2. 篩選邏輯：這裡示範列出「符合條件數 >= 4」的股票
                # 並依照「符合條件數」和「量比」排序
                filtered_df = df_analysis[df_analysis['符合條件數'] >= 3].sort_values(
                    by=['符合條件數', '量比(倍)'], ascending=False
                )
                
                # 取前 10 檔
                top_10 = filtered_df.head(10)
                
                st.success(f"分析完成！找到 {len(top_10)} 檔潛力股 (顯示最佳前 10 名)")
                
                # 3. 顯示結果與加入按鈕
                # 這裡不用 st.dataframe，改用 columns 方便放按鈕
                
                # 表頭
                cols = st.columns([1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 2])
                cols[0].write("**代號**")
                cols[1].write("**價格**")
                cols[2].write("**漲跌幅**")
                cols[3].write("**量比**")
                cols[4].write("**條件數**")
                cols[5].write("**趨勢**")
                cols[6].write("**動作**")
                st.divider()

                for index, row in top_10.iterrows():
                    cols = st.columns([1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 2])
                    
                    # 顏色標示
                    color = "red" if row['漲跌幅(%)'] > 0 else "green"
                    
                    cols[0].write(row['代號'])
                    cols[1].write(f"{row['價格']}")
                    cols[2].markdown(f":{color}[{row['漲跌幅(%)']}%]")
                    cols[3].write(f"{row['量比(倍)']} 倍")
                    cols[4].write(f"⭐ {row['符合條件數']}")
                    cols[5].write(f"{row['多頭排列']}")
                    
                    # 加入自選按鈕
                    # 每個按鈕需要唯一的 key
                    if row['代號'] in st.session_state.watchlist:
                        cols[6].write("✅ 已在自選")
                    else:
                        if cols[6].button("➕ 加入自選", key=f"add_{row['代號']}"):
                            st.session_state.watchlist.append(row['代號'])
                            st.rerun() # 重新整理畫面更新狀態
            else:
                st.warning("目前沒有抓到資料，請稍後再試。")

# ==========================================
# 分頁 2: 自選區
# ==========================================
with tab2:
    st.header("📋 我的自選股清單")
    
    # --- 新增股票功能 ---
    col1, col2 = st.columns([3, 1])
    with col1:
        new_stock = st.text_input("輸入股票代號加入 (例如 2603.TW)")
    with col2:
        st.write("") # 排版用
        st.write("") 
        if st.button("新增"):
            if new_stock and new_stock not in st.session_state.watchlist:
                st.session_state.watchlist.append(new_stock)
                st.success(f"已加入 {new_stock}")
                st.rerun()
            elif new_stock in st.session_state.watchlist:
                st.warning("該股票已在清單中")

    st.divider()

    # --- 顯示自選股資料 ---
    if st.session_state.watchlist:
        with st.spinner('正在更新自選股報價...'):
            df_watchlist = get_stock_data(st.session_state.watchlist)
            
            if not df_watchlist.empty:
                # 整理顯示欄位
                # 預估成交量邏輯：若是盤中，yfinance 資料可能有延遲，這裡我們用當日成交量代替
                # 並顯示六大指標相關數據
                
                display_df = df_watchlist[[
                    '代號', '價格', '漲跌幅(%)', '成交量(張)', '量比(倍)', 
                    'RSI', '站上月線', '多頭排列', '符合條件數'
                ]].copy()
                
                # 這裡使用 st.data_editor 讓表格比較漂亮，但不開放直接編輯數據
                st.dataframe(
                    display_df.style.map(lambda x: 'color: red' if isinstance(x, (int, float)) and x > 0 else 'color: green', subset=['漲跌幅(%)']),
                    use_container_width=True,
                    hide_index=True
                )
                
                # --- 刪除功能 ---
                st.subheader("管理清單")
                stock_to_remove = st.selectbox("選擇要移除的股票", st.session_state.watchlist)
                if st.button("🗑️ 移除選定股票"):
                    st.session_state.watchlist.remove(stock_to_remove)
                    st.rerun()
            else:
                st.error("無法取得報價資料。")
    else:
        st.info("您的自選清單目前是空的，請從「分析區」加入或手動輸入。")
