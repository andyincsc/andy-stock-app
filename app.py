import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# --- 頁面設定 ---
st.set_page_config(page_title="台股分批智慧掃描", layout="wide")
st.title("📊 台股分批智慧選股系統")

# --- 1. 定義股票名稱對照表 (手動維護以顯示中文) ---
# 為了讓介面顯示「台積電」而不是 "Taiwan Semiconductor"，我們建立一個對照字典
TICKER_NAME_MAP = {
    '2330.TW': '台積電', '2317.TW': '鴻海', '2454.TW': '聯發科', '2308.TW': '台達電', 
    '2303.TW': '聯電', '2881.TW': '富邦金', '2882.TW': '國泰金', '2886.TW': '兆豐金', 
    '2891.TW': '中信金', '2884.TW': '玉山金', '1301.TW': '台塑', '1303.TW': '南亞', 
    '2002.TW': '中鋼', '1216.TW': '統一', '2412.TW': '中華電', '3008.TW': '大立光', 
    '3045.TW': '台灣大', '2892.TW': '第一金', '2885.TW': '元大金', '2207.TW': '和泰車',
    '2357.TW': '華碩', '2880.TW': '華南金', '2887.TW': '台新金', '1101.TW': '台泥', 
    '2382.TW': '廣達', '2327.TW': '國巨', '2395.TW': '研華', '2408.TW': '南亞科', 
    '2883.TW': '開發金', '2603.TW': '長榮', '3711.TW': '日月光投控', '3034.TW': '聯詠',
    '2379.TW': '瑞昱', '3661.TW': '世芯-KY', '3443.TW': '創意', '3035.TW': '智原',
    '3006.TW': '晶豪科', '2344.TW': '華邦電', '2337.TW': '旺宏', '6770.TW': '力積電',
    '6415.TW': '矽力-KY', '8046.TW': '南電', '8299.TW': '群聯', '6239.TW': '力成',
    '3529.TW': '力旺', '3227.TW': '原相', '3105.TW': '穩懋', '4961.TW': '天鈺',
    '2409.TW': '友達', '3481.TW': '群創', '4958.TW': '臻鼎-KY', '5269.TW': '祥碩',
    '2449.TW': '京元電', '6271.TW': '同欣電', '3042.TW': '晶技', '8069.TW': '元太',
    '6147.TW': '頎邦', '3231.TW': '緯創', '6669.TW': '緯穎', '2356.TW': '英業達',
    '2376.TW': '技嘉', '2301.TW': '光寶科', '3017.TW': '奇鋐', '3706.TW': '神達',
    '2324.TW': '仁寶', '2421.TW': '建準', '2353.TW': '宏碁', '4938.TW': '和碩',
    '3533.TW': '嘉澤', '5274.TW': '信驊', '6117.TW': '迎廣', '8112.TW': '至上',
    '8114.TW': '振樺電', '2465.TW': '麗臺', '2498.TW': '宏達電', '3583.TW': '辛耘',
    '5215.TW': '科嘉-KY', '3653.TW': '健策', '3694.TW': '海華', '6214.TW': '精誠',
    '3321.TW': '同泰', '6205.TW': '詮欣', '2377.TW': '微星', '2609.TW': '陽明',
    '2615.TW': '萬海', '2618.TW': '長榮航', '2610.TW': '華航', '2637.TW': '慧洋-KY',
    '2605.TW': '新興', '2606.TW': '裕民', '5608.TW': '四維航', '2636.TW': '台驊投控',
    '1326.TW': '台化', '1304.TW': '台聚', '1308.TW': '亞聚', '1305.TW': '華夏',
    '1314.TW': '中石化', '1710.TW': '東聯', '1717.TW': '長興', '1722.TW': '台肥',
    '2014.TW': '中鴻', '2006.TW': '東和鋼鐵', '2027.TW': '大成鋼', '2031.TW': '新光鋼',
    '2105.TW': '正新', '2106.TW': '建大', '1102.TW': '亞泥', '1605.TW': '華新',
    '2890.TW': '永豐金', '5880.TW': '合庫金', '2834.TW': '臺企銀', '2888.TW': '新光金',
    '2838.TW': '聯邦銀', '2809.TW': '京城銀', '2812.TW': '台中銀', '2845.TW': '遠東銀',
    '2855.TW': '統一證', '5871.TW': '中租-KY', '5876.TW': '上海商銀', '6005.TW': '群益證',
    '2850.TW': '新產', '2852.TW': '第一保', '2867.TW': '三商壽', '2820.TW': '華票',
    '2801.TW': '彰銀', '2816.TW': '旺旺保', '2849.TW': '安泰銀', '2851.TW': '中再保'
}

