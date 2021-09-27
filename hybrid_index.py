import numpy as np
import talib as TA
import pandas as pd
#import lightgbm as lgb
class QuantCenter():
    def __init__(self,exchange,contract_type,MarginLevel):
        self.init_timestamp = time.time()
        self.exchange = exchange
        self.name = self.exchange.GetName()
        self.currency = self.exchange.GetCurrency()
        self.exchange.IO("trade_margin") ##逐仓期货模式
        self.exchange.SetContractType(contract_type)
        self.MarginLevel=self.exchange.SetMarginLevel(MarginLevel)

    def update_account(self):
        self.Balance = None
        self.Amount = None
        self.FrozenBalance = None
        self.FrozenStocks = None

        try:
            self.account = self.exchange.GetAccount()

            self.Balance = self.account['Balance']
            self.Amount = self.account['Stocks']
            self.FrozenBalance = self.account['FrozenBalance']
            self.FrozenStocks = self.account['FrozenStocks']
            ##币安期货
            #self.totalEquity = parseFloat(self.account.totalWalletBalance)
            return True
        except:
            return False

    def update_ticker(self):

        self.High = None
        self.Low = None
        self.Sell = None
        self.Buy = None
        self.Last = None
        self.Volume = None

        try:
            self.ticker = self.exchange.GetTicker()

            self.High = self.ticker['High']
            self.Low = self.ticker['Low']
            self.Sell = self.ticker['Sell']
            self.Buy = self.ticker['Buy']
            self.Last = self.ticker['Last']
            self.Volume = self.ticker['Volume']
            return True
        except:
            return False

    def update_depth(self):
        self.Asks = None
        self.Bids = None
        self.Asks_Price1 = None
        self.Asks_Amount1 = None
        self.Bids_Price1 = None
        self.Bids_Amount1 = None
        try:
            self.Depth = self.exchange.GetDepth()
            self.Asks = self.Depth['Asks']
            self.Bids = self.Depth['Bids']
            self.Asks_Price1 = self.Asks[0]["Price"]
            self.Asks_Amount1 = self.Asks[0]["Amount"]
            self.Bids_Price1 = self.Bids[0]["Price"]
            self.Bids_Amount1 = self.Bids[0]["Amount"]
            return True
        except:
            return False

    def update_kline(self, period=PERIOD_M5):
        try:
            self.Kline = exchange.GetRecords(period)
            return True
        except:
            return False

    def create_order(self, order_type, price, amount):
        if order_type == 'buy':
                trade_func = self.exchange.Buy
        elif order_type == 'sell':
                trade_func= self.exchange.Sell
        elif order_type =="closebuy":
                trade_func= self.exchange.Sell 
        elif  order_type =="closesell":
                trade_func = self.exchange.Buy
        self.exchange.SetDirection(order_type)
        return trade_func(price,amount)
    
    def openLong(self,price,amount):
        return self.create_order("buy",price,amount) 
    def openShort(self,price,amount):
        return self.create_order("sell",price,amount) 
    def coverLong(self,price,amount):
        return self.create_order("closebuy",price,amount) 
    def coverShort(self,price,amount):
        return self.create_order("closesell",price,amount) 
    
    def fetch_Position(self):
        '''
        [{'MarginLevel': 10.0, 'Amount': 1.4, 'FrozenAmount': 0.0, 'Price': 36766.623, 'Profit': 683.2518, 'Margin': 5147.32722, 'Type': 0, 'ContractType': 'swap'},
        {'MarginLevel': 10.0, 'Amount': 1.2, 'FrozenAmount': 0.0, 'Price': 36849.750833333, 'Profit': -485.891, 'Margin': 4421.9701, 'Type': 1, 'ContractType': 'swap'}]
        '''
        positions= self.exchange.GetPosition()
        for position in positions:
            if(position['Type']==PD_SHORT): #空仓      
                self.short_amount = position['Amount']#获取空单持仓
                self.short_profit = position['Profit']#获取空单盈利
                self.short_margin = position['Margin']
            elif(position['Type']==PD_LONG):
                self.long_amount = position['Amount']#获取多单持仓
                self.long_profit = position['Profit']#获取多单盈利
                self.long_margin = position['Margin']
    def fetch_order(self, id):
        #{'Id': 1, 'Price': 36805.78, 'Amount': 1.0, 'DealAmount': 1.0, 'AvgPrice': 36805.78,
        #'Type': 0, 'Offset': 0, 'Status': 1, 'ContractType': 'swap'}
        return self.exchange.GetOrder(id)

    def fetch_uncomplete_orders(self):
        # 获取所有未完成的订单
        return self.exchange.GetOrders()

    def cancel_order(self, order_id):
        ## return True or False
        return self.exchange.CancelOrder(order_id)
    
    def refresh_data(self, period=PERIOD_M5):

        if not self.update_account():
            return 'false_get_account'

        if not self.update_ticker():
            return 'false_get_ticker'
        if not self.update_depth():
            return 'false_get_depth'
        try:
            self.update_kline(period)
        except:
            return 'false_get_K_line_info'

        return 'refresh_data_finish!'

    def fetch_kline(self, period=PERIOD_M5):
        return self.exchange.GetRecords(period)

    def fetch_ticker(self):
        return self.exchange.GetTicker()

    def fetch_depth(self):
        return self.exchange.GetDepth()
