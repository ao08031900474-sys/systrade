
from pathlib import Path
import pandas as pd

# ============================================================
# PATH SETTINGS
# ============================================================

BASE_DIR = Path("/content/drive/MyDrive/system_trade_universe")

UNIVERSE_DIR = BASE_DIR / "universe"
CACHE_DIR = BASE_DIR / "cache"
RESULTS_DIR = BASE_DIR / "results"
LOGS_DIR = BASE_DIR / "logs"
SCRIPTS_DIR = BASE_DIR / "scripts"

UNIVERSE_PATH = UNIVERSE_DIR / "topix500_like_universe_20260430.csv"
PRICE_CACHE_PATH = CACHE_DIR / "price_cache_topix500.parquet"
NIKKEI_CACHE_PATH = CACHE_DIR / "nikkei_cache.parquet"

# ============================================================
# A0 LOGIC PARAMETERS
# 原則変更禁止
# ============================================================

GAP_THRESHOLD = 11.0
VOL_THRESHOLD = 3.4
NIKKEI_MA_RATIO = 1.03

# ============================================================
# TRADE PARAMETERS
# 原則変更禁止
# ============================================================

INITIAL_CAPITAL = 1_000_000
RISK_PER_TRADE = 0.02
MAX_POSITIONS = 5

ENTRY_SLIPPAGE = 0.001
EXIT_SLIPPAGE = 0.001
COMMISSION = 0.0015

STOP_LOSS = -0.04
TAKE_PROFIT = 0.10
MAX_HOLDING_DAYS = 10

# ============================================================
# PERIOD SETTINGS
# ============================================================

FULL_START = pd.Timestamp("2019-01-01")
FULL_END = pd.Timestamp("2026-05-01")

TRAIN_START = pd.Timestamp("2019-01-01")
TRAIN_END = pd.Timestamp("2024-12-31")

TEST_START = pd.Timestamp("2025-01-01")
TEST_END = pd.Timestamp("2026-05-01")

# ============================================================
# VALIDATION THRESHOLDS
# 暫定。今後ここだけ変更すれば判定基準を調整できる
# ============================================================

MIN_TRADES_ADOPT = 50
MIN_PF_ADOPT = 1.05
MAX_DD_ADOPT = -0.15
MIN_OOS_PF_ADOPT = 1.00

REJECT_TRADES_LT = 10
REJECT_PF_LT = 0.80
REJECT_DD_LT = -0.20
REJECT_OOS_DD_LT = -0.15
REJECT_OOS_TRADES_LT = 3

HOLD_TRADES_MIN = 10
HOLD_TRADES_MAX = 20
HOLD_PF_MIN = 0.80
HOLD_PF_MAX = 1.10

# ============================================================
# OUTPUT FILE NAMES
# ============================================================

SUMMARY_LOG = RESULTS_DIR / "research_summary_log.csv"
DECISION_LOG = RESULTS_DIR / "research_decision_log.csv"

# ============================================================
# UTILITY
# ============================================================

def ensure_dirs():
    for d in [UNIVERSE_DIR, CACHE_DIR, RESULTS_DIR, LOGS_DIR, SCRIPTS_DIR]:
        d.mkdir(parents=True, exist_ok=True)
