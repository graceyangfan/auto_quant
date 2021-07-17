##安装fmz
!git clone https://github.com/fmzquant/backtest_python.git
!python setup.py install 
##获取历史数据
from fmz import * 
import numpy as np
import pandas as pd

def get_bars(symbol, unit,ts_from,ts_to, count=50000):
    params = {"symbol": symbol, "resolution": unit, "from": ts_from, "to": ts_to, "size": count}
    data = json.loads(httpGet("http://"+ CLUSTER_IP + "/chart/history?"+urlencode(params), CLUSTER_DOMAIN))
    try:
        import pandas as pd
        from pandas.plotting import register_matplotlib_converters
        register_matplotlib_converters()
    except:
        return data
    index = []
    for ele in data:
        index.append(pd.Timestamp(ele[0], unit='s', tz='Asia/Shanghai'))
        ele.pop(0)
    columns=["open", "high", "low", "close", "volume"]
    if len(data) > 0 and len(data[0]) == 6:
        columns.append("openInterest")
    return pd.DataFrame(data, index=index, columns=columns)
  
   def get_data(symbol, unit='1d', start=None, end=None, count=50000):
    period_dict={"1d":86400,"1h":3600,"15m":900,"5m":300,"1m":60}
    delta_time = period_dict[unit]
    ## compute start and end 
    if hasattr(unit, 'endswith'):
        if unit.endswith('d'):
            unit = int(unit[:-1]) * 1440
        elif unit.endswith('h'):
            unit = int(unit[:-1]) * 60
        elif unit.endswith('m'):
            unit = int(unit[:-1])
    ts_to = int(time.time())
    if end is not None:
        end = end.replace('/', '-')
        ts_to = int(time.mktime(datetime.datetime.strptime(end, "%Y-%m-%d %H:%M:%S" if ' ' in end else "%Y-%m-%d").timetuple()))
    if start is not None:
        start = start.replace('/', '-')
        ts_from = int(time.mktime(datetime.datetime.strptime(start, "%Y-%m-%d %H:%M:%S" if ' ' in start else "%Y-%m-%d").timetuple()))
        if end is None:
            ts_to = ts_from+(unit*100*(count+10))
    else:
        if end is None:
            ts_from = 0
            ts_to = 0
        else:
            ts_from = ts_to-(unit*100*(count+10))
    
    ## init kline 
    kline = get_bars(symbol, unit, ts_from, ts_to,count)
    delta_size =len(kline)
    condition =  ts_to -ts_from 
    while condition > 0  :
        ##increase ts_from in s 
        ts_from = ts_from + delta_size*delta_time
        middle_data =get_bars(symbol,unit,ts_from,ts_to,count)
        kline = pd.concat([kline,middle_data])
        condition =  ts_to -ts_from 
        time.sleep(1)
    return kline
  
  ##example 
  kl=get_data('huobi.btc_usdt', unit='5m', start='2019-10-01 00:00:00', end='2021-07-01')
