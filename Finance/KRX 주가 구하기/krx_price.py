
# coding: utf-8

# # 시가총액 순위 정보
# ## 시장정보 → 주식 → 순위정보 → 시가총액 상/하위 정보로 가격 데이터 구축
# - 일별 전 종목 가격을 가져 올수있어, 네이버 전종목 가격데이타 구축보다 효율적임
# - DB만들때 INT 크기 신경써야 하고 DOUBLE 형으로도 필요함
# - 각 컬럼의 기본값을 Null로 설정해야 함.
# 
# * http://marketdata.krx.co.kr/contents/MKD/04/0404/04040200/MKD04040200.jsp
# * 일별: 종목코드, 종목명, 현재가, 등락률, 거래량, 거래대금, 시가총액, 시가총액비중(%), 상장주식수(천주), 외국인, 보유주식수, 외국인, 지분율(%)
# * 1995-05-02 부터 현재까지 일자별
# <img src="KRX_DB_컬럼및속성.jpg">

# # stock_master_krx()

# In[ ]:

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import requests
from io import BytesIO
import mysql.connector
import sqlalchemy
from sqlalchemy import create_engine

def stock_master_krx(date_str=None):
    # 시가총액순위 정보를 DataFrame으로 반환
    if date_str == None:
        date_str = datetime.today().strftime('%Y%m%d')

    # STEP 01: Generate OTP
    gen_otp_url = 'http://marketdata.krx.co.kr/contents/COM/GenerateOTP.jspx'
    gen_otp_data = {
        'name':'fileDown',
        'filetype':'xls',
        'url':'MKD/04/0404/04040200/mkd04040200_01',
        'market_gubun':'ALL', #시장구분: ALL=전체
        'indx_ind_cd':'',
        'sect_tp_cd':'',
        'schdate': date_str,
        'pagePath':'/contents/MKD/04/0404/04040200/MKD04040200.jsp',
    }
    
    r = requests.post(gen_otp_url, gen_otp_data)
    code = r.content
    
    # STEP 02: download
    down_url = 'http://file.krx.co.kr/download.jspx'
    down_data = {
        'code': code,
    }
    
    r = requests.post(down_url, down_data)
    df = pd.read_excel(BytesIO(r.content), header=0, thousands=',', converters={'종목코드': str})
    return df


# In[ ]:

if __name__ == "__main__":
    pwd = 'rlaehgus1'
    engine = create_engine('mysql+mysqlconnector://root:'+pwd+'@localhost/findb', echo=False)
    connector = engine.connect()

    start = datetime(1996, 1, 3)    # 주식시장 첫 거래일 지정
    end = datetime.today() - timedelta(days=1) # yearterday
    dates = pd.date_range(start=start, end=end)
    
    # db에 저장된 가장 최근 날짜 or 
    begin_date = str(datetime(1969, 1, 3))

    sql = 'SELECT date FROM krx_stock_price WHERE 종목코드=005930 ORDER BY date DESC LIMIT 1'    #가장 최신date, 쿼리 정확도를 위해 삼성전자 사용
    result = connector.execute(sql)
    imsi_day = result.fetchone()

    if imsi_day is not None:
        latest_date = imsi_day[0].strftime('%Y%m%d')
    elif imsi_day is None:
        latest_date = datetime(1969, 1, 3).strftime('%Y%m%d')

    # start date 찾기
    for date in dates:
        
        if date.strftime('%Y%m%d') <= latest_date:
            continue
            
        date_str = date.strftime('%Y%m%d')
        df = stock_master_krx(date_str)
        df['date'] = date
        df.set_index('date', inplace=True)
        print(date_str)
        print('count: ', len(df))
        df.rename(columns={'등락률': '등락률(%)','거래량': '거래량(주)','상장주식수(천주)': '상장주식수',                            '외국인 보유주식수': '외국인보유수량'}, inplace=True)
        try:
            if len(df) != 0:
                df.to_sql(name = 'krx_stock_price', con = engine, if_exists='append')
        except:
            print ('정보오류 입니다.')
    connector.close()


# In[ ]:



