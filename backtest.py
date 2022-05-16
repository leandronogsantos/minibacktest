from abc import ABC, abstractmethod

import pandas as pd
import statistics
import numpy as np

class Strategy(ABC):

    def __init__(self, stop_loss=-100, stop_gain=100):

        self.stop_loss = stop_loss
        self.stop_gain = stop_gain

        @abstractmethod
        def create_indicators(self, dataframe):
            pass

        @abstractmethod
        def buy_entry(self, dataframe):
            pass

        @abstractmethod
        def buy_exit(self, dataframe):
            pass

        @abstractmethod
        def sell_entry(self, dataframe):
            pass

        @abstractmethod
        def sell_exit(self, dataframe):
            pass


class Position:

    def __init__(self, hour, price_entry, position_type):
        self.hour = hour
        self.price_entry = price_entry
        self.position_type = position_type


class Backtest:

    def __init__(self, data, strategy):
        self.data = data
        self.data.columns = [
            'Date',
            'Open',
            'High',
            'Low',
            'Close',
            'Volume']
        self.strategy = strategy
        self.stop_loss = strategy.stop_loss
        self.stop_gain = strategy.stop_gain
        self.buy_trade = False
        self.sell_trade = False
        self.setted = None
        self.trades_results = list()
        self.trades_info = list()
        self.init_date = '01-23-2010 00:00:00'
        self.init_dataframe()
        self.populate_signals(self.data)

    def init_dataframe(self):
        # ToDo - Remove this function
        self.add_last_in_day()

        self.data['buy_entry'] = 0
        self.data['buy_exit'] = 0
        self.data['sell_entry'] = 0
        self.data['sell_exit'] = 0

    def gain(self, type_trade, exit_price, regist=True):
        gain = 0
        if type_trade == 'buy':
            gain = (exit_price - self.setted.price_entry) * 0.2
            if regist:
                self.trades_info.append({'type': 'buy', 'init': self.setted.price_entry,
                                         'end': exit_price, 'date': self.setted.hour})
        elif type_trade == 'sell':
            gain = (exit_price - self.setted.price_entry) * -0.2
            if regist:
                self.trades_info.append({'type': 'sell', 'init': self.setted.price_entry,
                                         'end': exit_price, 'date': self.setted.hour})

        return gain

    def calc_last(self):
        all_df = []
        for date in self.data['day'].unique():
            dfc = self.data[self.data['day'] == date].copy(deep=True)
            dfc['last'] = dfc['num_candle'] \
                == np.argmax(dfc['num_candle'])
            all_df.append(dfc)
        self.data['last'] = pd.concat(all_df)['last']

    def add_last_in_day(self):
        self.data['day'] = self.data['Date'].apply(lambda x: x[:-6])
        self.data['hour'] = self.data['Date'].apply(lambda x: x[-5:])
        self.data['num_candle'] = self.data.groupby('day').cumcount()
        self.calc_last()

    def run_backtest(self):
        valid_data = self.data[pd.to_datetime(self.data['Date']) >= self.init_date]
        for (_, row) in valid_data.iterrows():
            if row['last'] and self.setted or row['hour'] >= '17' \
                and self.setted:
                if self.buy_trade:
                    self.trades_results.append(self.gain(type_trade='buy', exit_price=row['Low']))
                    self.buy_trade = False
                elif self.sell_trade:
                    self.trades_results.append(self.gain(type_trade='sell', exit_price=row['High']))
                    self.sell_trade = False
                self.setted = False
            elif self.setted and self.buy_trade \
                and self.gain(type_trade='buy',
                              exit_price=row['Close'], regist=False) <= self.stop_loss:
                self.trades_results.append(self.gain(type_trade='buy', exit_price=row['Close']))
                self.buy_trade = False
                self.setted = False
            elif self.setted and self.sell_trade \
                and self.gain(type_trade='sell',
                              exit_price=row['Close'], regist=False) <= self.stop_loss:
                self.trades_results.append(self.gain(type_trade='buy', exit_price=row['Close']))
                self.sell_trade = False
                self.setted = False
            elif self.setted and self.buy_trade \
                and self.gain(type_trade='buy',
                              exit_price=row['Close'], regist=False) >= self.stop_gain:

                self.trades_results.append(self.gain(type_trade='buy', exit_price=row['Close']))
                self.buy_trade = False
                self.setted = False
            elif self.setted and self.sell_trade \
                and self.gain(type_trade='sell',
                              exit_price=row['Close'], regist=False) >= self.stop_gain:
                self.trades_results.append(self.gain(type_trade='buy', exit_price=row['Close']))
                self.sell_trade = False
                self.setted = False
            elif not self.setted and row['buy_entry'] and row['hour'] < '17':
                self.setted = Position(row['Date'], row['High'], 'buy')
                self.buy_trade = True
            elif self.setted and row['buy_exit']:
                self.buy_trade = False
                self.trades_results.append(self.gain(type_trade='buy', exit_price=row['Low']))
                self.setted = None
            elif not self.setted and row['sell_entry'] and row['hour'] < '17':
                self.setted = Position(row['Date'], row['Low'], 'sell')
                self.sell_trade = True
            elif self.setted and row['sell_exit']:
                self.sell_trade = False
                self.trades_results.append(self.gain(type_trade='sell', exit_price=row['High']))
                self.setted = None

        return self.get_results()

    def get_results(self):
        all_trades = self.trades_results
        gain = sum(self.trades_results)
        mean = 0
        try:
            mean = statistics.mean(self.trades_results)
        except Exception as ex:
            raise ex
        return {"all_trades_gain": all_trades, "total_gain": gain, "mean_gain": mean,
                "trades_info": self.trades_info}

    def populate_signals(self, dataframe):
        self.data = self.strategy.create_indicators(dataframe)
        self.data = self.strategy.buy_entry(dataframe)
        self.data = self.strategy.buy_exit(dataframe)
        self.data = self.strategy.sell_entry(dataframe)
        self.data = self.strategy.sell_exit(dataframe)
