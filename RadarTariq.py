# -*- coding: utf-8 -*-
"""
==================================================================================================
                 🇸🇦 TASI QUANT RADAR PRO - STREAMLIT WEB VERSION 🇸🇦
==================================================================================================
Supervisor: Abdullah (Stocks Radar Project Director)
Architecture: Streamlit Web Interface (Simplified - No Playwright)
Market Target: Saudi Stock Exchange (TASI - 238 Assets & Sector Indices)
==================================================================================================
FIX: Removed Playwright dependency for Streamlit Cloud compatibility
FIX: Fixed Python 3.14 compatibility issues
==================================================================================================
"""

import json
import math
import time
import asyncio
import logging
import datetime
import threading
import os
import sys
import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
import yfinance as yf
import streamlit as st

# ================================================================================================
# ⚙️ SYSTEM CORE ENVIRONMENT VARIABLES & CONSTANTS DEFINITION
# ================================================================================================

TELEGRAM_TOKEN = "5565126065:AAGsitmuhrNXZeciIeK9kS_m2wLC63GN21U"
CHAT_ID = "-1003863061290"
TOPIC_ID = "2"
ADMIN_ID = 1374850835

# Storage Node Filenames
SUBSCRIBERS_FILE = "tasi_radar_subscribers_v3.json"
SETTINGS_FILE = "tasi_radar_settings_v3.json"
PORTFOLIO_FILE = "tasi_radar_portfolios_v3.json"
SYSTEM_LOG_FILE = "tasi_radar_system_core.log"

# Engine State Controllers - Default values
DEFAULT_RADAR_ACTIVE = True
DEFAULT_PUBLIC_MODE = False
DEFAULT_SUBSCRIBERS = []

# ================================================================================================
# 📜 LOGGING CONFIGURATION
# ================================================================================================

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TasiRadarPro")

stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(logging.Formatter('%(asctime)s - [%(levelname)s] - %(message)s'))
logger.addHandler(stream_handler)

logger.info("Initializing TASI Quant Radar Engine v3.8.1 Streamlit Edition...")

# ================================================================================================
# 📂 DISK PERSISTENCE & DATA STORAGE
# ================================================================================================

def load_system_storage_matrices():
    """Loads system core variables from localized json nodes."""
    logger.info("Loading system localized metadata storage matrices...")
    
    subscribers = []
    radar_active = DEFAULT_RADAR_ACTIVE
    public_mode = DEFAULT_PUBLIC_MODE
    
    if os.path.exists(SUBSCRIBERS_FILE):
        try:
            with open(SUBSCRIBERS_FILE, "r", encoding="utf-8") as file_node:
                raw_data = json.load(file_node)
                subscribers = [int(user_id) for user_id in raw_data]
                logger.info(f"Loaded {len(subscribers)} authorized premium users.")
        except Exception as error:
            logger.error(f"Error loading subscribers: {error}")
            subscribers = []
        
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as file_node:
                settings_node = json.load(file_node)
                radar_active = settings_node.get("RADAR_ACTIVE", True)
                public_mode = settings_node.get("PUBLIC_MODE", False)
                logger.info(f"System State -> Radar Active: {radar_active}, Public Access: {public_mode}")
        except Exception as error:
            logger.error(f"Error loading settings: {error}")
            radar_active = True
            public_mode = False
    
    return subscribers, radar_active, public_mode

def save_subscribers_to_disk(subscribers):
    """Saves subscribers to disk."""
    try:
        with open(SUBSCRIBERS_FILE, "w", encoding="utf-8") as file_node:
            json.dump(subscribers, file_node, ensure_ascii=False, indent=4)
            logger.debug("Subscribers saved successfully.")
    except Exception as error:
        logger.error(f"Failed to save subscribers: {error}")

def save_settings_to_disk(radar_active, public_mode):
    """Saves settings to disk."""
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as file_node:
            json.dump({"RADAR_ACTIVE": radar_active, "PUBLIC_MODE": public_mode}, 
                     file_node, ensure_ascii=False, indent=4)
            logger.debug("Settings saved successfully.")
    except Exception as error:
        logger.error(f"Failed to save settings: {error}")

# Load data
loaded_subscribers, loaded_radar_active, loaded_public_mode = load_system_storage_matrices()

# ================================================================================================
# 🎛️ STREAMLIT SESSION STATE
# ================================================================================================

if "RADAR_ACTIVE" not in st.session_state:
    st.session_state.RADAR_ACTIVE = loaded_radar_active
if "PUBLIC_MODE" not in st.session_state:
    st.session_state.PUBLIC_MODE = loaded_public_mode
