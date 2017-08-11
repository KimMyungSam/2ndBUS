### bond5years - years, bbb_
### bond5yeas table에 매일 금리를 append함.

import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import mysql.connector
import sqlalchemy
from sqlalchemy import create_engine

pwd = 'rlaehgus1'
engine = create_engine('mysql+mysqlconnector://root:' + pwd + '@localhost/findb', echo=False)
con = engine.connect()

today = datetime.today()
yesterday = today - timedelta(1)
yesterday = yesterday.strftime("%Y%m%d")

url = 'http://www.kisrating.com/ratings/statics_interest.asp?gubun=1&sdate=' + yesterday
html = requests.get(url).text
soup = BeautifulSoup(html, 'lxml')
tr_list = soup.find_all('tr', '')
tr = tr_list[12].get_text()  # BBB- 찾기
txt = tr.split()
bbb_value = txt[8]  # 5년 금리 가져오기

sql = "INSERT INTO bond5years (year, bbb_) values(%s, %s)"
con.execute(sql, yesterday, bbb_value, if_exists='append')