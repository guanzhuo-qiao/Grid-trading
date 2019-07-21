# -*- coding: utf-8 -*-
"""
Created on Fri Apr 21 17:07:17 2017
抛物线逼近回测
@author: ttc
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import tushare as ts
#from scipy import optimize
#####定义一个函数用于方便生成买卖信号，（1：买进；-1：卖出）
#####要根据策略中一阶导数正负判断信号方向
def orient(a):
	if a>0:
		return 1
	else:
		return -1
 
#signal generate 根据策略生成信号
#####获取数据
df = ts.get_hist_data('000001',start='20050401')#tushare的时间有误差，实际起始时间为2016-01，目前先用指数做标的
df = pd.DataFrame(df[::-1],index=pd.to_datetime(df.index[::-1]))#按时间前后排序，时间转格式
data = df.ix[:,'close']#提取收盘价做策略分析
######初始化二次拟合起点
start = 0

######初始化二次拟合参数，前2值为0，第3个值为用前3个价格拟合结果
cof = pd.DataFrame(np.zeros((2,3)),index=data.index[:2])
cof = cof.append(pd.DataFrame(np.polyfit(range(1,(2-start+1)+1),data.ix[start:2+1],2).reshape(1,3),
                              index=[data.index[2]]))
######初始化买卖信号（0：观望；1：买进；-1：卖出），前两个值为0，第3个根据该点的一阶导得到
tactic = pd.DataFrame([0,0],index=data.index[:2])
tactic = tactic.append(pd.DataFrame([orient(cof.iloc[2,0]*3+cof.iloc[2,1])],
                                     index=[data.index[2]]))
#初始化 拐点信号hint 确认期间的计数器count 
hint = False
count=0
#策略系数：确认期长度n
n = 5 

'''
交易策略名称：二次函数拟合 找寻拐点（反转点) 
交易策略具体规则：
1，遍历每天的收盘价，以起始点到遍历点的价格与为因变量；价格时间先后下标为自变量 做二次函数拟合
2，如果当天的一阶导数与前一天的相反，则将当天看为“预备拐点 ” ，若一阶导相同，则不做操作
3，若出现预备拐点，则向后观察n期，在n期内不作操作，若第n期的拟合二阶导与出现预备拐点当天同号，则确认拐点，做出操作
   若二阶导异号，则认为预备拐点为假拐点，不做操作
'''

'''
shuoming=['kong','kong','kong']
a=[0,0,0]
'''
#xian=[0,0,0]
#zibian=[1,2,3]


for i in range(3,len(data)):#遍历每天
########从第start天到今天做二次函数拟合得到a，b，c
       cof = cof.append(pd.DataFrame(np.polyfit(range(1,(i-start+1)+1),data.ix[start:i+1],2).reshape(1,3),
                                     index = [data.index[i]]))
       #a,b滞后一期的值
       a_lag = cof.iloc[i-1,0]
       b_lag = cof.iloc[i-1,1]
       #当前a，b值
       a_cur = cof.iloc[i,0]
       b_cur = cof.iloc[i,1]
       #拟合中自变量的滞后一期值与当前值
       x_lag = i-start
       x_cur = i-start+1
       '''
       a.append((a_cur*x_cur+b_cur)-(a_lag*x_lag+b_lag))
       '''
       #xian.append((a_cur*x_cur+b_cur))
       #zibian.append(x_cur)
       
       
       if hint == False:#若果之前没有“预备拐点”信号
              #当天操作为观望
              tactic = tactic.append(pd.DataFrame([0],
                                                  index = [data.index[i]]))
              #判断当天的一阶导是否与其一天异号
              if (a_lag*x_lag+b_lag)*(a_cur*x_cur+b_cur) <= 0:#若异号
                     
                     start_ready=i#记录当天相对时间
                     tactic_ready=orient(a_cur*x_cur+b_cur)#记录当天根据反转趋势做出的操作，若确认以此操作
                     hint = True#记录预备拐点
                     #shuoming.append('预备拐点')
              else:
                     hint = False
                     #shuoming.append('普通')
       else:#若之前出现预备拐点信号
              if count <n:#判断是否为拐点确认点期间，若在不操作，并累加计数器
                     tactic = tactic.append(pd.DataFrame([0],
                                                         index = [data.index[i]]))
              
                     count+=1
                     #shuoming.append('拐点确认点之间')
              else:#若计数器到达n，即到达确认点，则启动确认程序
                     if a_cur*(cof.iloc[i-3,0]) >= 0:#若二阶导为同号，则确认先前拐点，产生策略，并初始化相关变量，尤其是拟合起点
                            tactic = tactic.append(pd.DataFrame([tactic_ready],
                                                         index = [data.index[i]]))
                            start = start_ready
                            hint = False
                            count = 0
                            #shuoming.append('确认')
                            
                     else:#若二阶导异号，则确认为假拐点，初始化相关变量，不对拟合起点做更改
                            tactic = tactic.append(pd.DataFrame([0],
                                                         index = [data.index[i]]))
                            hint = False
                            count = 0
                            #shuoming.append('假拐点')
#xian2 = pd.DataFrame(xian,index=[data.index])
#zibian = pd.DataFrame(zibian,index=[data.index])
'''
shuoming = pd.DataFrame(shuoming,index=[data.index])

'''
#回测
pool = [1000000]#资金池
amount = [0] #手数
security = [0]#证券池(随市价变化)
addup = [1000000]#总市值=资金+证券
option=['first']#操作说明

for i in range(len(tactic)-1):
       if tactic.iloc[i,0] == 0:#观望
              pool.append(pool[-1])
              amount.append(amount[-1])
              security.append(amount[-1]*df.iloc[i+1,2])
              option.append('still')
       elif tactic.iloc[i,0]==1:#买进
              amount.append(amount[-1]+pool[-1]/df.iloc[i+1,0])
              pool.append(0)
              security.append(amount[-1]*df.iloc[i+1,2])
              option.append('buy')
       else:#卖出
              pool.append(pool[-1]+amount[-1]*df.iloc[i+1,0])
              amount.append(0)
              security.append(0)
              option.append('sell')
       addup.append(pool[-1]+security[-1])

result = pd.DataFrame({"pool":pool,"amount":amount,"security":security,"addup":addup},
                      index = [data.index])#结果汇总



#report策略报告

annual_return = (result.ix[-1,'addup']/result.ix[0,'addup']-1)/len(result)*250
daily_return = ((-result.ix[:,'addup']+result.ix[:,'addup'].shift(-1))/result.ix[:,'addup'].shift(-1)).shift(1)
valatility = daily_return.var()
risk_free = ts.shibor_data(2015).ix[:,'1Y'].mean()/100#shibor一年平均值作无风险利率
sharp_ratio = (annual_return-risk_free)/valatility  
drawdown = (result['addup']/pd.expanding_max(result['addup'])-1).sort_values()
max_drawdown = pd.DataFrame(drawdown.ix[0,0],
                            index = [drawdown.index[0]],
                            columns=['max_drawdown'])     #最大回撤                 

tr_r = (1+daily_return.fillna(0)).cumprod()#策略累计收益
d_p_r = df.ix[:,'p_change'].copy()/100
d_p_r.ix[0,0] = 0
au_r = (1+d_p_r.fillna(0)).cumprod()#股票累计收益
###绘图
au_graph = plt.plot(au_r)
tr_graph = plt.plot(tr_r)
###说明
for_print=['年化收益率','夏普比率','方差','最大回撤']
for_data = [annual_return,sharp_ratio,valatility,max_drawdown]
for i in range(4):
       print('{}:{}'.format(for_print[i],for_data[i]))
