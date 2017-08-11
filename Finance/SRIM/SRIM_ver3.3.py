
# coding: utf-8

# #####  S-RIM
# - 기존 RIM에 사용되는 Beta를 사용하지 않고 ROE를 사용하는 RIM
# 
# #####  변경사항
# - RIM 할인율 미적용
# - save img svg형식으로 D디렉토리에 저장

# In[ ]:


import matplotlib.pyplot as plt
from matplotlib import font_manager, rc
import mysql.connector
import sqlalchemy
from sqlalchemy import create_engine
import pandas as pd
import numpy as np
from pandas import DataFrame, Series
from datetime import datetime
from copy import copy
from pandas_datareader import data, wb
from dateutil.relativedelta import relativedelta    # 상대적인 월(달) 구하기 위해서


# ##### 요구수익률, NPV 계산, 종목 Code 찾기

# In[ ]:

# 요구수익률 가져오기 (BBB- 5년 금리)
def get_required_rate_of_return():
    sql = 'SELECT * FROM bond ORDER BY date DESC LIMIT 1'
    result = connector.execute(sql)
    required = result.fetchone()
    return (required[1])

def get_npv(rate, values):
    values = np.asarray(values)
    return (values / (1+rate)**np.arange(1,len(values)+1)).sum(axis=0)

def get_code_name():
    sql = 'SELECT code, name FROM listed_company'
    df_code_name = pd.read_sql(sql,con = engine)
    return (df_code_name)


# ##### S-RIM 지속성장, 10년, 5년 성장에 따른 RIM 구하기

# In[ ]:

