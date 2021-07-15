from datetime import datetime, timedelta
import backtrader as bt
from backtrader import cerebro
import time
import ccxt as ccxt
class AtomClass():
    def __init__(self,user_exchange):
        self.init_timestamp = time.time()
        self.exchange = user_exchange
        self.symbol=self.exchange.symbol
        self.AmountPrecision= user_exchange.AmountPrecision
        self.PricePrecision= user_exchange.PricePrecision
    def get_account(self):
        self.account = '___'
        self.balance = '___'
        self.frozenbalance = '___'
        self.stocks = '___'
        self.frozenstocks = '___'
        
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
        self.high = '___' 
        self.low = '___'
        self.Sell =  '___'
        self.Buy =  '___'
        self.last =  '___'
        self.Volume = '___'
        
        try:
            self.ticker = self.exchange.fetchTicker(self.symbol)
            self.high = self.ticker['high']
            self.low = self.ticker['low']
            self.Sell =  self.ticker['ask']
            self.Buy =  self.ticker['bid']
            self.last =  self.ticker['last']
            self.bid_vol= self.ticker['bidVolume']
            self.ask_vol= self.ticker['askVolume']
            return True
        except:
            return False
        
    def get_depth(self):
        self.asks = '___'
        self.bids = '___'
        try:
            exchange_depth = self.exchange.fetch_order_book(self.symbol)
            self.asks = exchange_depth.get('asks')
            self.bids = exchange_depth.get("bids")
            return True
        except:
            return False
        
    def get_ohlc_data(self, period='1m'):
        self.ohlc_data =  '___'
        try:
            self.ohlc_data = self.exchange.fetchOHLCV(self.symbol,period)
            return True
        except:
            return False
        
    def create_order(self,order_type,order_side,price,amount):
        try:
            order_id = self.exchange.create_order(self.symbol,order_type,order_side, \
                                              order_amount,order_price)["id"]
            time.sleep(1)
            self.get_account()
            return order_id 
        except:
            return False
    def get_order(self,or_id):
        self.order_id= '___'
        self.order_price = '___'
        self.order_num = '___'
        self.order_deal_um = '___'
        self.order_avg_price = '___'
        self.order_status = '___'
        
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
        self.cancelresult= '___'
        try:
            self.cancelresult =self.exchange.cancelOrder(or_id,self.symbol)
            return True
        except:
            return False 
    def refreash_data(self):
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
            self.get_ohlc_data()
        except:
            return "False_on_ohlc_Data"
        
        return 'refreash_data_finish!'
    
