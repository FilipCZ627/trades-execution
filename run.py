import ccxt
import time
import download_data
import pandas as pd
import logging
import os

from ccxt.base.errors import ExchangeError, NetworkError


class Trading(object):

    def __init__(self) -> None:
        self.ftx = ccxt.ftx({
            'apiKey': API_KEY,
            'secret': API_SECRET,
            'enableRateLimit': True,
            'headers': {
                'FTX-SUBACCOUNT': API_SUBACCOUNT,
            }
        })

        self.trading_logger = logging.getLogger('trading_logger')
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(processName)s - %(module)s - %(funcName)s: %(message)s')
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        handler.setLevel(logging.INFO)
        handler_2 = logging.FileHandler('data/trading.log', 'a')
        handler_2.setFormatter(formatter)
        handler_2.setLevel(logging.DEBUG)

        self.trading_logger.addHandler(handler)
        self.trading_logger.addHandler(handler_2)
        self.trading_logger.setLevel(logging.DEBUG)

        try:
            self.ftx.private_post_account_leverage(params={'leverage': 20})
        except ExchangeError as e:
            self.trading_logger.info(f'Leverage overblown {e}.')

        download_data.main(market=MARKET)

        _info = self.ftx.loadMarkets()[f"{MARKET.upper().split('-')[0]}/USD:USD"]['info']
        self.size_increment = float(_info['sizeIncrement'])

        self.set_status_init()

    def get_position_amount(self, price: float, side: str, exit: bool) -> float:
        self.ftx.cancel_all_orders()
        position_amount = 0
        result = self.ftx.private_get_account()['result']
        collateral = float(result['collateral'])
        for position in result['positions']:
            if position['future'] == MARKET.upper():
                position_amount = float(position['netSize'])
        amount = max(collateral * LEVERAGE / price, self.size_increment)
        if exit:
            enter_amount = abs(position_amount)
        elif side == 'buy':
            enter_amount = amount - position_amount
        elif side == 'sell':
            enter_amount = amount + position_amount
        self.trading_logger.info(f'Calculated enter amount {enter_amount}.')
        return enter_amount

    def set_status(self, side: str, exit: bool) -> None:
        position_amount = 0
        time.sleep(1)
        positions = self.ftx.private_get_positions(params={'showAvgPrice': True})["result"]
        for item in positions:
            if item['future'] == MARKET.upper():
                position_amount = float(item['netSize'])
                avg_open_price = float(item["recentAverageOpenPrice"] or 0)
        if exit:
            self.status["status"] = 'sold_exit'
            self.status["tp"] = 0
            with open(f'data/.sold_exit_{MARKET}', 'w'):
                pass
        elif side == 'buy':
            self.status["status"] = 'bought'
            self.status["tp"] = 0
            if os.path.exists(f'data/.sold_exit_{MARKET}'):
                os.remove(f'data/.sold_exit_{MARKET}')
        elif side == 'sell':
            self.status["status"] = 'sold'
            try:
                if avg_open_price / self.status["avg_open_price"] < 0.995 and avg_open_price / self.status["avg_open_price"] > 0:
                    close_loss = avg_open_price / self.status["avg_open_price"]
                    self.trading_logger.debug(f'Adjusted tp {close_loss}.')
                    self.status["tp"] = avg_open_price * close_loss
                else:
                    self.trading_logger.debug('Short TP 0.995.')
                    self.status["tp"] = avg_open_price * 0.995
            except ZeroDivisionError:
                self.trading_logger.debug('Short TP 0.995.')
                self.status["tp"] = avg_open_price * 0.995
        self.status["amount"] = position_amount
        self.status["avg_open_price"] = avg_open_price
        self.trading_logger.info(f'Status set to {self.status}.')

    def set_status_init(self) -> None:
        status = None
        positions = self.ftx.private_get_positions(params={'showAvgPrice': True})["result"]
        for item in positions:
            if item['future'] == MARKET.upper():
                self.trading_logger.info(f'Current position in {MARKET} is {item["netSize"]}.')
                if float(item['netSize']) > 0:
                    status = 'bought'
                    tp = 0
                elif float(item['netSize']) < 0:
                    status = 'sold'
                    tp = float(item["recentAverageOpenPrice"]) * 0.995
                amount = (float(item['netSize']))
                avg_open_price = float(item["recentAverageOpenPrice"] or 0)
        if status:
            self.status = {'status': status, 'amount': amount, 'tp': tp, 'avg_open_price': avg_open_price}
        else:
            self.status = {'status': 'sold_exit' if os.path.exists(f'data/.sold_exit_{MARKET}') else None, 'amount': 0, 'tp': 0, 'avg_open_price': 0}

        self.trading_logger.info(f'Current setup is {self.status}.')


def main() -> None:
    tr = Trading()

    while True:
        try:
            tr.trading_logger.debug('Starting new iteration.')
            download_data.main(market=MARKET)
            df = pd.read_csv(f'data/ftx_{MARKET.upper()}.csv')
            df.set_index(pd.to_datetime(df['startTime'], format='%Y-%m-%dT%H:%M:%S'), inplace=True)
            df['ewma_s'] = df['close'].ewm(span=INTERVAL_S).mean()
            df['ewma_f'] = df['close'].ewm(span=INTERVAL_F).mean()

            ewma_s = float(df['ewma_s'][-1])
            ewma_f = float(df['ewma_f'][-1])
            act_price = float(df['close'][-1])

            tr.trading_logger.debug('Computed statistics.')

            if tr.status["status"] == 'sold' and act_price < tr.status['tp']:
                tr.trading_logger.info(f'Taking profit position {tr.status["status"]} at price: {act_price}.')
                tr.ftx.create_market_buy_order(MARKET.upper(), amount=tr.get_position_amount(price=act_price, side='buy', exit=True))
                tr.set_status(side='buy', exit=True)

            if (tr.status["status"] is None or tr.status["status"] in ['sold', 'sold_exit']) and ewma_s < ewma_f:
                tr.trading_logger.info(f'Received buy signal. Price: {act_price}, ewma_s: {ewma_s}, ewma_f: {ewma_f}.')
                tr.ftx.create_market_buy_order(MARKET.upper(), amount=tr.get_position_amount(price=act_price, side='buy', exit=False))
                tr.set_status(side='buy', exit=False)
            elif (tr.status["status"] is None or tr.status["status"] == 'bought') and ewma_s > ewma_f:
                tr.trading_logger.info(f'Received sell signal. Price: {act_price}, ewma_s: {ewma_s}, ewma_f: {ewma_f}.')
                tr.ftx.create_market_sell_order(MARKET.upper(), amount=tr.get_position_amount(price=act_price, side='sell', exit=False))
                tr.set_status(side='sell', exit=False)
            sleep = 60 - (time.time() % 60) + 1.5
        except NetworkError:
            tr.trading_logger.warning('Network error.')
            sleep = 1

        tr.trading_logger.debug('End iteration.')

        time.sleep(sleep)


if __name__ == '__main__':
    API_KEY = 'JuYwoIb82lSqO9KlmQfYpYZHdcU1C1SFEPw09vqd'
    API_SECRET = 'Mtvnb1p11oUCOnkwYJnh-DSkeZ6OnssC8ULRopeY'
    API_SUBACCOUNT = 'test-3'
    MARKET = 'SXP-PERP'
    INTERVAL_S = 1440
    INTERVAL_F = 720
    LEVERAGE = 2

    main()
