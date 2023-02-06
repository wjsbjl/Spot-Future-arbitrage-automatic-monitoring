# import requests
from bs4 import BeautifulSoup
import numpy as np
import pandas as pd
import re
import sys
sys.path.append("/Applications/Wind API.app/Contents/python")
from WindPy import w
import datetime
import os
if not os.path.exists('./result/'):   #os：operating system，包含操作系统功能，可以进行文件操作
    os.mkdir('./result/') #如果存在那就是这个result_path，如果不存在那就新建一个
from Crawl_ETF_cash import request_web
from time import sleep
from sendmail import send_mail
threshold_value = 0.4

ETFcash = dict()
ETFcash['基金标的'] = ['沪深300','上证50','中证500','中证1000','中证1000']
ETFcash['基金代码'] = [510300,510050,510500,512100,159633]
cash_amount = []
cash_date = []
for ETF in ETFcash['基金代码']:
    print(f'正在查询{ETF}')
    url = f'http://money.finance.sina.com.cn/fund/go.php/vAkFundInfo_JJSGSHJBXX/q/{ETF}.phtml'
    soup = BeautifulSoup(request_web(url), 'lxml')
    Findlist = soup.find(class_='tagmain').find_all('td')  # 作者习惯太差了，命名list覆盖了list函数
    _ = [float(i) for i in re.findall(r"\d+\.?\d*",str(Findlist[16]))]
    __ = re.findall(r"\d+\-?\d+\-?\d+",str(Findlist[10]))
    cash_amount.append(_[0])
    cash_date.append(__[0])
ETFcash['预估现金差额'] = cash_amount
ETFcash['更新日期'] = cash_date

pd.DataFrame(ETFcash).set_index('基金代码').to_csv('./result/ETFcash.csv', encoding='utf-8',index = '基金代码')
print('查询完成')
print(pd.DataFrame(ETFcash).set_index('基金代码'))

# 基金代码尾部为OF，期货为2302，2303，2306，2309.CFE
ETFCash = pd.read_csv('./result/ETFcash.csv').set_index('基金代码')
ETFCash.loc[:,'标的指数'] = ['000300.SH','000016.SH','000905.SH','000852.SH','000852.SH']
ETFCash.loc[:,'期货种类'] = ['IF','IH','IC','IM','IM']
ETFDict = dict({'ETFCash': ETFCash})
w.start() 
# w.isconnected()
# w.stop()
Totallst = [f'{x}' for x in ETFDict['ETFCash'].index]
PremOut = pd.DataFrame(index = ['基金名称','IOPV','  标的最新价','  标的代码',
                '  T日预估现金差额','  当日现金部分','  当日市值部分','  买入赎回最小份额',#'溢折率',
                '现货最新价','期货最新价','  2302','  2303','  2306','  2309',
                '期现套利值','  2302','  2303','  2306','  2309'],columns=Totallst)
PremOut.loc['  T日预估现金差额',:] = ETFCash.loc[:,'预估现金差额'].values
PremOut.loc['  标的代码',:] = ETFCash.loc[:,'标的指数'].values
PremOut.loc['基金名称',:] = ['华泰沪深300',	'南方中证500',	'华夏上证50','南方中证1000',	'易方达中证1000']
# PremOut.loc['基金名称',:] = ['华泰柏瑞沪深300ETF',	'南方中证500ETF',	'华夏上证50ETF','南方中证1000ETF',	'易方达中证1000ETF']
PremOut.loc['期现套利值',:] = ['','','','','']
PremOut.loc['期货最新价',:] = ['','','','','']
# MinNum = 
PremOut.loc['  买入赎回最小份额',:] = w.wsd([f"{x}.OF" for x in Totallst], "fund_etfpr_minnav",  "2023-02-06", "").Data[0]
Questlst = np.array([])
M1A = []
M3A = []
NumDict = dict()
for i in range(5): # 获取每日数量和价格
    Detaillst = w.wset("etfconstituent", f"date=20230206; windcode={Totallst[i]}.OF;") # 基金申购赎回信息，获取数量VOLUME
    ColEN = Detaillst.Fields
    ColCH = ['日期'	,'Wind代码'	,'证券名称'	,'数量'	,'现金替代标志'	,'现金替代溢价比例(%)'	,'固定替代金额'	,'申购固定代替金额'	,'现金替代折价比例'	,'赎回固定代替金额']
    Dailylst = pd.DataFrame(data = Detaillst.Data , index = ColCH)
    Dailylst = Dailylst.T.set_index('日期')
    ETFDict[Totallst[i]] = Dailylst
    Questlst = np.concatenate([Questlst,Dailylst.loc[:,'Wind代码'].values],axis = 0)
    M1A.append(sum(Dailylst[(Dailylst['现金替代标志'] == '必须') | (Dailylst['现金替代标志'] == '允许')].loc[:,'固定替代金额']))
    M3A.append(ETFCash.loc[ETFCash.index[i],'预估现金差额'])
    NumDict[Totallst[i]] = ETFDict[Totallst[i]][(ETFDict[Totallst[i]]['现金替代标志'] == '允许') | 
    (ETFDict[Totallst[i]]['现金替代标志'] == '禁止') | (ETFDict[Totallst[i]]['现金替代标志'] == '退补')].set_index('Wind代码').loc[:,['数量']]

