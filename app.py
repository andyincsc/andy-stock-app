import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# --- 頁面設定 ---
st.set_page_config(page_title="台股分批智慧掃描", layout="wide")
st.title("📊 台股分批智慧選股系統")

# --- 1. 定義股票池 (分批名單) ---
# 為了避免超時，我們將股票分成不同族群 (Batch)
# 您可以隨時在此擴充名單
STOCK_SECTORS = {
    "🔥 熱門權值股 (Top 30)": [
        '2330.TW', '2317.TW', '2454.TW', '2308.TW', '2303.TW', '2881.TW', '2882.TW', '2886.TW', '2891.TW', '2884.TW',
        '1301.TW', '1303.TW', '2002.TW', '1216.TW', '2412.TW', '3008.TW', '3045.TW', '2892.TW', '2885.TW', '2207.TW',
        '2357.TW', '2880.TW', '2887.TW', '1101.TW', '2382.TW', '2327.TW', '2395.TW', '2408.TW', '2883.TW', '2603.TW'
    ],
    "💻 半導體與電子零組件": [
        '2330.TW', '2454.TW', '3711.TW', '3034.TW', '2379.TW', '3661.TW', '3443.TW', '3035.TW', '3006.TW', '2344.TW',
        '2303.TW', '2337.TW', '6770.TW', '6415.TW', '8046.TW', '8299.TW', '6239.TW', '3529.TW', '3227.TW', '3105.TW',
        '4961.TW', '2409.TW', '3481.TW', '4958.TW', '5269.TW', '2449.TW', '6271.TW', '3042.TW', '8069.TW', '6147.TW'
    ],
    "🤖 AI 伺服器與電腦周邊": [
        '2317.TW', '3231.TW', '2382.TW', '6669.TW', '2356.TW', '2376.TW', '2357.TW', '2301.TW', '3017.TW', '3706.TW',
        '2324.TW', '2421.TW', '2353.TW', '4938.TW', '3533.TW', '5274.TW', '6117.TW', '8112.TW', '8114.TW', '2465.TW',
        '2395.TW', '2498.TW', '3583.TW', '5215.TW', '3653.TW', '3694.TW', '6214.TW', '3321.TW', '6205.TW', '2377.TW'
    ],
    "🚢 航運/塑化/傳產": [
        '2603.TW', '2609.TW', '2615.TW', '2618.TW', '2610.TW', '2637.TW', '2605.TW', '2606.TW', '5608.TW', '2636.TW',
        '1301.TW', '1303.TW', '1326.TW', '1304.TW', '1308.TW', '1305.TW', '1314.TW', '1710.TW', '1717.TW', '1722.TW',
        '2002.TW', '2014.TW', '2006.TW', '2027.TW', '2031.TW', '2105.TW', '2106.TW', '1101.TW', '1102.TW', '1605.TW'
    ],
    "💰 金融保險": [
        '2881.TW', '2882.TW', '2886.TW', '2891.TW', '2884.TW', '2892.TW', '2885.TW', '2880.TW', '2887.TW', '2883.TW',
        '2890.TW', '5880.TW', '2834.TW', '2888.TW', '2838.TW', '2809.TW', '2812.TW', '2845.TW', '2855.TW', '5871.TW',
        '5876.TW', '6005.TW', '2850.TW', '2852.TW', '2867.TW', '2820.TW', '2801.TW', '2816.TW', '2849.TW', '2851.TW'
    ]
}

# --- 2. 初始化 Session State (記憶體) ---
if 'watchlist' not in st.session_state:
    st.session_state.watchlist = ['2330.TW', '2317.TW'] # 預設

# --- 3. 核心運算函數 (優化版：批次下載) ---
@st.cache_data(ttl=300)
def analyze_stock_batch(ticker_list):
    results = []
    
    # 使用 yfinance 批次下載功能 (大幅加速)
    # threads=True 開啟多執行緒
    try:
        data = yf.download(ticker_list, period="3mo", group_by='ticker', threads=True, progress=False)
    except Exception as e:
        st.error(f"下載數據時發生錯誤: {e}")
        return pd.DataFrame()

    total_stocks = len(ticker_list)
    
    # 遍歷每一支股票
    for i, ticker in enumerate(ticker_list):
        try:
            # 處理 yfinance 多層索引資料結構
            # 如果只有一支股票，結構會不同，需要防呆
            if len(ticker_list) == 1:
                df = data
            else:
                # 取得該股票的 DataFrame，如果全是 NaN 則跳過
                df = data[ticker].dropna(how='all')

            if len(df) < 20: continue # 資料不足

            # 取出收盤價與成交量 Series，並移除 NaN
            close = df['Close'].dropna()
            volume = df['Volume'].dropna()
            
            if close.empty or volume.empty: continue

            # --- 計算指標 ---
            current_price = close.iloc[-1]
            prev_price = close.iloc[-2]
            change_pct = (current_price - prev_price) / prev_price * 100
            
            # 均線
            ma5 = close.rolling(5).mean().iloc[-1]
            ma10 = close.rolling(10).mean().iloc[-1]
            ma20 = close.rolling(20).mean().iloc[-1]
            
            # 成交量
            vol_current = volume.iloc[-1]
            vol_avg_10 = volume.rolling(10).mean().iloc[-1]
            vol_ratio = vol_current / vol_avg_10 if vol_avg_10 > 0 else 0
            
            # RSI
            delta = close.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs)).iloc[-1] if not rs.empty else 50

            # --- 六大條件判定 ---
            c1 = current_price > ma20            # 站上月線
            c2 = change_pct > 0                  # 今日上漲
            c3 = vol_current > 1000 * 1000       # 量 > 1000張 (yfinance單位是股)
            c4 = vol_ratio > 1.2                 # 量能放大
            c5 = 50 < rsi < 80                   # RSI 強勢區
            c6 = (ma5 > ma10) and (ma10 > ma20)  # 均線多頭排列

            score = sum([c1, c2, c3, c4, c5, c6])

            results.append({
                '代號': ticker,
                '價格': round(float(current_price), 2),
                '漲跌幅(%)': round(float(change_pct), 2),
                '成交量(張)': int(vol_current / 1000),
                '量比(倍)': round(float(vol_ratio), 2),
                'RSI': round(float(rsi), 2),
                '符合條件數': int(score),
                '多頭排列': "✅" if c6 else "❌",
                '站上月線': "✅" if c1 else "❌"
            })
            
        except Exception as e:
            continue
            
    return pd.DataFrame(results)

