from collections import deque
import datetime
import numpy as np
import sys

##sys.path.insert(0, '/home/jun/proj/qalgo/qstest/qstrader/')
sys.path.insert(0, '/home/jun/proj/qalgo/qstest/')

#from qstrader import settings   ## switch to my config
# from qstrader.compat import queue //import queue or Queue
from qstrader.config import Config
from qstrader.strategy.base import AbstractStrategy
from qstrader.event import SignalEvent, EventType
from qstrader.trading_session import TradingSession
import queue
import pickle

class MonthRebalanceStrategy(AbstractStrategy):
    """
    Requires:
    ticker - The ticker symbol being used for moving averages
    events_queue - A handle to the system events queue
    """
    def __init__(
        self, ticker_pool,
        events_queue,
        base_quantity=100
    ):
        self.ticker_pool = ticker_pool
        self.buy_list = []
        self.buy_num = 5
        self.events_queue = events_queue
        self.base_quantity = base_quantity
        self.bars = 0
        self.invested = False
        self.sw_bars = deque(maxlen=self.short_window)
        self.lw_bars = deque(maxlen=self.long_window)

    def calculate_signals(self, event):
        if (
            event.type == EventType.BAR and
            event.ticker == self.ticker
        ):
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
    title = ['Reblance Example']
    initial_equity = 10000.0
    ##start_date = datetime.datetime(2011, 1, 1)
    ##end_date = datetime.datetime(2020, 1, 1)
    start_date = datetime.datetime(2015, 1, 1)
    end_date = datetime.datetime(2020, 1, 1)

    # Use the MAC Strategy
    events_queue = queue.Queue()
    strategy = MonthRebalanceStrategy(
        tickers, events_queue
    )

    # Set up the backtest
    backtest = TradingSession(
        config, strategy, tickers,
        initial_equity, start_date, end_date,
        events_queue,
        session_type="backtest",
        name = "month_reb",
        title=title,
        benchmark=None
    )
    results = backtest.start_trading(testing=testing)
    return results


if __name__ == "__main__":
    # Configuration data
    testing = False
    #config = settings.from_file(settings.DEFAULT_CONFIG_FILENAME, testing)
    conf = Config()
    ticker_list = ["AAPL", "ADI", "ACN", "ANET", "CTSH",
                   "GLW",  "JKHY", "MSI", "PYPL", "V"]
    bencht = None
    filename = None
    run(conf, testing, ticker_list, filename)
