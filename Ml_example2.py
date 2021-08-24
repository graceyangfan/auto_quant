
import numpy as np
import talib as TA
import pandas as pd
import lightgbm as lgb
class QuantCenter():
    def __init__(self, exchange):
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

            self.Balance = self.account['Balance']
            self.Amount = self.account['Stocks']
            self.FrozenBalance = self.account['FrozenBalance']
            self.FrozenStocks = self.account['FrozenStocks']
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
            try:
                order_id = self.exchange.Buy(price, amount)
            except:
                return False

        elif order_type == 'sell':
            try:
                order_id = self.exchange.Sell(price, amount)
            except:
                return False

        return order_id

    def fetch_order(self, id):
        ##    Log("Id:", order["Id"], "Price:", order["Price"], "Amount:", order["Amount"], "DealAmount:",
        ##    order["DealAmount"], "Status:", order["Status"], "Type:", order["Type"])
        return self.exchange.GetOrder(id)

    def fetch_uncomplete_orders(self):
        # 获取所有未完成的订单
        return self.exchange.GetOrders()

    def cancel_order(self, order_id):
        ## return True or False
        return self.exchange.CancelOrder(order_id)

    def refresh_data(self, period=PERIOD_M5):

        #if not self.update_account():
            #return 'false_get_account'

        #if not self.update_ticker():
           # return 'false_get_ticker'
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
    