if "SUBSCRIBERS" not in st.session_state:
    st.session_state.SUBSCRIBERS = loaded_subscribers

# ================================================================================================
# 🇸🇦 WATCHLIST (238 ASSETS)
# ================================================================================================

WATCHLIST = [
    "2222.SR", "2010.SR", "2020.SR", "2210.SR", "2310.SR", "2060.SR", "2090.SR", "2110.SR", 
    "2180.SR", "2250.SR", "2270.SR", "2280.SR", "2330.SR", "2350.SR", "2380.SR", "3001.SR", 
    "3002.SR", "3003.SR", "3004.SR", "3005.SR", "3010.SR", "3020.SR", "3030.SR", "3040.SR", 
    "3050.SR", "3060.SR", "3080.SR", "3090.SR", "1211.SR", "2002.SR", "2001.SR", "2030.SR", 
    "2050.SR", "2080.SR", "2120.SR", "2170.SR", "2200.SR", "2230.SR", "2240.SR", "2290.SR", 
    "2312.SR", "2320.SR", "2340.SR", "2360.SR", "2381.SR", "2382.SR", "3007.SR", "3008.SR", 
    "1320.SR", "1201.SR", "1010.SR", "1020.SR", "1030.SR", "1050.SR", "1060.SR", "1080.SR", 
    "1120.SR", "1140.SR", "1150.SR", "1180.SR", "1182.SR", "1183.SR", "2190.SR", "8312.SR", 
    "1111.SR", "1181.SR", "1322.SR", "1325.SR", "1327.SR", "1328.SR", "8010.SR", "8012.SR", 
    "8020.SR", "8030.SR", "8040.SR", "8050.SR", "8060.SR", "8070.SR", "8100.SR", "8120.SR", 
    "8150.SR", "8160.SR", "8170.SR", "8180.SR", "8190.SR", "8200.SR", "8210.SR", "8230.SR", 
    "8240.SR", "8250.SR", "8260.SR", "8270.SR", "8280.SR", "8300.SR", "8311.SR", "8110.SR", 
    "8220.SR", "8290.SR", "8310.SR", "8011.SR", "7010.SR", "7020.SR", "7030.SR", "7040.SR", 
    "7200.SR", "7201.SR", "7202.SR", "7203.SR", "4070.SR", "6020.SR", "7204.SR", "7205.SR", 
    "6004.SR", "4001.SR", "4002.SR", "4003.SR", "4004.SR", "4005.SR", "4006.SR", "4007.SR", 
    "4009.SR", "4011.SR", "4013.SR", "2070.SR", "4014.SR", "4015.SR", "4016.SR", "2281.SR", 
    "2282.SR", "6001.SR", "6002.SR", "2100.SR", "5110.SR", "2150.SR", "4061.SR", "4130.SR", 
    "4160.SR", "4170.SR", "4240.SR", "4260.SR", "4290.SR", "6012.SR", "6013.SR", "6014.SR", 
    "6015.SR", "4008.SR", "4161.SR", "4162.SR", "4163.SR", "4164.SR", "4171.SR", "4172.SR", 
    "4261.SR", "4262.SR", "5111.SR", "5112.SR", "4150.SR", "4220.SR", "4250.SR", "4300.SR", 
    "4321.SR", "4323.SR", "4330.SR", "4331.SR", "4333.SR", "4335.SR", "4336.SR", "4337.SR", 
    "4338.SR", "4339.SR", "4340.SR", "4342.SR", "4344.SR", "4345.SR", "4346.SR", "4347.SR", 
    "4348.SR", "4320.SR", "4322.SR", "4325.SR", "4326.SR", "4327.SR", "4329.SR", "4341.SR", 
    "4343.SR", "4020.SR", "4030.SR", "4031.SR", "4040.SR", "4110.SR", "4140.SR", "4141.SR", 
    "4142.SR", "4180.SR", "4190.SR", "4191.SR", "4192.SR", "4200.SR", "4210.SR", "4230.SR", 
    "4270.SR", "1214.SR", "1301.SR", "1302.SR", "1303.SR", "1810.SR", "1820.SR", "1830.SR", 
    "1831.SR", "1832.SR", "1833.SR", "2040.SR", "2130.SR", "2140.SR", "4012.SR", "4050.SR", 
    "4080.SR", "4100.SR", "6040.SR", "6050.SR", "6060.SR", "6070.SR", "6090.SR", "7050.SR", 
    "1212.SR", "1213.SR", "1304.SR", "1321.SR", "1834.SR", "1835.SR", "4032.SR", "4090.SR", 
    "4143.SR", "4181.SR", "4211.SR", "4212.SR", "4231.SR", "4280.SR", "6011.SR", "4111.SR", 
    "4112.SR", "1210.SR", "1314.SR"
]

