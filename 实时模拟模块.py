# -*- coding: utf-8 -*-
"""
Created on Fri Jul 21 14:52:27 2017
grid trading applied on national debt futures marcket
capable to short
@author: ttc
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import tushare as ts
import time
beta=0.2
ceil=30
base=12.7#为了简便将参数设置为这样，实际操纵中这一参数通过历史经验估计或者其他统计手段得到
alpha = 0.05
n = 10 #分为n格；n+1条格线
base_ratio=0
def grid(base,ceil,beta,alpha,n):
       gap=pow(ceil/base,1/n)-1
       price = [round(base*pow(1+gap,i),2) for i in range(n+1)][::-1]
       price.insert(0,round(ceil*(1+beta),2))
       price.append(round(base*(1-alpha),2))
       grid = pd.DataFrame({'lines':price})
       return grid
grids = grid(base,ceil,beta,alpha,n)
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
positions = position1(n,base_ratio)#形成仓位
def update_position(base_ratio,positions):#更新仓位
        positions[1:-1]=[round(positions[q]+base_ratio,2) for q in range(1,len(positions)-1)]
        return positions



p_lag=[8]
tactic = [0]

pool = [1000000]#资金池
amount = [0] #持有证券股数
security = [0]#证券池(随市价变化)
addup = [1000000]#总市值=资金迟+证券池
p=[]

while True:
       df = ts.get_realtime_quotes('000014')
       price = float(df.ix[0,'price'])
       if p_lag[-1] not in  (0,len(grids)-1):
              if price>=grids.ix[p_lag[-1]-1,0]:
                     tactic.append(-1)
                     p_lag.append(p_lag[-1]-1)
              elif price<=grids.ix[p_lag[-1]+1,0]:
                     tactic.append(1)
                     p_lag.append(p_lag[-1]+1)
              else:
                     tactic.append(0)
                     p_lag.append(p_lag[-1])
       else:#到达阈值则一直空仓
              tactic.append(0)
              p_lag.append(p_lag[-1])
       if tactic[-1] == 0:#观望
              pool.append(pool[-1])
              amount.append(amount[-1])
              security.append(amount[-1]*price)
       else:#操作
              if int(p_lag[-1]) == len(grids)-2:#若触及base(可以是任意网格线) 底仓介入
                     positions = update_position(base_ratio,positions)
              pos = positions[int(p_lag[-1])]
              delta = pos*(pool[-1]+amount[-1]*price)-\
                          price*amount[-1]
              delt = round(delta/price/100)*100
              pool.append(pool[-1]-delt*price)
              amount.append(amount[-1]+delt)
              security.append(amount[-1]*price)
       addup.append(pool[-1]+security[-1])
       p.append(price)
       time.sleep(10)