class Strategy():
    def __init__(self, args):
        self.args = args
        self.quantcenter = args.quantcenter

        self.init_time = time.time()
        self.last_time = time.time()

        self.amount_N = args.amount_N
        self.price_N = args.price_N

        self.min_buy_money = args.min_buy_money
        self.min_sell_money = args.min_sell_money
        ##期货记录
        self.MarginLevel = self.quantcenter.MarginLevel
 
        self.quantcenter.update_kline(args.kline_period)
        self.kline = pd.DataFrame(self.quantcenter.Kline)
        self.price_percent_period = args.price_percent_period
        self.user_price_period = int(self.price_percent_period / len(self.kline) * 24 * 3600)
        ## 订单记录
        self.buy_orders=[]
        self.sell_orders=[]
        
        ##更新一下
        self.quantcenter.refresh_data()
    def refresh_account(self):
        self.quantcenter.update_account()
        self.Amount = self.quantcenter.Amount
        self.Balance = self.quantcenter.Balance
        self.Last_price= self.quantcenter.Last
        self.potential_buy_amount = round(self.Balance *self.MarginLevel/ self.Last_price, self.amount_N)
        self.potential_sell_amount = round(self.Amount, self.amount_N)
        self.total_Balance = self.Balance + self.Amount *self.Last_price/self.MarginLevel 
    def refresh_data(self, period):
        ##refresh account 
        self.refresh_account()
        self.quantcenter.refresh_data(period)
        ##update arr will be used in indicator
        self.kline = pd.DataFrame(self.quantcenter.Kline)
        self.close_Arr = self.kline["Close"].to_numpy()
        self.high_Arr = self.kline["High"].to_numpy()
        self.low_Arr = self.kline["Low"].to_numpy()
        self.volume_Arr = self.kline["Volume"].to_numpy()
        self.hlc3 = (self.high_Arr+self.low_Arr+self.close_Arr)/3.0
        self.ATR = TA.ATR(self.high_Arr,self.low_Arr,self.close_Arr,14)
        self.user_dataset = pd.DataFrame(self.quantcenter.fetch_kline(self.user_price_period))
        self.user_Max_price = self.user_dataset.High.max()
        self.user_Min_price = self.user_dataset.Low.min()
    def check_order(self,order_side,price,amount):
        if order_side == "openlong":
            if  price*amount/self.MarginLevel<self.min_buy_money or amount > self.potential_buy_amount:
                return False
            else:
                return True
        elif order_side == "openshort":
            if price*amount/self.MarginLevel<self.min_sell_money or amount> self.potential_sell_amount:
                return False
            else:
                return True
    def next(self):
        del_buy_orders= []
        del_sell_orders = [] 
        self.quantcenter.update_ticker()
        price = self.quantcenter.Last 
        upper,middle,lower = TA.BBANDS(self.close_Arr,timeperiod=20,nbdevup=2,nbdevdn=2,matype=0)
        rsi=TA.RSI(self.close_Arr,14)
        volume_dif = self.volume_Arr[-1] -self.volume_Arr[-2]
        
        K,D = TA.STOCH(self.high_Arr, self.low_Arr, self.close_Arr,
                        fastk_period=9,
                        slowk_period=3,
                        slowk_matype=0,
                        slowd_period=3,
                        slowd_matype=0)
        
        J = 3.0*K-2.0*D
        buy_siginal =J[-1] > K[-1] and K[-1] > D[-1] and  J[-2] < K[-2] and K[-2] < D[-2] and \
         rsi[-1] < 70  and  abs(price - lower[-1])<100  and  volume_dif >0 
        sell_siginal = J[-1] < K[-1]  and K[-1]  < D[-1] and  J[-2] > K[-2]  and K[-2]  > D[-2] and \
         rsi[-1] > 30  and  abs(price - upper[-1])<100   and  volume_dif >0 

        if buy_siginal or sell_siginal:
            Log("true sigina")
        ##正在插针，停止交易
        sell_siginal = False 
        buy_siginal = False 
        self.quantcenter.update_ticker()
        price = self.quantcenter.Last 
        if abs(self.close_Arr[-1] -self.close_Arr[-2])>self.close_Arr[-1]*0.003:
            sell_siginal = False 
            buy_siginal = False 
            if self.close_Arr[-1] > self.close_Arr[-2]:
                #平空仓
                for order in self.sell_orders:
                    self.quantcenter.coverShort(round(price,self.price_N),order["amount"])
                    del_sell_orders.append(order) 
                ##等待30s
                ##开多
                '''
                while(self.close_Arr[-1] > self.close_Arr[-2]):
                    Sleep(10*1000)
                    self.refresh_data(self.args.kline_period)
                
                self.quantcenter.update_ticker()
                trade_side = "openlong"
                trade_price = round(self.quantcenter.Last,self.price_N)
                trade_amount =  round(self.unit,self.amount_N)
                if self.check_order(trade_side,trade_price,trade_amount):
                    order_id = self.quantcenter.openLong(trade_price,trade_amount)
                    self.buy_orders.append({ 
                               "side":trade_side,
                               "price":trade_price,
                               "amount":trade_amount,
                               "id":order_id,
                               "timestamp":Unix()})
                 '''
            elif self.close_Arr[-1] <self.close_Arr[-2]:
                #平多仓
                for order in self.buy_orders:
                    self.quantcenter.coverLong(round(price,self.price_N),order["amount"])
                    del_buy_orders.append(order)
                '''
                ##开空
                while(self.close_Arr[-1] > self.close_Arr[-2]):
                    Sleep(10*1000)
                    self.refresh_data(self.args.kline_period)
                self.quantcenter.update_ticker()
                #trade_price = self.close_Arr[-1]*1.001
                trade_side = "openshort"
                trade_price = round(self.quantcenter.Last,self.price_N)
                trade_amount = round(self.unit,self.amount_N)
                if self.check_order(trade_side,trade_price,trade_amount):
                    order_id = self.quantcenter.openShort(trade_price,trade_amount)
                    self.sell_orders.append({ 
                               "side":trade_side,
                               "price":trade_price,
                               "amount":trade_amount,
                               "id":order_id,
                               "timestamp":Unix()})
                 '''
        ##(1)检查止盈止损单:
        for order in self.buy_orders:
            self.quantcenter.update_ticker()
            price = self.quantcenter.Last 
            ##止盈
            if price > order["price"]*1.3:
                self.quantcenter.coverLong(round(price,self.price_N),order["amount"])
                del_buy_orders.append(order)
            ##止损
            if price < order["price"]*0.9:
                self.quantcenter.coverLong(round(price,self.price_N),order["amount"])
                del_buy_orders.append(order)
        for order in self.sell_orders:
            self.quantcenter.update_ticker()
            price = self.quantcenter.Last 
            ##止盈
            if price < order["price"]*0.7:
                self.quantcenter.coverShort(round(price,self.price_N),order["amount"])
                del_sell_orders.append(order)
            ##止损
            if price > order["price"]*1.1:
                self.quantcenter.coverShort(round(price,self.price_N),order["amount"])
                del_sell_orders.append(order)            
        ##更新账户
        self.refresh_account()
        ##更新order 
        for order in del_buy_orders:
            self.buy_orders.remove(order) 
        for order in del_sell_orders:
            self.sell_orders.remove(order)
            
            
         ##update params 
        self.unit = (self.Balance*self.MarginLevel*0.01)/(self.ATR[-1])*0.1    
        
        if buy_siginal:
            self.quantcenter.update_ticker()
            #trade_price = self.close_Arr[-1]*1.001
            trade_side = "openlong"
            trade_price = round(self.quantcenter.Last,self.price_N)
            trade_amount =  round(self.unit,self.amount_N)
            if self.check_order(trade_side,trade_price,trade_amount):
                order_id = self.quantcenter.openLong(trade_price,trade_amount)
                self.buy_orders.append({ 
                               "side":trade_side,
                               "price":trade_price,
                               "amount":trade_amount,
                               "id":order_id,
                               "timestamp":Unix()})
        if sell_siginal :
            self.quantcenter.update_ticker()
            #trade_price = self.close_Arr[-1]*1.001
            trade_side = "openshort"
            trade_price = round(self.quantcenter.Last,self.price_N)
            trade_amount = round(self.unit,self.amount_N)
            if self.check_order(trade_side,trade_price,trade_amount):
                order_id = self.quantcenter.openShort(trade_price,trade_amount)
                self.sell_orders.append({ 
                               "side":trade_side,
                               "price":trade_price,
                               "amount":trade_amount,
                               "id":order_id,
                               "timestamp":Unix()})
class Args:
    amount_N = 4
    price_N = 4
    min_buy_money = 5
    min_sell_money = 5

    kline_period = PERIOD_M1
    
    ## true_period (Days)
    price_percent_period = 21
    order_max_wait_time = 3600 * 4
    price_percent_period = 7
    price_slip = 2.5e-5
    contract_type = "swap"
    MarginLevel = 10
    quantcenter = QuantCenter(exchange,contract_type,MarginLevel)        
        
def main():
    args = Args()
    strategy = Strategy(args)
    strategy.refresh_data(args.kline_period)
    Log("refresh_data ok")
    while (True):
        Sleep(1000 * 60*5 )
        # time.sleep(60)
        try:
            ## refresh_data and indicator
            strategy.refresh_data(args.kline_period)
            strategy.next()
        except:
            pass

