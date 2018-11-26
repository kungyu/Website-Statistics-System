#!/data/python_project/tongji/venv/bin/python
# -*- coding:utf-8 -*-
import datetime,time,redis
from pymongo import MongoClient

db = MongoClient().tongji
pool = redis.ConnectionPool(host='localhost',port=6379)
rd = redis.Redis(connection_pool=pool)

now_hour    =  time.strftime("%H")
if(str(now_hour)  == '00'):
    yesterday = str(datetime.date.today() + datetime.timedelta(-1))
    yes_visit = db.tongji_date.find_one({'date':yesterday})
    last_visit = rd.get('last_visit_count')
    if last_visit is None:
        last_visit = 0
    this_one_hour = int(yes_visit['date_ip']) - int(last_visit)
    one_hour_data = {"date":yesterday,'hour':"24",'visit_count':this_one_hour}
    db.one_hour_visit.insert(one_hour_data)
    rd.set('last_visit_count',0,4600)

else:
    td = time.strftime("%Y-%m-%d")
    print(td)
    now_visit = db.tongji_date.find_one({'date': td})
    print(now_visit)
    visit_count = now_visit['date_ip']
    last_visit = rd.get('last_visit_count')
    if last_visit is None:
        last_visit = 0
    this_one_hour = int(visit_count) - int(last_visit)
    one_hour_data = {"date":td,'hour':now_hour,'visit_count':this_one_hour}
    db.one_hour_visit.insert(one_hour_data)
    rd.set('last_visit_count',visit_count,4600)