def get_roe_date(code, coefficient,required_rate_of_return, ref_year,df_stock, type):
    # ref_year = datetime.date.today()       # date type
    # ref_year = ref_year.year - 1           # 현재 년도 실적 ROE는 없음으로 직전 년도를 기준으로 함.
    # required_rate_of_return는 현재 BBB- 5년를 사용하지만, 업종별, 종목별, 시장환경에 맞게 변경하여 판단이 필요함.
    try:
        year_capital = df_stock.loc['capital', ref_year]
        year_roe = df_stock.loc['roe',ref_year] / 100    # 단위 % 환산
        spread = year_roe - required_rate_of_return   # 단위 % - % 계산임으로 spread변수도 값이 %가 됨.
    
        # 테이블 계산을 위한 기본 setting 
        index = ['coefficient','roe','net_profit','earing','capital']
        df_table = pd.DataFrame({ref_year:[1, year_roe, 0, 0, year_capital]},index = index) 

        # 적정가치 구하기
        roe_max_len = len(df_stock.columns)           # 년도가 있는 컬럼의 최대 길이 구함
        year_index = df_stock.columns.values.tolist() #array자료형을 list형으로 변환
        year_index = year_index.index(ref_year)    # ref_year를 기준으로 컬럼에서 위치 찾음
        year_roe_count = roe_max_len - year_index
        year = copy(ref_year)                      # ref_year를 year로 copy하여 별도 변수로 사용 a is b로 테스트
        calculated_coefficient = 0
        calculated_roe = 0
        calculated_net_profit = 0
        calculated_earing = 0
        calculated_capital = 0
        
        for year_count in range(1,11): #10년 동안 계산
            calculated_coefficient = df_table.loc['coefficient',year] - coefficient       # dataframe에서 직전년도 roe와 계산
            if calculated_coefficient < 0.0:                                              #roe 0 이하이면 0으로 세팅
                calculated_coefficient = 0.0
            
        # 기준년을 참조하여 table상의 roe그대로 사용하고, roe참조가 끝나면 계산함.
            '''
            if year_roe_count >= year_count:
                calculated_roe = df_stock.loc['roe',year] / 100    # 단위 % 환산
            else:
                calculated_roe = spread * calculated_coefficient + required_rate_of_return  # spread와 required_rate_of_return는 %단위로 환산되어있음.
            '''
            calculated_roe = spread * calculated_coefficient + required_rate_of_return  # spread와 required_rate_of_return는 %단위로 환산되어있음.
            calculated_net_profit = df_table.loc['capital',year] * calculated_roe
            calculated_earing = calculated_net_profit - df_table.loc['capital',year] * required_rate_of_return    # 단위 % 환산
            calculated_capital = df_table.loc['capital',year] + calculated_net_profit
        
            if type == 'year':
                year = year + 1 # 1년 증가
            elif type == 'quarter':
                year_month = datetime.strptime(year,'%Y%m')
                year_month = year_month + relativedelta(months=+3)
                year = year_month.strftime('%Y%m')
                
            seri_table = pd.Series([calculated_coefficient,calculated_roe,calculated_net_profit,                           calculated_earing,calculated_capital],name=year,index = index)
            df_table = pd.concat([df_table, seri_table],axis=1)

        # NPV구하기
        pv_val = df_table.loc['earing'].values.tolist()
        pv_val = pv_val[1:]
        
        # pv = get_npv(required_rate_of_return, pv_val) #초기 투자금액은 0,np.npv(0.281,[-0, 39, 59, 55, 20])
        pv = np.npv(required_rate_of_return, pv_val)
        rim = year_capital + pv
        
        # 적정주가 구하기
        '''
        stock_date = stock.loc['date',ref_year] # date type
        today = datetime.date.today()       # date type
        date_delta = stock_date - today     # timedelta type
        date_delta = date_delta.days         # int type
    
        stock_value를 구할때 할인율의 산출일 기준으로 자승으로 곱하여 남은 날짜만큼 구하고 있음.
        그러나, 이것은 과거데이타 이용 및 현재 가치 판단시에 과한것으로 판단되어 일단, 사용하지 않음
        또한, 기준날짜 - 현재날짜 일때 ...컨센서스 데이타가 없을 때는 (-)값이 나와 엉뚱하게 과하게 나옴.
        stock_value1 = rim / (1 + required_rate_of_return)**(date_delta/365)
        '''
        
        # RIM 값을 구한후 미래가치에 대해 spread값만큼 자승하여 현재 가치를 구함
        # calculated_rim = rim / (1 + required_rate_of_return) roe를 해당 Year것을 사용하여 할인율 미적용함.
        share_outstanding = df_stock.loc['share_outstanding',ref_year]  # ROE가 계산되는 year의 보통주식수
        value_per_share = int((rim / share_outstanding) * 100000000)    # 단위:억원 환산, 정수처리
        '''
        # 자승하여 현재가지치구하지 않고 현재 year 기준으로 모든것을 구했음으로 미래가치 -> 현재가지 부분을 제외
        share_outstanding = df_stock.loc['share_outstanding',ref_year]  # ROE가 계산되는 year의 보통주식수
        value_per_share = int((rim / share_outstanding) * 100000000)    # 단위:억원 환산, 정수처리
        '''
    except :
        return (000000)    # 종목정보 오류는 000000으로 세팅
    else:
        return (value_per_share)


# ##### SRIM DB만들기
# - code, date, year, close
# - value_per_share10, value_per_share5, value_per_share10

# In[ ]:

