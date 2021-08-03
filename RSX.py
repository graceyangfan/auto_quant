import numpy as np
import talib as TA
import pandas as pd
import copy


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


## define Stragety
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
        self.buy_orders = []
        self.sell_orders = []
        self.trend_orders = []
        ## strategy params
        self.price_threshold = args.price_threshold
        self.position_max_percent = args.position_max_percent
        self.price_percent_period = args.price_percent_period
        self.user_price_period = int(self.price_percent_period / len(self.kline) * 24 * 3600)
        self.price_gap = args.price_gap
        self.max_orders = args.max_orders
        self.order_max_wait_time = args.order_max_wait_time
        ##moving average
        self.price_slip = args.price_slip

    def refresh_data(self, period):

        self.quantcenter.refresh_data(period)
        self.Amount = self.quantcenter.Amount
        self.Balance = self.quantcenter.Balance
        self.Buy_price = self.quantcenter.Buy
        self.Sell_price = self.quantcenter.Sell
        self.potential_buy_amount = round(self.Balance / self.Sell_price, self.amount_N)
        self.potential_sell_amount = round(self.Amount, self.amount_N)

        ##update arr will be used in indicator
        self.kline = pd.DataFrame(self.quantcenter.Kline)
        self.close_Arr = self.kline["Close"].to_numpy()
        self.high_Arr = self.kline["High"].to_numpy()
        self.low_Arr = self.kline["Low"].to_numpy()
        ##update user_define_price_percent
        self.user_dataset = pd.DataFrame(self.quantcenter.fetch_kline(self.user_price_period))
        self.user_Max_price = self.user_dataset.High.max()
        self.user_Min_price = self.user_dataset.Low.min()

    def trade_amount_compute(self, price, trade_side):
        price_percent = (price - self.user_Min_price) / (self.user_Max_price - self.user_Min_price)
        if trade_side == "buy":
            ##高估区间不买入
            if price > self.user_Max_price * self.price_threshold["buy"]:
                return False
                ##percent =1 amount =0  percent = 0 amount =1
            self.min_buy_amount = self.position_max_percent * self.Balance / price * (1.0 - price_percent)
            self.min_buy_amount = max(self.min_buy_amount, 0.0)
            self.min_buy_amount = min(self.min_buy_amount, self.Balance / price)
            self.min_buy_amount = round(self.min_buy_amount, self.amount_N)
            self.min_buy_balance = self.min_buy_amount * price
            if self.min_buy_balance < self.min_buy_money:
                return False
            else:
                return True

        elif trade_side == "sell":
            ##低估不卖出
            if price < self.user_Min_price * self.price_threshold["sell"]:
                return False
                ##percent =1 amount =1  percent = 0 amount =0
            self.min_sell_amount = self.position_max_percent * self.Amount * price_percent
            self.min_sell_amount = max(self.min_sell_amount, 0.0)
            self.min_sell_amount = min(self.min_sell_amount, self.Amount)
            self.min_sell_amount = round(self.min_sell_amount, self.amount_N)
            self.min_sell_balance = self.min_sell_amount * price
            if self.min_sell_balance < self.min_sell_money:
                return False
            else:
                return True
            
    def double_moving_average(self):
        fast_arr = TA.EMA(self.close_Arr, self.args.short_period)
        slow_arr = TA.EMA(self.close_Arr, self.args.long_period)

        cross_over = fast_arr[-1] > slow_arr[-1] and fast_arr[-2] < slow_arr[-2]
        cross_below = fast_arr[-1] < slow_arr[-1] and fast_arr[-2] > slow_arr[-2]
        RSX = self.rsx() 
        if cross_over and RSX[-1] > 50 +self.args.rsx_threshold:
            trade_price = round(self.quantcenter.Bids_Price1 * (1.0 + self.price_slip), self.price_N)
            will_trade = self.trade_amount_compute(trade_price, "buy")
            if will_trade:
                trade_id = self.quantcenter.create_order("buy", trade_price, self.min_buy_amount)
                if trade_id:
                    self.refresh_data(self.args.kline_period)
                    self.trend_orders.append({
                        "side": "buy",
                        "price": trade_price,
                        "amount": self.min_buy_amount,
                        "id": trade_id,
                        "timestamp": Unix()})
        if cross_below and RSX[-1] < 50 - self.args.rsx_threshold :
            trade_price = round(self.quantcenter.Asks_Price1 * (1.0 - self.price_slip), self.price_N)
            will_trade = self.trade_amount_compute(trade_price, "sell")
            if will_trade:
                trade_id = self.quantcenter.create_order("sell", trade_price, self.min_sell_amount)
                if trade_id:
                    self.refresh_data(self.args.kline_period)
                    self.trend_orders.append({
                        "side": "sell",
                        "price": trade_price,
                        "amount": self.min_sell_amount,
                        "id": trade_id,
                        "timestamp": Unix()})
