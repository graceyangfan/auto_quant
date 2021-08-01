import numpy as np 
import talib as TA
import pandas as pd 

class QuantCenter():
    def __init__(self,exchange):
        self.init_timestamp = time.time()
        self.exchange = exchange
        self.name = self.exchange.GetName()
        self.currency = self.exchange.GetCurrency()      
    def update_account(self):
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
    def update_ticker(self):

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
        
        
    def update_depth(self):
        self.Asks = None
        self.Bids = None
        self.Asks_Price1= None 
        self.Asks_Amount1 = None 
        self.Bids_Price1= None 
        self.Bids_Amount1 = None 
        try:
            self.Depth = self.exchange.GetDepth()
            self.Asks = self.Depth['Asks']
            self.Bids = self.Depth ['Bids']
            ##最小卖最大买
            self.Asks_Price1 = self.Asks[0]["Price"]
            self.Asks_Amount1 = self.Asks[0]["Amount"]
            self.Bids_Price1 = self.Bids[0]["Price"]
            self.Bids_Amount1 = self.Bids[0]["Amount"] 
            return True
        except:
            return False
        
        
    
    def update_kline(self, period = PERIOD_M5):
        try:
            self.Kline = exchange.GetRecords(period)
            return True 
        except:
            return False 

        
        
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
    
    def fetch_order(self,id):
        ##    Log("Id:", order["Id"], "Price:", order["Price"], "Amount:", order["Amount"], "DealAmount:", 
        ##    order["DealAmount"], "Status:", order["Status"], "Type:", order["Type"])
        return self.exchange.GetOrder(id)
    def fetch_uncomplete_orders(self):
        #获取所有未完成的订单
        return self.exchange.GetOrders()
    
    def cancel_order(self, order_id):
        ## return True or False 
        return self.exchange.CancelOrder(order_id)
        
    def refresh_data(self,period = PERIOD_M5):

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
    
    def fetch_kline(self, period = PERIOD_M5):
        return  self.exchange.GetRecords(period)
    def fetch_ticker(self):
        return self.exchange.GetTicker()
    def fetch_depth(self):
        return self.exchange.GetDepth()