# 輔助函式：取得股票中文名稱
def get_stock_name(ticker):
    return TICKER_NAME_MAP.get(ticker, ticker) # 如果找不到中文名，就回傳代號

# --- 2. 定義類股群組 ---
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

# --- 3. 初始化 Session State 與 Callbacks (修復按鈕問題) ---
if 'watchlist' not in st.session_state:
    st.session_state.watchlist = ['2330.TW', '2317.TW'] # 預設

# 初始化搜尋結果暫存 (新增這個變數)
if 'scan_results' not in st.session_state:
    st.session_state.scan_results = None

# 定義按鈕的回呼函數 (Callback)，這是修復按鈕無效的關鍵
def add_to_watchlist(ticker):
    if ticker not in st.session_state.watchlist:
        st.session_state.watchlist.append(ticker)
        # st.toast 可以在右下角跳出小提示
        st.toast(f"✅ 已成功加入 {get_stock_name(ticker)} ({ticker})")

def remove_from_watchlist(ticker):
    if ticker in st.session_state.watchlist:
        st.session_state.watchlist.remove(ticker)
        st.toast(f"🗑️ 已移除 {get_stock_name(ticker)}")

def add_manual_stock():
    # 用於自選區的手動輸入
    ticker = st.session_state.new_ticker_input
    if ticker:
        if ticker not in st.session_state.watchlist:
            st.session_state.watchlist.append(ticker)
            st.toast(f"✅ 已加入 {ticker}")
        else:
            st.toast("⚠️ 該股票已在清單中")
    # 清空輸入框
    st.session_state.new_ticker_input = ""

