class  grid(bt.Strategy):
    params = (('amount_N', 4),
              ('price_N', 4),
              ("position_max_percent",1.0),
              ("price_buy_threshold",1.0),
              ("price_sell_threshold",1.0),
              ("min_buy_money",5.0),
              ("min_sell_money",5.0),
             ("name","rsi"),)
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
        self.buy_orders=[]
        self.sell_orders=[]
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
    def update_account(self,order,trade_side):
        ##update potential buy money and potential sell amount after create order 
        if trade_side == "buy":
            self.potential_buy_money =self.potential_buy_money -order.size*order.price
            self.potential_buy_amount =self.potential_buy_money/order.price
        else:
            self.potential_sell_amount = self.potential_sell_amount -order.size
            self.potential_sell_money =self.potential_sell_amount*order.price
    def trade_amount_compute(self,price,trade_side):
        price_percent = (price-self.user_Min_price)/(self.user_Max_price-self.user_Min_price)
        if  trade_side == "buy":
            ##高估区间不买入
            if price > self.user_Max_price*self.price_buy_threshold:
                return False 
            ##percent =1 amount =0  percent = 0 amount =1 
            self.min_buy_amount = self.position_max_percent*self.potential_buy_amount *(1.0-price_percent)
            self.min_buy_amount = max(self.min_buy_amount,0.0)
            self.min_buy_amount = min(self.min_buy_amount,self.potential_buy_amount)
            self.min_buy_amount = round(self.min_buy_amount,self.amount_N)
            self.min_buy_balance = self.min_buy_amount*price
            if self.min_buy_balance < self.min_buy_money:
                return False
            else:
                return True
           
        elif trade_side == "sell":
            ##低估不卖出
            if  price < self.user_Min_price*self.price_sell_threshold:
                return False 
            ##percent =1 amount =1  percent = 0 amount =0 
            self.min_sell_amount = self.position_max_percent*self.potential_sell_amount *price_percent
            self.min_sell_amount = max(self.min_sell_amount,0.0)
            self.min_sell_amount = min(self.min_sell_amount,self.potential_sell_amount)
            self.min_sell_amount = round(self.min_sell_amount,self.amount_N)
            self.min_sell_balance = self.min_sell_amount*price
            if self.min_sell_balance <self.min_sell_money:
                return False 
            else:
                return True 
    def open_order(self):
        self.update_data()
        price_percent = (self.data.close[0]-self.user_Min_price)/(self.user_Max_price-self.user_Min_price)
        if price_percent <0.618:
            trade_price =self.data.close[0]*0.9999 
            if self.trade_amount_compute(trade_price,"buy"):
                order=self.buy(self.data,size=self.min_buy_amount,price=trade_price)
                self.update_account(order,"buy")
                self.buy_orders.append(order)
                
    def deal_over_orders(self):
        if len(self.sell_orders) >5:
            self.sell_orders.sort(key=lambda x: float(x.price), reverse=True)
            del_order =self.sell_orders[0]
            self.cancel(del_order)
        if len(self.buy_orders) >5:
            self.buy_orders.sort(key=lambda x: float(x.price), reverse=False)
            del_order =self.buy_orders[0]
            self.cancel(del_order)
            
    def next(self):
        if len(self.buy_orders) + len(self.sell_orders) <2:
            self.open_order()
        buy_del_orders=[]
        sell_del_orders=[]
        new_buy_orders=[]
        new_sell_orders=[]
        ##
        for order in self.buy_orders:
            if order.status in [order.Completed]:
                buy_del_orders.append(order)
                trade_price = round(order.price+self.price_gap,self.price_N)
                new_order=self.sell(self.data,size=order.size,price=trade_price)
                self.update_account(order,"sell")
                new_sell_orders.append(new_order)
                ##添加趋势单
                trade_price =round(order.price-self.price_gap,self.price_N)
                will_trade=self.trade_amount_compute(trade_price,"buy")
                if will_trade:
                    new_order =self.buy(self.data,size=self.min_buy_amount,price=trade_price)
                    self.update_account(order,"buy")
                    new_buy_orders.append(new_order)
            elif order.status in [order.Canceled, order.Margin, order.Rejected]:
                buy_del_orders.append(order)
        for order in self.sell_orders:
            if order.status in [order.Completed]:
                sell_del_orders.append(order)
                trade_price = round(order.price-self.price_gap,self.price_N)
                new_order =self.buy(self.data,size=order.size,price=trade_price)
                self.update_account(order,"buy")
                new_buy_orders.append(new_order)
                ##趋势单
                trade_price =round(order.price+self.price_gap,self.price_N)
                will_trade = self.trade_amount_compute(trade_price,"sell")
                if will_trade:
                    new_order =self.sell(self.data,size=self.min_sell_amount,price=trade_price)
                    self.update_account(order,"sell")
                    new_sell_orders.append(new_order)
            elif order.status in [order.Canceled, order.Margin, order.Rejected]:
                sell_del_orders.append(order)
        ##deal order list 
        for order in sell_del_orders:
            self.sell_orders.remove(order)
        for order in buy_del_orders:
            self.buy_orders.remove(order)
        for order in new_buy_orders:
            self.buy_orders.append(order)
        for order in new_sell_orders:
            self.sell_orders.append(order)
            
        self.deal_over_orders()