def insert_srim(icode, ref_year, value_per_share10, value_per_share5, value_per_share,type):
    # ref_year = ref_year + 1    #RIM은 현재 값이 아닌 과거값이여서 현재는 현재-1 임.
    if type == 'quarter':
        '''
        ref_year3month = datetime.strptime(ref_year,'%Y%m')
        ref_year3month = ref_year3month + relativedelta(months=+2)
        ref_year3month = ref_year3month.strftime('%Y%m')
        '''
    
        ref_year3month = datetime.strptime(ref_year,'%Y%m')
        ref_year3month = ref_year3month + relativedelta(months=-2)
        ref_year3month = ref_year3month.strftime('%Y%m')
    
    if type == 'year':
        # WHERE .. AND NOT ... 조건 사용. 두개 table 사용
        sql = 'INSERT INTO srim_year (code, date, close, year)                SELECT code, date, close, YEAR(date) FROM krx_stock_price WHERE code = %s AND YEAR(date) = %s                AND NOT EXISTS (SELECT * FROM srim_year WHERE code = %s AND YEAR(date) = %s)'
        connector.execute(sql, icode, ref_year, icode, ref_year)
    
        # 위 sql에서 WHERE ... AND NOT ... 조건 이면 update는 시행됨.
        sql = 'UPDATE srim_year SET value_per_share10 = %s, value_per_share5 = %s, value_per_share = %s                WHERE year = %s AND code = %s'
        connector.execute(sql,  value_per_share10, value_per_share5, value_per_share, ref_year, icode)
    
        sql = 'UPDATE srim_year SET roe = (SELECT `ROE(%)` FROM naverfs_y WHERE code = %s AND YEAR(date) = %s)                WHERE year = %s AND code = %s'
        connector.execute(sql, icode, ref_year,ref_year, icode)
    elif type == 'quarter':
        # 분기별로 구하것으로 year포맷을 YYYYmm으로 쿼리
        # 3개월 단위로 데이터 사용하기...
        sql = 'INSERT INTO srim_quarter (code, date, close, year)                SELECT code, date, close, date_format(date,"%Y%m") FROM krx_stock_price WHERE code = %s AND                date_format(date,"%Y%m") BETWEEN %s AND %s                AND NOT EXISTS (SELECT * FROM srim_quarter WHERE code = %s AND date_format(date,"%Y%m") BETWEEN %s AND %s)'
        connector.execute(sql, icode, ref_year3month, ref_year, icode, ref_year3month, ref_year)

        # 위 sql에서 WHERE ... AND NOT ... 조건 이면 update는 시행됨.
        sql = 'UPDATE srim_quarter SET value_per_share10 = %s, value_per_share5 = %s, value_per_share = %s                WHERE year BETWEEN %s AND %s AND code = %s'
        connector.execute(sql,  value_per_share10, value_per_share5, value_per_share, ref_year3month, ref_year, icode)
    
        sql = 'UPDATE srim_quarter SET roe = (SELECT `ROE(%)` FROM naverfs_q WHERE code = %s AND date_format(date,"%Y%m") = %s)                WHERE year BETWEEN %s AND %s AND code = %s'
        connector.execute(sql, icode, ref_year, ref_year3month, ref_year , icode)
    
    return None

def get_bond_kospi(start_year):
    # 국채 3년 금리 구하기
    sql = 'SELECT date, national_bond_3y FROM bond WHERE date > %(start_year)s'
    df_bond = pd.read_sql(sql, con=engine, params = {'start_year':start_year})
    df_bond = df_bond.set_index('date')
    # KOSPI 지수 구하기
    df_kospi = data.DataReader("KRX:KOSPI", 'google', start_year)
    # 두 dataframe 합치기
    df_bond_kospi = df_kospi.join(df_bond, how = 'inner')
    
    return (df_bond_kospi)


# ##### SRIM, CLOSE등 그래프 그리기

# In[ ]:

