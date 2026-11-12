import yfinance as yf
import pandas as pd
from datetime import datetime
from zoneinfo import ZoneInfo

# Stocks under $20 to monitor
STOCKS = [
    "SOFI", "PLUG", "OPEN", "ACHR", "JOBY",
    "RIVN", "LCID", "NIO", "MARA", "F"
]

# Cryptocurrencies to monitor
CRYPTO = [
    "BTC-USD", "ETH-USD", "XRP-USD",
    "SOL-USD", "DOGE-USD", "ADA-USD",
    "XLM-USD", "HBAR-USD", "LTC-USD",
    "XDC-USD"
]


def scan(tickers, market):
    print(f"\nScanning {market}...")

    for ticker in tickers:
        try:
            data = yf.Ticker(ticker).history(
                period="5d",
                interval="5m"
            )

            if data.empty or len(data) < 22:
                print(f"{ticker}: Insufficient data")
                continue

            close = data["Close"]
            volume = data["Volume"]

            price = float(close.iloc[-1])

            ema9 = close.ewm(span=9, adjust=False).mean().iloc[-1]
            ema20 = close.ewm(span=20, adjust=False).mean().iloc[-1]

            delta = close.diff()
            gains = delta.clip(lower=0)
            losses = -delta.clip(upper=0)

            avg_gain = gains.ewm(
                alpha=1 / 14, adjust=False
            ).mean()

            avg_loss = losses.ewm(
                alpha=1 / 14, adjust=False
            ).mean()

            if avg_loss.iloc[-1] == 0:
                rsi = 100.0
            else:
                rs = avg_gain.iloc[-1] / avg_loss.iloc[-1]
                rsi = 100 - (100 / (1 + rs))

            previous_high = float(
                data["High"].iloc[-21:-1].max()
            )

            recent_volume = float(volume.iloc[-5:].max())
            average_volume = float(
                volume.iloc[-21:-1].mean()
            )

            volume_ratio = (
                recent_volume / average_volume
                if average_volume > 0 else 0
            )

            breakout = price > previous_high

            if breakout and volume_ratio >= 2:
                signal = "BREAKOUT ALERT"

            elif (
                not breakout
                and ema9 > ema20
                and 50 <= rsi <= 70
                and previous_high > 0
                and price >= previous_high * 0.98
                and volume_ratio >= 1.5
            ):
                signal = "EARLY BREAKOUT"

            elif volume_ratio >= 2:
                signal = "UNUSUAL VOLUME"

            else:
                signal = "NORMAL"

            print(
                f"{ticker} | Price: ${price:.4f} | "
                f"RSI: {rsi:.1f} | "
                f"Volume: {volume_ratio:.2f}x | "
                f"Signal: {signal}"
            )

        except Exception as e:
            print(f"{ticker}: ERROR - {e}")


def stock_market_open():
    now = datetime.now(ZoneInfo("America/New_York"))

    return (
        now.weekday() < 5
        and (9, 30) <= (now.hour, now.minute) < (16, 0)
    )


if __name__ == "__main__":
    print("SNS AI Stock & Crypto Cloud Scanner")
    print("Starting scheduled scan...")

    scan(CRYPTO, "Cryptocurrency")

    if stock_market_open():
        scan(STOCKS, "Stocks")
    else:
        print("Stock market closed. Skipping stock scan.")

    print("\nScan complete!")
