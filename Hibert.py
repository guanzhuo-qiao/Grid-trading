# -*- coding: utf-8 -*-
"""
Created on Fri Aug 18 11:17:22 2017
Hibert transform signals
@author: ttc
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import math
from WindPy import w

w.start()
df = w.wsd("000300.SH","close","2005-04-08","2013-04-26")
df = pd.DataFrame(df.Data,index = df.Fields,columns = df.Times)
df = df.T
df.columns = ['close']
data = df.copy()
ma=5
de_noise=[data.ix[num-ma:num,'close'].mean() for num in range(ma,len(data)+1)]
de_noise=pd.DataFrame(de_noise,index=data.index[ma-1:],columns=['de_noise'])
de_trend=(de_noise-de_noise.shift(1)).dropna()
de_trend.columns=['de_trend']
#plt.plot(de_trend)
m=5
q_n=[]
sumup=0
for i in range(m,len(de_trend)-m):
       for r in range(1,2*m+2):
              if (r-m-1)%2==0:
                     urt = 0
              else:
                     urt = 2/(math.pi*(r-m-1))
              x_fun = de_trend.ix[i-m-1+r,'de_trend']
              sumup=sumup+urt*x_fun
       q_n.append(sumup)
       sumup = 0
#plt.plot(de_trend.ix[m:-m,'de_trend'],q_n)
phase = pd.DataFrame({'x':de_trend.ix[m:-m,'de_trend'],'y':q_n},
                      index = de_trend.index[2*m:])
result=[0]*(ma+m*2+1)
for coor in range(len(phase)-1):
       if phase.ix[coor,'y']<0:
              result.append(1)
       else:
              result.append(-1)
result=pd.DataFrame(result,index=data.index,columns=['result'])

stock_return=(data/data.shift(1)-1).fillna(0)
strategy_return=pd.DataFrame(stock_return.close*result.result,columns=['return'])
strategy_return = strategy_return+1

strategy_curve=strategy_return.cumprod()
stock_curv=(stock_return+1).cumprod()

plt.plot(stock_curv)
plt.plot(strategy_curve)
