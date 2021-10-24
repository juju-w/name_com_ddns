# -*- coding: utf-8 -*-
import sys
import json as js
import os
import configparser
import requests as rq

current_path = os.path.dirname(os.path.abspath(__file__))

config = configparser.ConfigParser()
ini_path = "%s/name.com_ddns.ini" % current_path
config.read(ini_path, encoding='utf-8')

def update_ddns():
    config.read(ini_path, encoding="utf-8")
    my_ip = rq.get('https://whois.pconline.com.cn/ipJson.jsp?json=true').json()
    now_ip = my_ip['ip']
    print('公网ip：%s, 所属：%s' % (now_ip, my_ip['addr']))
    if config.get('DDNS', 'last_ip') != now_ip:
        url = 'https://api.name.com/v4/domains/%s/records/%s' % (
            config.get('DDNS', 'domains'), config.get('DDNS', 'id'))
        post_js = {
            'host': config.get('DDNS', 'host'),
            'type': 'A',
            'answer': now_ip,
            'ttl': config.get('DDNS', 'ttl'),
        }
        rq.put(url, auth=(config.get('User', 'username'), config.get('User', 'token')), data=js.dumps(post_js))
    print("ip 更新成功")
    config.set('DDNS', 'last_ip', now_ip)


if sys.argv[1] is None:
    print('python name.com_ddns.py install | update | config | uninstall')
elif sys.argv[1] == 'install':
    username = input('输入name.com 用户名：')
    config.add_section('User')
    config.set('User', 'username', username)
    token = input('输入name.com token：')
    config.set('User', 'token', token)
    domains = input('输入name.com 域名【example.com】：')
    config.add_section('DDNS')
    config.set('DDNS', 'domains', domains)
    host = input('输入name.com 域【www/ddns】：')
    config.set('DDNS', 'host', host)
    interval = input('输入ddns 定时刷新间隔(分钟 1~59)【默认:30】：')
    interval = 30 if interval == '' else interval
    interval = "*/%s  *  *  *  *" % str(interval)
    config.add_section('Sys')
    config.set('Sys', 'interval', interval)

    rid, ip, ttl = '', '', ''
    req_url = "https://api.name.com/v4/domains/%s/records" % domains
    req = rq.get(req_url, auth=(username, token))
    if req.status_code == '200':
        data = req.json()['records']
    else:
        print('请求有误，请检查用户名以及token')
        sys.exit()
    for r in data:
        [rid, ip, ttl] = [r['id'], r['answer'], r['ttl']] if r['fqdn'] == "%s.%s." % (host, domains) and \
                                                             r['type'] == 'A' else ['', '', '']
    if (rid, ip, ttl) == ('', '', ''):
        print('未找到host')
        sys.exit()
    config.set('DDNS', 'id', str(rid))
    config.set('DDNS', 'last_ip', ip)
    config.set('DDNS', 'ttl', str(ttl))

    config.write(open(ini_path, 'w+', encoding='utf-8'))

    update_ddns()

    user = os.popen('whoami').read().rstrip()
    python = os.popen('which python').read().rstrip()
    cron_path = '/var/spool/cron/%s' % user
    os.system("echo '%s %s %s' >> %s" %
              (config.get("Sys", "interval"), python, current_path+'name.com_ddns.py', cron_path))
    print("成功写入定时任务")

elif sys.argv[1] == 'update':
    update_ddns()

elif sys.argv[1] == 'config':
    pass
elif sys.argv[1] == 'uninstall':
    pass
else:
    print('input invalid')