# Asset Name Mapping
ASSET_NAME_MAPPING = {
    "2222": "أرامكو السعودية", "2010": "سابك", "2020": "سافكو", "1120": "مصرف الراجحي",
    "1150": "مصرف الإنماء", "1180": "البنك الأهلي", "7010": "الاتصالات السعودية",
    "1010": "بنك الرياض", "1020": "بنك الجزيرة", "1050": "البنك السعودي الفرنسي",
    "1060": "البنك السعودي الأول", "1080": "العربي الوطني", "1140": "البلاد",
    "7020": "موبايلي", "7030": "زين السعودية", "4001": "أسواق عبدالله العثيم",
    "4002": "المواساة للرعاية الطبية", "4003": "إكسترا", "4190": "جرير",
    "1211": "معادن", "2280": "المراعي", "2350": "كيان السعودية",
    "2380": "بترورابغ", "2310": "سبكيم العالمية", "2210": "نماء للكيماويات",
    "2060": "التصنيع الوطنية", "2090": "الجوف للجبس", "2110": "الخزف السعودي",
    "2180": "فيبكو", "2250": "المجموعة السعودية", "2270": "سدافكو",
    "2330": "متقدمة", "3001": "أسمنت حائل الكبرى", "3010": "أسمنت العربية",
    "3020": "أسمنت اليمامة", "3030": "أسمنت السعودية", "3040": "أسمنت القصيم",
    "3050": "أسمنت الجنوبية", "3060": "أسمنت ينبع", "3080": "أسمنت الشرقية",
    "3090": "أسمنت تبوك", "8010": "بوبا العربية", "8012": "التعاونية",
    "8020": "ملاذ للتأمين", "8030": "ميدغلف للتأمين", "8040": "أليانز إس إف",
    "8050": "سلامة", "8060": "ولاء للتأمين", "8070": "الدرع العربي",
    "8100": "سايكو", "8120": "اتحاد الخليج الأهلية", "8150": "أسيج",
    "8160": "التأمين العربية", "8170": "الاتحاد للتأمين", "8180": "الصقر للتأمين",
    "8190": "المتحدة للتأمين", "8200": "إعادة السعودية", "8210": "بوان",
    "8230": "الراجحي للتأمين", "8240": "تشب للتأمين", "8250": "أكسا التعاونية",
    "8260": "خليجية عامة", "8270": "بروج للتأمين", "8280": "العالمية للتأمين",
    "8300": "أمانة للتأمين", "8311": "عناية", "7200": "علم",
    "1182": "أملاك العالمية", "4321": "المراكز العربية", "1301": "أسمنت حائل",
    "1302": "أسمنت المدينة", "1303": "أسمنت أم القرى", "1304": "أسمنت الجوف",
    "4011": "لازوردي", "4013": "دكتور سليمان الحبيب", "2070": "الدوائية",
    "4130": "البابطين", "4150": "التعمير", "4180": "مجموعة فتيحي",
    "4200": "الدريس", "4220": "إعمار", "4250": "جبل عمر",
    "4260": "بدجت السعودية", "4300": "دار الأركان", "6001": "حلواني إخوان",
    "6011": "نادك", "2150": "الراجحي", "2190": "سوليدرتي",
    "4020": "الوطنية", "4030": "أبوقير", "4040": "النقل الجماعي",
    "4050": "السعودية للكهرباء", "4080": "الغاز", "4100": "المواساة",
    "4140": "المتقدمة", "4141": "المتقدمة", "4142": "المتقدمة",
}

def resolve_asset_arabic_name(ticker_symbol):
    """Maps standard financial symbol code to Arabic text."""
    clean_code = ticker_symbol.split('.')[0] if '.' in ticker_symbol else ticker_symbol
    return ASSET_NAME_MAPPING.get(clean_code, f"سهم تداولي ({clean_code})")

# ================================================================================================
# 🔬 QUANTITATIVE COMPUTATION ENGINE
# ================================================================================================