# --- 4. 介面佈局 ---
tab1, tab2 = st.tabs(["🔍 類股分批篩選", "📋 我的自選股"])

# ==========================================
# 分頁 1: 分批篩選
# ==========================================
with tab1:
    st.markdown("### Step 1: 選擇要掃描的板塊")
    
    # 下拉選單：選擇批次
    selected_sector = st.selectbox(
        "請選擇類股 (分批掃描以提升速度)", 
        list(STOCK_SECTORS.keys())
    )
    
    target_stocks = STOCK_SECTORS[selected_sector]
    st.info(f"即將掃描 **{selected_sector}** 共 {len(target_stocks)} 檔股票")
    
    if st.button("🚀 開始分析", key="btn_scan"):
        with st.spinner(f"正在下載並計算 {selected_sector} 數據..."):
            df_result = analyze_stock_batch(target_stocks)
            
            if not df_result.empty:
                # 篩選邏輯：顯示符合條件數 >= 3 的股票，並排序
                filtered_df = df_result[df_result['符合條件數'] >= 3].sort_values(
                    by=['符合條件數', '量比(倍)'], ascending=False
                )
                top_10 = filtered_df.head(10)
                
                st.success(f"掃描完成！找到 {len(top_10)} 檔潛力股 (顯示前 10 名)")
                
                # 顯示結果表頭
                cols_header = st.columns([1.2, 1, 1.2, 1, 1, 1, 1.5])
                headers = ["代號", "價格", "漲跌", "量比", "RSI", "條件數", "操作"]
                for col, h in zip(cols_header, headers):
                    col.markdown(f"**{h}**")
                st.divider()

                # 顯示每一行
                for index, row in top_10.iterrows():
                    cols = st.columns([1.2, 1, 1.2, 1, 1, 1, 1.5])
                    
                    # 顏色
                    color = "red" if row['漲跌幅(%)'] > 0 else "green"
                    
                    cols[0].write(row['代號'])
                    cols[1].write(f"{row['價格']}")
                    cols[2].markdown(f":{color}[{row['漲跌幅(%)']}%]")
                    cols[3].write(f"{row['量比(倍)']}x")
                    cols[4].write(f"{row['RSI']}")
                    cols[5].write(f"⭐ {row['符合條件數']}")
                    
                    # 按鈕邏輯
                    if row['代號'] in st.session_state.watchlist:
                        cols[6].write("✅ 已加入")
                    else:
                        if cols[6].button("➕ 加入", key=f"add_{row['代號']}"):
                            st.session_state.watchlist.append(row['代號'])
                            st.rerun()
            else:
                st.warning("無法取得資料，請稍後再試。")

# ==========================================
# 分頁 2: 自選股管理
# ==========================================
with tab2:
    st.markdown("### 📋 自選股監控儀表板")
    
    # 增加手動輸入功能
    c1, c2 = st.columns([3, 1])
    input_ticker = c1.text_input("手動輸入代號 (如 2603.TW)")
    if c2.button("新增股票") and input_ticker:
        if input_ticker not in st.session_state.watchlist:
            st.session_state.watchlist.append(input_ticker)
            st.rerun()
            
    st.divider()

    if st.session_state.watchlist:
        # 取得自選股最新資料 (使用同樣的函式，方便快速)
        with st.spinner("正在更新自選股報價..."):
            df_watch = analyze_stock_batch(st.session_state.watchlist)
            
            if not df_watch.empty:
                # 整理顯示欄位，符合您的需求
                display_cols = ['代號', '價格', '漲跌幅(%)', '成交量(張)', '量比(倍)', 
                                'RSI', '符合條件數', '多頭排列', '站上月線']
                
                final_df = df_watch[display_cols].set_index('代號')
                
                # 互動式表格
                st.dataframe(
                    final_df.style.map(lambda x: 'color: red' if x > 0 else 'color: green', subset=['漲跌幅(%)']),
                    use_container_width=True
                )
                
                # 刪除功能
                st.markdown("#### 🗑️ 移除股票")
                to_remove = st.selectbox("選擇要刪除的股票", st.session_state.watchlist)
                if st.button("確認移除"):
                    st.session_state.watchlist.remove(to_remove)
                    st.rerun()
            else:
                st.error("目前無法取得自選股報價")
    else:
        st.info("目前沒有自選股，請去「分析區」挑選！")
