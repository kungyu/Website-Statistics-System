#!/data/python_project/tongji/venv/bin/python
# -*- coding:utf-8 -*-

import beanstalkc,time
from flask import Flask,request,render_template,session,redirect,url_for
from pymongo import MongoClient
from datetime import date,timedelta
from flask_paginate import Pagination,get_page_parameter
from bson.code import Code

app = Flask(__name__, template_folder='application/templates')
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

db = MongoClient().tongji

@app.route('/')
def index():

    # print(request.remote_addr)
    # for ims in request.__dict__.items():
    #     print(ims)
    request_info = {}
    request_info['Referer'] = request.headers.get('Referer')
    request_info['Origin'] = request.headers.get('Origin')
    proxy_for  = request.headers.get('X-Forwarded-For')
    rmaddr  = request.remote_addr

    request_info['UserIp']  = proxy_for if proxy_for else rmaddr
#    if(request_info['Referer'].index('dh.cx') == -1):
#        return ''

    kung = str(request_info)
    beanstalk = beanstalkc.Connection(host='localhost', port=11308)
    beanstalk.use('tongji')
    beanstalk.put(kung)
    beanstalk.close()
    return ''

@app.route('/login')
def login():
    return render_template('index.html')

@app.route('/login_act', methods=['post'])
def login_act():
    username = request.form['username']
    password = request.form['password']
    if(username == 'username' and password == 'password'):
        session['user_type'] = 'admin'
        redirect_url = url_for('dashbord')
    else:
        redirect_url = url_for('ycd_login')
    return redirect(redirect_url)

@app.route('/dashbord')
def dashbord():
    user_type = session['user_type']
    if(user_type != 'admin'):
        return ''
    td = time.strftime("%Y-%m-%d")
    date_info = db.tongji_date.find_one({"date":td})
    product_count = db.tongji_url_date.count({"date":td})
    seven_date = str(date.today() - timedelta(7))

    '''
    run_reduce = Code("function(doc, result){result.date_pv_all = result.date_pv_all + doc.date_pv, result.date_ip_all = result.date_ip_all + doc.date_ip}")
    seven_date_info = db.command({
        "group":{
            "ns":'tongji_url_date',
            "key":{"date":True},
            "initial":{"date_pv_all": 0, "date_ip_all":0},
            "$reduce":run_reduce,
            "condition":{"date":{"$gte":seven_date}}
        }
    })
    '''

    pipeline = [
        {"$unwind":"$date"},
        {"$match":{"date":{"$gte":seven_date}}},
        {
            "$group": {"_id": "$date","date_pv": {"$sum":"$date_pv"}, "date_ip": {"$sum":"$date_ip"}, "date":{"$first":"$date"}},
        },
        {"$sort":{"date": -1}}
    ]

    seven_date_info = db.tongji_url_date.aggregate(pipeline)
    seven_date_info_se = []

    if(seven_date_info):
        for doc in seven_date_info:
            doc['date_real_ip'] = db.tongji_date.find_one({"date":doc['date']})['date_ip']
            seven_date_info_se.append(doc)



    return render_template('dashbord.html',date_info=date_info, product_count=product_count,seven_date_info_se=seven_date_info_se)

@app.route('/ip_url_detail')
def ip_url_detail():
    user_type = session['user_type']
    if (user_type != 'admin'):
        return ''
    date = request.args.get('date')
    url_search = request.args.get('url_search')
    if(url_search):
        search_where = {'date': date,'url': url_search}
    else:
        search_where = {'date':date}
    # url  = urllib.unquote(request.args.get('url'),'utf-8')
    page = request.args.get(get_page_parameter(),type=int,default=1)
    perPage = 15
    start_data = (page - 1) * perPage
    url_date_info = db.tongji_url_date.find(search_where).sort([('date_ip', -1)]).skip(start_data).limit(perPage)
    url_date_info_count = db.tongji_url_date.count(search_where)
    pagination = Pagination(bs_version=3,per_page=perPage,page=page,total=url_date_info_count)
    data = {
        'url_date_info':url_date_info,
        'pagination':pagination,
        'date' : date,
        'url_search' : url_search
    }
    return render_template('ip_url_detail.html', **data)


if __name__ == '__main__':
    app.run(debug=True)

