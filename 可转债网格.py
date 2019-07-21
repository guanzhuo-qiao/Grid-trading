# -*- coding: utf-8 -*-
"""
Created on Mon Jul 24 11:04:13 2017

@author: ttc
"""


import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import tushare as ts

###########################数据获取############
df = pd.read_excel(r'C:\Users\ttc\Desktop\15国盛.xlsx')
df.set_index(pd.to_datetime(df.date),inplace=True)
data = df.ix[:,['close','open']]

#plt.plot(data['close'])
del df
################################################
###########################策略参数设置#############
beta=0.2
ceil=max(data['close'])
base=96#为了简便将参数设置为这样，实际操纵中这一参数通过历史经验估计或者其他统计手段得到
alpha = 0.01
n = 5 #分为n格；n+1条格线
base_ratio=0#底仓，这一仓位在指定网格线进入，当牛市来临时在高位抛出
###############################################3###

######生成网格#######
def grid(base,ceil,beta,alpha,n):
       gap=pow(ceil/base,1/n)-1
       price = [round(base*pow(1+gap,i),2) for i in range(n+1)][::-1]
       price.insert(0,round(ceil*(1+beta),2))
       price.append(round(base*(1-alpha),2))
       grid = pd.DataFrame({'lines':price})
       return grid
grids = grid(base,ceil,beta,alpha,n)
#####################


########################################策略生成###########
p_lag=[]#参考档位，当一交易完成后，参考档位挪至这一交易完成的价格，在这一参考档位上下相邻的网格线进行下一步的判断
tactic = []#1操作，0不操作，nan初始化，不操作
"""初始化   当价格触碰到某一网格线时，生成买入信号"""
ini_dop=float(grids[grids<=data.ix[0,0]].max())#下限价格(initial down price)
ini_dod=int(grids[grids<=data.ix[0,0]].idxmax())#下限索引(initial down index)
ini_upp=float(grids[grids>=data.ix[0,0]].min())#上限价格(initial up price)
ini_upd=int(grids[grids>=data.ix[0,0]].idxmin())#上限索引(initial up index)

for m in range(0,len(data)):
       if ini_dod ==ini_upd:
              tactic.append(1)
              p_lag.append(ini_dod)
              break
       else:
              if data.ix[m,0]>=ini_upp:
                     tactic.append(1)
                     p_lag.append(ini_upd)               
                     break
              elif data.ix[m,0]<=ini_dop:
                     tactic.append(1)
                     p_lag.append(ini_dod)
                     break
              else:
                     tactic.append(0)
                     p_lag.append(np.NaN)
del ini_dop,ini_dod,ini_upp,ini_upd
"""信号生成过程"""
for i in range(m+1,len(data)):
       if p_lag[-1] not in  (0,len(grids)-1):
              if data.ix[i,0]>=grids.ix[p_lag[-1]-1,0]:
                     tactic.append(-1)
                     p_lag.append(p_lag[-1]-1)
              elif data.ix[i,0]<=grids.ix[p_lag[-1]+1,0]:
                     tactic.append(1)
                     p_lag.append(p_lag[-1]+1)
              else:
                     tactic.append(0)
                     p_lag.append(p_lag[-1])
       else:#到达阈值则一直空仓
              tactic.append(0)
              p_lag.append(p_lag[-1])
strategy = pd.DataFrame({'open':data.ix[:,'open'],'close':data.ix[:,'close'],'tactic':tactic,'p_lag':p_lag},
                         index=data.index)#信号列表，包含按当日收盘价判断的买卖信号与调仓后的参考档位

######################################################
################仓位生成####################
"""每一网格线对应固定仓位比例，阈值处仓位为0，其余当价格由高至低时，仓位由0%+底仓至100%"""
def kai3fang(a):
       if a<0:
              return -pow(-a,1/3)
       else:
              return pow(a,1/3)

