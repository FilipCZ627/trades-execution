# trades-execution
## Introduction 
This code downloads historical data (1 minute candles) and execute an easy strategy based on two ewma crossing.

## Getting Started
1.	Installation process
Use virtual environment with python 3.8+.
If you need help with virtual env here is a great explenation https://realpython.com/python-virtual-environments-a-primer/.
2.	Software dependencies
Install dependencies by running `pip install -r requirements.txt`
3.	Running the trading script `run.py`
``` python
if __name__ == '__main__':
    API_KEY = 'xxxxxxxxxxxx'  # Insert API key for your subaccount.
    API_SECRET = 'xxxxxxxxxxx'  # Insert API secret for your subaccount.
    API_SUBACCOUNT = 'test'  # Insert your subaccount name (leave blank if you are trading on Main).
    MARKET = 'ETH-PERP'  # Select your market you would like to trade.
    INTERVAL_S = 5760  # Insert your slow interval parameter based on you backtesting effort.
    INTERVAL_F = 180  # Insert your fast interval parameter based on you backtesting effort.
    LEVERAGE = 1  # Insert your desired leverage. If you are new to this you should stick to leverage 1! ⚠️USING LEVERAGE GRATER THAN 1 SIGNIFICANTLY INCREASES THE LIKELIHOOD OF DEFAULT!!!🔥
    main()

```
