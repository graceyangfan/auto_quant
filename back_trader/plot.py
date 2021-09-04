%matplotlib inline
import mplfinance as mpf
def plot_candle(df,date_col="time",label="close"):
    #my_col=mpf.make_marketcolors(up="red",down="green",edge="inherit",volume="inherit")
    #my_style= mpf.make_mpf_style(marketcolors=my_col)
    df.index=pd.to_datetime(df[date_col])
    add_plot=[
        mpf.make_addplot(np.where(df['Type']>1, df['close'], np.nan),scatter=True,markersize=80,marker="v",color='g'),
        mpf.make_addplot(np.where(df['Type']==1, df['close'], np.nan),scatter=True,markersize=80,marker="^",color='b')
             ]
    mpf.plot(df,type="candle",addplot=add_plot,volume=True,ylabel=label,style='sas',tight_layout=True)
