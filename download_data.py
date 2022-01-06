import os
import time
import ccxt
import pandas as pd
import logging


trading_logger = logging.getLogger('trading_logger')


def get_api_data_csv(market):
    if os.path.exists(f'data/ftx_{market.upper()}.csv'):
        df = pd.read_csv(f'data/ftx_{market.upper()}.csv')
        ts_from = int(df.iat[-1, 1] / 1000) + 60
        mode = 'a'
        header = False
    else:
        os.makedirs('data', exist_ok=True)
        ts_from = int(time.time() - 60 * 60 * 24 * 200)
        mode = 'w'
        header = True

    ftx = ccxt.ftx()
    data_w = []
    trading_logger.info('Wait for the ohlc data to be downloaded from ftx!')
    for i in range(ts_from, int(time.time()), 300000):
        data = ftx.public_get_markets_market_name_candles(params={'market_name': market, 'resolution': 60, 'limit': 5000, 'start_time': i, 'end_time': i + 299940})['result']
        for n in data:
            data_w.append(n)
        time.sleep(0.2)
    df = pd.DataFrame(data_w)
    if not df.empty:
        df.set_index(pd.to_datetime(df['startTime'], format='%Y-%m-%d %H:%M:%S'), inplace=True)

    return df, mode, header


def main(market):
    start = time.time()
    df, mode, header = get_api_data_csv(market)
    if df.empty:
        trading_logger.debug("No data to download.")
    else:
        df = df[~df.index.duplicated(keep='last')]
        df.to_csv(f'data/ftx_{market}.csv', index=False, header=header, mode=mode)
        trading_logger.debug(f'Downloading ohlc api data for {market} took {time.time() - start}.')


if __name__ == "__main__":
    main(market='ETH-PERP')
