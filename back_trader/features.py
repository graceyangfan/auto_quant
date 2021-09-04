def get_model_input_tradition(df):
    ##[windows >5 <250]
    windows_list = [10 ,20 ,40,80]
    dif,dea,val =TA.MACD(df.close,12,26,9)
    df["MACD_dif_dif_init"]=val.diff()/df.close*100
    for i,windows in enumerate(windows_list):
        #df["MOM_"+str(i)]=TA.MOM(df.close, timeperiod=windows)/df.close
        df["ATR_"+str(i)]=TA.ATR(df.high,df.low,df.close,windows)/df.close
        ##RSV分子和分母
        df["Dochian_upper_"+str(i)]=(TA.MAX(df["high"],windows)-df["close"])/df.close
        df["Dochian_lower_"+str(i)]=(df["close"]-TA.MIN(df["low"],windows))/df.close
        df["MACD_dif_dif_"+str(i)]=val.diff(windows)/df.close*100
        df["MA_dif_dif_"+str(i)]=dif.diff(windows)/df.close*100
        ##与DI相关的指标
        #(1)price_dif
        df["MINUS_DI_"+str(i)]=TA.MINUS_DI(df.high, df.low, df.close, timeperiod=windows)/df.close
        df["MINUS_DM_"+str(i)]=TA.MINUS_DM(df.high, df.low, timeperiod=windows)/df.close
        #adxr and adx [0,100]
        df["ADXR_"+str(i)]=TA.ADXR(df.high, df.low, df.close, timeperiod=windows)
        df["ADX_"+str(i)]=TA.ADX(df.high, df.low, df.close, timeperiod=windows)
        ##[cci] 是比值不用缩放
        df["CCI_"+str(i)]=TA.CCI(df.high, df.low, df.close, timeperiod=windows)
        ##[0,100]
        df["ULTOSC_"+str(i)]=TA.ULTOSC(df.high, df.low, df.close, timeperiod1=windows//3, timeperiod2=windows//2, timeperiod3=windows)
        ##与RSI或强弱相关指标
        df["MFI_"+str(i)]=TA.MFI(df.high,df.low,df.close,df.volume,timeperiod=windows)
        df["slowk_"+str(i)], df["slowd"+str(i)] = TA.STOCH(df.high, df.low, df.close, fastk_period=windows, slowk_period=windows//2, slowk_matype=0, slowd_period=windows//2, slowd_matype=0)
        df["fastk_"+str(i)], df["fastd"+str(i)] = TA.STOCHF(df.high, df.low, df.close, fastk_period=windows, fastd_period=windows//2, fastd_matype=0)
        df["SRSI_fastk_"+str(i)],df["SRSI_fastd"+str(i)] =TA.STOCHRSI(df.close, timeperiod=windows, fastk_period=windows//2, fastd_period=windows//4, fastd_matype=0)
        ##与volume相关的
        df["AD_"+str(i)]=TA.SUM((df.close-df.low)/(df.high-df.low+1e-12)*df.volume,windows)/TA.SUM(df.volume,windows)
        df["OBV_"+str(i)]=TA.SUM((np.sign(df.close.diff())*df.volume),windows)/TA.SUM(df.volume,windows)
        df["VPSUMP_"+str(i)]=TA.SUM((df.volume*df.close).diff().clip(0,None),windows)/TA.SUM((df.volume*df.close).diff().abs())
        df["VPSUMN_"+str(i)]=TA.SUM((-(df.volume*df.close).diff()).clip(0,None),windows)/TA.SUM((-(df.volume*df.close).diff()).clip(0,None).abs())
        df["VPSUMD_"+str(i)]=df["VPSUMP_"+str(i)]-df["VPSUMN_"+str(i)]
    return df

def get_model_input_alpha158(df):
    oc_max=np.nanmax(df[["open","close"]].values, axis=1)
    oc_min=np.nanmin(df[["open","close"]].values, axis=1)
    df["KMID"] =(df.close-df.open)/df.open
    df["KLEN"] = (df.high-df.low)/df.open
    df["KMID2"] = (df.close-df.open)/(df.high-df.low+1e-12)
    df["KUP"] = (df.high-oc_max)/df.open
    df["KUP2"]=(df.high-oc_max)/(df.high-df.low+1e-12)
    df["KLOW"]=oc_min/df.open
    df["KLOW2"]=oc_min/(df.high-df.low+1e-12)
    df["KSFT"]=(2*df.close-df.high-df.low)/df.open
    df["KSFT2"]= (2*df.close-df.high-df.low)/(df.high-df.low+1e-12)
    #update high,low,open,close with a compare 
    for field in ["open", "high", "low"]:
        df[field+"_"+"_close_ratio"]=df[field]/df.close
    ##shift price and shift volume 
    for i in range(1,5):
        for field in ["open", "high", "low", "close"]:
            df[field+"_"+str(i)+"_close_ratio"]=df[field].shift(i)/df.close
    for i in range(1,5):
        field="volume"
        df[field+"_"+str(i)+"_volume_ratio"]=df[field].shift(i)/df.volume
    ##special character 
    windows_list=[5, 10, 20, 30, 60]
    for i,windows in enumerate(windows_list):
        df["log_return_"+str(i)]=np.log(df.close).diff(windows)
        df["VWAP_"+str(i)]=TA.SUM(df.volume*(df.high+df.low)/2,windows)/TA.SUM(df.volume,windows)
        df["VWAP_shift"+str(i)+"_close_ratio"]=df["VWAP_"+str(i)].shift()/df.close
        df["MA_"+field+"_"+str(i)+"_close_ratio"]=TA.MA(df.close,windows)/df.close
        df["STD_"+field+"_"+str(i)+"_close_ratio"]=TA.STDDEV(df.close,windows,nbdev=1)/df.close
        df["BETA_"+str(i)+"_close_ratio"]=rolling_slope(df.close.values,windows)/df.close
        df["RSQR_"+str(i)+"_close_ratio"]=rolling_rsquare(df.close.values,windows)/df.close
        df["RESI_"+str(i)+"_close_ratio"]=rolling_resi(df.close.values,windows)/df.close 
        df["MAX_high_"+str(i)+"_close_ratio"]=TA.MAX(df.high,windows)/df.close
        df["MIN_low_"+str(i)+"_close_ratio"]=TA.MIN(df.low,windows)/df.close
        df["QTLU_"+str(i)+"_close_ratio"]=df.close.rolling(windows).quantile(.8, interpolation='midpoint')/df.close
        df["QTLD_"+str(i)+"_close_ratio"]=df.close.rolling(windows).quantile(.2, interpolation='midpoint')/df.close
        df["RANK_"+str(i)]=df.close.rolling(windows).apply(rank, raw=True)
        df["RSV_"+str(i)]=(df.close-TA.MIN(df.close,windows))/(TA.MAX(df.high,windows)-TA.MIN(df.low,windows)+1e-12)
        df["IMAX_"+str(i)]=df.high.rolling(windows).apply(lambda x: x.argmax() + 1, raw=True)/windows
        df["IMIN_"+str(i)]=df.low.rolling(windows).apply(lambda x: x.argmin() + 1, raw=True)/windows
        df["IMXD_"+str(i)]=df["IMAX_"+str(i)]-df["IMIN_"+str(i)]
        df["Corr_"+str(i)]= corr(df.low,np.log(df.volume+1),windows)
        df["CORD_"+str(i)]=corr(df.close/df.close.shift(1),np.log(df.volume/df.volume.shift(1)+1),windows)
        df["CNTP_"+str(i)]=TA.MA(df.close>df.close.shift(1), windows)
        df["CNTD_"+str(i)]=TA.MA(df.close>df.close.shift(1), windows)-TA.MA(df.close<df.close.shift(1), windows)
        df["SUMP_"+str(i)]=TA.SUM((df.close-df.close.shift(1)).clip(0,None),windows)/TA.SUM((df.close-df.close.shift(1)).abs(),windows)
        df["SUMN_"+str(i)]=TA.SUM((-df.close+df.close.shift(1)).clip(0,None),windows)/TA.SUM((df.close-df.close.shift(1)).abs(),windows)
        df["SUMD_"+str(i)]=df["SUMP_"+str(i)]-df["SUMN_"+str(i)]
        df["VMA_"+str(i)]=TA.MA(df.volume,windows)/(df.volume)
        df["VSTD_"+str(i)]=TA.STDDEV(df.volume,windows,nbdev=1)/df.volume
        df["WVMA_"+str(i)]=TA.STDDEV((df.close/(df.close.shift(1)-1)).abs()*df.volume,windows,nbdev=1)/TA.MA((df.close/(df.close.shift(1)-1)).abs()*df.volume)
        df["VSUMP_"+str(i)]=TA.SUM((df.volume-df.volume.shift(1)).clip(0,None),windows)/TA.SUM((df.volume-df.volume.shift(1)).abs())
        df["VSUMN_"+str(i)]=TA.SUM((-df.volume+df.volume.shift(1)).clip(0,None),windows)/TA.SUM((df.volume-df.volume.shift(1)).abs())
        df["VSUMD_"+str(i)]=df["VSUMP_"+str(i)]-df["VSUMN_"+str(i)]
    return df


def create_label(df):
    zigzags = []
    ATR_MULTIPILIER=2.0
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
            "time": row["time"],
            "Value": row[key],
            "Type": taip 
        }
    for ix, row in df.iterrows():
        threshold = row['ATR_1'] * ATR_MULTIPILIER
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
    zigzags["PrevExt"] = zigzags.Value.shift(2)
    higher_highs = zigzags.dropna()
    higher_highs = higher_highs.loc[(higher_highs["Value"] > higher_highs["PrevExt"]) & (higher_highs["Type"] == "Peak") & (higher_highs.index != 2)]
    lower_lows = zigzags.dropna()
    lower_lows = lower_lows.loc[(lower_lows["Value"] < lower_lows["PrevExt"]) & (lower_lows["Type"] == "Trough") & (lower_lows.index != 2)]
    new_type=pd.concat([lower_lows,higher_highs])

    df=new_type.merge(df,left_on="time",right_on="time",how="right")
    df.Type = df.Type.map({"Trough":1,"Peak":2})
    df.Type=df.Type.replace(np.nan,0)
    return df
