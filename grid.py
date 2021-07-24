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
        self.price_gap = args.price_gap
        self.trade_amount_constant = args.trade_amount_constant 
        self.max_orders = args.max_orders 
        self.order_max_wait_time = args.order_max_wait_time
        
        
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
        
        
    def deal_over_orders(self):
        if len(self.buy_orders)+len(self.sell_orders) < 1:
            avg_price = (self.quantcenter.Asks_Price1+self.quantcenter.Bids_Price1)/2.0
            price_percent = (avg_price-self.user_Min_price)/(self.user_Max_price-self.user_Min_price)
            ##过低开多单,过高开空单
            if price_percent < 0.5:
                trade_price = round(self.quantcenter.Bids_Price1*(1.0 - self.price_gap),self.price_N)
                will_trade=self.trade_amount_compute(trade_price,"buy")
                if will_trade:
                    trade_id = self.quantcenter.create_order("buy",trade_price,self.min_buy_amount)
                    if trade_id:
                        ##once create order 
                        ##update balnace and amout 
                        self.quantcenter.update_account()
                        self.buy_orders.append({ 
                               "side":"buy",
                               "price":trade_price,
                               "amount":self.min_buy_amount,
                               "id":trade_id,
                               "timestamp":Unix()})
            else:
                trade_price = round(self.quantcenter.Asks_Price1*(1.0 + self.price_gap),self.price_N)
                will_trade=self.trade_amount_compute(trade_price,"sell")
                if will_trade:
                    trade_id = self.quantcenter.create_order("sell",trade_price,self.min_sell_amount)
                    if trade_id:
                        ##once create order 
                        ##update balnace and amout 
                        self.quantcenter.update_account()
                        self.sell_orders.append({ 
                               "side":"sell",
                               "price":trade_price,
                               "amount":self.min_sell_amount,
                               "id":trade_id,
                               "timestamp":Unix()})
                
        ##取消高价买入订单，低价卖出订单
        if len(self.buy_orders) > int(self.max_orders):
            trade_list = sorted(self.buy_orders,key = lambda x: float(x["price"]), reverse=True)
            cancel_order=trade_list[0]
            if self.quantcenter.cancel_order(cancel_order["id"]):
                self.quantcenter.update_account()
                self.buy_orders.remove(cancel_order)
    
        if len(self.sell_orders) > int(self.max_orders):
            trade_list = sorted(self.sell_orders,key = lambda x: float(x['price']), reverse=False) 
            cancel_order=trade_list[0]
            if self.quantcenter.cancel_order(cancel_order["id"]):
                self.quantcenter.update_account()
                self.sell_orders.remove(cancel_order)
            
    def deal_order(self):
        buy_del_orders = []
        sell_del_orders = []
        new_buy_orders = []
        new_sell_orders = [] 
        ##deal buy orders 
        trade_list = sorted(self.buy_orders,key = lambda x: float(x["price"]), reverse=True)
        ##new orders should not be remove 
        for order in trade_list:
            order_state = self.quantcenter.fetch_order(order["id"])["Status"]
            if order_state == ORDER_STATE_CLOSED:
                buy_del_orders.append(order)
                ##止盈单
                trade_price = round(order["price"] *(1.0 + self.price_gap),self.price_N)
                trade_id = self.quantcenter.create_order("sell",trade_price,order["amount"])
                if trade_id:
                    self.quantcenter.update_account()
                    new_sell_orders.append({ 
                           "side":"sell",
                           "price":trade_price,
                           "amount":order["amount"],
                           "id":trade_id,
                           "timestamp":Unix()})
        
                ##趋势单
                trade_price = round(order["price"] *(1.0 - self.price_gap),self.price_N)
                will_trade=self.trade_amount_compute(trade_price,"buy")
                if will_trade:
                    self.quantcenter.update_account()
                    trade_id = self.quantcenter.create_order("buy",trade_price,self.min_buy_amount)
                    if trade_id:
                        new_buy_orders.append({ 
                               "side":"buy",
                               "price":trade_price,
                               "amount":self.min_buy_amount,
                               "id":trade_id,
                               "timestamp":Unix()})
            elif order_state == ORDER_STATE_CANCELED:
                buy_del_orders.append(order) 
            else:
                ## 快进快出，如果订单已经存在较长的时间还未成交应该取消订单
                if  Unix() - order["timestamp"] > self.order_max_wait_time:
                    self.quantcenter.cancel_order(order["id"])
                    buy_del_orders.append(order) 
 

        for order in buy_del_orders:
            self.buy_orders.remove(order)
        ##卖单处理
        trade_list = sorted(self.sell_orders,key = lambda x: float(x["price"]), reverse=False)
        for order in trade_list:
            order_state = self.quantcenter.fetch_order(order["id"])["Status"]
            if order_state == ORDER_STATE_CLOSED:
                sell_del_orders.append(order)
            
                trade_price = round(order["price"] *(1.0 - self.price_gap),self.price_N)
                trade_id = self.quantcenter.create_order("buy",trade_price,order["amount"])  
                if trade_id:
                    self.quantcenter.update_account()
                    new_buy_orders.append({ 
                           "side":"buy",
                           "price":trade_price,
                           "amount":order["amount"],
                           "id":trade_id,
                           "timestamp":Unix()})
                ##高处下卖单
                trade_price = round(order["price"] *(1.0 + self.price_gap),self.price_N)
                will_trade=self.trade_amount_compute(trade_price,"sell")
                if will_trade:
                    trade_id = self.quantcenter.create_order("sell",trade_price,self.min_sell_amount)
                    if trade_id:
                        self.quantcenter.update_account()
                        new_sell_orders.append({ 
                               "side":"sell",
                               "price":trade_price,
                               "amount":self.min_sell_amount,
                               "id":trade_id,
                               "timestamp":Unix()})
            elif order_state == ORDER_STATE_CANCELED:
                sell_del_orders.append(order) 
            else:
                ## 快进快出，如果订单已经存在较长的时间还未成交应该取消订单
                if  Unix() - order["timestamp"] > self.order_max_wait_time:
                    self.quantcenter.cancel_order(order["id"])
                    sell_del_orders.append(order) 
            
        for order in sell_del_orders:
            self.sell_orders.remove(order)
    
    
        ## add new order 
        for order in new_buy_orders:
            self.buy_orders.append(order)
        for order in new_sell_orders:
            self.sell_orders.append(order)
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
    price_percent_period =  21
    price_gap = 0.005
    trade_amount_constant = 1 
    max_orders =  5
    order_max_wait_time = 1800
    quantcenter= QuantCenter(exchange) 
    

def main():
    
    args = Args() 
    strategy = Strategy(args) 
    strategy.refresh_data(args.kline_period)
    ##create init order 
    strategy.deal_over_orders()
    Log("refresh_data ok")
    while(True):
        Sleep(1000*60*60)
        #time.sleep(60)
        try:
            ## refresh_data and indicator 
            strategy.refresh_data(args.kline_period)
            strategy.deal_order()  
            strategy.deal_over_orders()
        except:
                pass 
