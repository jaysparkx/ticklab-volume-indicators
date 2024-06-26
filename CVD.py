import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from binance.client import Client
import os
import docker 


client = Client(docker.api_keys, docker.api_secret)

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
    print(f"Processing {symbol}...")
    trades = fetch_trades(symbol, start_time, end_time)
    df = calculate_cvd(trades)
    df['symbol'] = symbol
    return df

def plot_cvd_and_price(df, symbol, output_dir):
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), sharex=True)
 
    ax1.plot(df['timestamp'], df['price'], color='blue')
    ax1.set_title(f'Price and CVD for {symbol}')
    ax1.set_ylabel('Price')
    ax1.grid(True)
    
 
    ax2.plot(df['timestamp'], df['cvd'], color='green')
    ax2.set_xlabel('Date')
    ax2.set_ylabel('CVD')
    ax2.grid(True)
    
    plt.xticks(rotation=45)
    plt.tight_layout()
    

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    plt.savefig(os.path.join(output_dir, f'{symbol}_price_cvd_plot.png'))
    plt.close()

def main(symbols, duration_hours=24, output_dir='output'):
    end_time = int(datetime.now().timestamp() * 1000)
    start_time = int((datetime.now() - timedelta(hours=duration_hours)).timestamp() * 1000)
    
    all_data = pd.DataFrame()
    for symbol in symbols:
        symbol_data = process_symbol(symbol, start_time, end_time)
        all_data = pd.concat([all_data, symbol_data], ignore_index=True)
        plot_cvd_and_price(symbol_data, symbol, output_dir)
    
    return all_data

if __name__ == "__main__":
    symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']  
    result_df = main(symbols)
    print(f"Plots saved in the 'output' directory.")
    print(result_df.head())