PremOut.loc['  当日现金部分',:] = M1A
FutName = [*ETFCash.loc[ETFDict['ETFCash'].index,'期货种类']]
AllQuest = list()
AllQuest.extend(Questlst)
AllQuest.extend([f"{x}.OF" for x in Totallst])
AllQuest.extend(ETFDict['ETFCash'].loc[:,'标的指数'])
AllQuest.extend([f'{y}{x}.CFE' for y in FutName for x in ['2302','2303','2306','2309'] ])
AllQuest = list(set(AllQuest))

while True:
    AllPrc = w.wsq(AllQuest,"rt_last",func='DemoWSQCallback') # 实时价格
    AllPrice = pd.DataFrame(columns = AllPrc.Codes, data = AllPrc.Data,index = ['Price']).T    
    for i in range(5): # 获取每日数量和价格
        # i = 0
        NumDict[Totallst[i]].loc[:,'价格'] = [*AllPrice.loc[NumDict[Totallst[i]].index,:]['Price']]
        M2 = (NumDict[Totallst[i]].iloc[:,0] * NumDict[Totallst[i]].iloc[:,1]).sum()
        PremOut.loc['  当日市值部分',:][i] = M2
        PremOut.iloc[-9:-5,i] = [*AllPrice.loc[[f"{FutName[i]}{x}.CFE" for x in ['2302','2303','2306','2309']],'Price']]
    PremOut.loc['现货最新价',:] = [AllPrice.loc[x,'Price'] for x in ETFDict['ETFCash'].loc[:,'标的指数'].values]
    PremOut.loc['IOPV',:] = (PremOut.loc['  T日预估现金差额',:] + PremOut.loc['  当日现金部分',:] + PremOut.loc['  当日市值部分',:]) / PremOut.loc['  买入赎回最小份额',:]
    ETFPrice = AllPrice.loc[[f"{x}.OF" for x in Totallst],'Price']
    PremOut.loc['  标的最新价',:] = [*ETFPrice]
    PremDisc = 1 - PremOut.loc['IOPV',:] / PremOut.loc['  标的最新价',:]
    PremOut.iloc[-4:,:] = PremOut.iloc[-9:-5,:] / PremOut.loc['现货最新价',:] - (1-PremOut.loc['IOPV',:]/PremOut.loc['  标的最新价',:]) -1
    print(PremOut)
    quest_time = pd.to_datetime(AllPrc.Times[0])
    print("Time is ",pd.to_datetime(AllPrc.Times[0]))
    print("")
    # if sum((PremOut.iloc[-4:,:] > threshold_value).sum()): #如果触发阈值0.4
    #     PremOut.to_csv('./to_be_sent.csv')
    #     send_mail("m97862@163.com","smtp.163.com",'m97862@163.com',quest_time)
    #     print("Threshold is attached. Program over.")
    #     print("Threshold is attached. Program over.")
    #     print("Threshold is attached. Program over.")
    #     print("Threshold is attached. Program over.")
    #     print("Threshold is attached. Program over.")
    #     print("Threshold is attached. Program over.")
    #     print("Threshold is attached. Program over.")
    #     print("Threshold is attached. Program over.")
    #     break
    sleep(1)