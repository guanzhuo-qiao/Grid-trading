# -*- coding: utf-8 -*-
"""
Created on Sat May 27 18:33:15 2017

@author: ttc
"""
import pandas as pd
import matplotlib.pyplot as plt
import os
import tushare as ts

ssec2015 = ts.get_hist_data('sh',start='2014-01-01',end='2015-12-31')

close=df.close
lag5close=close.shift(5)

momentum5=close-lag5close
momentum5.tail()

plt.rcParams['font.sans-serif']=['SimHei']
plt.subplot(211)
plt.pplot(close,'b*')
plt.xlabel('date')
plt.ylabel('Close')
plt.title('donglaingtu')

plt.subplot(212)
plt.plot(close,'r-#')
plt.xlabel('date')
plt.ylabel('Momentum5')

def momentum(price,periond):
       lagPrice=price.shift(periond)
       momen=price-lagPrice
       momen=momen.dropna()
       return(momen)

momentum(close,5)





#k-plot
from matplotlib.dates import DateFormatter,WeekdayLocator,DayLocator,MONDAY,date2num
from matplotlib.finance import candlestick_ohlc
from datetime import datetime

plt.rcParams['font.sans-serif']=['SimHei']
plt.rcParams['axes.unicode_minus']=False

ssec2015.index=[date2num(datetime.strptime(date,'%Y-%m-%d'))\
               for date in ssec2015.index]
type(ssec2015)

ssec2015.drop(['price_change', 'p_change','ma5', 'ma10', 'ma20', 'v_ma5', 'v_ma10', 'v_ma20'],\
              axis=1,inplace=True)
ssec2015['Date']=ssec2015.index
ssec15list=[]
for i in range(len(ssec2015)):
       ssec15list.append(ssec2015.iloc[i,:])



ax= plt.subplot()
mondays = WeekdayLocator(MONDAY)
weekFormatter = DateFormatter('%y %b %d')
ax.xaxis.set_major_locator(mondays)
ax.xaxis.set_minor_locator(DayLocator() )
ax.xaxis.set_major_formatter(weekFormatter)
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False
ax.set_title("上证综指2015年3月份K线图")
candlestick_ohlc(ax, ssec15list, width=0.7,colorup='r', colordown='g')
plt.setp(plt.gca().get_xticklabels(),rotation=50, horizontalalignment='center')
plt.show()


data=ts.get_hist_data('600848')
data.index=pd.to_datetime(data.index)
data=data.ix[:,:5]
data.close.plot()