def plt_year_srim(icode,iname, bond_kospi):
    font_name = font_manager.FontProperties(fname="c:/Windows/Fonts/malgun.ttf").get_name()
    rc('font', family=font_name)
    try:
        fig = plt.figure(figsize=(15,12))
        ax1 = plt.subplot2grid((5,5), (0,0), colspan=5,rowspan=2) #종합지수,국채
        ax2 = plt.subplot2grid((5,5), (2,0), colspan=5,rowspan=3) #SRIM 6년

    
        # 종합주가지수, 국채3년금리 그리기, 이중 그래프
        ax1_index = pd.to_datetime(bond_kospi.index,format='%Y-%m')
        ax1.plot(ax1_index, bond_kospi.loc[:,'Close'].values, 'black', label = 'KOSPI')
        ax1.set_ylabel('KOSPI')
        for label in ax1.get_yticklabels():
            label.set_color("black")

        ax11 = ax1.twinx()
        ax11.plot(ax1_index, bond_kospi.loc[:,'national_bond_3y'].values, 'darkgreen', label = 'national_bond_3y')
        ax11.set_ylabel('national_bond_3y')
        for label in ax11.get_yticklabels():
            label.set_color("darkgreen")

    
        # subplot에 정보 표기
        # text box
        text_str = 'National_bond_3y=%s\nKOSPI=%s'                    % (bond_kospi.loc[:,'national_bond_3y'].iloc[-1],bond_kospi.loc[:,'Close'].iloc[-1])
        ax1.text(0.20, 0.80, text_str, transform = ax1.transAxes, color = 'red')
        # 타이틀
        ax1.set_title('KOSPI & National_bond_3y')
        # 레이블
        ax1.set_xlabel('Date')
        ax1.set_ylabel('KOSPI & National_bond')
        #그리드
        ax1.grid(True)
        # 법례
        ax1.legend(loc=3)
        ax11.legend(loc=2)
    
        # SRIM 6년 그래프 그리기
        sql = 'SELECT * FROM srim_year WHERE code = %(code)s ORDER BY date'    # ORDER BY date 미시행시 그래프 깨짐, 순서틀어짐
        df_srim = pd.read_sql(sql, con=engine, params = {'code':icode})
        srim = df_srim[['date', 'value_per_share','value_per_share10','value_per_share5','close', 'roe']]
        srim = srim.fillna(method='ffill')   # NaN는 앞의 값을 가지고 채우기

        # 5, 20일 이동평균선
        srim.loc[:,'MA_5'] = srim.loc[:,'close'].rolling(center=False,window=5).mean()
        srim.loc[:,'MA_20'] = srim.loc[:,'close'].rolling(center=False,window=20).mean()
        srim.loc[:,'diff'] = srim.loc[:,'MA_5'] - srim.loc[:,'MA_20']
        #
        ax2_index = pd.to_datetime(srim.loc[:,'date'].values,format='%Y-%m')
        ax2.plot(ax2_index, srim.loc[:,'value_per_share'].values, 'red', label='value_per_share')
        ax2.plot(ax2_index, srim.loc[:,'value_per_share10'].values, 'green', label='value_per_share10')
        ax2.plot(ax2_index, srim.loc[:,'value_per_share5'].values, 'blue', label='value_per_share5')
        ax2.plot(ax2_index, srim.loc[:,'close'].values, 'black', label='close')
        ax2.plot(ax2_index, srim.loc[:,'MA_5'].values, 'cyan', label='MA_5')
        ax2.plot(ax2_index, srim.loc[:,'MA_20'].values, 'magenta', label='MA_20')
        
        
        #5일, 20일 골드,데드 표기하기
        '''
        prev_key = prev_val = 0
        for key, val in srim.loc[:,'diff'].iteritems():
            if val == 0:
                continue
    
            if val * prev_val < 0 and val > prev_val:
                ax2.annotate('Golden', xy=(key, srim.loc[:,'MA_20'][key]), xytext=(10,-30),\
                textcoords='offset points', arrowprops=dict(arrowstyle='-|>'))
            elif val * prev_val < 0 and val < prev_val:
                ax2.annotate('Dead', xy=(key, srim.loc[:,'MA_20'][key]), xytext=(10,30),\
                textcoords='offset points', arrowprops=dict(arrowstyle='-|>'))
        prev_key, prev_val = key, val
        '''
        # tight_layout하지 않으면 두개 그래프 겹침
        # fig.tight_layout()
        

        # ROE subplot에 정보 표기
        ax22 = ax2.twinx()
        # ax22.plot(ax2_index, srim.loc[:,'roe'].values, 'magenta', label = 'ROE', linestyle = ':')
        ax22.plot(ax2_index, srim.loc[:,'roe'].values, 'black', label = 'ROE', linestyle = ':')
        ax22.set_ylabel('ROE(%)')
        for label in ax22.get_yticklabels():
            label.set_color("black")
        
        # subplot에 정보 표기
        text_str = 'code=%s\ncode_name=%s\nvalue_per_share=%s\nvalue_per_share10=%s\nvalue_per_share5=%s\nclose=%s\ndate=%s\n'\
                %(icode,iname, srim['value_per_share'].iloc[-1], srim['value_per_share10'].iloc[-1], srim['value_per_share5'].iloc[-1], srim['close'].iloc[-1],srim['date'].iloc[-1])

        ax2.text(0.20, 0.60, text_str, transform = ax2.transAxes, color = 'red')
        # 타이틀
        ax2.set_title('S-RIM_'+iname)
        # 레이블
        ax2.set_xlabel('Date')
        ax2.set_ylabel('Close')
        #그리드
        ax2.grid(True)
        # 법례
        ax2.legend(loc=2)
        ax22.legend(loc=3)
        
        dir ='D://srim//jpg//'
        fig.savefig(dir+'YearSrim_'+icode+'_'+iname+'.svg')    # svg 포맷으로 저장, 디스크 용량문제로 D:에 저장함.
        plt.close('all')
    except :
        return None
    else:
        return None


