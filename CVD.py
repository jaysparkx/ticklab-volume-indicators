import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from binance.client import Client
import ray
import os
import docker

client = Client(docker.api_keys, docker.api_secret)

@ray.remote
def fetch_trades(symbol, start_time, end_time):
    trades = []
    while start_time < end_time:
        new_trades = client.get_aggregate_trades(symbol=symbol, startTime=start_time, endTime=end_time, limit=1000)
        if not new_trades:
            break
        trades.extend(new_trades)
        start_time = max(int(trade['T']) for trade in new_trades) + 1
    return trades

def calculate_cvd(trades):
    cvd = 0
    cvd_data = []
    for trade in trades:
        volume = float(trade['q'])
        price = float(trade['p'])
        if trade['m']:  # If true, the buyer is the market maker
            cvd -= volume
        else:
            cvd += volume
        cvd_data.append({
            'timestamp': pd.to_datetime(trade['T'], unit='ms'),
            'cvd': cvd,
            'price': price
        })
    return pd.DataFrame(cvd_data)

def process_symbol(symbol, start_time, end_time):
    trades = ray.get(fetch_trades.remote(symbol, start_time, end_time))
    df = calculate_cvd(trades)
    df['symbol'] = symbol
    return df

def plot_cvd(df, symbol, output_dir):
    plt.figure(figsize=(12, 6))
    plt.plot(df['timestamp'], df['cvd'])
    plt.title(f'Cumulative Volume Delta (CVD) for {symbol}')
    plt.xlabel('Date')
    plt.ylabel('CVD')
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    plt.savefig(os.path.join(output_dir, f'{symbol}_cvd_plot.png'))
    plt.close()

def main(symbols, duration_hours=24, output_dir='output'):
    ray.init()
    
    end_time = int(datetime.now().timestamp() * 1000)
    start_time = int((datetime.now() - timedelta(hours=duration_hours)).timestamp() * 1000)
    
    results = []
    for symbol in symbols:
        results.append(process_symbol(symbol, start_time, end_time))
    
    all_data = pd.concat(results, ignore_index=True)
    

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    all_data.to_csv(os.path.join(output_dir, 'cvd_data.csv'), index=False)
    
    for symbol in symbols:
        symbol_data = all_data[all_data['symbol'] == symbol]
        plot_cvd(symbol_data, symbol, output_dir)
    
    ray.shutdown()
    return all_data

if __name__ == "__main__":
    symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']  
    result_df = main(symbols)
    print(result_df.head())
    print(f"Data and plots saved in the 'output' directory.")