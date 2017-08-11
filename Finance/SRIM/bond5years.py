### mysql create table 'bond5years'
### bond5years table - years, bbb_

import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import mysql.connector
import sqlalchemy
from sqlalchemy import create_engine
import numpy as np

def get_bond(yesterday, s_date):
    n = 0
    while int(yesterday) >= int(s_date):
        s_date = date + timedelta(n)
        s_date = s_date.strftime("%Y%m%d")
    
        url = 'http://www.kisrating.com/ratings/statics_interest.asp?gubun=1&sdate='+s_date
        html = requests.get(url).text
        soup = BeautifulSoup(html,'lxml')
        tr_list = soup.find_all('tr','')
        tr = tr_list[12].get_text() #BBB- 찾기
        txt = tr.split()
        bbb_value = txt[8] # 5년 금리 가져오기

        if bbb_value == "-":
            bbb_value = None # -문자를 NaN처리함 
        
	if bbb_value is not None:
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

