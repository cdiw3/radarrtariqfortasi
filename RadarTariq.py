# -*- coding: utf-8 -*-
"""
==================================================================================================
                 🇸🇦 TASI QUANT RADAR PRO SYSTEM - STREAMLIT WEB VERSION 🇸🇦
==================================================================================================
Supervisor: Abdullah (Stocks Radar Project Director)
Architecture: Streamlit Web Interface + Async Telegram Bot
Market Target: Saudi Stock Exchange (TASI - 238 Assets & Sector Indices)
==================================================================================================
FIX: Fixed global variable issues using st.session_state
FIX: Added proper session state management
==================================================================================================
"""
import subprocess
import sys

def install_packages():
    """تثبيت المتطلبات تلقائياً"""
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", 
            "--upgrade", "pip", "setuptools", "wheel"
        ])
        subprocess.check_call([
            sys.executable, "-m", "pip", "install",
            "streamlit", "yfinance", "pandas", "numpy",
            "aiohttp", "aiofiles", "playwright", "nest-asyncio"
        ])
        subprocess.check_call(["playwright", "install", "chromium"])
        print("✅ تم تثبيت جميع المتطلبات بنجاح!")
    except Exception as e:
        print(f"⚠️ خطأ في التثبيت: {e}")

# شغل التثبيت
install_packages()
import os
import sys
import json
import math
import time
import asyncio
import logging
import datetime
import threading
import nest_asyncio
from logging.handlers import RotatingFileHandler
import numpy as np
import pandas as pd
import yfinance as yf
import aiohttp
import aiofiles
import streamlit as st
from playwright.async_api import async_playwright

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
MARKET_CACHE_FILE = "tasi_market_cache_v3.json"
SYSTEM_LOG_FILE = "tasi_radar_system_core.log"

# Engine State Controllers - Default values
DEFAULT_RADAR_ACTIVE = True
DEFAULT_PUBLIC_MODE = False
DEFAULT_SUBSCRIBERS = []

# Rate Limiting & Anti-Spam Matrices
SPAM_CONTROL_MAP = {}
PROCESSED_UPDATES_REGISTRY = set()
MAX_REGISTRY_SIZE = 5000
TELEGRAM_FLOOD_DELAY = 0.05

# Dynamic Scanning Cache
RADAR_HIT_CACHE = {}
CACHE_EXPIRY_INTERVAL = datetime.timedelta(hours=4)

# ================================================================================================
# 📜 ADVANCED LOGGING & AUDIT SUBSYSTEM CONFIGURATION
# ================================================================================================

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TasiRadarPro")