# In[ ]:

def plt_quarter_srim(icode,iname):
    font_name = font_manager.FontProperties(fname="c:/Windows/Fonts/malgun.ttf").get_name()
    rc('font', family=font_name)
    try:
        fig = plt.figure(figsize=(15,5))
        ax1 = plt.subplot2grid((5,5), (0,0), colspan=5,rowspan=5)
           
        # SRIM 6년 그래프 그리기
        sql = 'SELECT * FROM srim_quarter WHERE code = %(code)s ORDER BY date'    # ORDER BY date 미시행시 그래프 깨짐, 순서틀어짐
        df_srim = pd.read_sql(sql, con=engine, params = {'code':icode})
        srim = df_srim[['date', 'value_per_share','value_per_share10','value_per_share5','close', 'roe']]
        srim = srim.fillna(method='ffill')   # NaN는 앞의 값을 가지고 채우기

        # 5, 20일 이동평균선
        srim.loc[:,'MA_5'] = srim.loc[:,'close'].rolling(center=False,window=5).mean()
        srim.loc[:,'MA_20'] = srim.loc[:,'close'].rolling(center=False,window=20).mean()
        srim.loc[:,'diff'] = srim.loc[:,'MA_5'] - srim.loc[:,'MA_20']
        #
        ax1_index = pd.to_datetime(srim.loc[:,'date'].values,format='%Y-%m')
        ax1.plot(ax1_index, srim.loc[:,'value_per_share'].values, 'red', label='value_per_share')
        ax1.plot(ax1_index, srim.loc[:,'value_per_share10'].values, 'green', label='value_per_share10')
        ax1.plot(ax1_index, srim.loc[:,'value_per_share5'].values, 'blue', label='value_per_share5')
        ax1.plot(ax1_index, srim.loc[:,'close'].values, 'black', label='close')
        ax1.plot(ax1_index, srim.loc[:,'MA_5'].values, 'cyan', label='MA_5')
        ax1.plot(ax1_index, srim.loc[:,'MA_20'].values, 'magenta', label='MA_20')
        
        
        #5일, 20일 골드,데드 표기하기
        '''
        prev_key = prev_val = 0
        for key, val in srim.loc[:,'diff'].iteritems():
            if val == 0:
                continue
    
            if val * prev_val < 0 and val > prev_val:
                ax2.annotate('Golden', xy=(key, srim.loc[:,'MA_20'][key]), xytext=(10,-30),\
                textcoords='offset points', arrowprops=dict(arrowstyle='-|>'))
            elif val * prev_val < 0 and val < prev_val:
                ax2.annotate('Dead', xy=(key, srim.loc[:,'MA_20'][key]), xytext=(10,30),\
                textcoords='offset points', arrowprops=dict(arrowstyle='-|>'))
        prev_key, prev_val = key, val
        '''
        # tight_layout하지 않으면 두개 그래프 겹침
        # fig.tight_layout()
        

        # ROE subplot에 정보 표기
        ax11 = ax1.twinx()
        # ax22.plot(ax2_index, srim.loc[:,'roe'].values, 'magenta', label = 'ROE', linestyle = ':')
        ax11.plot(ax1_index, srim.loc[:,'roe'].values, 'black', label = 'ROE', linestyle = ':')
        ax11.set_ylabel('ROE(%)')
        for label in ax11.get_yticklabels():
            label.set_color("black")
        
        # subplot에 정보 표기
        text_str = 'code=%s\ncode_name=%s\nvalue_per_share=%s\nvalue_per_share10=%s\nvalue_per_share5=%s\nclose=%s\ndate=%s\n'\
                %(icode,iname, srim['value_per_share'].iloc[-1], srim['value_per_share10'].iloc[-1], srim['value_per_share5'].iloc[-1], srim['close'].iloc[-1],srim['date'].iloc[-1])

        ax1.text(0.20, 0.60, text_str, transform = ax1.transAxes, color = 'red')
        # 타이틀
        ax1.set_title('S-RIM_'+iname)
        # 레이블
        ax1.set_xlabel('Date')
        ax1.set_ylabel('Close')
        #그리드
        ax1.grid(True)
        # 법례
        ax1.legend(loc=2)
        ax11.legend(loc=3)
        
        dir ='D://srim//jpg//'
        fig.savefig(dir+'QuarterSrim_'+icode+'_'+iname+'.svg')    # svg 포맷으로 저장, 디스크 용량문제로 D:에 저장함.
    except :
        return None
    else:
        return None


