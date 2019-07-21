# -*- coding: utf-8 -*-
"""
Created on Wed Aug 16 13:58:55 2017
LLT trade
@author: ttc
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from WindPy import w

w.start()
df = w.wsd("000001.SH","close","2005-09-06","2013-06-28")
df = pd.DataFrame(df.Data,index = df.Fields,columns = df.Times)
df = df.T
df.columns = ['close']
data = df.copy()
d=30
alpha = 2/(d+1)
llt=[data.ix[0,'close'],data.ix[1,'close']]

for i in range(2,len(data)):
       index = (alpha-alpha**2/4)*data.ix[i,'close']+(alpha**2/2)*data.ix[i-1,'close']-\
               (alpha-alpha**2*3/4)*data.ix[i-2,'close']+(2*(1-alpha))*llt[i-1]-\
               (1-alpha)**2*llt[i-2]
       llt.append(index)
llt=pd.DataFrame(llt,index = data.index,columns=['llt'])

result=[0,0]
for p in range(1,len(llt)-1):
       if llt.ix[p,'llt']-llt.ix[p-1,'llt']>0:
              result.append(1)
       elif llt.ix[p,'llt']-llt.ix[p-1,'llt']<0:
              result.append(-1)
       else:
              result.append(result[-1])
result=pd.DataFrame(result,index=data.index,columns=['result'])
stock_return=(data/data.shift(1)-1).fillna(0)
strategy_return=pd.DataFrame(stock_return.close*result.result,columns=['return'])
strategy_return = strategy_return+1

strategy_curve=strategy_return.cumprod()
stock_curv=(stock_return+1).cumprod()

plt.plot(stock_curv)
plt.plot(strategy_curve)
plt.plot(data)
plt.plot(llt)