def calculate_advanced_quantitative_confluence(df_daily, df_weekly):
    """Executes vectorized calculations over pricing tensors."""
    try:
        if df_daily is None or df_weekly is None or df_daily.empty or df_weekly.empty:
            return None
        if len(df_daily) < 35 or len(df_weekly) < 12:
            return None

        close_daily = df_daily['Close'].squeeze().to_numpy()
        high_daily = df_daily['High'].squeeze().to_numpy()
        low_daily = df_daily['Low'].squeeze().to_numpy()
        volume_daily = df_daily['Volume'].squeeze().to_numpy()
        close_weekly = df_weekly['Close'].squeeze().to_numpy()

        current_price = float(close_daily[-1])
        if math.isnan(current_price) or current_price <= 0:
            return None

        pd_close = pd.Series(close_daily)
        pd_high = pd.Series(high_daily)
        pd_low = pd.Series(low_daily)

        # ATR
        tr_elements_1 = pd_high - pd_low
        tr_elements_2 = (pd_high - pd_close.shift(1)).abs()
        tr_elements_3 = (pd_low - pd_close.shift(1)).abs()
        true_range = pd.concat([tr_elements_1, tr_elements_2, tr_elements_3], axis=1).max(axis=1)
        atr_series = true_range.rolling(window=14, min_periods=1).mean().to_numpy()
        atr_value = float(atr_series[-1]) if not math.isnan(atr_series[-1]) else (current_price * 0.025)

        # EMAs
        ema20_series = pd_close.ewm(span=20, adjust=False).mean().to_numpy()
        ema50_series = pd_close.ewm(span=50, adjust=False).mean().to_numpy()
        ema20_current = float(ema20_series[-1])
        ema50_current = float(ema50_series[-1])

        # RSI Daily
        delta_daily = pd_close.diff()
        gain_daily = delta_daily.where(delta_daily > 0, 0.0)
        loss_daily = (-delta_daily).where(delta_daily < 0, 0.0)
        avg_gain_d = gain_daily.rolling(window=14, min_periods=14).mean().to_numpy()
        avg_loss_d = loss_daily.rolling(window=14, min_periods=14).mean().to_numpy()
        
        if avg_loss_d[-1] == 0:
            rsi_daily = 100.0
        else:
            rs_d = avg_gain_d[-1] / avg_loss_d[-1]
            rsi_daily = 100.0 - (100.0 / (1.0 + rs_d))

        # RSI Weekly
        pd_close_w = pd.Series(close_weekly)
        delta_weekly = pd_close_w.diff()
        gain_weekly = delta_weekly.where(delta_weekly > 0, 0.0)
        loss_weekly = (-delta_weekly).where(delta_weekly < 0, 0.0)
        avg_gain_w = gain_weekly.rolling(window=14, min_periods=14).mean().to_numpy()
        avg_loss_w = loss_weekly.rolling(window=14, min_periods=14).mean().to_numpy()
        
        if avg_loss_w[-1] == 0:
            rsi_weekly = 50.0
        else:
            rs_w = avg_gain_w[-1] / avg_loss_w[-1]
            rsi_weekly = 100.0 - (100.0 / (1.0 + rs_w))

        # Bollinger Bands
        std20_series = pd_close.rolling(window=20).std().to_numpy()
        ma20_series = pd_close.rolling(window=20).mean().to_numpy()
        bb_upper_envelope = float(ma20_series[-1] + (std20_series[-1] * 2.0))
        bb_lower_envelope = float(ma20_series[-1] - (std20_series[-1] * 2.0))

        # MACD
        ema12_series = pd_close.ewm(span=12, adjust=False).mean()
        ema26_series = pd_close.ewm(span=26, adjust=False).mean()
        macd_line = (ema12_series - ema26_series).to_numpy()
        signal_line = pd.Series(macd_line).ewm(span=9, adjust=False).mean().to_numpy()
        macd_current = float(macd_line[-1])
        signal_current = float(signal_line[-1])
        macd_histogram_current = macd_current - signal_current

        # Fib levels
        lookback_window = min(len(high_daily), 45)
        highest_resistance_bound = float(np.max(high_daily[-lookback_window:]))
        lowest_support_bound = float(np.min(low_daily[-lookback_window:]))
        total_structural_range = highest_resistance_bound - lowest_support_bound
        fib_golden_ratio_618 = highest_resistance_bound - (total_structural_range * 0.618)

        # Volume
        volume_ma20 = pd.Series(volume_daily).rolling(window=20).mean().to_numpy()
        current_volume = float(volume_daily[-1])
        average_volume_20d = float(volume_ma20[-1]) if not math.isnan(volume_ma20[-1]) else 1.0
        volume_acceleration_ratio = current_volume / average_volume_20d if average_volume_20d > 0 else 1.0

        # Scoring
        scoring_confluence_index = 0
        structural_reasons = []
        
        if current_price > ema20_current:
            scoring_confluence_index += 15
        if ema20_current > ema50_current:
            scoring_confluence_index += 10
        if macd_current > signal_current:
            scoring_confluence_index += 15
        if macd_current > 0:
            scoring_confluence_index += 10
        if 42 <= rsi_daily <= 68:
            scoring_confluence_index += 20
        elif rsi_daily < 35:
            scoring_confluence_index += 15
        if volume_acceleration_ratio >= 1.5:
            scoring_confluence_index += 15
            structural_reasons.append("تسارع حجم التداول")
        if rsi_weekly > 52:
            scoring_confluence_index += 15

        # Trade levels
        calculated_entry_lower_bound = current_price - (atr_value * 0.4)
        calculated_entry_upper_bound = current_price
        calculated_target_zone_1 = current_price + (atr_value * 1.618)
        calculated_target_zone_2 = current_price + (atr_value * 2.618)
        calculated_stop_loss_level = max(current_price - (atr_value * 1.5), current_price * 0.90)
        calculated_capital_averaging_pool = lowest_support_bound if lowest_support_bound < current_price else current_price - (atr_value * 2.5)

        # Decision
        decision_label = "⚠️ الانتظار ومراقبة سلوك السعر"
        strategy_classification = "خارج النطاق الاستراتيجي"
        risk_profile_label = "⚪️ غير محدد"
        probability_success_percentage = 40
        
        if current_price >= bb_upper_envelope * 0.97 and rsi_daily >= 58 and macd_histogram_current > 0 and volume_acceleration_ratio >= 1.3:
            decision_label = "✅ مناسب للدخول الفوري القوي"
            strategy_classification = "⚡️ مضاربة سريعة"
            risk_profile_label = "🔴 عالية"
            probability_success_percentage = int(min(92, 75 + (volume_acceleration_ratio * 4)))
            structural_reasons.append("اختراق بولينجر مع زخم")
        elif current_price > ema20_current and current_price > ema50_current and (46 <= rsi_daily <= 65) and macd_current > 0:
            decision_label = "✅ مناسب للدخول الآمن"
            strategy_classification = "📈 استثمار متوسط الأجل"
            risk_profile_label = "🟡 متوسطة"
            probability_success_percentage = 85
            structural_reasons.append("استقرار فوق المتوسطات")
        elif (rsi_daily < 38 or current_price <= bb_lower_envelope * 1.03) and current_price >= fib_golden_ratio_618 * 0.97:
            decision_label = "✅ مناسب للدخول (اقتناص قيعان)"
            strategy_classification = "🎯 سوينق"
            risk_profile_label = "🟢 منخفضة"
            probability_success_percentage = 89
            structural_reasons.append(f"مناطق تشبع بيعي RSI: {round(rsi_daily,1)}")
        else:
            decision_label = "❌ تجنب الدخول"
            strategy_classification = "تحت ضغط التصحيح"
            risk_profile_label = "❌ خطورة قصوى"
            probability_success_percentage = 20
            structural_reasons.append("غياب التدفقات الإيجابية")

        if not structural_reasons:
            structural_reasons.append("تذبذب ضمن نطاقات التجميع")

        suggested_capital_allocation_pct = 10.0
        if "منخفضة" in risk_profile_label:
            suggested_capital_allocation_pct = 15.0
        elif "عالية" in risk_profile_label:
            suggested_capital_allocation_pct = 5.0
        elif "❌" in risk_profile_label:
            suggested_capital_allocation_pct = 0.0

        return {
            "current_price": round(current_price, 2),
            "decision": decision_label,
            "strategy": strategy_classification,
            "risk_level": risk_profile_label,
            "success_rate": f"{probability_success_percentage}%",
            "confluence_score": scoring_confluence_index,
            "reasons": " + ".join(structural_reasons),
            "entry_zone": f"{round(calculated_entry_lower_bound, 2)} - {round(calculated_entry_upper_bound, 2)}",
            "target_1": round(calculated_target_zone_1, 2),
            "target_2": round(calculated_target_zone_2, 2),
            "stop_loss": round(calculated_stop_loss_level, 2),
            "averaging_zone": round(calculated_capital_averaging_pool, 2),
            "rsi_d": round(rsi_daily, 1),
            "rsi_w": round(rsi_weekly, 1),
            "atr": round(atr_value, 2),
            "volume_ratio": round(volume_acceleration_ratio, 2),
            "allocation_pct": suggested_capital_allocation_pct
        }
    except Exception as error:
        logger.error(f"Error in calculations: {error}")
        return None