## define Stragety 
class Strategy():
    def __init__(self,args):
        self.args =args 
        self.quantcenter = args.quantcenter
        
        self.init_time = time.time()
        self.last_time = time.time()
        
        self.amount_N = args.amount_N
        self.price_N = args.price_N
        
        self.min_buy_money=args.min_buy_money
        self.min_sell_money=args.min_sell_money
        self.quantcenter.update_kline(args.kline_period)
        self.kline = pd.DataFrame(self.quantcenter.Kline)
        ##record orders
        self.buy_orders = []
        self.sell_orders = [] 
         ## strategy params 
        self.price_threshold = args.price_threshold 
        self.position_max_percent = args.position_max_percent 
        self.price_percent_period = args.price_percent_period
        self.user_price_period = int(self.price_percent_period/len(self.kline)*24*3600 )
        self.slip_gap = args.slip_gap
        
        
    def refresh_data(self,period):
        
        self.quantcenter.refresh_data(period)
        self.Amount = self.quantcenter.Amount
        self.Balance = self.quantcenter.Balance
        self.Buy_price = self.quantcenter.Buy
        self.Sell_price = self.quantcenter.Sell
        self.potential_buy_amount = round(self.Balance/self.Sell_price,self.amount_N)
        self.potential_sell_amount = round(self.Amount,self.amount_N)
        
        ##update arr will be used in indicator 
        self.kline = pd.DataFrame(self.quantcenter.Kline)
        self.close_Arr= self.kline["Close"].to_numpy()
        self.high_Arr= self.kline["High"].to_numpy()
        self.low_Arr= self.kline["Low"].to_numpy() 
        ##update user_define_price_percent 
        self.user_dataset = pd.DataFrame(self.quantcenter.fetch_kline(self.user_price_period))
        self.user_Max_price = self.user_dataset.High.max()
        self.user_Min_price = self.user_dataset.Low.min()
            
    def trade_amount_compute(self,price,trade_side):
        price_percent = (price-self.user_Min_price)/(self.user_Max_price-self.user_Min_price)
        if  trade_side == "buy":
            ##高估区间不买入
            if price > self.user_Max_price*self.price_threshold["buy"]:
                return False 
            ##percent =1 amount =0  percent = 0 amount =1 
            self.min_buy_amount = self.position_max_percent*self.Balance/price *(1.0-price_percent)
            self.min_buy_amount = max(self.min_buy_amount,0.0)
            self.min_buy_amount = min(self.min_buy_amount,self.Balance/price)
            self.min_buy_amount = round(self.min_buy_amount,self.amount_N)
            self.min_buy_balance = self.min_buy_amount*price
            if self.min_buy_balance < self.min_buy_money:
                return False
            else:
                return True
           
        elif trade_side == "sell":
            ##低估不卖出
            if  price < self.user_Min_price*self.price_threshold["sell"]:
                return False 
            ##percent =1 amount =1  percent = 0 amount =0 
            self.min_sell_amount = self.position_max_percent*self.Amount *price_percent
            self.min_sell_amount = max(self.min_sell_amount,0.0)
            self.min_sell_amount = min(self.min_sell_amount,self.Amount)
            self.min_sell_amount = round(self.min_sell_amount,self.amount_N)
            self.min_sell_balance = self.min_sell_amount*price
            if self.min_sell_balance <self.min_sell_money:
                return False 
            else:
                return True 
 
    def next(self):
        macd = TA.MACD(self.close_Arr,self.args.short_period,self.args.long_period,self.args.signal_period)
        dif = macd[0]
        dea = macd[1]
        val = macd[2] 
        cross_over = dif[-2] >0 and dea[-2] >0
        cross_below = dif[-2] < 0 and dea[-2] <0
        ##
        rsi=TA.RSI(self.close_Arr,self.args.RSI_period)
        ##相差过小，错误的信号
        ##if abs(val[-2])<40:
            ##return False 
        ##RSI跑步进入高区，买入，跑步离开高区卖出
        ##RSI跑步进入低区
        if cross_over and rsi[-1] - rsi[-2] >self.args.RSI_v_threshold:
            trade_price = round(self.quantcenter.Bids_Price1*(1.0 + self.slip_gap),self.price_N)
            will_trade=self.trade_amount_compute(trade_price,"buy")
            if will_trade:
                trade_id = self.quantcenter.create_order("buy",trade_price,self.min_buy_amount)
                if trade_id:
                    self.refresh_data(self.args.kline_period)
                    self.buy_orders.append({ 
                               "side":"buy",
                               "price":trade_price,
                               "amount":self.min_buy_amount,
                               "id":trade_id,
                               "timestamp":Unix()})
        if cross_below and rsi[-1] - rsi[-2] < - self.args.RSI_v_threshold:
            trade_price = round(self.quantcenter.Asks_Price1*(1.0 + self.slip_gap),self.price_N)
            will_trade=self.trade_amount_compute(trade_price,"sell")
            if will_trade:
                trade_id = self.quantcenter.create_order("sell",trade_price,self.min_sell_amount)
                if trade_id:
                    self.refresh_data(self.args.kline_period)
                    self.sell_orders.append({ 
                               "side":"sell",
                               "price":trade_price,
                               "amount":self.min_sell_amount,
                               "id":trade_id,
                               "timestamp":Unix()})
        
    
 ## main 
## define args 
class Args():
    amount_N = 4
    price_N = 4
    min_buy_money =5 
    min_sell_money =5 
    
    kline_period = PERIOD_M5
    position_max_percent = 0.5 
    price_threshold = {"buy":0.999,
                      "sell":1.001}
    ## true_period (Days) 
    price_percent_period =  15
    slip_gap = 2.5e-5
    short_period = 12
    long_period = 16
    signal_period = 9
    RSI_v_threshold = 3
    RSI_period = 14
    quantcenter= QuantCenter(exchange) 
    

def main():
    
    args = Args() 
    strategy = Strategy(args) 
    strategy.refresh_data(args.kline_period)
    Log("refresh_data ok")
    while(True):
        Sleep(1000*60*5)
        #time.sleep(60)
        try:
            ## refresh_data and indicator 
            strategy.refresh_data(args.kline_period)
            strategy.next()  
        except:
                pass 
