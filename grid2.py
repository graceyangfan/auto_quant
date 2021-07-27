###编写过程中遇到的问题以及解决办法（PS:主要是由于部分利用单无法成交引起）
###利用单成交后，不应该再挂两个探索单，因为那些很长时间没有成交的利用单和新的探索单的价格相差不多时，
###会出现挂了多个相近价格的单。
###另外要即使清理长时间无法成交的单


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
        self.trade_pair = []
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
        
    def init_orders(self):
        ##当探索和利用单都被用完了，需要选择网格的入场
        if len(self.trade_pair) < 1:
            avg_price = (self.quantcenter.Asks_Price1+self.quantcenter.Bids_Price1)/2.0
            price_percent = (avg_price-self.user_Min_price)/(self.user_Max_price-self.user_Min_price)
            ##黄金分割比例进场
            if price_percent < 0.382:
                trade_price = round(self.quantcenter.Bids_Price1*(1.0 - self.price_gap),self.price_N)
                will_trade=self.trade_amount_compute(trade_price,"buy")
                if will_trade:
                    trade_id = self.quantcenter.create_order("buy",trade_price,self.min_buy_amount)
                    if trade_id:
                        ##once create order 
                        ##update balnace and amout 
                        self.refresh_data(self.args.kline_period)
                        Exploration = { 
                               "side":"buy",
                               "price":trade_price,
                               "amount":self.min_buy_amount,
                               "id":trade_id,
                               "timestamp":Unix(),
                               "type":"Exploration"
                               }
                        self.trade_pair.append([None,Exploration])


            
    def deal_order(self):
        ##先遍历探索再遍历利用
        if len(self.trade_pair) <1 :
            self.init_orders()
        ##没有好的入场机会，不进入网格交易
        if len(self.trade_pair) < 1:
            return 0 
        ##开始处理交易对
        del_pairs = []
        new_pairs = [] 
        ##可能情况
        ##[None，探索] [利用，探索] [利用，None] [探索，探索] [None,None]
        ##取消超时订单
        for pair in self.trade_pair:
            for item in pair:
                if item is not None and  Unix() - item["timestamp"] > self.order_max_wait_time:
                    self.quantcenter.cancel_order(item["id"])
        ##检查order_status 是否已经被取消
        for i in range(len(self.trade_pair)):
            for j in range(len(self.trade_pair[i])):
                item = self.trade_pair[i][j]
                if item is not None:
                    order_state = self.quantcenter.fetch_order(item["id"])["Status"]
                    if order_state == ORDER_STATE_CANCELED:
                        self.trade_pair[i][j]=None       
        
        for pair in self.trade_pair:
            if pair[0] is None:
                if pair[1] is None:
                    del_pairs.append(pair)
                else:
                    ##pair[1] 必然是探索
                    order_status = self.quantcenter.fetch_order(pair[1]["id"])["Status"]
                    if order_status == ORDER_STATE_CLOSED:
                        del_pairs.append(pair)
                        ##下新的订单
                        new_pairs.append(self.create_pair_order(pair[1]))
            elif pair[0]["type"] == "Exploration":
                order_status0 = self.quantcenter.fetch_order(pair[0]["id"])["Status"]
                if order_status0 == ORDER_STATE_CLOSED:
                    del_pairs.append(pair)
                    ##取消订单2 
                    if pair[1] is not None:
                        self.quantcenter.cancel_order(pair[1]["id"])
                        ##下新的订单
                    new_pairs.append(self.create_pair_order(pair[0]))
                if pair[1] is not None:
                    order_status1 = self.quantcenter.fetch_order(pair[1]["id"])["Status"]
                    if order_status1 == ORDER_STATE_CLOSED:
                        del_pairs.append(pair)
                        ##取消订单1
                        self.quantcenter.cancel_order(pair[0]["id"])
                        ##下新的订单
                        new_pairs.append(self.create_pair_order(pair[1])) 
            elif pair[0]["type"] == "Exploitation":
                order_status0 = self.quantcenter.fetch_order(pair[0]["id"])["Status"]
                if order_status0 == ORDER_STATE_CLOSED:
                    del_pairs.append(pair)
                    if pair[1] is not None:
                        self.quantcenter.cancel_order(pair[1]["id"])
                else:
                    if pair[1] is not None:
                        order_status1 = self.quantcenter.fetch_order(pair[1]["id"])["Status"]
                        if order_status1 == ORDER_STATE_CLOSED:
                            del_pairs.append(pair)
                            new_pairs.append([pair[0],None])
                            ##下新的订单
                            new_pairs.append(self.create_pair_order(pair[1]))
                                             
        for pair in del_pairs:
            self.trade_pair.remove(pair)
        for pair in new_pairs:
            self.trade_pair.append(pair)
                    
    def  create_order_in_grid(self,closed_order,trade_side,trade_type):
        if trade_side == "sell":
            trade_price = round(closed_order["price"] *(1.0 + self.price_gap),self.price_N)
            trade_price = max(trade_price,self.quantcenter.Asks_Price1)
        else:
            trade_price = round(closed_order["price"] *(1.0 - self.price_gap),self.price_N)
            trade_price = min(trade_price,self.quantcenter.Bids_Price1)
        ##trade_amount 
        ##探索按照价格设定买卖
        if  trade_type == "Exploration":
            will_trade=self.trade_amount_compute(trade_price,trade_side)
            if will_trade and trade_side == "buy":
                trade_amount = self.min_buy_amount 
            elif will_trade and trade_side == "sell":
                trade_amount = self.min_sell_amount 
            else:
                return None
        else:
            trade_amount = closed_order["amount"]

        trade_id = self.quantcenter.create_order(trade_side,trade_price,trade_amount)
        self.refresh_data(self.args.kline_period)

        return  {   "side":trade_side,
                    "price":trade_price,
                    "amount":trade_amount,
                    "id":trade_id,
                    "timestamp":Unix(),
                    "type":trade_type }

    def create_pair_order(self,closed_order):
        anit_dict={"buy":"sell","sell":"buy"}
        if closed_order["type"] == "Exploitation":
            ##利用单完成下两个探索单
            order1 = self.create_order_in_grid(closed_order,"sell","Exploration")
            order2 = self.create_order_in_grid(closed_order,"buy","Exploration")
        else:
            ##探索单完成下一个利用一个探索
            order1 = self.create_order_in_grid(closed_order,anit_dict[closed_order["side"]],"Exploitation")
            order2 = self.create_order_in_grid(closed_order,closed_order["side"],"Exploration")
        return [order1,order2]
    
 ## main 
## define args 
class Args():
    amount_N = 4
    price_N = 4
    min_buy_money =5 
    min_sell_money =5 
    
    kline_period = PERIOD_M5
    position_max_percent = 0.1 
    price_threshold = {"buy":0.999,
                      "sell":1.001}
    ## true_period (Days) 
    price_percent_period =  7
    price_gap = 0.01
    trade_amount_constant = 1 
    max_orders =  5
    order_max_wait_time = 60*60*12
    quantcenter= QuantCenter(exchange) 
    

def main():
    
    args = Args() 
    strategy = Strategy(args) 
    strategy.refresh_data(args.kline_period)
    ##create init order 
    strategy.init_orders()
    Log("refresh_data ok")
    while(True):
        Sleep(1000*60*5)
        #time.sleep(60)
        try:
            ## refresh_data and indicator 
            strategy.refresh_data(args.kline_period)
            strategy.deal_order()  
        except:
                pass 
