
# coding: utf-8

# 네이버 파이낸스에서 재무제표 데이터를 크롤링 하기 위해 알아야 할 정보는 아래 URL이 전부다.
# 
# http://companyinfo.stock.naver.com/v1/company/ajax/cF1001.aspx?cmp_cd=105560&fin_typ=0&freq_typ=Y
# 
# URL을 구성하는 파라미터의 의미는 다음과 같다.
# 
# 인자 | 의미 | 값
# -- | -- | --
# cmp_cd |  종목코드 | 005930 (종목코드)
# fin_typ | 재무제표 타입 | 0: 주재무제표, 1: GAAP개별, 2: GAAP연결, 3: IFRS별도, 4:IFRS연결
# freq_typ | 기간 | Y:년, Q:분기

# In[ ]:

import re
from datetime import datetime
import pandas as pd
import requests
from bs4 import BeautifulSoup

'''
get_date_str(s) - 문자열 s 에서 "YYYY/MM" 문자열 추출
'''
def get_date_str(s):
    date_str = ''
    r = re.search("\d{4}/\d{2}", s)
    if r:
        date_str = r.group()
        date_str = date_str.replace('/', '-')

    return date_str

def save_naverFS(df,code):
    df['code'] = code
    df.to_sql('naverfs', con, if_exists = 'append')
    return None
    
'''
* code: 종목코드
* fin_type = '0': 재무제표 종류 (0: 주재무제표, 1: GAAP개별, 2: GAAP연결, 3: IFRS별도, 4:IFRS연결)
* freq_type = 'Y': 기간 (Y:년, Q:분기)
'''
def get_finstate_naver(code, fin_type='0', freq_type='Y'):
    url_tmpl = 'http://companyinfo.stock.naver.com/v1/company/ajax/cF1001.aspx?'                    'cmp_cd=%s&fin_typ=%s&freq_typ=%s'

    url = url_tmpl % (code, fin_type, freq_type)
    #print(url)

    dfs = pd.read_html(url, encoding="utf-8")
    df = dfs[0]
    if df.ix[0,0].find('해당 데이터가 존재하지 않습니다') >= 0:
        return None

    df.rename(columns={'주요재무정보':'date'}, inplace=True)
    df.set_index('date', inplace=True)

    cols = list(df.columns)
    if '연간' in cols: cols.remove('연간')
    if '분기' in cols: cols.remove('분기')
    cols = [get_date_str(x) for x in cols]
    df = df.ix[:, :-1]
    df.columns = cols
    dft = df.T
    dft.index = pd.to_datetime(dft.index)

    # remove if index is NaT
    dft = dft[pd.notnull(dft.index)]
    
    #종목별 컬럼name 오류를 수정함
    dft.rename(columns={'유보율': '자본유보율'}, inplace=True)
    dft.rename(columns={'현금배당성향': '현금배당성향(%)'}, inplace=True)
    
    return dft


# In[ ]:

import mysql.connector
import sqlalchemy
from sqlalchemy import create_engine
import pandas as pd

if __name__ == "__main__":
    dir = 'D:/naver/FS/'
    year = '2017'    
    
    pwd = 'rlaehgus1'
    engine = create_engine('mysql+mysqlconnector://root:'+pwd+'@localhost/findb', echo=False)
    con = engine.connect()
    
    sql = 'SELECT * FROM listed_company'
    comp_code = pd.read_sql(sql, con=engine)

    for inx, row in comp_code.iterrows():
        code = row['code']
      
        # 네이버금융 데이터에서 재주재표 정보 가져오기
        df = get_finstate_naver(code)
      
        if df is not None:
            # db전체를 저장
            save_naverFS(df,code) 
        
            # csv파일로 저장
            fname = dir + year + '_ifrs_con_' + code + '.csv'
            df.to_csv(fname)


# naver colums(
# ['매출액', '영업이익', '세전계속사업이익', '당기순이익', '당기순이익(지배)', 
# '당기순이익(비지배)', '자산총계',       '부채총계', '자본총계', '자본총계(지배)', 
# '자본총계(비지배)', '자본금', '영업활동현금흐름', '투자활동현금흐름',       
# '재무활동현금흐름', 'CAPEX', 'FCF', '이자발생부채', '영업이익률', '순이익률',
# 'ROE(%)','ROA(%)', '부채비율', '자본유보율', 'EPS(원)', 'PER(배)', 'BPS(원)',
# 'PBR(배)','현금DPS(원)', '현금배당수익률', '현금배당성향(%)', '발행주식수(보통주)'],
# dtype='object', name='주요재무정보')

# data 디렉토리의 "naver_finstate_" + 아래 표의 이름을 붙여 디렉토리를 지정
# 
# 디렉토리 문자열	설명	기간
# year_gaap	GAAP	년
# year_ifrs_con	IFRS 연결	년
# year_ifrs_sep	IFRS 별도	년
# quater_gaap	GAAP	분기
# quater_ifrs_con	IFRS 연결	분기
# quater_ifrs_sep	IFRS 별도	분기