# ================================================================================================
# 🌐 DATA FETCHING FUNCTIONS
# ================================================================================================

def fetch_single_asset_data(asset_code):
    """Fetches historical data for a single asset."""
    try:
        if not asset_code.endswith(".SR"):
            asset_code += ".SR"
        
        daily_df = yf.download(asset_code, period="90d", interval="1d", progress=False, auto_adjust=True)
        weekly_df = yf.download(asset_code, period="2y", interval="1wk", progress=False, auto_adjust=True)
        
        if daily_df.empty or len(daily_df) < 35 or weekly_df.empty or len(weekly_df) < 12:
            return None, None
        
        return daily_df, weekly_df
    except Exception as error:
        logger.error(f"Error fetching data for {asset_code}: {error}")
        return None, None

def fetch_bulk_data(ticker_list, period_d="90d", period_w="2y"):
    """Fetches bulk data for multiple assets."""
    try:
        daily_df = yf.download(tickers=ticker_list, period=period_d, interval="1d", 
                              group_by="ticker", progress=False, auto_adjust=True)
        weekly_df = yf.download(tickers=ticker_list, period=period_w, interval="1wk", 
                               group_by="ticker", progress=False, auto_adjust=True)
        return daily_df, weekly_df
    except Exception as error:
        logger.error(f"Error fetching bulk data: {error}")
        return pd.DataFrame(), pd.DataFrame()

