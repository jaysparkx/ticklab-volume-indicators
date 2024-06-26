import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

BASE_URL = "https://api.binance.com/api/v3"

def get_klines(symbol, interval, limit):
    endpoint = f"{BASE_URL}/klines"
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": limit
    }
    response = requests.get(endpoint, params=params)
    return response.json()

def process_klines_data(klines):
    df = pd.DataFrame(klines, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 
                                       'close_time', 'quote_asset_volume', 'number_of_trades', 
                                       'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
    df[['open', 'high', 'low', 'close', 'volume']] = df[['open', 'high', 'low', 'close', 'volume']].astype(float)
    return df

def create_price_levels(df, tick_size):
    price_low = df['low'].min()
    price_high = df['high'].max()
    price_levels = np.arange(price_low, price_high + tick_size, tick_size)
    return price_levels

def create_tpo_profile(df, price_levels, tpo_period='30T'):
    df_resampled = df.resample(tpo_period, on='timestamp').agg({
        'high': 'max',
        'low': 'min',
        'close': 'last'
    })

    tpo_profile = pd.DataFrame(index=price_levels, columns=df_resampled.index)

    for timestamp, row in df_resampled.iterrows():
        tpo_profile.loc[row['low']:row['high'], timestamp] = timestamp.strftime('%A')[:1]

    return tpo_profile

def calculate_value_area(tpo_profile, value_area_percentage=0.7):
    total_tpos = tpo_profile.notna().sum().sum()
    target_tpos = int(total_tpos * value_area_percentage)

    tpo_counts = tpo_profile.notna().sum(axis=1).sort_values(ascending=False)
    cumulative_tpos = tpo_counts.cumsum()

    value_area_prices = cumulative_tpos[cumulative_tpos <= target_tpos].index

    value_area_high = value_area_prices.max()
    value_area_low = value_area_prices.min()
    poc = tpo_counts.index[0]

    return poc, value_area_low, value_area_high

def create_market_profile(df, tick_size, tpo_period='30T'):
    price_levels = create_price_levels(df, tick_size)
    tpo_profile = create_tpo_profile(df, price_levels, tpo_period)
    poc, va_low, va_high = calculate_value_area(tpo_profile)


    summary = pd.DataFrame({
        'price_level': price_levels,
        'tpo_count': tpo_profile.notna().sum(axis=1),
        'is_poc': price_levels == poc,
        'in_value_area': (price_levels >= va_low) & (price_levels <= va_high)
    })

    summary['tpo_letters'] = tpo_profile.apply(lambda row: ''.join(row.dropna().values), axis=1)

    return summary, tpo_profile, poc, va_low, va_high

def main():
    symbol = 'BTCUSDT'
    interval = '15m'  
    limit = 1000  
    tick_size = 10  

    klines = get_klines(symbol, interval, limit)
    df = process_klines_data(klines)

    market_profile_summary, tpo_profile, poc, va_low, va_high = create_market_profile(df, tick_size)

    print("Market Profile Summary:")
    print(market_profile_summary)

    print(f"\nPoint of Control (POC): {poc}")
    print(f"Value Area Low: {va_low}")
    print(f"Value Area High: {va_high}")


    market_profile_summary.to_csv("market_profile_summary.csv", index=False)
    tpo_profile.to_csv("output/tpo_profile.csv")
    print("Market Profile data saved to CSV files")

if __name__ == "__main__":
    main()