import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

def calculate_rsi(prices, period=14):
    delta = prices.diff()
    gains = delta.clip(lower=0)
    losses = -delta.clip(upper=0)

    avg_gain = gains.ewm(alpha=1 / period, adjust=False).mean()
    avg_loss = losses.ewm(alpha=1 / period, adjust=False).mean()

    rs = avg_gain / avg_loss.replace(0, float("nan"))
    rsi = 100 - (100 / (1 + rs))

    return rsi.fillna(100).iloc[-1]

# ==========================================
# SNS AI STOCK & CRYPTO SCANNER
# ==========================================

st.set_page_config(
    page_title="SNS AI Stock & Crypto Scanner",
    page_icon="📈",
    layout="wide"
)

st.title("📈 SNS AI Stock & Crypto Scanner")

st.write(
    "Monitor stocks and cryptocurrency for "
    "momentum, unusual volume, and potential breakouts."
)

st.info(
    "Market data may be delayed. "
    "The scanner refreshes every 5 minutes while open."
)

# ==========================================
# STOCK WATCHLIST
# ==========================================

stocks = [
    "SOFI", "PLUG", "RIVN", "LCID", "OPEN",
    "ACHR", "JOBY", "SOUN", "IONQ", "BBAI",
    "F", "NIO", "RKLB", "HIMS", "MARA",
    "RIOT", "CLSK", "BITF", "WULF", "QBTS",
    "RGTI", "SIRI", "LYFT", "SNAP", "PFE",
    "HOOD", "HIMS", "DNA", "RKLB", "ASTS",
    "T", "NOK", "WBD", "BTG", "GOLD",
    "CLOV", "TLRY", "GRAB", "QS", "CHPT",
]

# ==========================================
# CRYPTO WATCHLIST
# ==========================================

crypto = [
    "XRP-USD",
    "BTC-USD",
    "ETH-USD",
    "SOL-USD",
    "DOGE-USD",
    "ADA-USD",
    "LINK-USD",
    "AVAX-USD",
    "LTC-USD",
    "BCH-USD",
    "XLM-USD",
    "SHIB-USD"
]

# ==========================================
# SCANNER SETTINGS
# ==========================================

MAX_STOCK_PRICE = 20
VOLUME_ALERT = 2.0
PRICE_ALERT = 2.0

# ==========================================
# DOWNLOAD MARKET DATA
# ==========================================

@st.cache_data(ttl=240, show_spinner=False)
def get_market_data(ticker):

    data = yf.Ticker(ticker).history(
        period="5d",
        interval="5m",
        prepost=True
    )

    return data


# ==========================================
# SCAN MARKET
# ==========================================

def scan_market(tickers, asset_type):

    results = []

    for ticker in tickers:

        try:

            data = get_market_data(ticker)

            if data.empty or len(data) < 22:
                continue

            data = data.dropna(
                subset=["Close", "Volume"]
            )

            if len(data) < 22:
                continue

            price = float(data["Close"].iloc[-1])

            rsi = calculate_rsi(data["Close"])
            
            if price <= 0:
                continue

            # Stocks under $20 only
            if asset_type == "Stock":
                if price >= MAX_STOCK_PRICE:
                    continue

            previous = float(
                data["Close"].iloc[-2]
            )

            if previous <= 0:
                continue

            # Latest 5-minute price change
            change = (
                (price - previous) / previous
            ) * 100

            # Volume calculation
            current_volume = float(
                data["Volume"].iloc[-1]
            )

            average_volume = float(
                data["Volume"].iloc[-21:-1].mean()
            )

            if average_volume > 0:
                volume_ratio = (
                    current_volume / average_volume
                )
            else:
                volume_ratio = 0

            # Moving average
            ma20 = float(
                data["Close"].tail(20).mean()
            )

            # Previous 20-candle high
            previous_high = float(
                data["High"].iloc[-21:-1].max()
            )

            breakout = price > previous_high

            # ==================================
            # MOMENTUM SCORE
            # ==================================

            score = 0

            if change > 0:
                score += 15

            if change >= 1:
                score += 15

            if change >= 2:
                score += 15

            if volume_ratio >= 1.5:
                score += 15

            if volume_ratio >= 2:
                score += 15

            if price > ma20:
                score += 10
            if ema9 > ema20:
                score += 10
            if breakout:
                score += 15

            score = min(score, 100)

            # ==================================
            # ALERT SIGNALS
            # ==================================

            if breakout and volume_ratio >= 2:
                signal = "🚀 BREAKOUT ALERT"

            elif change >= PRICE_ALERT:
                signal = "🔥 PRICE SURGE"

            elif volume_ratio >= VOLUME_ALERT:
                signal = "🚨 UNUSUAL VOLUME"

            elif score >= 60:
                signal = "🟢 STRONG MOMENTUM"

            elif score >= 40:
                signal = "🟡 WATCH"

            else:
                signal = "⚪ NORMAL"

            results.append({
                "Symbol": ticker,
                "Type": asset_type,
                "Price": round(price, 6),
                "RSI": round(float(rsi), 2),
                "5m Change %": round(change, 2),
                "Volume Ratio": round(volume_ratio, 2),
                "Score": score,
                "Signal": signal
            })

        except Exception as e:
            st.error(f"Scanner error for {ticker}: {e}")
            # Skip symbols with unavailable data
            continue

    if not results:
        return pd.DataFrame()

    df = pd.DataFrame(results)

    df = df.sort_values(
        by=[
            "Score",
            "5m Change %"
        ],
        ascending=False
    )

    return df.reset_index(drop=True)


