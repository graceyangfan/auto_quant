import time
from datetime import datetime
import backtrader as bt

import pandas as pd
import logging
import sys

def get_data(path):
    df= pd.read_csv(path,parse_dates=True,index_col=0)
    df.index=pd.to_datetime(df['time'])
    df['openinterest']=0
    df=df[['open','high','low','close','volume','openinterest']]
    df=df.iloc[:1000]
    data=bt.feeds.PandasData(dataname=df)
    return data
  
data=get_data("../btc.csv")

##策略
class MyStrategy(bt.Strategy):
    params = (('short', 30),
              ('long', 70),
             ("name","rsi"),)
 
    def __init__(self):
        self.rsi = bt.indicators.RSI_SMA(self.data.close, period=21)
        info_format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        logging.basicConfig(level=logging.INFO,format=info_format)
        self.logger = logging.getLogger(self.params.name)
    def loginfo(self, txt):
        self.logger.info(txt)
        
    def next(self):
        if self.rsi < 100:
            print("before")
            print(self.getposition(self.data).size)
            #self.order_target_percent(target=0.5)
            self.buy(self.data, size=0.1, price=self.data.close[0])
            print("middle")
            print(self.getposition(self.data).size)
            self.buy(self.data, size=0.1, price=self.data.close[0])
            print("after")
            print(self.getposition(self.data).size)
##
class CommInfoFractional(bt.CommissionInfo):
    def getsize(self, price, cash):
        '''Returns fractional size for cash operation @price'''
        return self.p.leverage * (cash / price)
##
def run(args):
    cerebro=bt.Cerebro()
    cerebro.adddata(data)
    cerebro.addstrategy(args.stragey)
    cerebro.broker.setcash(args.init_crash)
    cerebro.broker.setcommission(args.commision)
    #cerebro.addsizer(bt.sizers.FixedSize, stake=1)
    ## fraction buy 
    #cerebro.broker.addcommissioninfo(CommInfoFractional())
    cerebro.broker.set_slippage_perc(perc=args.slip_perc)
    cerebro.run()
 class Args:
    stragey=MyStrategy
    init_crash=10000
    commision=0.0002
    slip_perc=0.0001
args=Args()
run(args)
