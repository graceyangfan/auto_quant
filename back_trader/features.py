def get_model_input_tradition(df):
    ##[windows >5 <250]
    windows_list = [10 ,20 ,40,80]
    dif,dea,val =TA.MACD(df.close,12,26,9)
    df["MACD_dif_dif_init"]=val.diff()/df.close*100
    for i,windows in enumerate(windows_list):
        df["MOM_"+str(i)]=TA.MOM(df.close, timeperiod=windows)/df.close
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
        df["AD_"+str(i)]=TA.SUM((df.close-df.low)/(df.high-df.low)*df.volume,windows)/TA.SUM(df.volume,windows)
        df["OBV_"+str(i)]=TA.SUM((np.sign(df.close.diff())*df.volume),windows)/TA.SUM(df.volume,windows)
        df["VPSUMP_"+str(i)]=TA.SUM((df.volume*df.close).diff().clip(0,None),windows)/TA.SUM((df.volume*df.close).diff().abs())
        df["VPSUMN_"+str(i)]=TA.SUM((-(df.volume*df.close).diff()).clip(0,None),windows)/TA.SUM((-(df.volume*df.close).diff()).clip(0,None).abs())
        df["VPSUMD_"+str(i)]=df["VPSUMP_"+str(i)]-df["VPSUMN_"+str(i)]
    return df
