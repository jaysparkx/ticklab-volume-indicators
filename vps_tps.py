import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

BASE_URL = "https://api.binance.com/api/v3"

def get_trades(symbol, limit=1000):
    endpoint = f"{BASE_URL}/trades"
    params = {
        "symbol": symbol,
        "limit": limit
    }
    response = requests.get(endpoint, params=params)
    return response.json()

def process_trades_data(trades):
    df = pd.DataFrame(trades)
    df['time'] = pd.to_datetime(df['time'], unit='ms')
    df['qty'] = df['qty'].astype(float)
    df['quoteQty'] = df['quoteQty'].astype(float)
    return df

def calculate_tps(df, interval='1S'):
    """
    Calculate Trades Per Second (TPS)
    
    :param df: DataFrame containing trade data
    :param interval: Resampling interval (default is '1S' for 1 second)
    :return: DataFrame with TPS for each interval
    """
    tps = df.resample(interval, on='time').size().to_frame('tps')
    return tps

def calculate_vps(df, interval='1S'):
    """
    Calculate Volume Per Second (VPS)
    
    :param df: DataFrame containing trade data
    :param interval: Resampling interval (default is '1S' for 1 second)
    :return: DataFrame with VPS for each interval
    """
    vps = df.resample(interval, on='time')['qty'].sum().to_frame('vps')
    return vps

def calculate_metrics(df, interval='1S'):
    """
    Calculate both TPS and VPS
    
    :param df: DataFrame containing trade data
    :param interval: Resampling interval (default is '1S' for 1 second)
    :return: DataFrame with both TPS and VPS for each interval
    """
    metrics = df.resample(interval, on='time').agg({
        'id': 'count',
        'qty': 'sum'
    }).rename(columns={'id': 'tps', 'qty': 'vps'})
    return metrics

def get_tps_vps_stats(metrics):
    """
    Calculate statistics for TPS and VPS
    
    :param metrics: DataFrame containing TPS and VPS data
    :return: Dictionary with statistics
    """
    stats = {
        'tps_mean': metrics['tps'].mean(),
        'tps_median': metrics['tps'].median(),
        'tps_max': metrics['tps'].max(),
        'vps_mean': metrics['vps'].mean(),
        'vps_median': metrics['vps'].median(),
        'vps_max': metrics['vps'].max()
    }
    return stats

def main():
    symbol = 'BTCUSDT'
    limit = 1000  # Number of recent trades to fetch
    interval = '1S'  # Interval for TPS and VPS calculation

    trades = get_trades(symbol, limit)
    df = process_trades_data(trades)

    tps = calculate_tps(df, interval)
    vps = calculate_vps(df, interval)
    metrics = calculate_metrics(df, interval)

    print(f"TPS for {symbol}:")
    print(tps.head())
    print(f"\nVPS for {symbol}:")
    print(vps.head())
    print(f"\nCombined metrics for {symbol}:")
    print(metrics.head())

    stats = get_tps_vps_stats(metrics)
    print("\nStatistics:")
    for key, value in stats.items():
        print(f"{key}: {value:.2f}")

    # Save data to CSV
    tps.to_csv(f"output/{symbol}_tps.csv")
    vps.to_csv(f"output/{symbol}_vps.csv")
    metrics.to_csv(f"output/{symbol}_metrics.csv")
    print("\nData saved to CSV files")

if __name__ == "__main__":
    main()