#!/data/python_project/tongji/venv/bin/python
# -*- coding:utf-8 -*-

import beanstalkc,redis,time
from pymongo import MongoClient

db = MongoClient().tongji
bt = beanstalkc.Connection('localhost',11308)
bt.watch('tongji')

pool = redis.ConnectionPool(host='localhost',port=6379)


while 1:
    rd = redis.Redis(connection_pool=pool)
    job = bt.reserve()

    rq_info = eval(job.body)
    userIp = rq_info['UserIp']
    td = time.strftime("%Y-%m-%d")
    td_end = td + " 23:59:59"
    td_arr = time.strptime(td_end, "%Y-%m-%d %H:%M:%S")
    td_end_timestamp = int(time.mktime(td_arr))
    now_timestamp = int(time.time())
    expire_time = (td_end_timestamp - now_timestamp) if (td_end_timestamp - now_timestamp) > 0 else 1

    ip_key = userIp + td
    is_ip_exist = rd.get(ip_key)

    if(is_ip_exist):
        date_info = db.tongji_date.find_one({'date': td})
        date_pv   = date_info['date_pv'] + 1

        db.tongji_date.update({'date':td},{"$set":{'date_pv':date_pv}})
    else:
        rd.set(ip_key,1,expire_time)
        date_info = db.tongji_date.find_one({'date': td})
        if(date_info):
            date_ip_new = date_info['date_ip'] + 1
            date_pv_new = date_info['date_pv'] + 1

            db.tongji_date.update({'date': td}, {"$set": {'date_ip':date_ip_new,'date_pv': date_pv_new}})
        else:
            date_new_info = {'date':td,'date_ip':1,'date_pv':1}
            db.tongji_date.insert(date_new_info)

    if(rq_info['Origin'] != 'http://www.baidu.com'):
        try:
            url_ip_key = rq_info['Origin'] + userIp + td
            url_set = rq_info['Origin']
        except TypeError:
            error_ip_info = {'date':td,'ip':userIp}
            db_ip_info    = db.error_ip.find(error_ip_info)
            if(not db_ip_info):
                db.error_ip.insert(error_ip_info)
            job.delete()
            continue
    else:
        try:
            Referer_arr = rq_info['Referer'].split('/')
            query_uid = Referer_arr[3]
            url_ip_key = rq_info['Origin'] + '/' + query_uid + userIp + td
            url_set = rq_info['Origin'] + '/' + query_uid
        except TypeError:
            error_ip_info = {'date':td,'ip':userIp}
            db_ip_info    = db.error_ip.find(error_ip_info)
            if(not db_ip_info):
                db.error_ip.insert(error_ip_info)
            job.delete()
            continue

    print(ip_key)
    print(is_ip_exist)

    is_url_is_exist = rd.get(url_ip_key)

    if(is_url_is_exist):
        url_date_info = db.tongji_url_date.find_one({'date':td,'url':url_set})

        if(url_date_info):
            url_date_pv = url_date_info['date_pv'] + 1

            db.tongji_url_date.update({'date':td,'url':url_set},{"$set":{'date_pv':url_date_pv}})
    else:
        rd.set(url_ip_key,1,expire_time)
        url_date_info = db.tongji_url_date.find_one({'date': td, 'url': url_set})
        if(url_date_info):
            date_ip_url_new = url_date_info['date_ip'] + 1
            date_pv_url_new = url_date_info['date_pv'] + 1

            db.tongji_url_date.update({'date':td,'url':url_set},{"$set":{'date_ip':date_ip_url_new,'date_pv':date_pv_url_new}})
        else:
            if (rq_info['Origin'] == 'http://www.baidu.com'):
                user_plan = 1
            else:
                user_plan = 2
            date_url_new_info = {'date':td,'url':url_set,'date_ip':1,'date_pv':1,'user_plan':user_plan}
            db.tongji_url_date.insert(date_url_new_info)
    job.delete()
