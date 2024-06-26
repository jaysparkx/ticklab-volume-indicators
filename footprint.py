import requests
import pandas as pd
import numpy as np

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
    df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume', 'taker_buy_base_asset_volume']]
    df[['open', 'high', 'low', 'close', 'volume', 'taker_buy_base_asset_volume']] = df[['open', 'high', 'low', 'close', 'volume', 'taker_buy_base_asset_volume']].astype(float)
    df['taker_sell_base_asset_volume'] = df['volume'] - df['taker_buy_base_asset_volume']
    return df

def create_price_levels(df, tick_size):
    price_low = df['low'].min()
    price_high = df['high'].max()
    price_levels = np.arange(price_low, price_high + tick_size, tick_size)
    return price_levels

def calculate_footprint_data(df, price_levels):
    footprint_data = []
    
    for _, candle in df.iterrows():
        candle_low = candle['low']
        candle_high = candle['high']
        candle_buy_volume = candle['taker_buy_base_asset_volume']
        candle_sell_volume = candle['taker_sell_base_asset_volume']
        

        level_count = sum((price_levels >= candle_low) & (price_levels <= candle_high))
        if level_count > 0:
            buy_volume_per_level = candle_buy_volume / level_count
            sell_volume_per_level = candle_sell_volume / level_count
            
            for price in price_levels[(price_levels >= candle_low) & (price_levels <= candle_high)]:
                footprint_data.append({
                    'timestamp': candle['timestamp'],
                    'price': price,
                    'buy_volume': buy_volume_per_level,
                    'sell_volume': sell_volume_per_level
                })
    
    return pd.DataFrame(footprint_data)

def main():
    symbol = 'BTCUSDT'
    interval = '15m'  
    limit = 100  
    tick_size = 10  

    klines = get_klines(symbol, interval, limit)
    df = process_klines_data(klines)
    
    price_levels = create_price_levels(df, tick_size)
    footprint_df = calculate_footprint_data(df, price_levels)
    
    print(footprint_df.head())
    print(f"\nShape of footprint DataFrame: {footprint_df.shape}")
    

    footprint_df.to_csv("output/footprint_data.csv", index=False)
    print("Footprint data saved to footprint_data.csv")



if __name__ == "__main__":
    main()