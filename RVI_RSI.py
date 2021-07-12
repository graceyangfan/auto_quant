import numpy as np 
import talib as TA
import pandas as pd 

class QuantCenter():
    def __init__(self,exchange):
        self.init_timestamp = time.time()
        self.exchange = exchange
        self.name = self.exchange.GetName()
        self.currency = self.exchange.GetCurrency()      
    def get_account(self):
        self.Balance = None
        self.Amount = None
        self.FrozenBalance = None
        self.FrozenStocks = None
        
        try:
            self.account = self.exchange.GetAccount()

            self.Balance =  self.account['Balance']
            self.Amount = self.account['Stocks']
            self.FrozenBalance =  self.account['FrozenBalance']
            self.FrozenStocks = self.account['FrozenStocks']
            return True
        except:
            return False
    def get_ticker(self):

        self.High = None
        self.Low = None
        self.Sell =  None
        self.Buy =  None
        self.Last =  None
        self.Volume = None
        
        try:
            self.ticker = self.exchange.GetTicker()
        
            self.High = self.ticker['High']
            self.Low = self.ticker['Low']
            self.Sell =  self.ticker['Sell']
            self.Buy =  self.ticker['Buy']
            self.Last =  self.ticker['Last']
            self.Volume = self.ticker['Volume']
            return True
        except:
            return False
        
        
    def get_depth(self):
        self.Ask = None
        self.Bids = None
        
        try:
            self.Depth = self.exchange.GetDepth()
            self.Ask = self.Depth['Asks']
            self.Bids = self.Depth ['Bids']
            return True
        except:
            return False
        
        
    
    def get_kline(self, period = PERIOD_M5):
        
        self.Kline = exchange.GetRecords(period)

        
        
    def create_order(self, order_type, price, amount):
        if order_type == 'buy':
            try:
                order_id = self.exchange.Buy( price, amount)
            except:
                return False
            
        elif order_type == 'sell':
            try:
                order_id = self.exchange.Sell( price, amount)
            except:
                return False
        
        return order_id
    
    def get_orders(self):
        self.undo_ordes = self.exchange.GetOrders()
        return self.undo_ordes
    
    def cancel_order(self, order_id):

        return self.exchange.CancelOrder(order_id)
        
    def refresh_data(self,period = PERIOD_M5):

        if not self.get_account():
            return 'false_get_account'
        
        if not self.get_ticker():
            return 'false_get_ticker'
        if not self.get_depth():
            return 'false_get_depth'
        try:
            self.get_kline(period)
        except:
            return 'false_get_K_line_info'
        
        return 'refresh_data_finish!'

    
## define Stragety 

