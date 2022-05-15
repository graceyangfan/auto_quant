# %%
from tuneta.tune_ta import TuneTA
import pandas as pd
from pandas_ta import percent_return
from sklearn.model_selection import train_test_split
import os
import talib as ta
import numpy as np

# %%
def create_label(df):
        zigzags = []
        ATR_MULTIPILIER= 3
        df["atr"] = ta.ATR(df.high,df.low,df.close,40)
        def calc_change_since_pivot(row, key):
            current = row[key]
            last_pivot = zigzags[-1]["Value"]
            if(last_pivot == 0): last_pivot = 1 ** (-100) # avoid division by 0
            perc_change_since_pivot = (current - last_pivot) / abs(last_pivot)
            return perc_change_since_pivot

        def get_zigzag(row, taip=None):
            if(taip == "Peak"): key = "high"
            elif(taip == "Trough"): key = "low"
            else: key = "close"

            return {
                "Time": row["time"],
                "Value": row[key],
                "Type": taip 
            }
        for ix, row in df.iterrows():

            threshold = row['atr'] / row["open"] * ATR_MULTIPILIER
            # handle first point
            is_starting = ix == 0
            if(is_starting):
                zigzags.append(get_zigzag(row))

                continue

            # handle first line
            is_first_line = len(zigzags) == 1
            if(is_first_line):
                perc_change_since_pivot = calc_change_since_pivot(row, "close")

                if(abs(perc_change_since_pivot) >= threshold):
                    if(perc_change_since_pivot > 0):
                        zigzags.append(get_zigzag(row, "Peak"))
                        zigzags[0]["Type"] = "Trough"
                    else: 
                        zigzags.append(get_zigzag(row, "Trough"))
                        zigzags[0]["Type"] = "Peak"
                
                continue
    
            # handle other lines
            is_trough = zigzags[-2]["Value"] > zigzags[-1]["Value"]
            is_ending = ix == len(df.index) - 1
            last_pivot = float(zigzags[-1]["Value"])
            # based on last pivot type, look for reversal or continuation
            if(is_trough):
                perc_change_since_pivot = calc_change_since_pivot(row, "high")
                is_reversing = (perc_change_since_pivot >= threshold) or is_ending
                is_continuing = row["low"] <= last_pivot
                if (is_continuing): 
                    zigzags[-1] = get_zigzag(row, "Trough")
                elif (is_reversing): 
                    zigzags.append(get_zigzag(row, "Peak"))
            else:
                perc_change_since_pivot = calc_change_since_pivot(row, "low")
                is_reversing = (perc_change_since_pivot <= -threshold) or is_ending
                is_continuing = row["high"] >= last_pivot
                if(is_continuing): 
                    zigzags[-1] = get_zigzag(row, "Peak")
                elif (is_reversing): 
                    zigzags.append(get_zigzag(row, "Trough"))
        zigzags = pd.DataFrame(zigzags)
        zigzags["PrevExt"] = zigzags.Value
        df=zigzags.merge(df,left_on="Time",right_on="time",how="right")
        df.Type = df.Type.map({"Trough":1,"Peak":2})
        df.Type=df.Type.replace(np.nan,0)
        df["PrevExt"] = df["PrevExt"].fillna(method='bfill')
        df["target"] = df["PrevExt"]/df["close"]
        return df

# %%
base_dir = "nautilus_trader-develop/test/test_kit/data"
'''
# %%
df=pd.read_parquet(os.path.join(base_dir,"BTC-USDT.parquet"))

# %%
df["time"] = df.index

# %%
df.index = range(len(df))
# %%
df = create_label(df)
# %%
df["label"] = (df["PrevExt"]-df["close"])/df["close"]
df['sym'] = "BTC"
df.index = df.time 
df.set_index('sym', append=True, inplace=True)

# %%s
import datetime
df = df.iloc[-40000:]
'''
# %%
df2=pd.read_parquet(os.path.join(base_dir,"ETH-USDT.parquet"))

# %%
df2["time"] = df2.index

# %%
df2.index = range(len(df2))
# %%
df2 = create_label(df2)
# %%
df2["label"] = (df2["PrevExt"]-df2["close"])/df2["close"]
# %%
df2['sym'] = "ETH"
df2.index = df2.time 
df2.set_index('sym', append=True, inplace=True)
df2 = df2.iloc[-40000:]
'''

df3=pd.read_parquet(os.path.join(base_dir,"APE-USDT.parquet"))

# %%
df3["time"] = df3.index

# %%
df3.index = range(len(df3))
# %%
df3 = create_label(df3)
# %%
df3["label"] = (df3["PrevExt"]-df3["close"])/df3["close"]
# %%
df3['sym'] = "ETH"
df3.index = df3.time 
df3.set_index('sym', append=True, inplace=True)
df3 = df3.iloc[-40000:]
'''
# %%
#df = pd.concat([df, df2, df3], axis=0).sort_index()
df = df2
# %%
X = df[["open","close","high","low","volume"]]

y = df["label"]


# %%
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=.3, shuffle=False)

# %%
tt = TuneTA(n_jobs=6, verbose=True)


# %%
tt.fit(X_train, y_train,
    indicators=['pta.rvi',"pta.cfo","pta.pdist",
               "pta.vortex","pta.kvo","pta.inertia",
               "pta.eri","pta.increasing",
               "pta.bop","pta.mfi","pta.eom","pta.vhf",
               "pta.skew","pta.amat","pta.stc"],
    ranges=[(5,120)],
    trials=100,
    early_stop=20,
)

# %%

tt.prune(max_inter_correlation=.7)
tt.report(target_corr=True, features_corr=True)



