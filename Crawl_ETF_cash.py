# https://vip.fxxkpython.com/?p=1903
import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
# import xlwt

import os
if not os.path.exists('./result/'):   #os：operating system，包含操作系统功能，可以进行文件操作
    os.mkdir('./result/') #如果存在那就是这个result_path，如果不存在那就新建一个

def request_web(url):
    headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                        'Chrome/88.0.4324.146 Safari/537.36', # 这是一个header，伪装成电脑
        }

    try:
        response = requests.get(url=url, headers=headers)
        if response.status_code == 200:
            return response.text
    except requests.RequestException:
        return None

if __name__ == '__main__':
    ETFcash = dict()
    ETFcash['基金标的'] = ['沪深300','上证50','中证500','中证1000','中证1000']
    ETFcash['基金代码'] = [510300,510050,510500,512100,159633]
    cash_amount = []
    cash_date = []
    for ETF in ETFcash['基金代码']:
        print(f'正在查询{ETF}')
        url = f'http://money.finance.sina.com.cn/fund/go.php/vAkFundInfo_JJSGSHJBXX/q/{ETF}.phtml'
        soup = BeautifulSoup(request_web(url), 'lxml')
        list = soup.find(class_='tagmain').find_all('td') 
        _ = [float(i) for i in re.findall(r"\d+\.?\d*",str(list[16]))]
        __ = re.findall(r"\d+\-?\d+\-?\d+",str(list[10]))
        cash_amount.append(_[0])
        cash_date.append(__[0])
    ETFcash['预估现金差额'] = cash_amount
    ETFcash['更新日期'] = cash_date

    pd.DataFrame(ETFcash).set_index('基金代码').to_csv('./result/ETFcash.csv', encoding='utf-8',index = '基金代码')
    print('查询完成')
    pd.DataFrame(ETFcash).set_index('基金代码')