class Strategy():
    def __init__(self,args):
        self.quantcenter = args.quantcenter
        
        self.init_time = time.time()
        self.last_time = time.time()
        
        self.amount_N = args.amount_N
        self.price_N = args.price_N
        self.RSI_threshold = args.RSI_threshold
        self.RVI_threshold = args.RVI_threshold
        self.trade_list = []
        
        self.min_buy_money=args.min_buy_money
        self.min_sell_money=args.min_sell_money
        self.quantcenter.get_kline(PERIOD_M5)
        self.kline = pd.DataFrame(self.quantcenter.Kline)
        self.close_Arr= self.kline["Close"].to_numpy()
    
        
    def refresh_data(self,period):
        
        self.quantcenter.refresh_data(period)
        self.Amount = self.quantcenter.Amount
        self.Balance = self.quantcenter.Balance
        self.Buy_price = self.quantcenter.Buy
        self.Sell_price = self.quantcenter.Sell
        self.potential_buy_amount = round(self.Balance/self.Sell_price,self.amount_N)
        self.potential_sell_amount = round(self.Amount,self.amount_N)
        
        
    def make_trade_by_dict(self, trade_dicts):
        for trade in trade_dicts:
            trade_price = round(trade["price"],self.price_N)
            trade_amount=round(trade["amount"],self.amount_N)
            trade_id=self.quantcenter.create_order(trade["side"],trade_price,trade_amount)
            self.trade_list.append(trade_id)
            
    def trade_amount_compute(self,trade_side):
        ##200 日最高和最低价格 2*101 天
        my_dataset = pd.DataFrame(self.quantcenter.exchange.GetRecords(24*3600*2))
        Max_price = my_dataset.High.max()
        Min_price = my_dataset.Low.min()
        price_percent = (self.close_Arr[-1]-Min_price)/(Max_price-Min_price)
        if  trade_side == "buy":
            ##percent =1 amount =0  percent = 0 amount =1 
            self.min_buy_amount = self.potential_buy_amount *(1.0-price_percent)
            self.min_buy_amount = max(self.min_buy_amount,0.0)
            self.min_buy_amount = min(self.min_buy_amount,self.potential_buy_amount)
            self.min_buy_amount = round(self.min_buy_amount,self.amount_N)
            self.min_buy_balance = self.min_buy_amount*self.Buy_price
            if self.min_buy_balance < self.min_buy_money:
                return False
            else:
                return True
           
        elif trade_side == "sell":
            ##percent =1 amount =1  percent = 0 amount =0 
            self.min_sell_amount = self.potential_sell_amount *price_percent
            self.min_sell_amount = max(self.min_sell_amount,0.0)
            self.min_sell_amount = min(self.min_sell_amount,self.potential_sell_amount)
            self.min_sell_amount = round(self.min_sell_amount,self.amount_N)
            self.min_sell_balance = self.min_sell_amount*self.Sell_price
            if self.min_sell_balance <self.min_sell_money:
                return False 
            else:
                return True 
    
    def strategy_condition(self,std_period,nbdev,moving_period):
        
        ## use for data_process 
        ## in fmz every time refresh Kline length is 101 
       # Log("start strategy_condition compute")
        ## self.quantcenter.Kline is not update  or change smooth 
       
        #Log("Kline is update ")
        self.kline = pd.DataFrame(self.quantcenter.Kline)
        self.close_Arr= self.kline["Close"].to_numpy()
        ##https://www.marketvolume.com/technicalanalysis/relativevolatilityindex.asp    
        close_std = TA.STDDEV(self.close_Arr, std_period,nbdev)
        ## 
        u = np.zeros(len(close_std)-1)
        d = np.zeros(len(close_std)-1)
        for i in range(1,len(close_std)):
            if close_std[i] > close_std[i-1]:
                u[i-1] = close_std[i] 
            else:
                d[i-1] = close_std[i] 
        ## nan to 0 
        u = np.nan_to_num(u)
        d = np.nan_to_num(d)
        
        ##compute rolling average 
        Usum = TA.MA(u,moving_period)
        Dsum = TA.MA(d,moving_period)  
        ## numpy 数组直接加减乘除
        rvi = 100 * Usum /(Usum + Dsum)
        ##RSI 
        rsi=TA.RSI(self.close_Arr)
        #Log("rsi",rsi[-1])
        trade_side = False
        if rvi[-1] > self.RVI_threshold + 50 and rsi[-1] > self.RSI_threshold + 50:
            trade_side = "buy"
        if rvi[-1] < 50 - self.RVI_threshold and rsi[-1] < 50 - self.RSI_threshold:
            trade_side = "sell"
        return trade_side 
    def make_trade_dicts(self,std_period,nbdev,moving_period):
        # 趋势判定是否买卖["buy","sell",False]
        Strategy_state = self.strategy_condition(std_period,nbdev,moving_period)
        if Strategy_state:
            Log("Strategy_state",Strategy_state)
        ##(also update self.close_Arr in strategy_condition)
        if Strategy_state is False:
            return False 
        ##compute Asset_state 
        Asset_state = self.trade_amount_compute(Strategy_state)
        if Asset_state:
            trade_dicts = []
            if Strategy_state == "buy":
                trade_dicts.append(
                {
                    "side":"buy",
                    "price":round(self.Buy_price,self.amount_N),
                    "amount":self.min_buy_amount
                })
            elif Strategy_state == "sell":
                trade_dicts.append(
                {
                    "side":"sell",
                    "price":round(self.Sell_price,self.amount_N),
                    "amount":self.min_sell_amount
                })
            return trade_dicts
        else:
            return False
 ## main 
## define args 
class Args():
    amount_N = 4
    price_N = 4
    min_buy_money =5 
    min_sell_money =5 
    std_period = 10 
    nbdev =  2.0
    moving_period = 10 
    RSI_threshold = 15  ## [0,50 ]
    RVI_threshold = 20  ## [0,50 ]
    quantcenter= QuantCenter(exchange) 
    

def main():
    
    args = Args() 
    strategy = Strategy(args) 
    strategy.refresh_data(PERIOD_M5)
    Log("refresh_data ok")
    while(True):
        Sleep(1000*60*5)
        #time.sleep(60)
        try:
            strategy.refresh_data(PERIOD_M5)
            now_trade_dicts = strategy.make_trade_dicts(args.std_period,args.nbdev,args.moving_period)
            if now_trade_dicts:
                strategy.make_trade_by_dict(now_trade_dicts)
                now_trade_dicts =False
        except:
                pass 