def generate_market_status():
    """Generates market status report."""
    try:
        df = yf.download("^TASI.SR", period="5d", progress=False, auto_adjust=True)
        
        if df.empty or len(df) < 2:
            df = yf.download("2222.SR", period="5d", progress=False, auto_adjust=True)
            if df.empty or len(df) < 2:
                return "❌ تعذر الاتصال بسيرفرات البيانات"
            
            close = df['Close'].squeeze()
            current = round(float(close.iloc[-1]), 2)
            previous = round(float(close.iloc[-2]), 2)
            change = round(current - previous, 2)
            pct = round((change / previous) * 100, 2)
            emoji = "🟢" if change >= 0 else "🔴"
            
            return f"📊 *تقرير السوق (أرامكو)* 📊\n\n📌 السعر: `{current}` ر.س\n📈 التغير: {emoji} `{change}` ({pct}%)"

        close = df['Close'].squeeze()
        current = round(float(close.iloc[-1]), 2)
        previous = round(float(close.iloc[-2]), 2)
        change = round(current - previous, 2)
        pct = round((change / previous) * 100, 2)
        emoji = "🟢" if change >= 0 else "🔴"
        
        return f"📊 *تقرير سوق تاسي* 📊\n\n📌 المؤشر: `{current}`\n📈 التغير: {emoji} `{change}` ({pct}%)"
    except Exception as error:
        return f"❌ خطأ: {str(error)}"

def run_investment_sweep():
    """Runs investment sweep across all stocks."""
    candidates = []
    daily_tensor, weekly_tensor = fetch_bulk_data(WATCHLIST)
    
    if daily_tensor.empty or weekly_tensor.empty:
        return "❌ فشل في جلب البيانات"
    
    for ticker in WATCHLIST:
        try:
            if ticker not in daily_tensor.columns.levels[0]:
                continue
            
            daily_df = daily_tensor[ticker].dropna(subset=['Close'])
            weekly_df = weekly_tensor[ticker].dropna(subset=['Close'])
            
            if len(daily_df) < 35 or len(weekly_df) < 12:
                continue
            
            result = calculate_advanced_quantitative_confluence(daily_df, weekly_df)
            
            if result and "✅" in result["decision"]:
                code = ticker.split('.')[0]
                candidates.append({
                    "code": code,
                    "name": resolve_asset_arabic_name(ticker),
                    "price": result["current_price"],
                    "success": result["success_rate"],
                    "score": result["confluence_score"],
                    "target1": result["target_1"],
                    "target2": result["target_2"],
                    "stop": result["stop_loss"],
                    "strategy": result["strategy"]
                })
        except:
            continue
    
    if not candidates:
        return "ℹ️ لا توجد فرص استثمارية حالياً"
    
    sorted_candidates = sorted(candidates, key=lambda x: x["score"], reverse=True)[:5]
    
    report = "🎯 *الفرص الاستثمارية المستخرجة* 🎯\n\n"
    for i, asset in enumerate(sorted_candidates, 1):
        report += f"*{i}. {asset['name']} ({asset['code']})*\n"
        report += f"💰 السعر: {asset['price']} ر.س | 🎯 الهدف: {asset['target1']}\n"
        report += f"📊 النجاح: {asset['success']} | درجة: {asset['score']}/100\n\n"
    
    return report

