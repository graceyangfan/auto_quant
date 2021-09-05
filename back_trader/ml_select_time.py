class MLStrategy(bt.Strategy):
    params = (('amount_N', 4),
              ('price_N', 4),
              ("position_max_percent",1.0),
              ("price_buy_threshold",1.0),
              ("price_sell_threshold",1.0),
              ("min_buy_money",5.0),
              ("min_sell_money",5.0),)
    def __init__(self):
        self.amount_N = self.params.amount_N
        self.price_N = self.params.price_N
        self.position_max_percent = self.params.position_max_percent
        self.price_buy_threshold =self.params.price_buy_threshold 
        self.price_sell_threshold=self.params.price_sell_threshold
        self.min_buy_money=self.params.min_buy_money
        self.min_sell_money=self.params.min_sell_money
        self.highest = bt.indicators.Highest(self.data.high, period=100, subplot=False)
        self.lowest = bt.indicators.Lowest(self.data.low, period=100, subplot=False)
        ## trade record 
        self.trade_pairs=[]
    def update_data(self):
        ##account info 
        self.Balance = self.broker.getcash()
        self.Sell_price = self.data.close[0]
        self.Amount = self.getposition(self.data).size
        ##potential value 
        self.potential_buy_money =self.Balance
        self.potential_buy_amount = round(self.Balance/self.Sell_price,self.amount_N)
        self.potential_sell_money = self.Amount*self.Sell_price 
        self.potential_sell_amount = round(self.Amount,self.amount_N)
        ## params for grid 
        self.user_Max_price =self.highest[0]
        self.user_Min_price =self.lowest[0]
        self.price_gap  = (self.user_Max_price-self.user_Min_price)/10.0
    def update_account(self,order,execute_type):
        ##update potential buy money and potential sell amount after create order 
        if execute_type == "trade":
            if  order.isbuy():
                self.potential_buy_money =self.potential_buy_money -order.size*order.price
                self.potential_buy_amount =self.potential_buy_money/order.price
            else:
                self.potential_sell_amount = self.potential_sell_amount -order.size
                self.potential_sell_money =self.potential_sell_amount*order.price
        elif execute_type == "cancel":
            if order.isbuy():
                self.potential_buy_money =self.potential_buy_money +order.size*order.price
                self.potential_buy_amount =self.potential_buy_money/order.price
            else:
                self.potential_sell_amount = self.potential_sell_amount +order.size
                self.potential_sell_money =self.potential_sell_amount*order.price
                
    def check_order(self,order):
        if order.isbuy():
            if order.size*order.price<self.min_buy_money or order.size > self.potential_buy_amount:
                return False
            else:
                return True
        elif order.issell():
            if order.size*order.price<self.min_sell_money or order.size > self.potential_sell_amount:
                return False
            else:
                return True
            
    def open_order(self):
        price_percent = (self.data.close[0]-self.user_Min_price)/(self.user_Max_price-self.user_Min_price)
        if price_percent <0.618:
            trade_price =self.data.close[0]*0.9999 
            if self.trade_amount_compute(trade_price,"buy"):
                order=self.buy(self.data,size=self.min_buy_amount,price=trade_price)
                self.update_account(order,"buy")
                self.buy_orders.append(order)
                
    def next(self):
        self.update_data()  
        ##检查止盈止损单:
        del_trade_pair =[]
        for trade_pair in self.trade_pairs:
            order1 = trade_pair[0]
            order2 = trade_pair[1]
            if order1.status in[order1.Completed]:
                self.cancel(order2)
                self.update_account(order2,"cancel")
                print("cancel order1")
            if order2.status in [order2.Completed]:
                self.cancel(order1)
                self.update_account(order1,"cancel")
                print("cancel order2")
            del_trade_pair.append(trade_pair)
        for pair in del_trade_pair:
            self.trade_pairs.remove(pair)
            
        ##根据信号下单，并同时下止盈止损单
        if not self.position:
            if self.data.predicted[0] == 1:
                order = self.buy(self.data,price=self.data.close[0],size=self.potential_buy_amount)
                self.update_account(order,"trade")
                if self.check_order(order):
                    order_stop = self.sell(self.data,exectype=bt.Order.Stop,
                                      size=order.size,price=order.price*1.2)
                    order_limit = self.sell(self.data,exectype=bt.Order.Limit,
                                      size=order.size,price=order.price*0.9)
                    self.trade_pairs.append([order_stop,order_limit])
                else:
                    self.cancel(order)
                    self.update_account(order,"cancel")
        else:
            if self.data.predicted[0] == 2:
                order = self.sell(self.data,price=self.data.close[0],size=self.potential_sell_amount)
                self.update_account(order,"trade")
                if self.check_order(order):
                    pass
                else:
                    self.cancel(order)
                    self.update_account(order,"cancel")