# --- 4. 核心運算函數 ---
@st.cache_data(ttl=300)
def analyze_stock_batch(ticker_list):
    results = []
    
    # 防呆：如果清單是空的，直接回傳空 DF
    if not ticker_list:
        return pd.DataFrame()

    try:
        data = yf.download(ticker_list, period="3mo", group_by='ticker', threads=True, progress=False)
    except Exception as e:
        st.error(f"下載數據時發生錯誤: {e}")
        return pd.DataFrame()

    for i, ticker in enumerate(ticker_list):
        try:
            if len(ticker_list) == 1:
                df = data
            else:
                df = data[ticker].dropna(how='all')

            if len(df) < 20: continue 

            close = df['Close'].dropna()
            volume = df['Volume'].dropna()
            
            if close.empty or volume.empty: continue

            # --- 計算指標 ---
            current_price = close.iloc[-1]
            prev_price = close.iloc[-2]
            change_pct = (current_price - prev_price) / prev_price * 100
            
            ma5 = close.rolling(5).mean().iloc[-1]
            ma10 = close.rolling(10).mean().iloc[-1]
            ma20 = close.rolling(20).mean().iloc[-1]
            
            vol_current = volume.iloc[-1]
            vol_avg_10 = volume.rolling(10).mean().iloc[-1]
            vol_ratio = vol_current / vol_avg_10 if vol_avg_10 > 0 else 0
            
            delta = close.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs)).iloc[-1] if not rs.empty else 50

            # --- 六大條件判定 ---
            c1 = current_price > ma20            
            c2 = change_pct > 0                  
            c3 = vol_current > 1000 * 1000       
            c4 = vol_ratio > 1.2                 
            c5 = 50 < rsi < 80                   
            c6 = (ma5 > ma10) and (ma10 > ma20)  

            score = sum([c1, c2, c3, c4, c5, c6])

            results.append({
                '代號': ticker,
                '名稱': get_stock_name(ticker), # 新增這一欄
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

# --- 5. 介面佈局 ---
tab1, tab2 = st.tabs(["🔍 類股分批篩選", "📋 我的自選股"])

# ==========================================
# 分頁 1: 分批篩選
# ==========================================
with tab1:
    st.markdown("### Step 1: 選擇要掃描的板塊")
    
    selected_sector = st.selectbox(
        "請選擇類股 (分批掃描以提升速度)", 
        list(STOCK_SECTORS.keys())
    )
    
    target_stocks = STOCK_SECTORS[selected_sector]
    
    # 修改：按鈕只負責「更新資料到記憶體」
    if st.button("🚀 開始分析", key="btn_scan"):
        with st.spinner(f"正在分析 {selected_sector}..."):
            df_result = analyze_stock_batch(target_stocks)
            
            if not df_result.empty:
                filtered_df = df_result[df_result['符合條件數'] >= 3].sort_values(
                    by=['符合條件數', '量比(倍)'], ascending=False
                )
                # 將結果存入 session_state
                st.session_state.scan_results = filtered_df.head(10)
            else:
                st.session_state.scan_results = pd.DataFrame()

    # 修改：顯示邏輯改為「只要記憶體有資料就顯示」，不依賴按鈕狀態
    if st.session_state.scan_results is not None:
        if not st.session_state.scan_results.empty:
            top_10 = st.session_state.scan_results
            
            st.success(f"掃描完成！找到 {len(top_10)} 檔潛力股 (顯示前 10 名)")
            
            # 調整欄位寬度以容納「名稱」
            cols_header = st.columns([1.2, 1.2, 1, 1.2, 1, 1, 1, 1.5])
            headers = ["代號", "名稱", "價格", "漲跌", "量比", "RSI", "條件數", "操作"]
            for col, h in zip(cols_header, headers):
                col.markdown(f"**{h}**")
            st.divider()

            for index, row in top_10.iterrows():
                cols = st.columns([1.2, 1.2, 1, 1.2, 1, 1, 1, 1.5])
                
                color = "red" if row['漲跌幅(%)'] > 0 else "green"
                
                cols[0].write(row['代號'])
                cols[1].write(row['名稱']) # 顯示名稱
                cols[2].write(f"{row['價格']}")
                cols[3].markdown(f":{color}[{row['漲跌幅(%)']}%]")
                cols[4].write(f"{row['量比(倍)']}x")
                cols[5].write(f"{row['RSI']}")
                cols[6].write(f"⭐ {row['符合條件數']}")
                
                # 按鈕修復：使用 on_click 回呼函數
                if row['代號'] in st.session_state.watchlist:
                    cols[7].write("✅ 已加入")
                else:
                    # 這裡的重點是 on_click=add_to_watchlist
                    cols[7].button(
                        "➕ 加入", 
                        key=f"add_{row['代號']}", 
                        on_click=add_to_watchlist, 
                        args=(row['代號'],)
                    )
        else:
            st.warning("無法取得資料，請稍後再試。")

# ==========================================
# 分頁 2: 自選股管理
# ==========================================
with tab2:
    st.markdown("### 📋 自選股監控儀表板")
    
    # 手動輸入區域
    c1, c2 = st.columns([3, 1])
    # 使用 key 來綁定 session_state
    c1.text_input("手動輸入代號 (如 2603.TW)", key="new_ticker_input")
    c2.button("新增股票", on_click=add_manual_stock)
            
    st.divider()

    if st.session_state.watchlist:
        with st.spinner("正在更新自選股報價..."):
            df_watch = analyze_stock_batch(st.session_state.watchlist)
            
            if not df_watch.empty:
                display_cols = ['代號', '名稱', '價格', '漲跌幅(%)', '成交量(張)', '量比(倍)', 
                                'RSI', '符合條件數', '多頭排列', '站上月線']
                
                final_df = df_watch[display_cols].set_index('代號')
                
                st.dataframe(
                    final_df.style.map(lambda x: 'color: red' if x > 0 else 'color: green', subset=['漲跌幅(%)']),
                    use_container_width=True
                )
                
                st.markdown("#### 🗑️ 移除股票")
                # 這裡使用列出按鈕的方式來刪除，比較直覺
                st.write("點擊下方按鈕移除股票：")
                remove_cols = st.columns(6)
                for i, ticker in enumerate(st.session_state.watchlist):
                    col_idx = i % 6
                    if remove_cols[col_idx].button(
                        f"刪除 {get_stock_name(ticker)}", 
                        key=f"del_{ticker}",
                        on_click=remove_from_watchlist,
                        args=(ticker,)
                    ):
                        pass # 邏輯都在 on_click 裡處理了
                
            else:
                st.error("目前無法取得自選股報價")
    else:
        st.info("目前沒有自選股，請去「分析區」挑選！")
