# -*- coding: utf-8 -*-
"""
Created on Mon Jul 24 15:13:54 2017
分钟数据网格
国债期货TF1703、TF1706、TF1709
"""




import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
#import tushare as ts
from math import isnan
from WindPy import w
from 参数生成 import parameters
###########################数据获取与处理############
w.start()
   
df1 = w.wsi('tf1703.cfe','open,close','2016-12-21','2017-01-24')
df1 = pd.DataFrame(df1.Data,index = df1.Fields,columns = df1.Times)
df1 = df1.T
df1 = df1.dropna()
df1.columns = ['open','close']
return1 = df1.ix[:,'close']/df1.ix[:,'close'].shift(1)

df2 = w.wsi('tf1706.cfe','open,close','2017-01-23','2017-05-10')
df2 = pd.DataFrame(df2.Data,index = df2.Fields,columns = df2.Times)
df2 = df2.T
df2 = df2.dropna()
df2.columns = ['open','close']
return2 = df2.ix[:,'close']/df2.ix[:,'close'].shift(1)

df3 = w.wsi('tf1709.cfe','open,close','2017-05-09')
df3 = pd.DataFrame(df3.Data,index = df3.Fields,columns = df3.Times)
df3 = df3.T
df3 = df3.dropna()
df3.columns = ['open','close']
return3 = df3.ix[:,'close']/df3.ix[:,'close'].shift(1)
ult_return = return1.append(return2.ix['2017-01-24':]).append(return3.ix['2017-05-10':])
ult_return = pd.DataFrame(ult_return)
ult_return = ult_return.fillna(1)
df=[df1.ix[0,'close']]
for rate_num in range(1,len(ult_return)):
       df.append(ult_return.ix[rate_num,0]*df[-1])
df=pd.DataFrame(df,index = ult_return.index,columns=['close'])
del df1,df2,df3,return1,return2,return3,rate_num

train = df.ix[:'2017-04-05',:]
data = df.ix['2017-04-06':,:]

'''
au(t+d)
2014-01-02to2015-02-03 train data
2015-02-03to2016-07-06 test data

国债期货
2016-12-21至2017-04-05训练集
2017-04-06至2017-08-02测试集
'''
#df = pd.read_csv(r'C:\Users\ttc\Desktop\AU(T+D)_SGE_15minutes.csv')
#df.set_index(pd.to_datetime(df.date),inplace=True)
#data = df.ix[:,['close','open']]
#data = data.ix['2017-02-01':,:]
#plt.plot(df)

################################################
###########################策略参数设置#############
'''beta=0.01
ceil=max(data['close'])
base=min(data['close'])#为了简便将参数设置为这样，实际操纵中这一参数通过历史经验估计或者其他统计手段得到
alpha = 0.01
n = 5 #分为n格；n+1条格线
base_ratio=0#底仓，这一仓位在指定网格线进入，当牛市来临时在高位抛出
'''
###############################################3###

beta=0.01
alpha = 0.01
base_ratio=0
ceil,base,n=parameters(train,10)

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
'''for n in range(len(grids)):
       if n==0 or n==len(grids)-1:
              plt.axhline(grids.ix[n,0],linestyle='--',color='red')
       else:
              plt.axhline(grids.ix[n,0],linestyle='--',color='green')
'''
########################################策略生成###########
p_lag=[]#参考档位，当一交易完成后，参考档位挪至这一交易完成的价格，在这一参考档位上下相邻的网格线进行下一步的判断
tactic = []#1操作，0不操作，nan初始化，不操作
"""初始化   当价格触碰到某一网格线时，生成买入信号"""
ini_dop=float(grids[grids<=data.ix[0,'close']].max())#下限价格(initial down price)
ini_dod=int(grids[grids<=data.ix[0,'close']].idxmax())#下限索引(initial down index)
ini_upp=float(grids[grids>=data.ix[0,'close']].min())#上限价格(initial up price)
ini_upd=int(grids[grids>=data.ix[0,'close']].idxmin())#上限索引(initial up index)

for m in range(0,len(data)):
       if ini_dod ==ini_upd:
              tactic.append(1)
              p_lag.append(ini_dod)
              break
       else:
              if data.ix[m,'close']>=ini_upp:
                     tactic.append(1)
                     p_lag.append(ini_upd)               
                     break
              elif data.ix[m,'close']<=ini_dop:
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
              if data.ix[i,'close']>=grids.ix[0,0]:
                     tactic.append(2)
                     p_lag.append(0)
              elif data.ix[i,'close']<=grids.ix[len(grids)-1,0]:
                     tactic.append(2)
                     p_lag.append(len(grids)-1)
              else:
                     if data.ix[i,'close']>=grids.ix[p_lag[-1]-1,0]:
                            tactic.append(-1)
                            p_lag.append(p_lag[-1]-1)
                     elif data.ix[i,'close']<=grids.ix[p_lag[-1]+1,0]:
                            tactic.append(1)
                            p_lag.append(p_lag[-1]+1)
                     else:
                            tactic.append(0)
                            p_lag.append(p_lag[-1])
       else:#到达阈值则一直空仓
              tactic.append(2)
              p_lag.append(p_lag[-1])
