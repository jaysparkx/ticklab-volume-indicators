import requests
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
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

def calculate_volume_profile(df, num_bins=100):
    price_min, price_max = df['low'].min(), df['high'].max()
    price_bins = np.linspace(price_min, price_max, num_bins)
    volume_profile = np.zeros(num_bins - 1)
    
    for _, row in df.iterrows():
        idx = np.digitize(row['close'], price_bins) - 1
        volume_profile[idx] += row['volume']
    
    return price_bins, volume_profile

def find_poc_and_value_area(price_bins, volume_profile, value_area_threshold=0.7):
    poc_index = np.argmax(volume_profile)
    poc_price = price_bins[poc_index]
    
    total_volume = np.sum(volume_profile)
    threshold = value_area_threshold * total_volume
    cumulative_volume = 0
    value_area_min_index = value_area_max_index = poc_index

    for i in range(len(volume_profile)):
        lower_index = max(0, poc_index - i)
        upper_index = min(len(volume_profile) - 1, poc_index + i)
        
        if lower_index != poc_index:
            cumulative_volume += volume_profile[lower_index]
            if cumulative_volume > threshold:
                value_area_min_index = lower_index
        
        if upper_index != poc_index:
            cumulative_volume += volume_profile[upper_index]
            if cumulative_volume > threshold:
                value_area_max_index = upper_index
        
        if cumulative_volume > threshold:
            break

    value_area_min = price_bins[value_area_min_index]
    value_area_max = price_bins[value_area_max_index]
    
    return poc_price, value_area_min, value_area_max

def plot_volume_profile_and_price(df, price_bins, volume_profile, poc_price, value_area_min, value_area_max, symbol):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6), gridspec_kw={'width_ratios': [1, 3]})

    # Volume profile
    ax1.barh(price_bins[:-1], volume_profile, height=price_bins[1] - price_bins[0], color='lightgray')
    ax1.barh(price_bins[np.where(price_bins >= value_area_min)[0][0]:np.where(price_bins <= value_area_max)[0][-1]], 
             volume_profile[np.where(price_bins >= value_area_min)[0][0]:np.where(price_bins <= value_area_max)[0][-1]], 
             height=price_bins[1] - price_bins[0], color='lightblue')
    ax1.barh(poc_price, np.max(volume_profile), height=price_bins[1] - price_bins[0], color='red')
    ax1.axhline(y=value_area_min, color='blue', linestyle='--')
    ax1.axhline(y=value_area_max, color='blue', linestyle='--')
    ax1.set_xlabel('Volume')
    ax1.set_ylabel('Price')
    ax1.set_title('Volume Profile')

    # Price chart
    ax2.plot(df['timestamp'], df['close'], label='Close Price')
    ax2.axhline(y=poc_price, color='red', linestyle='--', label='POC')
    ax2.axhline(y=value_area_min, color='blue', linestyle='--', label='Value Area')
    ax2.axhline(y=value_area_max, color='blue', linestyle='--')
    ax2.fill_between(df['timestamp'], value_area_min, value_area_max, alpha=0.1, color='blue')
    ax2.set_xlabel('Date')
    ax2.set_ylabel('Price')
    ax2.set_title(f'{symbol} Price Chart')
    ax2.legend()

    plt.suptitle('TickLab.IO - Volume Profile', fontsize=16, fontweight='bold')
    plt.tight_layout()
    plt.show()

def main():
    symbol = 'BTCUSDT'
    interval = '1h'
    limit = 1000

    klines = get_klines(symbol, interval, limit)
    df = process_klines_data(klines)
    price_bins, volume_profile = calculate_volume_profile(df)
    poc_price, value_area_min, value_area_max = find_poc_and_value_area(price_bins, volume_profile)
    plot_volume_profile_and_price(df, price_bins, volume_profile, poc_price, value_area_min, value_area_max, symbol)

if __name__ == "__main__":
    main()