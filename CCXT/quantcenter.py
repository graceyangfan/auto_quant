from datetime import datetime, timedelta
import backtrader as bt
from backtrader import cerebro
import time
import ccxt as ccxt
import pandas as pd 

class QuantCenter():
    def __init__(self,user_exchange):
        self.init_timestamp = time.time()
        self.exchange = user_exchange
        self.symbol=self.exchange.symbol
        self.AmountPrecision= user_exchange.AmountPrecision
        self.PricePrecision= user_exchange.PricePrecision
    def get_account(self):
        self.account = None
        self.balance = None
        self.frozenbalance = None
        self.stocks = None
        self.frozenstocks = None
        
        self.symbol_stocks_name = self.symbol.split('/')[0]
        self.symbol_balance_name = self.symbol.split('/')[1]
        try:
            self.account = self.exchange.fetchBalance()
            self.balance = self.account[self.symbol_balance_name]['free']
            self.frozenbalance = self.account[self.symbol_balance_name]['used']
            self.stocks = self.account[self.symbol_stocks_name]['free']
            self.frozenstocks = self.account[self.symbol_stocks_name]['used']
            return True
        except:
            return False
        
    def get_ticker(self):
        self.high = None
        self.low = None
        self.Sell =  None
        self.Buy =  None
        self.last =  None
        self.Volume = None
        
        try:
            self.ticker = self.exchange.fetchTicker(self.symbol)
            self.High = self.ticker['high']
            self.Low = self.ticker['low']
            self.Sell =  self.ticker['ask']
            self.Buy =  self.ticker['bid']
            self.Last =  self.ticker['last']
            self.BuyVol= self.ticker['bidVolume']
            self.SellVol= self.ticker['askVolume']
            return True
        except:
            return False
        
    def get_depth(self):
        self.asks = None
        self.bids = None
        try:
            exchange_depth = self.exchange.fetch_order_book(self.symbol)
            self.Asks = exchange_depth.get('asks')
            self.Bids = exchange_depth.get("bids")
            return True
        except:
            return False
        
    def get_kline(self, period='1m'):
        self.Kline =  None
        try:
            col=["timestamp","Open","Highest","Lowest","Close","Volume"]
            self.Kline = pd.DataFrame(self.exchange.fetchOHLCV(self.symbol,period),columns=col)
            self.Open_Arr = self.Kline.Open.to_numpy()
            self.Highest_Arr = self.Kline.Highest.to_numpy()
            self.Lowest_Arr = self.Kline.Lowest.to_numpy()
            self.Close_Arr = self.Kline.Close.to_numpy()
            self.Volume_Arr = self.Kline.Volume.to_numpy()
            return True
        except:
            return False
        
    def create_order(self,order_side,price,amount):
        try:
            ## order_type = "market" "limit"
            ## order_side = "buy" "sell "
            if order_side == "buy":
                order_id = self.exchange.create_limit_buy_order(self.symbol,amount,price)["id"]
            elif order_side == "sell":
                order_id = self.exchange.create_limit_sell_order(self.symbol,amount,price)["id"]
            time.sleep(1)
            self.get_account()
            return order_id 
        except:
            return False
    def get_order(self,or_id):
        self.order_id= None
        self.order_price =None
        self.order_num = None
        self.order_deal_um = None
        self.order_avg_price = None
        self.order_status = None
        
        try:
            self.order= self.exchange.fetchOrder(or_id,self.symbol)
            self.order_id = self.order['id']
            self.order_price = self.order['price']
            self.order_num = self.order['amount']
            self.order_deal_num = self.order['filled']
            self.order_avg_price = self.order['average']
            self.order_status = self.order['status']
            return True
        except:
            return False
    def cancel_order(self,or_id):
        self.cancelresult= None
        try:
            self.cancelresult =self.exchange.cancelOrder(or_id,self.symbol)
            return True
        except:
            return False 
    def refreash_data(self, period='1m'):
        '''
        刷新信息
        '''
        if not self.get_account():
            return "False_on_get_Account"
        if not self.get_ticker():
            return "False_on_get_Ticker"
        if not self.get_depth():
            return "False_on_get_Depth"
        try:
            self.get_kline(period)
        except:
            return "False_on_ohlc_Data"
        
        return 'refreash_data_finish!'
    
    
