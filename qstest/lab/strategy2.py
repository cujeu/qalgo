from collections import deque
import datetime
import numpy as np
import sys
import pandas as pd

##sys.path.insert(0, '/home/jun/proj/qalgo/qstest/qstrader/')
sys.path.insert(0, '/home/jun/proj/qalgo/qstest/')

#from qstrader import settings   ## switch to my config
# from qstrader.compat import queue //import queue or Queue
from qstrader.config import Config
from qstrader.strategy.base import AbstractStrategy
from qstrader.event import SignalEvent, EventType
from qstrader.trading_session import TradingSession
from qstrader.evaluation import Evaluation
import queue
import pickle

class MovingAverageCrossStrategy(AbstractStrategy):
    """
    Requires:
    ticker - The ticker symbol being used for moving averages
    events_queue - A handle to the system events queue
    short_window - Lookback period for short moving average
    long_window - Lookback period for long moving average
    """
    def __init__(
        self, ticker,
        events_queue,
        short_window=100,
        long_window=300,
        base_quantity=100):

        self.ticker = ticker
        self.events_queue = events_queue
        self.short_window = short_window
        self.long_window = long_window
        self.base_quantity = base_quantity
        self.bars = 0
        self.invested = False
        self.sw_bars = deque(maxlen=self.short_window)
        self.lw_bars = deque(maxlen=self.long_window)

    def calculate_signals(self, event):
        if (event.type == EventType.BAR and
            event.ticker == self.ticker):

            # Add latest adjusted closing price to the
            # short and long window bars
            self.lw_bars.append(event.adj_close_price)
            if self.bars > self.long_window - self.short_window:
                self.sw_bars.append(event.adj_close_price)

            # Enough bars are present for trading
            if self.bars > self.long_window:
                # Calculate the simple moving averages
                short_sma = np.mean(self.sw_bars)
                long_sma = np.mean(self.lw_bars)
                # Trading signals based on moving average cross
                if short_sma > long_sma and not self.invested:
                    print("LONG %s: %s" % (self.ticker, event.time))
                    signal = SignalEvent(
                        self.ticker, "BOT",
                        suggested_quantity=self.base_quantity
                    )
                    self.events_queue.put(signal)
                    self.invested = True
                elif short_sma < long_sma and self.invested:
                    print("SHORT %s: %s" % (self.ticker, event.time))
                    signal = SignalEvent(
                        self.ticker, "SLD",
                        suggested_quantity=self.base_quantity
                    )
                    self.events_queue.put(signal)
                    self.invested = False
            self.bars += 1


def run(config, testing, tickers, filename):
    # Backtest information
    title = ['Moving Average Crossover Example']
    initial_equity = 10000.0
    ##start_date = datetime.datetime(2011, 1, 1)
    ##end_date = datetime.datetime(2020, 1, 1)
    start_date = datetime.datetime(2015, 1, 1)
    end_date = datetime.datetime(2020, 1, 1)

    # Use the MAC Strategy
    events_queue = queue.Queue()
    strategy = MovingAverageCrossStrategy(
        tickers[0], events_queue,
        short_window=50,
        long_window=100)

    # Set up the backtest
    backtest = TradingSession(
        config, strategy, tickers,
        initial_equity, start_date, end_date,
        events_queue,
        session_type="backtest",
        name = "strategy1",
        #benchmark=tickers[1],
        title=title)
    results = backtest.start_trading(testing=testing)
    #print(type(backtest))
    return results


if __name__ == "__main__":
    # Configuration data
    testing = False
    #config = settings.from_file(settings.DEFAULT_CONFIG_FILENAME, testing)
    conf = Config()
    ticker_list = ["AAPL", "ADI", "SPY"]
    ##bencht = "SPY"
    ##tickers = ["PEP", "PM"]
    filename = None
    eva = Evaluation()

    for t in ticker_list:
        tickers = []
        tickers.append(t)
        #tickers.append(bencht)
        rt = run(conf, testing, tickers, filename)
        eva.add_result(t, rt)
    print("===================")

    df_csv = pd.DataFrame()
    for t in ticker_list:
        month_series = eva.get_monthly_result(t)
        #print(month_series)
        frame_result = {'MonthReturn': month_series}
        df_result = pd.DataFrame(frame_result)
        df_result['ticker'] = t
        #df_result.reset_index()
        df_result.set_index("ticker", append=True, inplace = True)
        df_result.index.names = ['year', 'month', 'ticker']
        #df_csv.concat([df_result], ignore_index=True)
        df_csv = df_csv.append(df_result)
        #print(df_result)
    perf_name = conf.get_output_dir() + "/month.csv"
    df_csv.to_csv(perf_name)

    df_csv = pd.DataFrame()
    for t in ticker_list:
        year_series = eva.get_yearly_result(t)
        frame_result = {'YearReturn': year_series}
        df_result = pd.DataFrame(frame_result)
        df_result['ticker'] = t
        df_result.set_index("ticker", append=True, inplace = True)
        df_result.index.names = ['year', 'ticker']
        df_csv = df_csv.append(df_result)
    perf_name = conf.get_output_dir() + "/year.csv"
    df_csv.to_csv(perf_name)

    print("===================")
    print(eva.get_total_result("AAPL"))
    print("===================")
    #print(eva.get_monthly_result("ADI"))
    #print(eva.get_total_result("ADI"))