# ==========================================
# AUTOMATIC SCANNER
# ==========================================

@st.fragment(run_every="300s")
def run_scanner():

    st.write(
        "🕒 Last scan:",
        datetime.now().strftime(
            "%Y-%m-%d %I:%M:%S %p"
        )
    )

    # ==================================
    # SCAN STOCKS
    # ==================================

    st.subheader("📈 Stocks Under $20")

    with st.spinner("Scanning stocks..."):

        stock_results = scan_market(
            stocks,
            "Stock"
        )

    if not stock_results.empty:

        st.dataframe(
            stock_results,
            width="stretch",
            hide_index=True
        )

    else:
        st.warning(
            "No stock data available."
        )

    # ==================================
    # SCAN CRYPTO
    # ==================================

    st.subheader("₿ Cryptocurrency Scanner")

    with st.spinner("Scanning crypto..."):

        crypto_results = scan_market(
            crypto,
            "Crypto"
        )

    if not crypto_results.empty:

        st.dataframe(
            crypto_results,
            width="stretch",
            hide_index=True
        )

    else:
        st.warning(
            "No cryptocurrency data available."
        )

    # ==================================
    # TOP 10 OPPORTUNITIES
    # ==================================

    st.subheader("🏆 Top 10 Market Opportunities")

    frames = []

    if not stock_results.empty:
        frames.append(stock_results)

    if not crypto_results.empty:
        frames.append(crypto_results)

    if frames:

        combined = pd.concat(
            frames,
            ignore_index=True
        )

        combined = combined.sort_values(
            by=[
                "Score",
                "5m Change %"
            ],
            ascending=False
        )

        top_10 = combined.head(10)

        st.dataframe(
            top_10,
            width="stretch",
            hide_index=True
        )

        # ==================================
        # DASHBOARD ALERTS
        # ==================================

        st.subheader("🚨 Active Scanner Alerts")

        alerts = combined[
            combined["Signal"].isin([
                "🚀 BREAKOUT ALERT",
                "🔥 PRICE SURGE",
                "🚨 UNUSUAL VOLUME"
            ])
        ]

        if not alerts.empty:

            for _, row in alerts.iterrows():

                st.warning(
                    f"{row['Symbol']} | "
                    f"{row['Signal']} | "
                    f"Change: {row['5m Change %']}% | "
                    f"Score: {row['Score']}"
                )

        else:
            st.success(
                "No active scanner alerts."
            )

    else:
        st.warning(
            "No market results available."
        )

    st.caption(
        "Market data: Yahoo Finance via yfinance. "
        "Prices may be delayed or unavailable. "
        "Signals are rule-based indicators, not "
        "predictions or trading recommendations."
    )


# ==========================================
# START SCANNER
# ==========================================

run_scanner()