##rsx indicator
    def rsx(self):
        length= int(self.args.rsx_period)  if self.args.rsx_period > 0 else 14
        if self.close_Arr is None:
            return 0 
        # variables
        vC, v1C = 0, 0
        v4, v8, v10, v14, v18, v20 = 0, 0, 0, 0, 0, 0
        f0, f8, f10, f18, f20, f28, f30, f38 = 0, 0, 0, 0, 0, 0, 0, 0
        f40, f48, f50, f58, f60, f68, f70, f78 = 0, 0, 0, 0, 0, 0, 0, 0
        f80, f88, f90 = 0, 0, 0

        m = len(self.close_Arr)
        result = [np.nan for _ in range(0, length - 1)] + [0]
        for i in range(length, m):
            if f90 == 0:
                f90 = 1.0
                f0 = 0.0
                if length - 1.0 >= 5:
                    f88 = length - 1.0
                else:
                    f88 = 5.0
                f8 = 100.0 * self.close_Arr[i]
                f18 = 3.0 / (length + 2.0)
                f20 = 1.0 - f18
            else:
                if f88 <= f90:
                    f90 = f88 + 1
                else:
                    f90 = f90 + 1
                f10 = f8
                f8 = 100 * self.close_Arr[i]
                v8 = f8 - f10
                f28 = f20 * f28 + f18 * v8
                f30 = f18 * f28 + f20 * f30
                vC = 1.5 * f28 - 0.5 * f30
                f38 = f20 * f38 + f18 * vC
                f40 = f18 * f38 + f20 * f40
                v10 = 1.5 * f38 - 0.5 * f40
                f48 = f20 * f48 + f18 * v10
                f50 = f18 * f48 + f20 * f50
                v14 = 1.5 * f48 - 0.5 * f50
                f58 = f20 * f58 + f18 * abs(v8)
                f60 = f18 * f58 + f20 * f60
                v18 = 1.5 * f58 - 0.5 * f60
                f68 = f20 * f68 + f18 * v18
                f70 = f18 * f68 + f20 * f70
                v1C = 1.5 * f68 - 0.5 * f70
                f78 = f20 * f78 + f18 * v1C
                f80 = f18 * f78 + f20 * f80
                v20 = 1.5 * f78 - 0.5 * f80

                if f88 >= f90 and f8 != f10:
                    f0 = 1.0
                if f88 == f90 and f0 == 0.0:
                    f90 = 0.0

            if f88 < f90 and v20 > 0.0000000001:
                v4 = (v14 / v20 + 1.0) * 50.0
                if v4 > 100.0:
                    v4 = 100.0
                if v4 < 0.0:
                    v4 = 0.0
            else:
                v4 = 50.0
            result.append(v4)
        return np.array(result)
                    
    def next(self):
        self.double_moving_average()


## main
## define args
class Args():
    amount_N = 4
    price_N = 4
    min_buy_money = 5
    min_sell_money = 5

    kline_period = PERIOD_M5
    position_max_percent = 0.1
    price_threshold = {"buy": 0.999,
                       "sell": 1.001}
    ## true_period (Days)
    price_percent_period = 21
    price_gap = 0.005
    max_orders = 5
    order_max_wait_time = 3600 * 4
    ##Moing average
    short_period = 100
    long_period =169
    price_slip = 2.5e-5
    ##ADX
    ADX_period = 14
    ADX_threshold = 30
    ##RSX 
    rsx_period = 14 
    rsx_threshold = 15
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
