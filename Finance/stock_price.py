#!/usr/bin/python

# stock_price.py
# findata.db 

import requests
import pandas as pd
import io
import mysql.connector
import sqlalchemy
from sqlalchemy import create_engine
import datetime

pwd = 'rlaehgus1'
engine = create_engine('mysql+mysqlconnector://root:'+pwd+'@localhost/findb', echo=False)

def get_last_page_num(code):
    npage = 1
    url = 'http://finance.naver.com/item/sise_day.nhn?code=%s&page=1' % (code)
    r = requests.get(url)
    soup = BeautifulSoup(r.text, "lxml")
    td = soup.find('td', attrs={'class':'pgRR'})
    if td:
        npage = td.a['href'].split('page=')[1]
    return int(npage)

def get_data_naver(code, start=datetime(1900,1,1), end=nowDate):
    url_tmpl = 'http://finance.naver.com/item/sise_day.nhn?code=%s&page=%d'
    npages = get_last_page_num(code)
    df_price = pd.DataFrame()
    for p in range(1, npages+1):
        url = url_tmpl % (code, p)
        dfs = pd.read_html(url)
        
        # first page
        df = dfs[0] 
        df.columns = ['date', 'close', 'change', 'open', 'high', 'low', 'volume']
        df = df[1:]
        df.dropna(inplace=True)
        df = df.replace('\.', '-', regex=True)

        # select date range
        start_str = start.strftime("%Y-%m-%d")
        end_str = end.strftime("%Y-%m-%d")
        mask = (df['date'] >= start_str) & (df['date'] <= end_str)
        df_in = df[mask]

        # merge dataframe
        df_price = df_price.append(df_in)
        print('%d,' % p, end='', flush=True)
        print(df['date'].max())
        if df['date'].max() <= start_str:
            break
    print()
    df_price['date'] = pd.to_datetime(df_price['date'])
    int_cols = ['close', 'change', 'open', 'high', 'low', 'volume']
    df_price[int_cols] = df_price[int_cols].astype('int', raise_on_error=False)
    df_price.set_index('date', inplace=True)
    return df_price
    
if __name__ == "__main__":
    sql = 'SELECT * FROM listed_company'
    df_master = pd.read_sql(sql, con=engine)
    
    for inx, row in df_master.iterrows():
        print(row['code'], row['name'])
        #  start: DB에 저장된 마지막 날짜 + 1일
        df_max = pd.read_sql('SELECT MAX (date) AS "maxdate" FROM stock_price WHERE code="%s"' % row['code'], conn)
        last_date = datetime(1900,1,1)
        if df_max['maxdate'].iloc[0] != None:
            last_date = datetime.strptime(df_max['maxdate'].iloc[0], "%Y-%m-%d %H:%M:%S")
        start = last_date + timedelta(1)

        # end: 전일
        yday = datetime.today() - timedelta(1)
        end = datetime(yday.year, yday.month, yday.day)
        
        now = datetime.datetime.now()
        nowDate = now.strftime('%Y,%m,%d')
        
        df_price = get_data_naver(row['code'], start, nowDate)
        df_price['code'] = row['code']
        df_price.to_sql('stock_price', conn, if_exists='append', index=True)
        print('%d rows' % len(df_price))
    conn.close()