log_formatter = logging.Formatter(
    fmt='%(asctime)s - [%(levelname)s] - [%(filename)s:%(lineno)d] - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

file_handler = RotatingFileHandler(
    filename=SYSTEM_LOG_FILE,
    maxBytes=30 * 1024 * 1024,
    backupCount=10,
    encoding="utf-8"
)
file_handler.setFormatter(log_formatter)
logger.addHandler(file_handler)

stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(log_formatter)
logger.addHandler(stream_handler)

logger.info("Initializing TASI Quant Radar Engine v3.8.1 Streamlit Edition...")

# ================================================================================================
# 📂 DISK PERSISTENCE & DATA STORAGE ARCHITECTURE
# ================================================================================================

def load_system_storage_matrices():
    """Loads system core variables from localized json nodes during boot sequence."""
    logger.info("Loading system localized metadata storage matrices...")
    
    subscribers = []
    radar_active = DEFAULT_RADAR_ACTIVE
    public_mode = DEFAULT_PUBLIC_MODE
    portfolios = {}
    
    if os.path.exists(SUBSCRIBERS_FILE):
        try:
            with open(SUBSCRIBERS_FILE, "r", encoding="utf-8") as file_node:
                raw_data = json.load(file_node)
                subscribers = [int(user_id) for user_id in raw_data]
                logger.info(f"Loaded {len(subscribers)} authorized premium users into active matrix.")
        except Exception as error:
            logger.error(f"Critical error mapping subscribers JSON repository: {error}")
            subscribers = []
    else:
        subscribers = []
        
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as file_node:
                settings_node = json.load(file_node)
                radar_active = settings_node.get("RADAR_ACTIVE", True)
                public_mode = settings_node.get("PUBLIC_MODE", False)
                logger.info(f"System State Loaded -> Radar Active: {radar_active}, Public Access: {public_mode}")
        except Exception as error:
            logger.error(f"Critical error mapping system configurations file: {error}")
            radar_active = True
            public_mode = False
    else:
        radar_active = True
        public_mode = False
        
    if os.path.exists(PORTFOLIO_FILE):
        try:
            with open(PORTFOLIO_FILE, "r", encoding="utf-8") as file_node:
                portfolios = json.load(file_node)
                logger.info(f"Successfully structuralized {len(portfolios)} investor portfolio profiles.")
        except Exception as error:
            logger.error(f"Critical error mapping user capitals portfolio matrix: {error}")
            portfolios = {}
    else:
        portfolios = {}
    
    return subscribers, radar_active, public_mode, portfolios

# Load data
loaded_subscribers, loaded_radar_active, loaded_public_mode, loaded_portfolios = load_system_storage_matrices()

# ================================================================================================
# 🎛️ STREAMLIT SESSION STATE INITIALIZATION
# ================================================================================================

if "RADAR_ACTIVE" not in st.session_state:
    st.session_state.RADAR_ACTIVE = loaded_radar_active
if "PUBLIC_MODE" not in st.session_state:
    st.session_state.PUBLIC_MODE = loaded_public_mode
if "SUBSCRIBERS" not in st.session_state:
    st.session_state.SUBSCRIBERS = loaded_subscribers
if "PORTFOLIOS" not in st.session_state:
    st.session_state.PORTFOLIOS = loaded_portfolios

# Sync globals with session state
RADAR_ACTIVE = st.session_state.RADAR_ACTIVE
PUBLIC_MODE = st.session_state.PUBLIC_MODE
SUBSCRIBERS = st.session_state.SUBSCRIBERS
PORTFOLIOS = st.session_state.PORTFOLIOS

async def flush_subscribers_to_disk():
    """Asynchronously flushes premium subscriber tables down to non-volatile memory block."""
    try:
        async with aiofiles.open(SUBSCRIBERS_FILE, "w", encoding="utf-8") as file_handle:
            serialized_payload = json.dumps(st.session_state.SUBSCRIBERS, ensure_ascii=False, indent=4)
            await file_handle.write(serialized_payload)
            logger.debug("Premium subscriber table successfully synchronization flushed.")
    except Exception as error:
        logger.error(f"Failed to execute asynchronous flush on subscriber node: {error}")

async def flush_settings_to_disk():
    """Asynchronously flushes runtime engine environmental constraints to permanent file storage."""
    try:
        async with aiofiles.open(SETTINGS_FILE, "w", encoding="utf-8") as file_handle:
            payload = {
                "RADAR_ACTIVE": st.session_state.RADAR_ACTIVE, 
                "PUBLIC_MODE": st.session_state.PUBLIC_MODE
            }
            await file_handle.write(json.dumps(payload, ensure_ascii=False, indent=4))
            logger.debug("System operational global settings synchronized on disk.")
    except Exception as error:
        logger.error(f"Failed to execute asynchronous flush on settings node: {error}")

async def flush_portfolios_to_disk():
    """Asynchronously structuralizes user assets, buys, and capital allocations to persistent registry."""
    try:
        async with aiofiles.open(PORTFOLIO_FILE, "w", encoding="utf-8") as file_handle:
            serialized_payload = json.dumps(st.session_state.PORTFOLIOS, ensure_ascii=False, indent=4)
            await file_handle.write(serialized_payload)
            logger.debug("User assets portfolio maps updated across flash hardware blocks.")
    except Exception as error:
        logger.error(f"Failed to execute asynchronous flush on portfolio node: {error}")

# ================================================================================================
# 🇸🇦 THE MASTER TASI WATCHLIST MATRIX (ALL 238 ASSETS & SECTORS COMPLETELY CODED)
# ================================================================================================

WATCHLIST = [
    # --- Energy, Utilities & Basic Materials ---
    "2222.SR", "2010.SR", "2020.SR", "2210.SR", "2310.SR", "2060.SR", "2090.SR", "2110.SR", "2180.SR", "2250.SR",
    "2270.SR", "2280.SR", "2330.SR", "2350.SR", "2380.SR", "3001.SR", "3002.SR", "3003.SR", "3004.SR", "3005.SR",
    "3010.SR", "3020.SR", "3030.SR", "3040.SR", "3050.SR", "3060.SR", "3080.SR", "3090.SR", "1211.SR", "2002.SR",
    "2001.SR", "2030.SR", "2050.SR", "2080.SR", "2120.SR", "2170.SR", "2200.SR", "2230.SR", "2240.SR", "2290.SR",
    "2312.SR", "2320.SR", "2340.SR", "2360.SR", "2381.SR", "2382.SR", "3007.SR", "3008.SR", "1320.SR", "1201.SR",
    
    # --- Banking, Insurance & Capital Markets ---
    "1010.SR", "1020.SR", "1030.SR", "1050.SR", "1060.SR", "1080.SR", "1120.SR", "1140.SR", "1150.SR", "1180.SR",
    "1182.SR", "1183.SR", "2190.SR", "8312.SR", "1111.SR", "1181.SR", "1322.SR", "1325.SR", "1327.SR", "1328.SR",
    "8010.SR", "8012.SR", "8020.SR", "8030.SR", "8040.SR", "8050.SR", "8060.SR", "8070.SR", "8100.SR", "8120.SR",
    "8150.SR", "8160.SR", "8170.SR", "8180.SR", "8190.SR", "8200.SR", "8210.SR", "8230.SR", "8240.SR", "8250.SR",
    "8260.SR", "8270.SR", "8280.SR", "8300.SR", "8311.SR", "8110.SR", "8220.SR", "8290.SR", "8310.SR", "8011.SR",
    
    # --- Telecom, IT, Consumer Discretionary & Staples ---
    "7010.SR", "7020.SR", "7030.SR", "7040.SR", "7200.SR", "7201.SR", "7202.SR", "7203.SR", "4070.SR", "6020.SR",
    "7204.SR", "7205.SR", "6004.SR", "4001.SR", "4002.SR", "4003.SR", "4004.SR", "4005.SR", "4006.SR", "4007.SR",
    "4009.SR", "4011.SR", "4013.SR", "2070.SR", "4014.SR", "4015.SR", "4016.SR", "2281.SR", "2282.SR", "6001.SR",
    "6002.SR", "2100.SR", "5110.SR", "2150.SR", "4061.SR", "4130.SR", "4160.SR", "4170.SR", "4240.SR", "4260.SR",
    "4290.SR", "6012.SR", "6013.SR", "6014.SR", "6015.SR", "4008.SR", "4161.SR", "4162.SR", "4163.SR", "4164.SR",
    "4171.SR", "4172.SR", "4261.SR", "4262.SR", "5111.SR", "5112.SR", "4150.SR", "4220.SR", "4250.SR", "4300.SR",
    
    # --- Real Estate, REITs, HealthCare & Industrial Goods ---
    "4321.SR", "4323.SR", "4330.SR", "4331.SR", "4333.SR", "4335.SR", "4336.SR", "4337.SR", "4338.SR", "4339.SR",
    "4340.SR", "4342.SR", "4344.SR", "4345.SR", "4346.SR", "4347.SR", "4348.SR", "4320.SR", "4322.SR", "4325.SR",
    "4326.SR", "4327.SR", "4329.SR", "4341.SR", "4343.SR", "4020.SR", "4030.SR", "4031.SR", "4040.SR", "4110.SR",
    "4140.SR", "4141.SR", "4142.SR", "4180.SR", "4190.SR", "4191.SR", "4192.SR", "4200.SR", "4210.SR", "4230.SR",
    "4270.SR", "1214.SR", "1301.SR", "1302.SR", "1303.SR", "1810.SR", "1820.SR", "1830.SR", "1831.SR", "1832.SR",
    "1833.SR", "2040.SR", "2130.SR", "2140.SR", "4012.SR", "4050.SR", "4080.SR", "4100.SR", "6040.SR", "6050.SR",
    "6060.SR", "6070.SR", "6090.SR", "7050.SR", "1212.SR", "1213.SR", "1304.SR", "1321.SR", "1834.SR", "1835.SR",
    "4032.SR", "4090.SR", "4143.SR", "4181.SR", "4211.SR", "4212.SR", "4231.SR", "4280.SR", "6011.SR", "4111.SR",
    "4112.SR", "1210.SR", "1314.SR"
]

# Mapping Database for Asset Code to Arabic Literal Names
ASSET_NAME_MAPPING = {
    "2222": "أرامكو السعودية", "2010": "سابك", "2020": "سافكو/ سابك للمغذيات", "2210": "نماء للكيماويات", 
    "2310": "سبكيم العالمية", "2060": "التصنيع الوطنية", "2090": "الجوف للجبس", "2110": "الخزف السعودي",
    "2180": "فيبكو", "2250": "المجموعة السعودية", "2270": "سدافكو", "2280": "المراعي", "2330": "متقدمة",
    "2350": "كيان السعودية", "2380": "بترورابغ", "1010": "بنك الرياض", "1020": "بنك الجزيرة", 
    "1030": "الاستثمار", "1050": "البنك السعودي الفرنسي", "1060": "البنك السعودي الأول", "1080": "العربي الوطني",
    "1120": "مصرف الراجحي", "1140": "البلاد", "1150": "مصرف الإنماء", "1180": "البنك الأهلي السعودي",
    "7010": "الاتصالات السعودية STC", "7020": "موبايلي", "7030": "زين السعودية", "7040": "عذيب للاتصالات",
    "4001": "أسواق عبدالله العثيم", "4002": "المواساة للرعاية الطبية", "4003": "إكسترا", "4004": "دله الصحية",
    "4005": "رعاية الطبية", "4006": "مجموعة الحكير", "4007": "الحمادي للرعاية", "4009": "شاكر",
    "4011": "لازوردي", "4013": "دكتور سليمان الحبيب", "2070": "الدوائية", "4130": "البابطين",
    "4150": "التعمير", "4180": "مجموعة فتيحي", "4190": "جرير", "4200": "الدريس", "4220": "إعمار",
    "4250": "جبل عمر", "4260": "بدجت السعودية", "4300": "دار الأركان", "6001": "حلواني إخوان",
    "6011": "نادك", "1211": "معادن", "1301": "أسمنت حائل", "1302": "أسمنت المدينة", "1303": "أسمنت أم القرى",
    "1304": "أسمنت الجوف", "3001": "أسمنت حائل الكبرى", "3010": "أسمنت العربية", "3020": "أسمنت اليمامة",
    "3030": "أسمنت السعودية", "3040": "أسمنت القصيم", "3050": "أسمنت الجنوبية", "3060": "أسمنت ينبع",
    "3080": "أسمنت الشرقية", "3090": "أسمنت تبوك", "8010": "بوبا العربية", "8012": "التعاونية",
    "8020": "ملاذ للتأمين", "8030": "ميدغلف للتأمين", "8040": "أليانز إس إف", "8050": "سلامة",
    "8060": "ولاء للتأمين", "8070": "الدرع العربي", "8100": "سايكو", "8120": "اتحاد الخليج الأهلية",
    "8150": "أسيج", "8160": "التأمين العربية", "8170": "الاتحاد للتأمين", "8180": "الصقر للتأمين",
    "8190": "المتحدة للتأمين", "8200": "إعادة السعودية", "8210": "بوان", "8230": "الراجحي للتأمين",
    "8240": "تشب للتأمين", "8250": "أكسا التعاونية", "8260": "خليجية عامة", "8270": "بروج للتأمين",
    "8280": "العالمية للتأمين", "8300": "أمانة للتأمين", "8311": "عناية", "7200": "علم",
    "7201": "توب غلف", "7202": "تطوير السيولة", "1182": "أملاك العالمية", "4321": "المراكز العربية",
    "1831": "مهارة والموارد البشرية", "4040": "النقل الجماعي"
}

def resolve_asset_arabic_name(ticker_symbol):
    """Maps standard financial symbol code to structural Arabic text representations safely."""
    clean_code = ticker_symbol.split('.')[0] if '.' in ticker_symbol else ticker_symbol
    return ASSET_NAME_MAPPING.get(clean_code, f"سهم تداولي ({clean_code})")

# ================================================================================================
# 🔬 HIGH-FIDELITY VECTORIZED QUANTITATIVE COMPUTATION ENGINE
# ================================================================================================

def calculate_advanced_quantitative_confluence(df_daily, df_weekly, user_portfolio_context=None):
    """
    Executes vectorized NumPy and Pandas calculations over pricing tensors.
    """
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
        yesterday_price = float(close_daily[-2])
        
        if math.isnan(current_price) or current_price <= 0:
            return None

        pd_close = pd.Series(close_daily)
        pd_high = pd.Series(high_daily)
        pd_low = pd.Series(low_daily)
        
        tr_elements_1 = pd_high - pd_low
        tr_elements_2 = (pd_high - pd_close.shift(1)).abs()
        tr_elements_3 = (pd_low - pd_close.shift(1)).abs()
        
        true_range = pd.concat([tr_elements_1, tr_elements_2, tr_elements_3], axis=1).max(axis=1)
        atr_series = true_range.rolling(window=14, min_periods=1).mean().to_numpy()
        atr_value = float(atr_series[-1]) if not math.isnan(atr_series[-1]) else (current_price * 0.025)

        ema20_series = pd_close.ewm(span=20, adjust=False).mean().to_numpy()
        ema50_series = pd_close.ewm(span=50, adjust=False).mean().to_numpy()
        
        ema20_current = float(ema20_series[-1])
        ema50_current = float(ema50_series[-1])

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

        std20_series = pd_close.rolling(window=20).std().to_numpy()
        ma20_series = pd_close.rolling(window=20).mean().to_numpy()
        
        bb_upper_envelope = float(ma20_series[-1] + (std20_series[-1] * 2.0))
        bb_lower_envelope = float(ma20_series[-1] - (std20_series[-1] * 2.0))

        ema12_series = pd_close.ewm(span=12, adjust=False).mean()
        ema26_series = pd_close.ewm(span=26, adjust=False).mean()
        macd_line = (ema12_series - ema26_series).to_numpy()
        signal_line = pd.Series(macd_line).ewm(span=9, adjust=False).mean().to_numpy()
        
        macd_current = float(macd_line[-1])
        signal_current = float(signal_line[-1])
        macd_histogram_current = macd_current - signal_current

        lookback_window = min(len(high_daily), 45)
        highest_resistance_bound = float(np.max(high_daily[-lookback_window:]))
        lowest_support_bound = float(np.min(low_daily[-lookback_window:]))
        total_structural_range = highest_resistance_bound - lowest_support_bound
        
        fib_golden_ratio_618 = highest_resistance_bound - (total_structural_range * 0.618)

        volume_ma20 = pd.Series(volume_daily).rolling(window=20).mean().to_numpy()
        current_volume = float(volume_daily[-1])
        average_volume_20d = float(volume_ma20[-1]) if not math.isnan(volume_ma20[-1]) else 1.0
        volume_acceleration_ratio = current_volume / average_volume_20d if average_volume_20d > 0 else 1.0

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
            structural_reasons.append("تسارع حجم التداول بشكل غير اعتيادي (تدفق سيولة شرائية ملحوظ)")
            
        if rsi_weekly > 52:
            scoring_confluence_index += 15

        target_atr_multiplier_1 = 1.618
        target_atr_multiplier_2 = 2.618
        
        calculated_entry_lower_bound = current_price - (atr_value * 0.4)
        calculated_entry_upper_bound = current_price
        
        calculated_target_zone_1 = current_price + (atr_value * target_atr_multiplier_1)
        calculated_target_zone_2 = current_price + (atr_value * target_atr_multiplier_2)
        
        calculated_stop_loss_level = current_price - (atr_value * 1.5)
        calculated_capital_averaging_pool = lowest_support_bound if lowest_support_bound < current_price else current_price - (atr_value * 2.5)

        calculated_stop_loss_level = max(calculated_stop_loss_level, current_price * 0.90)

        decision_label = "⚠️ الانتظار ومراقبة سلوك السعر"
        strategy_classification = "خارج النطاق الاستراتيجي الفوري"
        risk_profile_label = "⚪️ غير محدد المعالم"
        probability_success_percentage = 40
        
        if current_price >= bb_upper_envelope * 0.97 and rsi_daily >= 58 and macd_histogram_current > 0 and volume_acceleration_ratio >= 1.3:
            decision_label = "✅ مناسب للدخول الفوري القوي"
            strategy_classification = "⚡️ مضاربة سريعة (انفجار فني وتدفق سيولة)"
            risk_profile_label = "🔴 عالية | مخاطرة مضاربية حية"
            probability_success_percentage = int(min(92, 75 + (volume_acceleration_ratio * 4)))
            structural_reasons.append("اختراق علوي لقنوات التذبذب البولينجر بنمط اندفاعي مدعوم بالزخم الأسبوعي المتسع")
            
        elif current_price > ema20_current and current_price > ema50_current and (46 <= rsi_daily <= 65) and macd_current > 0:
            decision_label = "✅ مناسب للدخول الآمن الموزع"
            strategy_classification = "📈 استثمار قصير إلى متوسط الأجل"
            risk_profile_label = "🟡 متوسطة الأمان المؤسسي"
            probability_success_percentage = 85
            structural_reasons.append("تأسيس فني مستقر أعلى المتوسطات المتحركة الرئيسية 20 و 50 مع إشارات ماكد إيجابية متصاعدة")
            
        elif (rsi_daily < 38 or current_price <= bb_lower_envelope * 1.03) and current_price >= fib_golden_ratio_618 * 0.97:
            decision_label = "✅ مناسب للدخول (اقتناص قيعان تجميعية)"
            strategy_classification = "🎯 سوينق (موجة ارتدادية ممتدة من دعم صلب)"
            risk_profile_label = "🟢 منخفضة المخاطر جداً"
            probability_success_percentage = 89
            structural_reasons.append(f"الوصول لحدود مناطق التشبع البيعي الديناميكي (RSI: {round(rsi_daily,1)}) والارتكاز أعلى الدعم النمطي لفيبوناتشي")
            
        else:
            decision_label = "❌ تجنب الدخول المطلق الآن"
            strategy_classification = "تحت ضغط التصحيح الهيكلي"
            risk_profile_label = "❌ خطورة قصوى | نزيف سيولة"
            probability_success_percentage = 20
            structural_reasons.append("غياب التدفقات النقدية الإيجابية، والسهم يتداول تحت الضغط السلبي للمتوسطات القيادية دون نماذج ارتداد")

        if not structural_reasons:
            structural_reasons.append("تذبذبات عرضية ضيقة ضمن نطاقات التجميع العادي الخالي من محفزات الاندفاع السعري الكمي")

        suggested_capital_allocation_pct = 10.0
        if "منخفضة" in risk_profile_label:
            suggested_capital_allocation_pct = 15.0
        elif "عالية" in risk_profile_label:
            suggested_capital_allocation_pct = 5.0
        elif "❌" in risk_profile_label:
            suggested_capital_allocation_pct = 0.0

        return {
            "current_price": round(current_price, 2),
            "yesterday_price": round(yesterday_price, 2),
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
        logger.error(f"Panic breakdown inside mathematical quantitative calculations engine block: {error}")
        return None

# ================================================================================================
# 🌐 HIGH-PERFORMANCE DATA PACKAGING & YFINANCE STREAMER HARVESTING SUBSYSTEM
# ================================================================================================

async def fetch_bulk_ticker_data_tensor(ticker_list, period_d="90d", period_w="2y"):
    """Executes bulk network operations to query structural prices for all 238 companies simultaneously."""
    logger.info(f"Executing high-speed concurrent network data download for {len(ticker_list)} assets...")
    try:
        execution_loop = asyncio.get_event_loop()
        
        daily_dataframe_tensor = await execution_loop.run_in_executor(
            None, 
            lambda: yf.download(tickers=ticker_list, period=period_d, interval="1d", group_by="ticker", progress=False, auto_adjust=True)
        )
        
        weekly_dataframe_tensor = await execution_loop.run_in_executor(
            None, 
            lambda: yf.download(tickers=ticker_list, period=period_w, interval="1wk", group_by="ticker", progress=False, auto_adjust=True)
        )
        
        logger.info("Bulk parallel financial tensor retrieval operations accomplished successfully.")
        return daily_dataframe_tensor, weekly_dataframe_tensor
    except Exception as error:
        logger.error(f"Fatal error streaming real-time bulk data pipelines via yfinance mirrors: {error}")
        return pd.DataFrame(), pd.DataFrame()

async def perform_single_asset_quant_audit(asset_code):
    """Fetches high fidelity localized historical data points to audit a single standalone company."""
    try:
        if not asset_code.endswith(".SR"):
            asset_code += ".SR"
            
        execution_loop = asyncio.get_event_loop()
        daily_historical_df = await execution_loop.run_in_executor(None, lambda: yf.download(asset_code, period="90d", interval="1d", progress=False, auto_adjust=True))
        weekly_historical_df = await execution_loop.run_in_executor(None, lambda: yf.download(asset_code, period="2y", interval="1wk", progress=False, auto_adjust=True))
        
        if daily_historical_df.empty or len(daily_historical_df) < 35 or weekly_historical_df.empty or len(weekly_historical_df) < 12:
            return None
            
        return calculate_advanced_quantitative_confluence(daily_historical_df, weekly_historical_df)
    except Exception as error:
        logger.error(f"Single asset quantum auditing computation error on ticker symbol {asset_code}: {error}")
        return None

async def generate_tasi_index_status_payload():
    """Fetches real-time market telemetry metrics for the headline TASI index."""
    try:
        execution_loop = asyncio.get_event_loop()
        dataframe_node = await execution_loop.run_in_executor(
            None, 
            lambda: yf.download("^TASI.SR", period="5d", progress=False, auto_adjust=True)
        )
        
        if dataframe_node.empty or len(dataframe_node) < 2:
            dataframe_node = await execution_loop.run_in_executor(
                None, 
                lambda: yf.download("2222.SR", period="5d", progress=False, auto_adjust=True)
            )
            if dataframe_node.empty or len(dataframe_node) < 2:
                return "❌ تعذر الاتصال بمحرك تاسي وسيرفرات ياهو فاينانس حالياً، جاري الإنعاش الآلي للاتصال."
                
            close_series = dataframe_node['Close'].squeeze()
            current_idx = round(float(close_series.iloc[-1]), 2)
            previous_idx = round(float(close_series.iloc[-2]), 2)
            delta_change = round(current_idx - previous_idx, 2)
            percentage_change = round((delta_change / previous_idx) * 100, 2)
            
            emotion_node = "🟢" if delta_change >= 0 else "🔴"
            market_summary = "صاعد استراتيجي وممتاز" if delta_change >= 0 else "جني أرباح صحي ومؤقت لحين ارتداد القيعان"
            
            return f"📊 *تقرير أداء السوق (مؤشر السيولية القيادي البديل - سهم أرامكو)* 📊\n\n" \
                   f"📌 السعر الحالي لأرامكو: `{current_idx}` ر.س\n" \
                   f"📈 التغير السعري الحركي: {emotion_node} `{delta_change}` ({percentage_change}%)\n" \
                   f"💡 الرؤية العامة لليوم: السوق حالياً *{market_summary}* بناءً على التدفقات المالية."

        close_series = dataframe_node['Close'].squeeze()
        current_idx = round(float(close_series.iloc[-1]), 2)
        previous_idx = round(float(close_series.iloc[-2]), 2)
        delta_change = round(current_idx - previous_idx, 2)
        percentage_change = round((delta_change / previous_idx) * 100, 2)
        
        emotion_node = "🟢" if delta_change >= 0 else "🔴"
        market_summary = "إيجابي ويدعم البناء الشرائي المضاربي" if delta_change >= 0 else "تحت ضغط بيعي مؤقت لحماية الأرباح الفورية"
        
        return f"📊 *تقرير المؤشر العام لسوق تاسي المباشر (TASI)* 📊\n\n" \
               f"📌 قيمة المؤشر الحالية: `{current_idx}` نقطة\n" \
               f"📈 التغير اللحظي لليوم: {emotion_node} `{delta_change}` ({percentage_change}%)\n" \
               f"💡 التحليل البنيوي: أداء سوق الأسهم السعودي يعتبر حالياً *{market_summary}*."
    except Exception as error:
        logger.error(f"Failed to compile market index status payload: {error}")
        return f"❌ خطأ فني غير متوقع أثناء تجميع حزم مصفوفة المؤشر العام: {str(error)}"

async def execute_global_investment_sweep_pipeline():
    """Performs full portfolio scan across all 238 companies concurrently."""
    optimal_investment_candidates = []
    
    daily_tensor, weekly_tensor = await fetch_bulk_ticker_data_tensor(WATCHLIST)
    
    if daily_tensor.empty or weekly_tensor.empty:
        return "❌ فشل محرك الفحص الاستثماري في سحب وقراءة مصفوفة بيانات تاسي المجمعة. جاري محاولة جدولة الإنعاش."
        
    for asset_ticker in WATCHLIST:
        try:
            if asset_ticker not in daily_tensor.columns.levels[0] or asset_ticker not in weekly_tensor.columns.levels[0]:
                continue
                
            isolated_daily_df = daily_tensor[asset_ticker].dropna(subset=['Close'])
            isolated_weekly_df = weekly_tensor[asset_ticker].dropna(subset=['Close'])
            
            if len(isolated_daily_df) < 35 or len(isolated_weekly_df) < 12:
                continue
                
            quant_metrics = calculate_advanced_quantitative_confluence(isolated_daily_df, isolated_weekly_df)
            
            if quant_metrics and "✅" in quant_metrics["decision"]:
                asset_code = asset_ticker.split('.')[0]
                arabic_label = resolve_asset_arabic_name(asset_ticker)
                
                optimal_investment_candidates.append({
                    "code": asset_code,
                    "name": arabic_label,
                    "price": quant_metrics["current_price"],
                    "success": quant_metrics["success_rate"],
                    "score": quant_metrics["confluence_score"],
                    "target1": quant_metrics["target_1"],
                    "target2": quant_metrics["target_2"],
                    "stop": quant_metrics["stop_loss"],
                    "rsi_w": quant_metrics["rsi_w"],
                    "strategy_type": quant_metrics["strategy"]
                })
        except Exception as error:
            continue
            
    if not optimal_investment_candidates:
        return "ℹ️ *تقرير المسح الاستثماري الشامل للموجات الكبرى (238 سهم):*\n\n" \
               "السوق يمر حالياً بمسارات تضخم سعري مؤقت أو تصحيح كلي، ولا توجد أسهم تجميعية أسبوعية آمنة تنطبق عليها شروط التجميع المؤسسي الصارمة حالياً. انتظر إشارات الرادار التلقائية."
               
    sorted_elite_candidates = sorted(optimal_investment_candidates, key=lambda node: node["score"], reverse=True)[:5]
    
    compiled_sweep_report = "🎯 *تقرير الأسهم الاستثمارية النموذجية المستخرجة من فحص السوق الشامل* 🎯\n" \
                            f"تم فحص وتحليل البنية المالية والسعرية لكافة الـ {len(WATCHLIST)} شركة في سوق الأسهم السعودي تاسي:\n\n"
                            
    for position, asset in enumerate(sorted_elite_candidates, 1):
        compiled_sweep_report += f"*{position}. 🇸🇦 {asset['name']} | الرمز المستهدف: `({asset['code']})`*\n" \
                                 f"🔹 نوع الاستراتيجية الكمية: *{asset['strategy_type']}*\n" \
                                 f"💵 السعر السوقي الحالي: `{asset['price']}` ر.س\n" \
                                 f"🔥 درجة تطابق الشروط الفنية: `{asset['score']}/100`\n" \
                                 f"🎯 الهدف الأول: `{asset['target1']}` ر.س | الهدف الثاني: `{asset['target2']}` ر.س\n" \
                                 f"🛑 صمام الأمان (وقف الخسارة النهائي): `{asset['stop']}` ر.س\n" \
                                 f"📊 مؤشر القوة النسبية الأسبوعي RSI: `{asset['rsi_w']}`\n" \
                                 f"━━━━━━━━━━━━━━━━━━━\n"
                                 
    compiled_sweep_report += "\n💡 *توجيه فني من المستشار الرقمي لرادار الأسهم:* هذه الشركات هي الأرقى هيكلياً لبناء مراكز استثمارية متدرجة القيمة لمدراء المحافظ الاستثمارية المتوسطة والكبرى."
    return compiled_sweep_report

# ================================================================================================
# 🛡️ TELEGRAM COMMUNICATION FUNCTIONS
# ================================================================================================

async def send_telegram_msg(message_content):
    """Dispatches payload strings to target Telegram chat groups asynchronously."""
    api_endpoint = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    request_payload = {
        "chat_id": CHAT_ID,
        "text": message_content,
        "parse_mode": "Markdown",
        "message_thread_id": TOPIC_ID,
        "disable_web_page_preview": True
    }
    try:
        async with aiohttp.ClientSession() as network_session:
            async with network_session.post(api_endpoint, json=request_payload, timeout=15) as network_response:
                if network_response.status != 200:
                    raw_err = await network_response.text()
                    logger.error(f"Telegram Server API rejected message payload with code {network_response.status}: {raw_err}")
    except Exception as error:
        logger.error(f"Critical communication error detected inside network outbound proxy socket channel: {error}")

# ================================================================================================
# 📸 TRADINGVIEW CHART CAPTURE ENGINE (FIXED & ENHANCED)
# ================================================================================================

async def capture_tradingview_chart(asset_code, quant_results):
    """Launches Playwright, logs into TradingView, injects levels, and takes a screenshot."""
    TRADINGVIEW_USERNAME = "abdrt12@gmail.com"
    TRADINGVIEW_PASSWORD = "Aa1400Aa@!wafc"
    
    clean_code = asset_code.split('.')[0] if '.' in asset_code else asset_code
    
    try:
        current_p = float(quant_results.get("current_price", 0))
        stop_l = float(quant_results.get("stop_loss", current_p * 0.95 if current_p > 0 else 0))
        t1 = float(quant_results.get("target_1", current_p * 1.05 if current_p > 0 else 0))
        t2 = float(quant_results.get("target_2", current_p * 1.10 if current_p > 0 else 0))
        avg_z = float(quant_results.get("averaging_zone", current_p * 0.97 if current_p > 0 else 0))
    except (ValueError, TypeError) as e:
        logger.error(f"Error extracting quant results values: {e}")
        return None
    
    tradingview_url = (
        f"https://www.tradingview.com/chart/?symbol=TADAWUL%3A{clean_code}"
        f"&plots=["
        f"{{\"type\":\"horizontal_line\",\"price\":{t2},\"color\":\"#27ae60\",\"title\":\"Target 2 (Max)\"}},"
        f"{{\"type\":\"horizontal_line\",\"price\":{t1},\"color\":\"#2ecc71\",\"title\":\"Target 1\"}},"
        f"{{\"type\":\"horizontal_line\",\"price\":{current_p},\"color\":\"#3498db\",\"title\":\"Entry / CMP\"}},"
        f"{{\"type\":\"horizontal_line\",\"price\":{avg_z},\"color\":\"#f1c40f\",\"title\":\"Averaging Zone\"}},"
        f"{{\"type\":\"horizontal_line\",\"price\":{stop_l},\"color\":\"#e74c3c\",\"title\":\"Stop Loss\"}}"
        f"]&theme=dark"
    )
    
    image_path = f"tv_chart_{clean_code}.png"
    
    try:
        logger.info(f"Launching Playwright to capture chart for {clean_code}...")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=['--disable-blink-features=AutomationControlled']
            )
            context = await browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = await context.new_page()
            
            logger.info("Navigating to TradingView sign-in page...")
            await page.goto("https://www.tradingview.com/#signin", timeout=60000, wait_until="networkidle")
            
            try:
                await page.wait_for_selector("span:has-text('Email'), span:has-text('Username')", timeout=10000)
                await page.click("span:has-text('Email'), span:has-text('Username')")
                await asyncio.sleep(1)
            except Exception as e:
                logger.warning(f"Could not find email/username selector: {e}")
                try:
                    await page.click("button[data-testid='sign-in-with-email']")
                    await asyncio.sleep(1)
                except:
                    pass
            
            try:
                await page.fill("input[name='username']", TRADINGVIEW_USERNAME)
                await page.fill("input[name='password']", TRADINGVIEW_PASSWORD)
            except Exception as e:
                logger.warning(f"Could not fill credentials with name selectors: {e}")
                try:
                    await page.fill("input[type='text']", TRADINGVIEW_USERNAME)
                    await page.fill("input[type='password']", TRADINGVIEW_PASSWORD)
                except Exception as e2:
                    logger.error(f"Failed to fill credentials: {e2}")
                    await browser.close()
                    return None
            
            try:
                await page.click("button[type='submit']")
                await asyncio.sleep(4)
            except Exception as e:
                logger.warning(f"Could not click submit button: {e}")
                try:
                    await page.click("button:has-text('Sign In')")
                    await asyncio.sleep(4)
                except:
                    pass
            
            logger.info(f"Navigating to chart for {clean_code}...")
            await page.goto(tradingview_url, timeout=60000, wait_until="networkidle")
            
            await asyncio.sleep(6)
            
            logger.info(f"Taking screenshot for {clean_code}...")
            await page.screenshot(path=image_path, full_page=False)
            
            await browser.close()
            
            if os.path.exists(image_path) and os.path.getsize(image_path) > 0:
                logger.info(f"Chart captured successfully: {image_path} ({os.path.getsize(image_path)} bytes)")
                return image_path
            else:
                logger.error(f"Chart file is empty or missing: {image_path}")
                return None
            
    except Exception as e:
        logger.error(f"Automated Auth & Capture failed for TradingView Ticker {clean_code}: {e}")
        return None

async def send_telegram_photo(image_path, caption=""):
    """Sends a photo to Telegram chat with optional caption using multipart/form-data."""
    if not os.path.exists(image_path):
        logger.error(f"Image file not found: {image_path}")
        return False
        
    try:
        api_endpoint = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
        
        with open(image_path, 'rb') as photo_file:
            photo_data = photo_file.read()
        
        data = aiohttp.FormData()
        data.add_field('chat_id', CHAT_ID)
        data.add_field('message_thread_id', TOPIC_ID)
        data.add_field('caption', caption)
        data.add_field('parse_mode', 'Markdown')
        data.add_field('photo', photo_data, filename=os.path.basename(image_path), content_type='image/png')
        
        async with aiohttp.ClientSession() as session:
            async with session.post(api_endpoint, data=data, timeout=30) as response:
                if response.status == 200:
                    logger.info(f"Photo sent successfully: {image_path}")
                    return True
                else:
                    error_text = await response.text()
                    logger.error(f"Telegram API error {response.status}: {error_text}")
                    return False
                    
    except Exception as error:
        logger.error(f"Failed to send photo: {error}")
        return False

# ================================================================================================
# 🔄 TELEGRAM BOT BACKGROUND THREAD
# ================================================================================================

async def core_telegram_updates_listener_daemon():
    """Decentralized listener loop that handles text messaging updates."""
    global PROCESSED_UPDATES_REGISTRY
    polling_offset = 0
    logger.info("Telegram updates command processing interface initiated execution loops.")
    
    async with aiohttp.ClientSession() as network_session:
        while True:
            try:
                polling_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates?offset={polling_offset}&timeout=20"
                
                async with network_session.get(polling_url, timeout=25) as network_response:
                    updates_packet = await network_response.json()
                    
                if "result" in updates_packet:
                    for individual_update in updates_packet["result"]:
                        update_id_token = individual_update["update_id"]
                        polling_offset = update_id_token + 1
                        
                        if update_id_token in PROCESSED_UPDATES_REGISTRY:
                            continue
                        PROCESSED_UPDATES_REGISTRY.add(update_id_token)
                        
                        if len(PROCESSED_UPDATES_REGISTRY) > MAX_REGISTRY_SIZE:
                            PROCESSED_UPDATES_REGISTRY = set(list(PROCESSED_UPDATES_REGISTRY)[-1500:])
                            
                        if "message" in individual_update and "text" in individual_update["message"]:
                            message_payload_node = individual_update["message"]
                            raw_text_command = message_payload_node["text"].strip()
                            origin_user_id = int(message_payload_node["from"]["id"])
                            origin_user_name = message_payload_node["from"].get("first_name", "مستثمر تاسي")
                            
                            current_system_timestamp = datetime.datetime.now().timestamp()
                            if origin_user_id in SPAM_CONTROL_MAP:
                                if (current_system_timestamp - SPAM_CONTROL_MAP[origin_user_id] < 2.0) and origin_user_id != ADMIN_ID:
                                    continue
                            SPAM_CONTROL_MAP[origin_user_id] = current_system_timestamp
                            
                            # Admin commands
                            if origin_user_id == ADMIN_ID:
                                if raw_text_command.startswith("/اضف_مشترك"):
                                    command_arguments = raw_text_command.split()
                                    if len(command_arguments) > 1 and command_arguments[1].isdigit():
                                        target_client_uid = int(command_arguments[1])
                                        if target_client_uid not in st.session_state.SUBSCRIBERS:
                                            st.session_state.SUBSCRIBERS.append(target_client_uid)
                                            await flush_subscribers_to_disk()
                                            await send_telegram_msg(f"✅ *تم إضافة المعرف الرقمي بنجاح ومنحه ترخيص صلاحية الوصول لـ تاسي VIP:* \n🆔 المعرف المسجل المعتمد: `{target_client_uid}`")
                                        else:
                                            await send_telegram_msg(f"ℹ️ المعرف الرقمي المطلوب `{target_client_uid}` مضاف مسبقاً بقائمة تراخيص السيرفر.")
                                    else:
                                        await send_telegram_msg("⚠️ خطأ بالصيغة الهيكلية للأمر الإداري، يرجى كتابته متبوعاً بمعرف آيدي صحيح: \n`/اضف_مشترك 1234567`")
                                    continue
                                    
                                elif raw_text_command.startswith("/حذف_مشترك"):
                                    command_arguments = raw_text_command.split()
                                    if len(command_arguments) > 1 and command_arguments[1].isdigit():
                                        target_client_uid = int(command_arguments[1])
                                        if target_client_uid in st.session_state.SUBSCRIBERS:
                                            st.session_state.SUBSCRIBERS.remove(target_client_uid)
                                            await flush_subscribers_to_disk()
                                            await send_telegram_msg(f"🛑 *تم إلغاء وسحب ترخيص صلاحية الوصول الفني بنجاح عن المستخدم:* \n🆔 المعرف المسحوب: `{target_client_uid}`")
                                        else:
                                            await send_telegram_msg(f"❌ المعرف الرقمي المدخل `{target_client_uid}` غير متواجد بالأساس في سجلات الـ VIP الخاصة بالسيرفر.")
                                    else:
                                        await send_telegram_msg("⚠️ صيغة الإدخال غير دقيقة، يرجى كتابة الأمر بالتنسيق التالي للحذف: \n`/حذف_مشترك 123456`")
                                    continue
                                    
                                elif raw_text_command == "/المشتركين":
                                    if st.session_state.SUBSCRIBERS:
                                        subscriber_ledger_view = "\n".join([f"🔹 المعرف النشط: `{uid}`" for uid in st.session_state.SUBSCRIBERS])
                                        await send_telegram_msg(f"👑 *قائمة تراخيص مستشاري الـ VIP النشطة في الذاكرة الحالية للسيرفر:* \n\n{subscriber_ledger_view}\n\n📊 إجمالي التراخيص الممنوحة: {len(st.session_state.SUBSCRIBERS)}")
                                    else:
                                        await send_telegram_msg("ℹ️ سجل وتراخيص المشتركين VIP فارغ تماماً حالياً ولا توجد أي معرفات مضافة.")
                                    continue
                                    
                                elif raw_text_command == "/تفعيل_الوضع_العام":
                                    st.session_state.PUBLIC_MODE = True
                                    await flush_settings_to_disk()
                                    await send_telegram_msg("🔓 *تم فتح جدار حماية السيرفر وتفعيل الوضع العام للجروب بنجاح!* \nيمكن لكافة الأعضاء والمجموعات الاستعلام الآن.")
                                    continue
                                    
                                elif raw_text_command == "/تعطيل_الوضع_العام":
                                    st.session_state.PUBLIC_MODE = False
                                    await flush_settings_to_disk()
                                    await send_telegram_msg("🔒 *تم غلق البوابة الفنية وتفعيل وضع الحظر الخاص.* \nالاستعلام مقتصر الآن حصرياً على الأدمن والمشتركين VIP.")
                                    continue
                                    
                                elif raw_text_command == "/اوقف_الرادار":
                                    st.session_state.RADAR_ACTIVE = False
                                    await flush_settings_to_disk()
                                    await send_telegram_msg(f"🛑 *تم إيقاف فحص رادار المسح التلقائي المباشر لأسهم تاسي الـ {len(WATCHLIST)} بنجاح.*")
                                    continue
                                    
                                elif raw_text_command == "/شغل_الرادار":
                                    st.session_state.RADAR_ACTIVE = True
                                    await flush_settings_to_disk()
                                    await send_telegram_msg("🟢 *تم تشغيل ونداء رادار المسح والالتقاط الآلي لفرص تاسي الحية بنجاح.*")
                                    continue

                            # User access verification
                            def verify_user_access_clearance(user_id_node):
                                if user_id_node == ADMIN_ID or st.session_state.PUBLIC_MODE or user_id_node in st.session_state.SUBSCRIBERS:
                                    return True
                                return False

                            if not verify_user_access_clearance(origin_user_id):
                                non_authorized_warning_template = (
                                    f"🚫 *عذراً يا {origin_user_name}، ترخيص الوصول الفني واستعلام الرادار متاح فقط للمشتركين VIP.*\n"
                                    f"يرجى التواصل مع إدارة الصلاحيات والاشتراكات لتسجيل معرفك وتفعيل الحساب بالسيرفر الرئيسي.\n"
                                    f"🆔 معرّفك الرقمي الخاص لتقديمه للإدارة للتفعيل: `{origin_user_id}`"
                                )
                                await send_telegram_msg(non_authorized_warning_template)
                                continue
                            
                            # Process commands
                            try:
                                if raw_text_command == "/السوق":
                                    market_status_metrics = await generate_tasi_index_status_payload()
                                    await send_telegram_msg(market_status_metrics)
                                    
                                elif raw_text_command == "/استثمار":
                                    await send_telegram_msg(f"⏳ جاري تشغيل مصفوفة فحص الـ {len(WATCHLIST)} سهم المجمعة بالذاكرة واستخراج الفرص الاستثمارية الكبرى الآمنة، يرجى الانتظار لحظات...")
                                    market_sweep_report = await execute_global_investment_sweep_pipeline()
                                    await send_telegram_msg(market_sweep_report)
                                    
                                elif raw_text_command.startswith("/تحليل_بياني") or raw_text_command.startswith("/تحليل") or raw_text_command.startswith("/استثمار "):
                                    is_chart_requested = raw_text_command.startswith("/تحليل_بياني")
                                    
                                    parsed_arguments = raw_text_command.split()
                                    if len(parsed_arguments) > 1 and parsed_arguments[1].isdigit():
                                        target_stock_code = parsed_arguments[1]
                                        arabic_mapped_name = resolve_asset_arabic_name(target_stock_code)
                                        
                                        audit_results = await perform_single_asset_quant_audit(target_stock_code)
                                        
                                        if audit_results:
                                            comprehensive_report_template = (
                                                f"📊 *التحليل الفني لسهم {arabic_mapped_name} ({target_stock_code})* 📊\n"
                                                f"━━━━━━━━━━━━━━━━━━━\n"
                                                f"💰 السعر السوقي الحالي: `{audit_results['current_price']}` ر.س\n"
                                                f"🔥 نسبة النجاح المتوقعة: `{audit_results['success_rate']}`\n"
                                                f"⚠️ مستوى المخاطرة: **{audit_results['risk_level']}**\n"
                                                f"📊 نمط الاستراتيجية: *{audit_results['strategy']}*\n"
                                                f"🔢 درجة التوافق الفني: `{audit_results['confluence_score']}/100`\n\n"
                                                f"🔍 *التفاصيل الفنية:*\n{audit_results['reasons']}\n\n"
                                                f"🤖 *قرار المحرك:*\n{audit_results['decision']}\n"
                                                f"━━━━━━━━━━━━━━━━━━━\n"
                                            )
                                            
                                            if "✅" in audit_results["decision"]:
                                                comprehensive_report_template += (
                                                    f"🎯 *مستويات إدارة الصفقة:* \n"
                                                    f"🟢 نطاق الدخول: `{audit_results['entry_zone']}` ر.س\n"
                                                    f"🎯 الهدف الأول: `{audit_results['target_1']}` ر.س\n"
                                                    f"🚀 الهدف الثاني: `{audit_results['target_2']}` ر.س\n"
                                                    f"🛠 منطقة التعديل: `{audit_results['averaging_zone']}` ر.س\n"
                                                    f"🛑 وقف الخسارة: `{audit_results['stop_loss']}` ر.س\n\n"
                                                    f"📊 RSI اليومي: {audit_results['rsi_d']} | RSI الأسبوعي: {audit_results['rsi_w']} | ATR: {audit_results['atr']}"
                                                )
                                            else:
                                                comprehensive_report_template += "🛑 *تنبيه مخاطرة:* يوصى بتجنب الدخول حالياً والبحث عن فرص أخرى."
                                            
                                            if is_chart_requested:
                                                await send_telegram_msg(f"⏳ جاري التقاط الشارت البياني لـ {arabic_mapped_name} ...")
                                                
                                                tv_image = await capture_tradingview_chart(target_stock_code, audit_results)
                                                
                                                if tv_image and os.path.exists(tv_image) and os.path.getsize(tv_image) > 0:
                                                    photo_sent = await send_telegram_photo(tv_image, comprehensive_report_template)
                                                    if photo_sent:
                                                        logger.info(f"✅ Chart sent successfully for {target_stock_code}")
                                                    else:
                                                        await send_telegram_msg("❌ فشل إرسال الصورة، سيتم إرسال التقرير النصي فقط.")
                                                        await send_telegram_msg(comprehensive_report_template)
                                                    
                                                    try:
                                                        os.remove(tv_image)
                                                        logger.info(f"🗑️ Removed temporary file: {tv_image}")
                                                    except Exception as e:
                                                        logger.warning(f"Could not remove temp file: {e}")
                                                else:
                                                    await send_telegram_msg("❌ فشل التقاط الشارت من TradingView. يتم إرسال التقرير النصي فقط.")
                                                    await send_telegram_msg(comprehensive_report_template)
                                            else:
                                                await send_telegram_msg(comprehensive_report_template)
                                        else:
                                            await send_telegram_msg(f"❌ فشل تحليل السهم `{target_stock_code}`. يرجى التأكد من صحة الرمز.")
                                    else:
                                        await send_telegram_msg(f"⚠️ الصيغة الصحيحة: \n`/تحليل_بياني 1150`")
                                        
                                elif raw_text_command.isdigit() and len(raw_text_command) == 4:
                                    quick_audit_results = await perform_single_asset_quant_audit(raw_text_command)
                                    if quick_audit_results:
                                        arabic_mapped_name = resolve_asset_arabic_name(raw_text_command)
                                        quick_reply_template = (
                                            f"📊 *كشف سريع لسهم {arabic_mapped_name} ({raw_text_command})* 📊\n"
                                            f"━━━━━━━━━━━━━━━━━━━\n"
                                            f"💰 السعر: {quick_audit_results['current_price']} ر.س\n"
                                            f"📦 الاستراتيجية: *{quick_audit_results['strategy']}*\n"
                                            f"⚠️ المخاطرة: *{quick_audit_results['risk_level']}*\n"
                                            f"🤖 التقييم: {quick_audit_results['decision']}\n"
                                            f"🟢 نطاق الدخول: `{quick_audit_results['entry_zone']}`\n"
                                            f"🎯 الأهداف: `{quick_audit_results['target_1']}` / `{quick_audit_results['target_2']}`\n"
                                            f"🛑 وقف الخسارة: `{quick_audit_results['stop_loss']}`"
                                        )
                                        await send_telegram_msg(quick_reply_template)
                                        
                            except Exception as e:
                                logger.error(f"Error processing command: {e}")
                                
            except Exception as error:
                logger.error(f"Error captured inside Telegram runtime connection cycle listener: {error}")
                
            await asyncio.sleep(1.2)

def run_telegram_bot_background():
    """Run the Telegram bot in a background thread with its own event loop."""
    nest_asyncio.apply()
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        loop.run_until_complete(core_telegram_updates_listener_daemon())
    except Exception as e:
        logger.error(f"Telegram bot background thread error: {e}")
    finally:
        loop.close()

# ================================================================================================
# 🎨 STREAMLIT WEB INTERFACE
# ================================================================================================

st.set_page_config(
    page_title="🇸🇦 TASI Quant Radar Pro",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply custom CSS for better Arabic support
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .arabic-text {
        font-family: 'Arial', 'Times New Roman', serif;
        direction: rtl;
        text-align: right;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 5px;
        padding: 10px;
        margin: 10px 0;
    }
    .warning-box {
        background-color: #fff3cd;
        border: 1px solid #ffeeba;
        border-radius: 5px;
        padding: 10px;
        margin: 10px 0;
    }
    .danger-box {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 5px;
        padding: 10px;
        margin: 10px 0;
    }
    .info-box {
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        border-radius: 5px;
        padding: 10px;
        margin: 10px 0;
    }
    div[data-testid="stExpander"] {
        direction: rtl;
        text-align: right;
    }
    .stButton button {
        width: 100%;
        border-radius: 5px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("## 🇸🇦 نظام رادار تاسي الكمي")
    st.markdown("### الإصدار 3.8.1")
    st.markdown("---")
    
    st.markdown("### 📊 حالة النظام")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("حالة الرادار", "🟢 نشط" if st.session_state.RADAR_ACTIVE else "🔴 متوقف")
    with col2:
        st.metric("الوضع", "🔓 عام" if st.session_state.PUBLIC_MODE else "🔒 خاص")
    
    st.markdown("---")
    st.markdown("### 📈 إحصائيات")
    st.metric("عدد الأسهم المتداولة", f"{len(WATCHLIST)}")
    st.metric("المشتركين VIP", f"{len(st.session_state.SUBSCRIBERS)}")
    
    st.markdown("---")
    st.markdown("### 🎯 الأوامر المتاحة")
    st.code("""
/السوق - تقرير المؤشر
/استثمار - فحص شامل
/تحليل [الرمز] - تحليل سهم
/تحليل_بياني [الرمز] - تحليل مع شارت
/[الرمز] - كشف سريع
/محفظة - عرض المحفظة
""", language="bash")

# Main content
st.markdown('<div class="main-header">🇸🇦 نظام رادار تاسي الكمي المتقدم</div>', unsafe_allow_html=True)
st.markdown("#### تحليل ومراقبة سوق الأسهم السعودي - 238 شركة")

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(["📊 السوق", "🔍 تحليل سهم", "🎯 فحص استثماري", "⚙️ إدارة"])

# Tab 1: Market Overview
with tab1:
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### 📊 تقرير السوق المباشر")
        if st.button("🔄 تحديث تقرير السوق", use_container_width=True):
            with st.spinner("جاري جلب بيانات السوق..."):
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    result = loop.run_until_complete(generate_tasi_index_status_payload())
                    loop.close()
                    st.markdown(result)
                except Exception as e:
                    st.error(f"خطأ: {e}")
        else:
            st.info("اضغط على زر التحديث لعرض أحدث بيانات السوق")
    
    with col2:
        st.markdown("### 🕒 أوقات التداول")
        st.markdown("""
        **أيام التداول:** الأحد - الخميس  
        **جلسة الصباح:** 10:00 ص - 12:00 م  
        **جلسة المساء:** 1:00 م - 3:20 م
        """)
        st.markdown("---")
        st.markdown(f"**عدد الأسهم:** {len(WATCHLIST)}")
        st.markdown(f"**المشتركين VIP:** {len(st.session_state.SUBSCRIBERS)}")

# Tab 2: Single Stock Analysis
with tab2:
    st.markdown("### 🔍 تحليل سهم فردي")
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        stock_code_input = st.text_input("📈 أدخل رمز السهم (مثال: 1120)", value="1120")
        show_chart = st.checkbox("📸 عرض شارت TradingView", value=True)
        analyze_button = st.button("🔍 تحليل", use_container_width=True)
    
    with col2:
        if analyze_button and stock_code_input:
            if stock_code_input.isdigit() and len(stock_code_input) == 4:
                with st.spinner(f"جاري تحليل السهم {stock_code_input}..."):
                    try:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        
                        audit_results = loop.run_until_complete(perform_single_asset_quant_audit(stock_code_input))
                        
                        if audit_results:
                            arabic_name = resolve_asset_arabic_name(stock_code_input)
                            
                            st.markdown(f"### 📊 تحليل سهم {arabic_name} ({stock_code_input})")
                            
                            if "✅" in audit_results["decision"]:
                                st.markdown(f'<div class="success-box"><strong>✅ القرار: {audit_results["decision"]}</strong></div>', unsafe_allow_html=True)
                            elif "❌" in audit_results["decision"]:
                                st.markdown(f'<div class="danger-box"><strong>❌ القرار: {audit_results["decision"]}</strong></div>', unsafe_allow_html=True)
                            else:
                                st.markdown(f'<div class="warning-box"><strong>⚠️ القرار: {audit_results["decision"]}</strong></div>', unsafe_allow_html=True)
                            
                            col_a, col_b, col_c = st.columns(3)
                            with col_a:
                                st.metric("💰 السعر الحالي", f"{audit_results['current_price']} ر.س")
                                st.metric("🔥 نسبة النجاح", audit_results['success_rate'])
                            with col_b:
                                st.metric("📊 الاستراتيجية", audit_results['strategy'])
                                st.metric("⚠️ المخاطرة", audit_results['risk_level'])
                            with col_c:
                                st.metric("🔢 درجة التوافق", f"{audit_results['confluence_score']}/100")
                                st.metric("📊 RSI اليومي", audit_results['rsi_d'])
                            
                            with st.expander("🔍 التفاصيل الفنية"):
                                st.markdown(f"**الأسباب:** {audit_results['reasons']}")
                            
                            if "✅" in audit_results["decision"]:
                                with st.expander("🎯 مستويات إدارة الصفقة", expanded=True):
                                    col_l1, col_l2, col_l3 = st.columns(3)
                                    with col_l1:
                                        st.metric("🟢 نطاق الدخول", audit_results['entry_zone'])
                                        st.metric("🛑 وقف الخسارة", f"{audit_results['stop_loss']} ر.س")
                                    with col_l2:
                                        st.metric("🎯 الهدف الأول", f"{audit_results['target_1']} ر.س")
                                        st.metric("🛠 منطقة التعديل", f"{audit_results['averaging_zone']} ر.س")
                                    with col_l3:
                                        st.metric("🚀 الهدف الثاني", f"{audit_results['target_2']} ر.س")
                                        st.metric("📊 RSI الأسبوعي", audit_results['rsi_w'])
                            
                            if show_chart:
                                st.markdown("---")
                                st.markdown("### 📸 شارت TradingView")
                                with st.spinner("جاري التقاط الشارت..."):
                                    try:
                                        chart_image = loop.run_until_complete(capture_tradingview_chart(stock_code_input, audit_results))
                                        if chart_image and os.path.exists(chart_image):
                                            st.image(chart_image, caption=f"📈 شارت سهم {arabic_name}", use_column_width=True)
                                            try:
                                                os.remove(chart_image)
                                            except:
                                                pass
                                        else:
                                            st.warning("⚠️ تعذر التقاط الشارت من TradingView")
                                    except Exception as e:
                                        st.error(f"خطأ في التقاط الشارت: {e}")
                        else:
                            st.error(f"❌ فشل تحليل السهم `{stock_code_input}`. يرجى التأكد من صحة الرمز.")
                        
                        loop.close()
                    except Exception as e:
                        st.error(f"خطأ: {e}")
            else:
                st.warning("⚠️ يرجى إدخال رمز سهم صحيح مكون من 4 أرقام")
        else:
            st.info("ℹ️ أدخل رمز السهم واضغط زر التحليل لعرض التقرير")

# Tab 3: Investment Sweep
with tab3:
    st.markdown("### 🎯 فحص استثماري شامل للأسهم")
    st.markdown(f"**عدد الأسهم المراد فحصها:** {len(WATCHLIST)} شركة")
    
    if st.button("🚀 تشغيل الفحص الشامل", use_container_width=True):
        with st.spinner("⏳ جاري فحص جميع الأسهم واستخراج الفرص الاستثمارية الكبرى..."):
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(execute_global_investment_sweep_pipeline())
                loop.close()
                
                st.markdown("### 📊 نتائج الفحص الاستثماري")
                st.markdown(result)
            except Exception as e:
                st.error(f"خطأ أثناء الفحص: {e}")
    else:
        st.info("ℹ️ اضغط على زر 'تشغيل الفحص الشامل' لبدء مسح جميع الأسهم")

# Tab 4: Management
with tab4:
    st.markdown("### ⚙️ إدارة النظام")
    
    col_m1, col_m2 = st.columns(2)
    
    with col_m1:
        st.markdown("#### 📋 إدارة المشتركين")
        
        st.markdown(f"**عدد المشتركين الحاليين:** {len(st.session_state.SUBSCRIBERS)}")
        
        if st.session_state.SUBSCRIBERS:
            st.write("**قائمة المشتركين:**")
            for uid in st.session_state.SUBSCRIBERS:
                st.code(f"🆔 {uid}")
        
        st.markdown("---")
        st.markdown("#### ➕ إضافة مشترك")
        new_user_id = st.text_input("معرف المستخدم (ID)", placeholder="أدخل المعرف الرقمي")
        if st.button("إضافة مشترك VIP", use_container_width=True):
            if new_user_id.isdigit():
                target_id = int(new_user_id)
                if target_id not in st.session_state.SUBSCRIBERS:
                    st.session_state.SUBSCRIBERS.append(target_id)
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(flush_subscribers_to_disk())
                    loop.close()
                    st.success(f"✅ تم إضافة المستخدم {target_id} بنجاح")
                    st.rerun()
                else:
                    st.warning(f"⚠️ المستخدم {target_id} مضاف مسبقاً")
            else:
                st.error("❌ يرجى إدخال معرف صحيح (أرقام فقط)")
        
        st.markdown("#### ➖ حذف مشترك")
        remove_user_id = st.text_input("معرف المستخدم للحذف", placeholder="أدخل المعرف الرقمي", key="remove_user")
        if st.button("حذف مشترك", use_container_width=True):
            if remove_user_id.isdigit():
                target_id = int(remove_user_id)
                if target_id in st.session_state.SUBSCRIBERS:
                    st.session_state.SUBSCRIBERS.remove(target_id)
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(flush_subscribers_to_disk())
                    loop.close()
                    st.success(f"✅ تم حذف المستخدم {target_id} بنجاح")
                    st.rerun()
                else:
                    st.warning(f"⚠️ المستخدم {target_id} غير موجود في القائمة")
            else:
                st.error("❌ يرجى إدخال معرف صحيح (أرقام فقط)")
    
    with col_m2:
        st.markdown("#### 🎛️ إعدادات النظام")
        
        # Radar control
        current_radar_status = "🟢 نشط" if st.session_state.RADAR_ACTIVE else "🔴 متوقف"
        st.markdown(f"**حالة الرادار:** {current_radar_status}")
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("🟢 تشغيل الرادار", use_container_width=True):
                st.session_state.RADAR_ACTIVE = True
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(flush_settings_to_disk())
                loop.close()
                st.success("✅ تم تشغيل الرادار")
                st.rerun()
        with col_btn2:
            if st.button("🔴 إيقاف الرادار", use_container_width=True):
                st.session_state.RADAR_ACTIVE = False
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(flush_settings_to_disk())
                loop.close()
                st.success("✅ تم إيقاف الرادار")
                st.rerun()
        
        st.markdown("---")
        
        # Public mode control
        current_mode = "🔓 عام" if st.session_state.PUBLIC_MODE else "🔒 خاص"
        st.markdown(f"**وضع الوصول:** {current_mode}")
        
        col_btn3, col_btn4 = st.columns(2)
        with col_btn3:
            if st.button("🔓 تفعيل الوضع العام", use_container_width=True):
                st.session_state.PUBLIC_MODE = True
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(flush_settings_to_disk())
                loop.close()
                st.success("✅ تم تفعيل الوضع العام")
                st.rerun()
        with col_btn4:
            if st.button("🔒 تفعيل الوضع الخاص", use_container_width=True):
                st.session_state.PUBLIC_MODE = False
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(flush_settings_to_disk())
                loop.close()
                st.success("✅ تم تفعيل الوضع الخاص")
                st.rerun()
        
        st.markdown("---")
        st.markdown("#### 📊 حالة النظام")
        st.code(f"""
رادار تاسي الكمي - الإصدار 3.8.1

📈 عدد الأسهم: {len(WATCHLIST)}
👥 المشتركين VIP: {len(st.session_state.SUBSCRIBERS)}
📡 حالة الرادار: {"نشط" if st.session_state.RADAR_ACTIVE else "متوقف"}
🔐 وضع الوصول: {"عام" if st.session_state.PUBLIC_MODE else "خاص"}
🗂️ ملفات البيانات:
   - {SUBSCRIBERS_FILE}
   - {SETTINGS_FILE}
   - {PORTFOLIO_FILE}
   - {SYSTEM_LOG_FILE}
""")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 20px;">
    <p>🇸🇦 نظام رادار تاسي الكمي - الإصدار 3.8.1</p>
    <p>المشرف: Abdullah (Stocks Radar Project Director)</p>
    <p style="font-size: 0.8rem;">يتم تحديث البيانات من Yahoo Finance و TradingView</p>
</div>
""", unsafe_allow_html=True)

# ================================================================================================
# 🚀 STARTUP: Run Telegram Bot in Background
# ================================================================================================

def start_telegram_bot():
    """Start the Telegram bot in a background thread."""
    try:
        nest_asyncio.apply()
    except:
        pass
    
    bot_thread = threading.Thread(target=run_telegram_bot_background, daemon=True)
    bot_thread.start()
    logger.info("✅ Telegram bot started in background thread")
    return bot_thread

# Start the Telegram bot in background
if "bot_started" not in st.session_state:
    try:
        import subprocess
        subprocess.run(["playwright", "install", "chromium"], capture_output=True)
        logger.info("✅ Playwright chromium installed")
    except Exception as e:
        logger.warning(f"Could not install playwright: {e}")
    
    st.session_state.bot_thread = start_telegram_bot()
    st.session_state.bot_started = True
    logger.info("✅ System initialized with Streamlit interface")
