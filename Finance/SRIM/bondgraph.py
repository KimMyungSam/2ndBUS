import matplotlib.pyplot as plt
import pandas as pd
import mysql.connector
import sqlalchemy
from sqlalchemy import create_engine

pwd = 'rlaehgus1'
engine = create_engine('mysql+mysqlconnector://root:'+pwd+'@localhost/findb', echo=False)
con = engine.connect()

sql = 'SELECT * FROM bond5years'
df = pd.read_sql(sql,con=engine, index_col='year')
bbb_ = df.fillna(method = 'backfill') #결측치는 뒤값으로 채움

fig = plt.figure()
ax = fig.add_axes([0, 0, 0.9, 0.9]) # lower, bottom, width, height (0~1)
# ax.figure(facecolor='lightgrey', edgecolor='r')
ax.plot(bbb_)