def position1(n,base_ratio):#x^1/3 x为档位,按三得之一次幂的形式调仓，在中间价位迅速调仓，在高位和低位慢速调仓
       x = [i*2/n for i in range(n+1)]
       pos=[round((1-base_ratio)*(kai3fang(r-1)/2+0.5),3) for r in x]
       pos.insert(0,0)
       pos.append(0)
       return pos
"""
def position2(base_ratio,primary,n):#x(1+a)^n
       rate = pow((1-base_ratio)/primary,1/(n-1))-1
       x=[primary*pow(1+rate,power) for power in range(0,n)]
       x.insert(0,0)
       x=[round(pos+base_ratio,2) for pos in x]
       x.insert(0,0)
       x.append(0)
       return x
primary=1/6
"""
def position3(n):#linear
       x = [i*1/n for i in range(n+1)]
       x.insert(0,0)
       x.append(0)
       return x

positions = position1(n,base_ratio)
#positions = position2(base_ratio,primary,n)#指数增长
#positions = position1(n,base_ratio)#形成仓位

def update_position(base_ratio,positions):#更新仓位
        positions[1:-1]=[round(positions[q]+base_ratio,2) for q in range(1,len(positions)-1)]
        return positions


#################################################################
####################回测过程##################
pool = [1000000]#资金池
amount = [0] #持有证券股数
security = [0]#证券池(随市价变化)
addup = [1000000]#总市值=资金迟+证券池

#当日的收盘价用以结算，当日开盘价用以执行前一天策略
for p in range(len(tactic)-1):
       if strategy.ix[p,'tactic']in (0 , np.NaN):#观望
              pool.append(pool[-1])
              amount.append(amount[-1])
              security.append(amount[-1]*data.ix[p+1,'close'])
       elif strategy.ix[p,'tactic']==1:#买进
              pos = positions[int(strategy.ix[p,'p_lag'])]
              delta = pos*(pool[-1]+amount[-1]*data.ix[p+1,'open'])-\
                          data.ix[p+1,'open']*amount[-1]
              amount.append(amount[-1]+delta/data.ix[p+1,'open'])
              pool.append(pool[-1]-delta)
              security.append(amount[-1]*data.ix[p+1,'close'])
       else:
              pos = positions[int(strategy.ix[p,'p_lag'])]
              delta = pos*(pool[-1]+amount[-1]*data.ix[p+1,'open'])-\
                          data.ix[p+1,'open']*amount[-1]
              pool.append(pool[-1]-delta)
              amount.append(amount[-1]+delta/data.ix[p+1,'open'])
              security.append(amount[-1]*data.ix[p+1,'close'])
       addup.append(pool[-1]+security[-1])

result = pd.DataFrame({"pool":pool,"amount":amount,"security":security,"addup":addup},
                      index = [data.index])#结果汇总

##########################################################
#####################策略回测结果报告######################

annual_return = (result.ix[-1,'addup']/result.ix[0,'addup']-1)/len(result)*252
daily_return = ((-result.ix[:,'addup']+result.ix[:,'addup'].shift(-1))/result.ix[:,'addup']).shift(1)
valatility = daily_return.var()
risk_free = ts.shibor_data(2015).ix[:,'1Y'].mean()/100#shibor一年平均值作无风险利率
sharp_ratio = (annual_return-risk_free)/valatility  
drawdown = (result['addup']/pd.expanding_max(result['addup'])-1).sort_values()
max_drawdown = pd.DataFrame(drawdown.ix[0,0],
                            index = [drawdown.index[0]],
                            columns=['max_drawdown'])     #最大回撤                 

dr = ((-data.ix[:,'close']+data.ix[:,'close'].shift(-1))/data.ix[:,'close']).shift(1)
tr_r = (1+daily_return.fillna(0)).cumprod()#策略累计收益
au_r = (1+dr.fillna(0)).cumprod()#股票累计收益
###绘图
au_graph = plt.plot(au_r)
tr_graph = plt.plot(tr_r)
###说明
for_print=['年化收益率','夏普比率','方差','最大回撤']
for_data = [annual_return,sharp_ratio,valatility,max_drawdown]
for i in range(4):
       print('{}:{}'.format(for_print[i],for_data[i]))