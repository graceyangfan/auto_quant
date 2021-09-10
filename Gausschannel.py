def Gaussfilter(source,period=144,poles=4):
    "https://ctrader.com/algos/indicators/show/150"
    beta = (1 - np.cos(2*np.pi/period))/(np.power(np.sqrt(2),2.0/poles) - 1)
    alpha = -beta + np.sqrt(beta*(beta + 2))
    coeff = 1.0 - alpha;
    alphaPow = np.power(alpha, poles)
    Results = [] 
    for index in range(poles):
        Results.append(source.iloc[index])
    for index in range(poles,len(source)):
        result = alphaPow * source.iloc[index] + poles * coeff * Results[-1]
        if poles == 4:
            result -= 6 * np.power(coeff, 2.0) * Results[-2]-4*np.power(coeff,3.0)*Results[-3]+np.power(coeff, 4.0)*Results[-4]
        elif poles == 3:
            result -= 3 * np.power(coeff, 2.0) * Results[-2]- np.power(coeff,3.0)*Results[-3]
        elif poles == 2:
            result -= np.power(coeff, 2.0) * Results[-2]
        Results.append(result)
    return Results 

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
        ## 止盈止损单对
        self.trade_pairs=[]
    def refresh_account(self):
        self.quantcenter.refresh_account()
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
        self.hlc3 = (self.high_Arr+self.low_Arr+self.close_Arr)/3
        self.ATR = TA.ATR(self.high_Arr,self.low_Arr,self.close_Arr,14)
        self.unit = int((self.Balance*self.MarginLevel)/(self.ATR))/self.quantcenter.Last
    def check_order(self,order):
        if order.Type == ORDER_TYPE_BUY:
            if  order.Amount*order.Price/self.MarginLevel<self.min_buy_money or order.Amount > self.potential_buy_amount:
                return False
            else:
                return True
        elif order.Type == ORDER_TYPE_SELL:
            if order.Amount*order.Price/self.MarginLevel<self.min_sell_money or order.Amount > self.potential_sell_amount:
                return False
            else:
                return True
    def next(self):
        ##检查止盈止损单:
        del_trade_pair =[]
        for trade_pair in self.trade_pairs:
            order1 = trade_pair[0]
            order2 = trade_pair[1]
            if order1.Status in[ORDER_STATE_CLOSED]:
                self.quantcenter.cancel(order2)
                self.refresh_account()
                print("cancel order1")
            if order2.Status in [ORDER_STATE_CLOSED]:
                self.quantcenter.cancel(order1)
                self.refresh_account()
            del_trade_pair.append(trade_pair)
        for pair in del_trade_pair:
            self.trade_pairs.remove(pair)
        ##compute Indicator 
        mid = Gaussfilter(self.hlc3)
        hband = mid + 1.44*self.ATR 
        lband = mid - 1.44*self.ATR 
        ##开单
        upcross = mid[-1] > mid [-2] and mid[-3] > mid[-2] and self.close_Arr[-1] > hband[-1]
        downcross = mid[-1] < mid [-2] and mid[-3] < mid[-2] and self.close_Arr[-1] < lband[-1]
        if upcross:
            #self.quantcenter.update_ticker()
            trade_price = self.close_Arr[-1]*1.001
            trade_amount = self.unit
            order = self.quantcenter.openLong(trade_price,trade_amount)
            ##止盈止损单
            delta_price = abs(self.close_Arr[-1] - mid[-1])
            stoploss_order = self.quantcenter.coverLong(mid[-1],trade_amount)
            stopwin_order  = self.quantcenter.coverLong(mid[-1]+1.5*delta_price,trade_amount)
            self.trade_pairs.append([stoploss_order,stopwin_order])
        if downcross:
            #self.quantcenter.update_ticker()
            trade_price = self.close_Arr[-1]*0.9999
            trade_amount = self.unit
            order = self.quantcenter.openShort(trade_price,trade_amount)
            ##止盈止损单
            delta_price = abs(mid[-1] -self.close_Arr[-1])
            stoploss_order = self.quantcenter.coverShort(mid[-1],trade_amount)
            stopwin_order  = self.quantcenter.coverShort(mid[-1]-1.5*delta_price,trade_amount)
            self.trade_pairs.append([stoploss_order,stopwin_order])
          
    
