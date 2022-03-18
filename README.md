# trades-execution
## Introduction 
This code downloads historical data (1 minute candles) and execute an easy strategy based on two ewma crossing.

## Getting Started
1.	Installation process
Use virtual environment with python 3.8+.
If you need help with virtual env here is a great explenation https://realpython.com/python-virtual-environments-a-primer/.
2.	Software dependencies
Install dependencies by running `pip install -r requirements.txt`
4. Create config file `main.conf`
```
[eth-perp]
interval_s=5760  # Insert your slow interval parameter based on you backtesting effort.
interval_f=240   # Insert your fast interval parameter based on you backtesting effort.
leverage=1  # Insert your desired leverage. If you are new to this you should stick to leverage 1! ⚠️USING LEVERAGE GRATER THAN 1 SIGNIFICANTLY INCREASES THE LIKELIHOOD OF DEFAULT!!!🔥
api_key=xxxxxxxxxxxx  # Insert API key for your subaccount.
api_secret=xxxxxxxxxxx  # Insert API secret for your subaccount.
api_subaccount=test  # Insert your subaccount name (leave blank if you are trading on Main).
```
3.	Run the trading script `run.py`
``` python
if __name__ == '__main__':
    main(market='ETH-PERP')

```