# ##### Main Start

# In[ ]:

if __name__ == "__main__":
    value_per_share10 = 0
    value_per_share5 = 0
    value_per_share = 0
    ref_year = 0
    
    pwd = 'rlaehgus1'
    engine = create_engine('mysql+mysqlconnector://root:'+pwd+'@localhost/findb', echo=False)
    connector = engine.connect()

    #요구수익률 가져오기
    required_rate_of_return = get_required_rate_of_return() 
    required_rate_of_return = required_rate_of_return / 100    # 단위 % 환산
    
    #국채 금리구하기
    sql = 'SELECT * FROM naverfs_y ORDER BY date LIMIT 1'
    result = connector.execute(sql)
    s_year = result.fetchone()
    
    s_year = s_year[0]
    df_bond_kospi = get_bond_kospi(s_year)

    df_code_name = get_code_name()
    
    li_code = df_code_name.loc[:,'code']
    li_name = df_code_name.loc[:,'name']
    '''
    li_code = ['139480']
    li_name = ['국순당']
    '''
        
    for i in range(0,len(li_code)):
        icode = li_code[i]
        icode = icode.zfill(6)
        iname = li_name[i]
        
        #------------------------------------------  년간 SRIM 구하기
        # naverfs_y에서 RIM작성을 위한 데이터 추출
        sql = 'SELECT code, date, `roe(%)`, `자본총계(지배)`, `발행주식수(보통주)`                FROM naverfs_y WHERE code = %s ORDER BY date'
        result = connector.execute(sql, icode)
        stock = result.fetchall()

        columns = ['code','date','roe','capital','share_outstanding']
        index = list()    #index만들기 위해 선언해 놓음
        df_stock = DataFrame(stock, columns = columns)
    
        # date를 기준으로 정력하고 year만을 취하여 index함.
        # df_stock = df_stock.sort_values(by='date')
        for i in range(0,len(df_stock)):
            index.append(df_stock.loc[i,'date'].year)
        last_year = index[len(index) - 1]
        # start_year = df_stock.loc[0,'date']
        df_stock = DataFrame(stock, columns = columns, index = index)
        df_stock = df_stock.fillna(method='ffill')   # NaN는 앞의 값을 가지고 채우기
        df_stock = df_stock.T                      # 행,렬 바뀌기
        #

        sql = 'SELECT date FROM naverfs_y WHERE code = %s ORDER BY date '
        imsi_result = connector.execute(sql, icode)
        li_date = imsi_result.fetchall()
        
        for i in range(0,len(li_date)):
            ref_year = li_date[i][0].year    
            #년 단위 SRIM 계산
            coefficients = [0.0, 0.1, 0.2]
            for coefficient in coefficients:    # 0.0 - 지속, 0.1 - 10%, 10년, 0.2 - 20%, 5년:
                r_value_per_share = get_roe_date(icode, coefficient, required_rate_of_return,ref_year,df_stock, 'year')
                if coefficient == 0.0:    # 지속성장
                    value_per_share = r_value_per_share
                elif coefficient == 0.1:    #10년 성장
                    value_per_share10 = r_value_per_share
                elif coefficient == 0.2:    #5년 성장
                    value_per_share5 = r_value_per_share
            # 년도별 srim 테이블 만들기
            insert_srim(icode, ref_year, value_per_share10, value_per_share5, value_per_share, 'year')
        # srim 전체 그래프 그리기
        plt_year_srim(icode, iname, df_bond_kospi)
        
        #-----------------------------------------   분기별 SRIM 구하기
        # naverfs_q에서 RIM작성을 위한 데이터 추출
        sql = 'SELECT code, date, `roe(%)`, `자본총계(지배)`, `발행주식수(보통주)`                FROM naverfs_q WHERE code = %s ORDER BY date'
        result = connector.execute(sql, icode)
        stock = result.fetchall()

        columns = ['code','date','roe','capital','share_outstanding']
        index = list()    #index만들기 위해 선언해 놓음
        df_stock = DataFrame(stock, columns = columns)

        # date를 기준으로 정력하고 Year + Month 인덱스 만들기
        # df_stock = df_stock.sort_values(by='date')
        for i in range(0,len(df_stock)):
            index.append(df_stock.loc[i,'date'].strftime('%Y%m'))
        last_year = index[len(index) - 1]
        # start_year = df_stock.loc[0,'date']
        df_stock = DataFrame(stock, columns = columns, index = index)
        df_stock = df_stock.fillna(method='ffill')   # NaN는 앞의 값을 가지고 채우기
        df_stock = df_stock.T                      # 행,렬 바뀌기
        #
        sql = 'SELECT date FROM naverfs_q WHERE code = %s ORDER BY date '
        imsi_result = connector.execute(sql, icode)
        li_date = imsi_result.fetchall()
        
        for i in range(0,len(li_date)):
            ref_month = li_date[i][0].strftime('%Y%m')
            #분기 단위 SRIM 계산
            coefficients = [0.0, 0.1, 0.2]
            for coefficient in coefficients:    # 0.0 - 지속, 0.1 - 10%, 10년, 0.2 - 20%, 5년:
                r_value_per_share = get_roe_date(icode, coefficient, required_rate_of_return,ref_month, df_stock, 'quarter')
                if coefficient == 0.0:    # 지속성장
                    value_per_share = r_value_per_share
                elif coefficient == 0.1:    #10년 성장
                    value_per_share10 = r_value_per_share
                elif coefficient == 0.2:    #5년 성장
                    value_per_share5 = r_value_per_share

            # 년도별 srim 테이블 만들기
            insert_srim(icode, ref_month, value_per_share10, value_per_share5, value_per_share, 'quarter')
        # srim 전체 그래프 그리기
        plt_quarter_srim(icode, iname)
        
    connector.close()


# In[ ]:



