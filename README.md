### Backtest of strategies to operate in Brazilian Mini Indice and Mini Dollar
- Minibacktest was created to facilitate the run of backtesting for this mode of investing very common in Brazil.


How to run:

```
from backtest import Strategy, Backtest

strategy = SmaCross()
backtest = Backtest(df, strategy)
result = backtest.run_backtest()
```

SmaCross must inherit from the Strategy class and implement the methods below:
```
-  create_indicators(dataframe)
-  buy_entry(dataframe)
-  buy_exit(dataframe)
-  sell_entry(dataframe)
-  sell_exit(dataframe)
```
Check the [example](https://github.com/leandronogsantos/minibacktest/blob/master/examples/SmaCross.ipynb) strategy
