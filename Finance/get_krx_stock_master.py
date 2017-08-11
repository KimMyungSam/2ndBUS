
# coding: utf-8

# # KRX 종목 마스터 만들기
# 거래소 상장회사검색 http://marketdata.krx.co.kr/contents/MKD/04/0406/04060100/MKD04060100.jsp

# In[1]:

import requests
import pandas as pd
import io
import mysql.connector
import sqlalchemy
from sqlalchemy import create_engine


# In[2]:

# pwd=input('Enter Password for server:')
pwd = 'rlaehgus1'
engine = create_engine('mysql+mysqlconnector://root:'+pwd+'@localhost/findb', echo=False)

def get_krx_stock_master():
    # STEP 01: Generate OTP
    gen_otp_url = 'http://marketdata.krx.co.kr/contents/COM/GenerateOTP.jspx'
    gen_otp_data = {
        'name':'fileDown',
        'filetype':'xls',
        'url':'MKD/04/0406/04060100/mkd04060100_01',
        'market_gubun':'ALL', # ''ALL':전체, STK': 코스피
        'isu_cdnm':'전체',
        'sort_type':'A',
        'std_ind_cd':'01',
        'lst_stk_vl':'1',
        'in_lst_stk_vl':'',
        'in_lst_stk_vl2':'',
        'pagePath':'/contents/MKD/04/0406/04060100/MKD04060100.jsp',
    }

    r = requests.post(gen_otp_url, gen_otp_data)
    code = r.content

    # STEP 02: download
    down_url = 'http://file.krx.co.kr/download.jspx'
    down_data = {
        'code': code,
    }
    
    #io를 사용하여 다운로드 파일을 받지않고 file type으로 만들어준다
    r = requests.post(down_url, down_data)
    f = io.BytesIO(r.content)
    
    usecols = ['종목코드', '기업명', '업종코드','업종','상장주식수(주)','자본금(원)','액면가(원)', '대표전화', '주소']
    df = pd.read_excel(f, converters={'종목코드': str, '업종코드': str}, usecols=usecols)
    df.columns = ['code', 'name', 'sector_code', 'sector','lilsted_stock','capital','par_value','telephone', 'address']
    return df


# In[5]:

# 상장회사 목록을 listed_company table명으로 만든다.

if __name__ == "__main__":
            
    df = get_krx_stock_master()
    df.to_sql(name='listed_company', con=engine, if_exists='replace',index=False)


# ### database table에서 data 불러오기...
# ### sql = 'SELECT * from 테이블이름' , 모두불러오기
# ### df = pd.read_sql(sql, con=engine) , sql문 전달하기
# ### sql = 'SELECT code FROM company WHERE sector LIKE "%제조업%"' , company테이블에서 sector필드중 제조업 단어가 들어있는 모든 row 추출..
