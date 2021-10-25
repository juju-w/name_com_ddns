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


def print_help():
    print('Usage:\n\t python name.com_ddns.py { install | update | config | reinstall | uninstall }')


def update_ddns():
    config.read(ini_path, encoding="utf-8")
    my_ip = rq.get('https://whois.pconline.com.cn/ipJson.jsp?json=true').json()
    now_ip = my_ip['ip']
    print('Public Net Ip：%s, Address：%s' % (now_ip, my_ip['addr']))
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
    print("ip update success")
    config.set('DDNS', 'last_ip', now_ip)
    config.write(open(ini_path, 'w', encoding='utf-8'))


def write_to_cronfile():
    user = os.popen('whoami').read().rstrip()
    python = os.popen('which python').read().rstrip()
    cron_path = '/var/spool/cron/%s' % user
    os.system("echo '%s %s %s' >> %s update" %
              (config.get("Sys", "interval"), python, os.path.join(current_path, 'name.com_ddns.py'), cron_path))
    print("crontab updated ")


def name_ddns():
    try:
        sys.argv[1]
    except Exception:
        print_help()
        sys.exit()
    if sys.argv[1] is None:
        print('python name.com_ddns.py install | update | config | uninstall')
    elif sys.argv[1] == 'install':
        username = input('input your name.com username：')
        config.add_section('User')
        config.set('User', 'username', username)
        token = input('input your name.com token：')
        config.set('User', 'token', token)
        domains = input('input your name.com domains [like:example.com]:')
        config.add_section('DDNS')
        config.set('DDNS', 'domains', domains)
        host = input('input your name.com host [like:www/ddns]:')
        config.set('DDNS', 'host', host)
        interval = input('input your ddns refresh (min:1~59)[default:30 min]：')
        interval = 30 if interval == '' else interval
        interval = "*/%s  *  *  *  *" % str(interval)
        config.add_section('Sys')
        config.set('Sys', 'interval', interval)

        rid, ip, ttl = '', '', ''
        req_url = "https://api.name.com/v4/domains/%s/records" % domains
        req = rq.get(req_url, auth=(username, token))
        if req.status_code == 200:
            data = req.json()['records']
        else:
            print('request failed, please check your username and token ')
            sys.exit()
        for r in data:
            [rid, ip, ttl] = [r['id'], r['answer'], r['ttl']] if r['fqdn'] == "%s.%s." % (host, domains) and \
                                                                 r['type'] == 'A' else ['', '', '']
        if (rid, ip, ttl) == ('', '', ''):
            print('can not find your host')
            sys.exit()
        config.set('DDNS', 'id', str(rid))
        config.set('DDNS', 'last_ip', ip)
        config.set('DDNS', 'ttl', str(ttl))
        config.write(open(ini_path, 'w+', encoding='utf-8'))
        update_ddns()
        write_to_cronfile()
    elif sys.argv[1] == 'reinstall':
        config.read(ini_path, encoding='utf-8')
        try:
            config.get('DDNS', 'id')
            write_to_cronfile()
        except Exception:
            print('please install at first to get your id value')
            print_help()
            sys.exit()
    elif sys.argv[1] == 'update':
        update_ddns()
    elif sys.argv[1] == 'config':
        while 1:
            config.read(ini_path, encoding='utf-8')
            try:
                config.get('User', 'username')
                print('#########################################')
                print("username: %s" % config.get('User', 'username'))
                print("token: %s" % config.get('User', 'token'))
                print("domains: %s" % config.get('DDNS', 'domains'))
                print("host: %s" % config.get('DDNS', 'host'))
                print('#########################################')
            except Exception:
                print('please install at first')
                print_help()
                sys.exit()
            choice = ['username', 'token', 'domains', 'host', 'exit']
            print('\n'.join(['[%i]: %s' % (i+1, choice[i]) for i in range(len(choice))]))
            ins = int(input('Select the parameter to modify:'))-1
            if choice[ins] == 'exit':
                sys.exit()
            elif choice[ins] in ['username', 'token']:
                rep = input('change value to:')
                config.set('User', choice[ins], rep)
                config.write(open(ini_path, 'w+', encoding='utf-8'))
            elif choice[ins] in ['domains', 'host']:
                rep = input('change value to:')
                config.set('DDNS', choice[ins], rep)
                config.write(open(ini_path, 'w+', encoding='utf-8'))
    elif sys.argv[1] == 'uninstall':
        user = os.popen('whoami').read().rstrip()
        cron_path = '/var/spool/cron/%s' % user
        os.system("sed -i '/name.com_ddns.py/'d %s" % cron_path)
        print('uninstall complete')
    else:
        print('input invalid')
        print_help()


if __name__ == '__main__':
    name_ddns()