def get_model_input(df):
    df["CCI"]=TA.CCI(df.High, df.Low, df.Close, timeperiod=14)
    df["BOP"] = TA.BOP(df.Open, df.High, df.Low, df.Close)
    df["MV_1"]=df.Close.diff(1)*df.Volume 
    df["fastk"], df["fastd"] = TA.STOCHF(df.High, df.Low, df.Close, fastk_period=5, fastd_period=3, fastd_matype=0)
    df["SRSI_fastk"],df["SRSI_fastd"] =TA.STOCHRSI(df.Close, timeperiod=14, fastk_period=5, fastd_period=3, fastd_matype=0)
    df["aroondown"], df["aroonup"] = TA.AROON(df.High, df.Low, timeperiod=14)
    df["slowk"], df["slowd"] = TA.STOCH(df.High, df.Low, df.Close, fastk_period=5, slowk_period=3, slowk_matype=0, slowd_period=3, slowd_matype=0)
    dif,dea,val =TA.MACD(df.Close,12,26,9)
    df["macd_dif"]= dif -dea
    df["macd_dif_dif"]=df["macd_dif"].diff()
    df["ULTOSC"]=TA.ULTOSC(df.High, df.Low, df.Close, timeperiod1=7, timeperiod2=14, timeperiod3=28)
    df["RSI"]=TA.RSI(df.Close)
    df["Dochian_upper"]=TA.MAX(df["High"],20)-df["Close"]
    df["Dochian_lower"]=df["Close"]-TA.MIN(df["Low"],10)
    df["MFI"]=TA.MFI(df.High,df.Low,df.Close,df.Volume)
    df["MINUS_DI"]=TA.MINUS_DI(df.High, df.Low, df.Close, timeperiod=14)
    df["PLUS_DI"]=TA.PLUS_DI(df.High, df.Low, df.Close, timeperiod=14)
    df["VP_diff"]=TA.MA(df.Close*df.Volume,100)-TA.MA(df.Close*df.Volume,169)
    df["VP_diff_dif"]=df["VP_diff"].diff()
    df["ADX"]=TA.ADX(df.High, df.Low, df.Close, timeperiod=14)
    df["TSM"]=TA.MA(df.Close.diff(),14)/TA.MA(df.High-df.Low,14)
    df["CMO"]=TA.CMO(df.Close, timeperiod=14)
    df["TRIX"]=TA.TRIX(df.Close,18)
    df["VO"]=TA.MA(df.Volume,14)/TA.MA(df.Volume,34)
    df["ADXR"]=TA.ADXR(df.High, df.Low, df.Close, timeperiod=14)
    df["DX"]= TA.DX(df.High, df.Low, df.Close, timeperiod=14)
    df["macd"], df["macdsignal"], df["macdhist"] =TA.MACDEXT(df.Close, fastperiod=12, fastmatype=0, slowperiod=26, slowmatype=0, signalperiod=9, signalmatype=0)
    columns=['macdhist','fastd','DX','ADXR','VO','TRIX','SRSI_fastk','macd_dif','CMO','Dochian_upper','TSM','ADX','VP_diff_dif','PLUS_DI','MINUS_DI',
     'MFI','Dochian_lower','RSI','ULTOSC','macd_dif_dif','slowk','slowd','Volume','aroonup','aroondown','SRSI_fastd','fastk',
     'MV_1','BOP','CCI']
    df.dropna(inplace=True)
    df=df[columns]
    x=df.iloc[-1].values
    x=x.reshape(1,x.shape[0])
    return x

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
        self.quantcenter.update_kline(args.kline_period)
        self.kline = pd.DataFrame(self.quantcenter.Kline)
        ##record orders
        self.status = {}
        self.buy_orders = []
        self.sell_orders = []
        ##局部信息周期
        self.price_percent_period = args.price_percent_period
        self.user_price_period = int(self.price_percent_period / len(self.kline) * 24 * 3600)
        ##price slip  和 未成交订单最长存在时间
        self.price_slip = args.price_slip 
        self.order_max_wait_time = args.order_max_wait_time

        ##仓位信息
        #0 none仓 1 多头 -1 空头
        self.status["position"] =  0 
        self.status["last_trade_price"] = 0
        ##海龟策略
        
        ##读取模型
        self.models = [] 
        for i in range(5,10):
            self.models.append(lgb.Booster(model_file="lightgbm_"+str(i)+".txt"))
    def refresh_account(self):
        ## update  buy,sell price and position 
        self.quantcenter.update_account()
        self.quantcenter.update_ticker()
        self.Amount = self.quantcenter.Amount
        self.Balance = self.quantcenter.Balance
        self.Buy_price = self.quantcenter.Buy
        self.Sell_price = self.quantcenter.Sell
        self.potential_buy_amount = round(self.Balance / self.Sell_price, self.amount_N)
        self.potential_sell_amount = round(self.Amount, self.amount_N)
        self.total_Balance = self.Balance + self.Amount * self.Sell_price
    def refresh_data(self, period):
        ##refresh account 
        self.refresh_account()
        self.quantcenter.refresh_data(period)
        ##update arr will be used in indicator
        self.kline = pd.DataFrame(self.quantcenter.Kline)
        self.close_Arr = self.kline["Close"].to_numpy()
        self.high_Arr = self.kline["High"].to_numpy()
        self.low_Arr = self.kline["Low"].to_numpy()
        ##update user_define_price_percent
        self.user_dataset = pd.DataFrame(self.quantcenter.fetch_kline(self.user_price_period))
        self.user_Max_price = self.user_dataset.High.max()
        self.user_Min_price = self.user_dataset.Low.min()
    def  create_order_dict(self,trade_side,trade_price,trade_amount):
        if trade_side == "sell":
            trade_price = round(trade_price *(1.0 + self.price_slip ),self.price_N)
            trade_price = max(trade_price,self.quantcenter.Asks_Price1)
            trade_amount = max(trade_amount,0.0)
            trade_amount = min(trade_amount,self.Amount)
            trade_amount = round(trade_amount,self.amount_N)
            if trade_amount*trade_price <self.min_sell_money:
                return False 
        elif trade_side == "buy":
            trade_price = round(trade_price *(1.0 - self.price_slip ),self.price_N)
            trade_price = min(trade_price,self.quantcenter.Bids_Price1)
            trade_amount = max(trade_amount,0.0)
            trade_amount = min(trade_amount,self.Balance/trade_price)
            trade_amount = round(trade_amount,self.amount_N)
            if trade_amount*trade_price <self.min_buy_money:
                return False 
        trade_id = self.quantcenter.create_order(trade_side,trade_price,trade_amount)
        self.refresh_account()
        return  {   
                    "side":trade_side,
                    "price":trade_price,
                    "amount":trade_amount,
                    "id":trade_id,
                    "timestamp":Unix()
                }
    def predict_siginal(self):
        predict=[]
        x=get_model_input(self.kline)
        for model in self.models:
            predict.append(model.predict(x))
        prob=np.mean(predict,axis=0)
        prob_max =np.max(prob)
        ##prob_max to small no trade 
        if prob_max>0.8:
            siginal = np.argmax(prob)
        else:
            siginal =0 
        return siginal 
        
    def next(self):
        siginal =self.predict_siginal()
        trade_price = self.quantcenter.Last 
        ##先做全仓操作
        if siginal == 0:
            pass
        ##空仓且买入信号
        elif siginal == 1 and self.status["position"] == 0:
            dic= self.create_order_dict("buy",trade_price,0.1*self.potential_buy_amount)
            if dic:
                self.buy_orders.append(dic)
                self.status["position"] = 1
                self.status["last_trade_price"]  = dic["price"]
        ##已多仓且卖出信号
        elif siginal == 2 and self.status["position"] == 1:
            dic = self.create_order_dict("sell",trade_price,self.Amount)
            if dic:
                self.sell_orders.append(dic)
                self.status["position"] = 0 
                self.status["last_trade_price"]  = dic["price"]

## main
## define args
class Args():
    amount_N = 4
    price_N = 4
    min_buy_money = 5
    min_sell_money = 5

    kline_period = PERIOD_M5
    
    ## true_period (Days)
    price_percent_period = 21
    order_max_wait_time = 3600 * 4

    price_slip = 2.5e-5
    
    quantcenter = QuantCenter(exchange)


def main():
    args = Args()
    strategy = Strategy(args)
    strategy.refresh_data(args.kline_period)
    Log("refresh_data ok")
    while (True):
        Sleep(1000 * 60 * 5)
        # time.sleep(60)
        try:
            ## refresh_data and indicator
            strategy.refresh_data(args.kline_period)
            strategy.next()
        except:
            pass

