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

def define_sessions(df, session_start, session_end):
    df['session'] = ((df['timestamp'].dt.time >= session_start) & 
                     (df['timestamp'].dt.time < session_end)).astype(int)
    df['session'] = df['session'].cumsum()
    return df

def calculate_session_volume_profile(df, num_bins=100):
    sessions = df['session'].unique()
    session_data = []

    overall_min = df['low'].min()
    overall_max = df['high'].max()
    price_range = overall_max - overall_min

    for session in sessions:
        session_df = df[df['session'] == session]
        session_start = session_df['timestamp'].min()
        session_end = session_df['timestamp'].max()
        
        price_bins = np.linspace(overall_min, overall_max, num_bins)
        volume_profile = np.zeros(num_bins - 1)
        
        for _, row in session_df.iterrows():
            idx = np.clip(np.digitize(row['close'], price_bins) - 1, 0, num_bins - 2)
            volume_profile[idx] += row['volume']
        
        poc_index = np.argmax(volume_profile)
        poc_price = price_bins[poc_index]
        
        total_volume = np.sum(volume_profile)
        value_area_threshold = 0.7 * total_volume
        cumulative_volume = 0
        value_area_min_index = value_area_max_index = poc_index

        for i in range(len(volume_profile)):
            lower_index = max(0, poc_index - i)
            upper_index = min(len(volume_profile) - 1, poc_index + i)
            
            if lower_index != poc_index:
                cumulative_volume += volume_profile[lower_index]
                if cumulative_volume > value_area_threshold:
                    value_area_min_index = lower_index
            
            if upper_index != poc_index:
                cumulative_volume += volume_profile[upper_index]
                if cumulative_volume > value_area_threshold:
                    value_area_max_index = upper_index
            
            if cumulative_volume > value_area_threshold:
                break

        value_area_min = price_bins[value_area_min_index]
        value_area_max = price_bins[value_area_max_index]
        
        session_data.append({
            'session': session,
            'start_time': session_start,
            'end_time': session_end,
            'open': session_df['open'].iloc[0],
            'high': session_df['high'].max(),
            'low': session_df['low'].min(),
            'close': session_df['close'].iloc[-1],
            'volume': session_df['volume'].sum(),
            'poc': poc_price,
            'value_area_min': value_area_min,
            'value_area_max': value_area_max,
            'price_range': price_range,
            'volume_profile': volume_profile.tolist(),
            'price_bins': price_bins.tolist()
        })
    
    return pd.DataFrame(session_data)

def main():
    symbol = 'BTCUSDT'
    interval = '15m'  
    limit = 1000

    klines = get_klines(symbol, interval, limit)
    df = process_klines_data(klines)


    session_start = pd.to_datetime('00:00:00').time()
    session_duration = timedelta(hours=8)
    df = define_sessions(df, session_start, (datetime.combine(datetime.min, session_start) + session_duration).time())

    session_df = calculate_session_volume_profile(df)
    
    print(session_df)
    

    session_df.to_csv("session_volume_profile.csv", index=False)
    print("Session data saved to session_volume_profile.csv")

if __name__ == "__main__":
    main()