# ================================================================================================
# 🎨 STREAMLIT WEB INTERFACE
# ================================================================================================

st.set_page_config(
    page_title="🇸🇦 TASI Radar Pro",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {font-size: 2.5rem; font-weight: bold; color: #1f77b4; text-align: center; margin-bottom: 1rem;}
    .success-box {background-color: #d4edda; border: 1px solid #c3e6cb; border-radius: 5px; padding: 10px; margin: 10px 0;}
    .warning-box {background-color: #fff3cd; border: 1px solid #ffeeba; border-radius: 5px; padding: 10px; margin: 10px 0;}
    .danger-box {background-color: #f8d7da; border: 1px solid #f5c6cb; border-radius: 5px; padding: 10px; margin: 10px 0;}
    .stButton button {width: 100%; border-radius: 5px; font-weight: bold;}
</style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("## 🇸🇦 نظام رادار تاسي")
    st.markdown("### الإصدار 3.8.1")
    st.markdown("---")
    
    st.markdown("### 📊 حالة النظام")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("الرادار", "🟢 نشط" if st.session_state.RADAR_ACTIVE else "🔴 متوقف")
    with col2:
        st.metric("الوضع", "🔓 عام" if st.session_state.PUBLIC_MODE else "🔒 خاص")
    
    st.markdown("---")
    st.markdown("### 📈 إحصائيات")
    st.metric("عدد الأسهم", f"{len(WATCHLIST)}")
    st.metric("المشتركين", f"{len(st.session_state.SUBSCRIBERS)}")

# Main Header
st.markdown('<div class="main-header">🇸🇦 نظام رادار تاسي الكمي المتقدم</div>', unsafe_allow_html=True)

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(["📊 السوق", "🔍 تحليل سهم", "🎯 فحص استثماري", "⚙️ إدارة"])

# Tab 1: Market
with tab1:
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("### 📊 تقرير السوق")
        if st.button("🔄 تحديث"):
            with st.spinner("جاري التحديث..."):
                result = generate_market_status()
                st.markdown(result)
        else:
            st.info("اضغط على زر التحديث")
    with col2:
        st.markdown("### 🕒 أوقات التداول")
        st.markdown("""
        **أيام التداول:** الأحد - الخميس  
        **جلسة الصباح:** 10:00 ص - 12:00 م  
        **جلسة المساء:** 1:00 م - 3:20 م
        """)

# Tab 2: Single Stock
with tab2:
    st.markdown("### 🔍 تحليل سهم فردي")
    col1, col2 = st.columns([1, 3])
    
    with col1:
        stock_code = st.text_input("📈 رمز السهم (مثال: 1120)", value="1120")
        analyze_btn = st.button("🔍 تحليل", use_container_width=True)
    
    with col2:
        if analyze_btn and stock_code.isdigit() and len(stock_code) == 4:
            with st.spinner(f"جاري تحليل {stock_code}..."):
                daily_df, weekly_df = fetch_single_asset_data(stock_code)
                if daily_df is not None and weekly_df is not None:
                    result = calculate_advanced_quantitative_confluence(daily_df, weekly_df)
                    if result:
                        name = resolve_asset_arabic_name(stock_code)
                        st.markdown(f"### 📊 {name} ({stock_code})")
                        
                        if "✅" in result["decision"]:
                            st.markdown(f'<div class="success-box">✅ {result["decision"]}</div>', unsafe_allow_html=True)
                        elif "❌" in result["decision"]:
                            st.markdown(f'<div class="danger-box">❌ {result["decision"]}</div>', unsafe_allow_html=True)
                        else:
                            st.markdown(f'<div class="warning-box">⚠️ {result["decision"]}</div>', unsafe_allow_html=True)
                        
                        col_a, col_b, col_c = st.columns(3)
                        with col_a:
                            st.metric("💰 السعر", f"{result['current_price']} ر.س")
                            st.metric("📊 RSI يومي", result['rsi_d'])
                        with col_b:
                            st.metric("📈 الاستراتيجية", result['strategy'])
                            st.metric("📊 RSI أسبوعي", result['rsi_w'])
                        with col_c:
                            st.metric("🎯 النجاح", result['success_rate'])
                            st.metric("📊 المخاطرة", result['risk_level'])
                        
                        if "✅" in result["decision"]:
                            with st.expander("🎯 مستويات الصفقة", expanded=True):
                                col_x, col_y, col_z = st.columns(3)
                                with col_x:
                                    st.metric("🟢 نطاق الدخول", result['entry_zone'])
                                    st.metric("🛑 وقف الخسارة", f"{result['stop_loss']} ر.س")
                                with col_y:
                                    st.metric("🎯 الهدف الأول", f"{result['target_1']} ر.س")
                                    st.metric("🛠 منطقة التعديل", f"{result['averaging_zone']} ر.س")
                                with col_z:
                                    st.metric("🚀 الهدف الثاني", f"{result['target_2']} ر.س")
                                    st.metric("📊 درجة التوافق", f"{result['confluence_score']}/100")
                    else:
                        st.error("فشل تحليل السهم")
                else:
                    st.error("فشل جلب البيانات")
        else:
            st.info("أدخل رمز السهم (4 أرقام) واضغط تحليل")

# Tab 3: Investment Sweep
with tab3:
    st.markdown("### 🎯 فحص استثماري شامل")
    st.markdown(f"**عدد الأسهم:** {len(WATCHLIST)} شركة")
    
    if st.button("🚀 تشغيل الفحص", use_container_width=True):
        with st.spinner("⏳ جاري الفحص..."):
            result = run_investment_sweep()
            st.markdown(result)

# Tab 4: Management
with tab4:
    st.markdown("### ⚙️ إدارة النظام")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📋 المشتركين")
        st.markdown(f"**العدد:** {len(st.session_state.SUBSCRIBERS)}")
        
        if st.session_state.SUBSCRIBERS:
            for uid in st.session_state.SUBSCRIBERS:
                st.code(f"🆔 {uid}")
        
        st.markdown("---")
        st.markdown("#### ➕ إضافة مشترك")
        new_id = st.text_input("معرف المستخدم")
        if st.button("إضافة"):
            if new_id.isdigit():
                uid = int(new_id)
                if uid not in st.session_state.SUBSCRIBERS:
                    st.session_state.SUBSCRIBERS.append(uid)
                    save_subscribers_to_disk(st.session_state.SUBSCRIBERS)
                    st.success(f"✅ تم إضافة {uid}")
                    st.rerun()
                else:
                    st.warning("⚠️ موجود مسبقاً")
        
        st.markdown("#### ➖ حذف مشترك")
        del_id = st.text_input("معرف المستخدم للحذف", key="del")
        if st.button("حذف"):
            if del_id.isdigit():
                uid = int(del_id)
                if uid in st.session_state.SUBSCRIBERS:
                    st.session_state.SUBSCRIBERS.remove(uid)
                    save_subscribers_to_disk(st.session_state.SUBSCRIBERS)
                    st.success(f"✅ تم حذف {uid}")
                    st.rerun()
                else:
                    st.warning("⚠️ غير موجود")
    
    with col2:
        st.markdown("#### 🎛️ الإعدادات")
        
        st.markdown(f"**الرادار:** {'🟢 نشط' if st.session_state.RADAR_ACTIVE else '🔴 متوقف'}")
        btn1, btn2 = st.columns(2)
        with btn1:
            if st.button("🟢 تشغيل"):
                st.session_state.RADAR_ACTIVE = True
                save_settings_to_disk(st.session_state.RADAR_ACTIVE, st.session_state.PUBLIC_MODE)
                st.success("✅ تم التشغيل")
                st.rerun()
        with btn2:
            if st.button("🔴 إيقاف"):
                st.session_state.RADAR_ACTIVE = False
                save_settings_to_disk(st.session_state.RADAR_ACTIVE, st.session_state.PUBLIC_MODE)
                st.success("✅ تم الإيقاف")
                st.rerun()
        
        st.markdown("---")
        st.markdown(f"**الوضع:** {'🔓 عام' if st.session_state.PUBLIC_MODE else '🔒 خاص'}")
        btn3, btn4 = st.columns(2)
        with btn3:
            if st.button("🔓 عام"):
                st.session_state.PUBLIC_MODE = True
                save_settings_to_disk(st.session_state.RADAR_ACTIVE, st.session_state.PUBLIC_MODE)
                st.success("✅ تم التفعيل")
                st.rerun()
        with btn4:
            if st.button("🔒 خاص"):
                st.session_state.PUBLIC_MODE = False
                save_settings_to_disk(st.session_state.RADAR_ACTIVE, st.session_state.PUBLIC_MODE)
                st.success("✅ تم التفعيل")
                st.rerun()

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 20px;">
    <p>🇸🇦 نظام رادار تاسي الكمي - الإصدار 3.8.1</p>
    <p>المشرف: Abdullah (Stocks Radar Project Director)</p>
</div>
""", unsafe_allow_html=True)
