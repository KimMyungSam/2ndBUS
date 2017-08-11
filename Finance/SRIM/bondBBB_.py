### mysql create table 'bond5years'
### bond5years table - years, bbb_

import requests
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import mysql.connector
import sqlalchemy
from sqlalchemy import create_engine
from io import  StringIO

def get_bond(yesterday, s_date):
    n = 0
    url = 'https://www.kisrating.com/ratingsStatistics/statics_spread.do'

    while int(yesterday) >= int(s_date):
        s_date = date + timedelta(n)
        s_date = s_date.strftime("%Y%m%d")
    
        data = {
            'startDt':s_date
        }

        r = requests.post(url, data=data)
        dfs = pd.read_html(StringIO(r.text))
        df = dfs[0]
        
        if not df.empty:
            df.set_index('구분', inplace=True)

            # Respected rate of return
            bbb_value = float(df.loc['BBB-', '5년'])
            sql = "INSERT INTO bond5years (year, bbb_) values(%s, %s)"
            # 한번만 실행함으로 comment처리해 놓음.
            con.execute(sql, s_date, bbb_value, if_exists='replace')
            print (s_date,bbb_value)
        n += 1

if __name__ == "__main__":
    pwd = 'rlaehgus1'
    engine = create_engine('mysql+mysqlconnector://root:'+pwd+'@localhost/findb', echo=False)
    con = engine.connect()
    
    today = datetime.today()
    yesterday = today - timedelta(1)
    yesterday = yesterday.strftime("%Y%m%d")
    date = datetime(2002,1,2) # 한신평 채권금리 첫 제공 일자
    s_date = date.strftime("%Y%m%d")

    get_bond(yesterday, s_date)