strategy = pd.DataFrame({'close':data.ix[:,'close'],'tactic':tactic,'p_lag':p_lag},
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
def position3(n,base_ratio):#linear
       x = [round(i*(1-base_ratio)/n,2) for i in range(n+1)]
       x.insert(0,0)
       x.append(0)
       return x

positions = position3(n,base_ratio)
#positions = position2(base_ratio,primary,n)#指数增长
#positions = position1(n,base_ratio)#形成仓位

def update_position(base_ratio,positions):#更新仓位
        positions[1:-1]=[round(positions[q]+base_ratio,2) for q in range(1,len(positions)-1)]
        return positions


#################################################################
####################回测过程##################
pool = [1000000]#资金池
amount1 = [0] #多头数量
amount2=[0]#空头数量
securities1=[0]
securities2=[0]
addup = [1000000]#总市值

#当日的收盘价用以结算，当日开盘价用以执行前一天策略
for p in range(len(tactic)-1):
       if strategy.ix[p,'tactic']==0:#观望
              amount1.append(amount1[-1])
              amount2.append(amount2[-1])
              securities1.append(amount1[-1]*data.ix[p+1,'close'])
              securities2.append(amount2[-1]*data.ix[p+1,'close'])
              pool.append(pool[-1])
       elif strategy.ix[p,'tactic']==1:#买进
              if isnan(strategy.ix[p-1,'p_lag']) or p == 0:#初始建仓
                     pos = positions[int(strategy.ix[p,'p_lag'])]
                     delta = (pool[-1]*(1-base_ratio)/data.ix[p,'close'])
                     amount1.append(pos*delta)
                     amount2.append((1-pos)*delta)
                     securities1.append(amount1[-1]*data.ix[p+1,'close'])
                     securities2.append(amount2[-1]*data.ix[p+1,'close'])
                     pool.append(pool[-1]+(amount2[-1]-amount1[-1])*data.ix[p,'close'])
              else:#平空建多
                     pos = positions[int(strategy.ix[p,'p_lag'])]
                     delta = pos*(amount1[-1]+amount2[-1])-amount1[-1]
                     amount1.append(amount1[-1]+delta)
                     amount2.append(amount2[-1]-delta)
                     securities1.append(amount1[-1]*data.ix[p+1,'close'])
                     securities2.append(amount2[-1]*data.ix[p+1,'close'])
                     pool.append(pool[-1]-2*delta*(data.ix[p,'close']+0.01))
       elif strategy.ix[p,'tactic']==-1:#平多建空
              pos = positions[int(strategy.ix[p,'p_lag'])]
              delta = pos*(amount1[-1]+amount2[-1])-amount1[-1]
              amount1.append(amount1[-1]+delta)
              amount2.append(amount2[-1]-delta)
              securities1.append(amount1[-1]*data.ix[p+1,'close'])
              securities2.append(amount2[-1]*data.ix[p+1,'close'])
              pool.append(pool[-1]-2*delta*(data.ix[p,'close']-0.01))
       else:#清仓tactic==2
              pool.append(pool[-1]+securities1[-1]-securities2[-1])
              amount1.append(0)
              amount2.append(0)
              securities1.append(amount1[-1]*data.ix[p+1,'close'])
              securities2.append(amount2[-1]*data.ix[p+1,'close'])
       addup.append(pool[-1]+securities1[-1]-securities2[-1])

result = pd.DataFrame({"pool":pool,
                       "amount1":amount1,
                       "amount2":amount2,
                       "securities1":securities1,
                       "securities2":securities2,
                       "addup":addup},index = [data.index])#结果汇总

##########################################################
#####################策略回测结果报告######################

annual_return = (result.ix[-1,'addup']/result.ix[0,'addup']-1)/len(result)*252
daily_return = ((-result.ix[:,'addup']+result.ix[:,'addup'].shift(-1))/result.ix[:,'addup']).shift(1)
valatility = daily_return.var()
#risk_free = ts.shibor_data(2015).ix[:,'1Y'].mean()/100#shibor一年平均值作无风险利率
#sharp_ratio = (annual_return-risk_free)/valatility  
drawdown = (result['addup']/pd.expanding_max(result['addup'])-1).sort_values()
max_drawdown = pd.DataFrame(drawdown.ix[0,0],
                            index = [drawdown.index[0]],
                            columns=['max_drawdown'])     #最大回撤                 

dr = ((-data.ix[:,'close']+data.ix[:,'close'].shift(-1))/data.ix[:,'close']).shift(1)
tr_r = result.ix[:,'addup']/result.ix[0,'addup']#策略累计收益
au_r = data.ix[:,'close']/data.ix[0,'close']#股票累计收益
###绘图
print(max_drawdown)
print(tr_r[-1])
print(au_r[-1])
plt.plot(au_r)
plt.plot(tr_r)
for q in range(len(tactic)):
       if strategy.ix[q,'tactic']==1:
              plt.annotate(u"b",xy=(au_r.index[q],au_r[q]))
       elif strategy.ix[q,'tactic']== -1:
              plt.annotate(u"s",xy=(au_r.index[q],au_r[q]))
       else:
              continue
for r in range(len(grids)):
       if r==0 or r==len(grids)-1:
              plt.axhline((grids/data.ix[0,'close']).ix[r,0],linestyle='--',color='red')
       else:
              plt.axhline((grids/data.ix[0,'close']).ix[r,0],linestyle='--',color='green')
       
###说明
#for_print=['年化收益率','夏普比率','方差','最大回撤']
#for_data = [annual_return,sharp_ratio,valatility,max_drawdown]
#for i in range(4):
#       print('{}:{}'.format(for_print[i],for_data[i]))