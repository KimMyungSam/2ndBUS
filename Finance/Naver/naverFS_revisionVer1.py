
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

# In[4]:

import re
from datetime import datetime
import pandas as pd
import requests
from bs4 import BeautifulSoup
import mysql.connector
import sqlalchemy
from sqlalchemy import create_engine
import pandas as pd


# get_date_str(s) - 문자열 s 에서 "YYYY/MM" 문자열 추출
def get_date_str(s):
    date_str = ''
    r = re.search("\d{4}/\d{2}", s)
    if r:
        date_str = r.group()
        date_str = date_str.replace('/', '-')
    return date_str

# 년도별, 분기별 data있음을 체크하여 DB에 저장
def save_naverFS(df,freq_type, code):
    df['code'] = code
    if freq_type == 'Y':
        df.to_sql('naverfs_y', con, if_exists = 'append', index_label='date')
    elif freq_type == 'Q':
        df.to_sql('naverfs_q', con, if_exists = 'append', index_label='date')
    return None


# * code: 종목코드
# * fin_type = '0': 재무제표 종류 (0: 주재무제표, 1: GAAP개별, 2: GAAP연결, 3: IFRS별도, 4:IFRS연결)
# * freq_type = 'Y': 기간 (Y:년, Q:분기)
# 
# - 2017.7.01  네이버재무제표 구조가 단일 리스트 컬럼 구조에서 이중 리스트 구조로 변경되어 df[i][1] 형태로 date 정보를 가져옴
# 문제점과 해결방안
# 표시된 DataFrame을 자세히 살펴보면 아래와 같은 문제점들이 있다. (대부분 네이버 파이낸스 페이지의 HTML TABLE 표현의 문제다)
# 
# 문제점
# '연간'이른 컬럼명이 추가되었고, 컬럼 이름이 한 컬럼씩 오른쪽으로 밀렸다.
# 마지막 컬럼의 값이 NaN 값 (컬럼 이름이 밀려서 발생)
# 날짜에 "(IFRS연결)"와 같이 불필요한 문자열 포함하고 있다.
# 시계열 데이터로 처리하려면, '주요재무정보'가 컬럼이 되고 날짜가 행(row)가 되는 것이 편리하다.
# 각 문제에 대한 해결방안
# 컬럼명 '연간' 삭제
# 컬럼 문자열에서 날짜(년, 월)만 추출 (정규식 사용)
# 마지막 컬럼 삭제
# 컬럼과 로우를 전환 (df.T) 한다 (transpose 우리말로 전치행렬 이라고 한다)

# In[5]:

def get_finstate_naver(code, fin_type, freq_type):
    url_tmpl = 'http://companyinfo.stock.naver.com/v1/company/ajax/cF1001.aspx?'                    'cmp_cd=%s&fin_typ=%s&freq_typ=%s'
    url = url_tmpl % (code, fin_type, freq_type)
    
    dfs = pd.read_html(url, encoding="utf-8")
    df = dfs[0]
    if df.iloc[0,0].find('해당 데이터가 존재하지 않습니다') >= 0:
        return None

    new_cols = []
    #df = df.reset_index(drop=True)
    cols = list(df.columns)
    
    for i in range(0,len(cols)):
        new_cols.append(cols[i][1])
    '''
    if '연간' in new_cols: new_cols.remove('연간')
    if '분기' in new_cols: new_cols.remove('분기')
    '''
    cols = ['date']
    for x in new_cols[:-1]:
        cols.append(get_date_str(x))
    df.columns = cols
    df.set_index('date', inplace=True)
    dft = df.T
    dft.index = pd.to_datetime(dft.index)

    # remove if index is NaT
    dft = dft[pd.notnull(dft.index)]
    
    #종목별 컬럼name 오류를 수정함
    dft.rename(columns={'유보율': '자본유보율'}, inplace=True)
    dft.rename(columns={'현금배당성향': '현금배당성향(%)'}, inplace=True)

    return dft


# In[6]:

if __name__ == "__main__":
    # NULL row에 대해 삭제가 필요함. 코드 추가 필요함
    dir = 'D:/naver/FS/'
    
    pwd = 'rlaehgus1'
    engine = create_engine('mysql+mysqlconnector://root:'+pwd+'@localhost/findb', echo=False)
    con = engine.connect()
    
    sql = 'SELECT * FROM listed_company'
    comp_code = pd.read_sql(sql, con=engine)

    for inx, row in comp_code.iterrows():
        code = row['code']
        print ('code=',code)
        
        # 네이버금융 데이터에서 재주재표 정보 가져오기
        df_year = get_finstate_naver(code, 0, 'Y')    #년간 재무제표
        df_quarter = get_finstate_naver(code, 0, 'Q')    #분기별 재무제표

        if df_year is not None:
            save_naverFS(df_year,'Y', code)    # 년간 db전체를 저장
        
            # csv파일로 저장
            # fname = dir + year + '_ifrs_con_' + code + '.csv'
            # df_year.to_csv(fname)
            
        if df_quarter is not None:
            save_naverFS(df_quarter,'Q', code)    # 분기별 db전체를 저장
        
            # csv파일로 저장
            # fname = dir + quarter + '_ifrs_con_' + code + '.csv'
            # df_quarter.to_csv(fname)


# naver colums(
# ['매출액', '영업이익', '세전계속사업이익', '당기순이익', '당기순이익(지배)', 
# '당기순이익(비지배)', '자산총계',       '부채총계', '자본총계', '자본총계(지배)', 
# '자본총계(비지배)', '자본금', '영업활동현금흐름', '투자활동현금흐름',       
# '재무활동현금흐름', 'CAPEX', 'FCF', '이자발생부채', '영업이익률', '순이익률',
# 'ROE(%)','ROA(%)', '부채비율', '자본유보율', 'EPS(원)', 'PER(배)', 'BPS(원)',
# 'PBR(배)','현금DPS(원)', '현금배당수익률', '현금배당성향(%)', '발행주식수(보통주)'],
# dtype='object', name='주요재무정보')

# ##### data 디렉토리의 "naver_finstate_" + 아래 표의 이름을 붙여 디렉토리를 지정
# 
# ##### 디렉토리 문자열	설명	기간
# ##### year_gaap	GAAP	년
# ##### year_ifrs_con	IFRS 연결	년
# ##### year_ifrs_sep	IFRS 별도	년
# ##### quater_gaap	GAAP	분기
# ##### quater_ifrs_con	IFRS 연결	분기
# ##### quater_ifrs_sep	IFRS 별도	분기

# In[ ]:



