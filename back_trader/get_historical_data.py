import requests 
from datetime import date,datetime
import time
import pandas as pd

def unix_time_millis(date):
    # epoch = datetime.utcfromtimestamp(0)
    dt = datetime.strptime(date, "%Y-%m-%d")
    # return int((dt - epoch).total_seconds() * 1000)
    return int(dt.timestamp() * 1000)
 
def GetKlines(symbol='BTC',start='2020-8-10',end='2021-8-10',period='1h'):
    Klines = []
    start_time = unix_time_millis(start)
    end_time = unix_time_millis(end)
    while start_time < end_time:
        res = requests.get('https://fapi.binance.com/fapi/v1/klines?symbol=%sUSDT&interval=%s&startTime=%s&limit=1000'%(symbol,period,start_time))
        res_list = res.json()
        Klines += res_list
        #print(datetime.utcfromtimestamp(start_time/1000).strftime('%Y-%m-%d %H:%M:%S') ,len(res_list))
        start_time = res_list[-1][0]
    return pd.DataFrame(Klines,columns=['time','open','high','low','close','amount','end_time','volume','count','buy_amount','buy_volume','null']).astype('float')
  
