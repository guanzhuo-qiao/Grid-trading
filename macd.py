#读入数据
import xlrd
company="G:\strategy regression\汉王科技.xls"
data = xlrd.open_workbook(company)
table = data.sheet_by_name(u'汉王')
tradetime = table.col_values(2)  #交易日

weektime = table.col_values(4)   #停牌

opnprc = table.col_values(5)     #开盘价

highest = table.col_values(6)    #最高价

lowest = table.col_values(7)     #最低价

clsprc = table.col_values(8)     #收盘价 
rate = table.col_values(14)
# 指标模型建立
def EMA(n,ema0,price=[]):
    pierid=n+1
    ema=[ema0]
    for x in range(1,len(price)):
        ema.append((pierid-2)/pierid*ema[x-1]+2/pierid*price[x])
    return ema
def DIF(emaf=[],emas=[]):
    dif=[]
    for x in range(0,len(emaf)):
        dif.append(emaf[x]-emas[x])
    return dif
def MACD(f,emaf0,s,emas0,k,dea0,price=[]):
    emaf=EMA(f,emaf0,price)
    emas=EMA(s,emas0,price)
    dif=DIF(emaf,emas)
    dea=EMA(k,dea0,dif)
    macd_original=DIF(dif,dea)
    macd_common=[]
    for x in range(0,len(macd_original)):
        macd_common.append(2*macd_original[x])
    return macd_common

macd=MACD(12,clsprc[0],26,clsprc[0],9,0,clsprc)

#账户模型建立
pool = [1000000]
amount = [0] #手数
asset = [0]
plus = [1000000]
option=['first']

#策略模型建立
for i in range(1,len(clsprc)):
    if i==len(clsprc)-1:   #平仓了结
      pool.append(pool[i-1]+amount[i-1]*clsprc[i]*100)
      plus.append(pool[i])
      amount.append(0)
      asset.append(0)
      option.append('final')
    else:
     
      if macd[i-1]>0 and amount[i-1] == 0:     #买入
        amount.append(pool[i-1]//(opnprc[i]*100))  
        asset.append(amount[i]*opnprc[i]*100)
        pool.append(pool[i-1]-asset[i])
        option.append('buy')
      elif macd[i-1]<0 and amount[i-1] != 0:   #卖出
        amount.append(0)
        asset.append(amount[i]*opnprc[i])
        pool.append(pool[i-1]+amount[i-1]*opnprc[i]*100)
        option.append('sell')
      else:                                         #观望
        amount.append(amount[i-1])
        asset.append(amount[i]*opnprc[i]*100)
        pool.append(pool[i-1])
        option.append('still')
      plus.append(pool[i]+asset[i])
#print(plus)
#print(option)
#策略报告
import matplotlib.pyplot as plt
#threadList = range(len(tradetime))
plusr=[]
for x in range(1,len(plus)):
    plusr.append(plus[x]/10000)
line1 = plt.plot(plusr)
line2 =plt.plot(clsprc)
plt.show()





