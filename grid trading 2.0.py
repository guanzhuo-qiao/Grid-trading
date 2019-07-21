# -*- coding: utf-8 -*-
"""
Created on Tue Jul 18 09:37:47 2017
grid trading 2.0
网格交易2.0
(此版本较上一个版本改进：
1，摒弃分成不同的小账户的策略，而是采用整体调仓的思想
2，首先生成一个固定的网格
3，不去刻意寻找低位介入，(在低位介入的整体效果不好)，改用初始价位在触碰到网格时进场
4，仓位成指数型上涨，价格越高减仓越重)

回测分为三个部分：
1，策略信号生成，结果为strategy
2，模拟账户交易，结果为result 不考虑交易手续费、碎股
3，回测报告

网格交易
    网格交易是将价格分为几个固定的网格，当股价由下向上涨到某个网格线时卖出，当股价由上向下跌
到某个网格线时买入，买入与卖出的量以最后达到固定的仓位比例而决定。
    例如：
    ceil--------/-\----------$4 仓位：0%
        ------/----\---------$3 仓位：30%
        ----/-------\--------$2 仓位：60%
    base--/----------\-------$1 仓位：100%
    当价格从$1涨到$2，我们需要减仓至60%；
    当价格从$4跌到$3，我们需要加仓至30%。
    每接触到网格线，便交易一次。
    
    如果股票在base与ceil之间不断波动，我们就可以从中获利，故应该挑选波动率大的股票
    此外，最好在股票下跌的时段开始策略，因为这一策略本身是一种补仓与减仓的思想，在补仓
过程中，它有助于缩减损失，相应的如果在上涨阶段开始模型，则会因为不断减仓而使利润减少。
    本策略还预设置了底仓，是当股价下降到一定阶段购入的资金的固定比率，设置这一底仓的目的是为了
当牛市来临时，底仓可以把握住这一时机。（本策略还没有完善这一方面，故测试时base_ratio=0)
    本策略在ceil之上，base之下设置了阈值（beta、alpha），当股价超出时抛出所有仓位。
    
@author: ttc
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import tushare as ts

###########################数据获取############
df = ts.get_k_data('000011',start='2015-05-10')
df.set_index(pd.to_datetime(df.date),inplace=True)
df.drop(['date','code'],axis=1, inplace=True)
data = df.ix[:,['close','open']]
################################################
###########################策略参数设置#############
beta=0.2
base=min(data['close'])#为了简便将参数设置为这样，实际操纵中这一参数通过历史经验估计或者其他统计手段得到
ceil=max(data['close'])#同上
alpha = 0.05
n = 10 #分为n格；n+1条格线
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
tactic = []#1买进，-1卖出，0观望
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

"""信号生成过程"""
for i in range(m+1,len(data)):
       if p_lag[-1] not in  (grids.iloc[0,0],grids.iloc[-1,0]):
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
def position(base_ratio,primary,n):
       rate = pow((1-base_ratio)/primary,1/(n-1))-1
       x=[primary*pow(1+rate,power) for power in range(0,n)]
       x.insert(0,0)
       x=[round(pos+base_ratio,2) for pos in x]
       x.insert(0,0)
       x.append(0)
       return x
primary=1/6
base_ratio=0
positions = position(base_ratio,primary,n)#仓位列表
###########################################
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