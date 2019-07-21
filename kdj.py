import xlrd
company="万科A.xls"
data = xlrd.open_workbook(company)
table = data.sheet_by_name(u'FinanceDeal')
tradetime = table.col_values(2)  #交易日

weektime = table.col_values(4)   #停牌

opnprc = table.col_values(5)     #开盘价

highest = table.col_values(6)    #最高价

lowest = table.col_values(7)     #最低价

clsprc = table.col_values(8)     #收盘价 
# 指标模型建立
n = 9   #周期（可调）
nrows = table.nrows
rsv_lst = []
K_lst = []
D_lst = []
J_lst = []
new_k = 57.08
new_d = 62.37
for i in range(nrows):
    if weektime[i]=='是':
       continue
    else:
      if i<n-1:
          continue
      elif i >= n-1:
         ln = min(lowest[(i-(n-1)):i+1])
         hn = max(highest[(i-(n-1)):(i+1)])
         new_rsv=round((clsprc[i]-ln)/(hn-ln)*100,2)
         new_k=round(2*new_k/3+new_rsv/3,2)
         new_d=round(2*new_d/3+new_k/3,2)
         new_j=round(3*new_k-2*new_d,2)
         rsv_lst.append(new_rsv)
         K_lst.append(new_k)
         D_lst.append(new_d)
         J_lst.append(new_j)
#print(rsv_lst)     
#print(K_lst)
#print(D_lst)
#print(J_lst)

#账户模型建立
pool = [1000000]
amount = [0] #手数
asset = [0]
plus = [1000000]
option=['first']

#策略模型建立
for i in range(len(K_lst)):
    if i==len(K_lst)-1:   #平仓了结
      pool[i]=pool[i]+amount[i]*clsprc[i+8]*100   
      plus[i]=pool[i]
      amount[i]=0
      asset[i]=0
      option[i]='final'
    else:
     
      if J_lst[i]>K_lst[i] and amount[i] == 0:  #买入
        amount.append(pool[i]//(opnprc[i+1+8]*100))  
        asset.append(amount[i+1]*opnprc[i+1+8]*100)
        pool.append(pool[i]-asset[i+1])
        option.append('buy')
      elif J_lst[i]<K_lst[i] and amount[i] != 0:   #卖出
        amount.append(0)
        asset.append(amount[i+1]*opnprc[i+1+8])
        pool.append(pool[i]+amount[i]*opnprc[i+1+8]*100)
        option.append('sell')
      else:                                         #观望
        amount.append(amount[i])
        asset.append(amount[i+1]*opnprc[i+1+8]*100)
        pool.append(pool[i])
        option.append('still')
      plus.append(pool[i]+asset[i])
#print(plus)
#print(option)
      
#策略报告
import matplotlib.pyplot as plt
#threadList = range(len(tradetime))
dataList1 = plus
line1 = plt.plot(dataList1)
plt.show()
        
        
        
        
        
        