#!/usr/bin/env python
# -*- coding: utf-8 -*-

import MySQLdb
from contextlib import closing
import re
import subprocess

import login


LAMEDB_LOCAL = '/home/pi/dreamberry/epg/lamedb'
RADIO = ':2:0'
ARD = 'p:ARD'
ZDF = 'p:ZDFvision'


def replacechars(path):

    a = ['ä', 'ö', 'ü', 'Ä', 'Ö', 'Ü', 'ß', ' ']
    b = ['ae', 'oe', 'ue', 'Ae', 'Oe', 'Ue', 'ss', '_']

    i = 0
    while i < len(a):
        if a[i] in path:
            path = path.replace(a[i], b[i])
        i += 1

    path = re.compile('[^a-zA-Z0-9_-]').sub('', path.lower())
    
    return path


def get_host():

    with closing(MySQLdb.connect(
            login.DB_HOST, login.DB_USER,
            login.DB_PASSWORD, login.DB_DATABASE, charset='utf8')) as connection:
        with closing(connection.cursor()) as cursor:
            cursor.execute('SELECT host FROM enigma_host WHERE id="1"')
            host = cursor.fetchone()[0]

    return host


def ping(host):

    ping = subprocess.Popen(
        ['ping', '-c 1', host],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    ping.wait()
    status = ping.communicate()

    return status


def fetch_lamedb(lamedb_remote):

    download = subprocess.Popen(['scp', lamedb_remote, LAMEDB_LOCAL])
    download.wait()


def parse_lamedb(lines, host):

    channel = []
    alias = []
    sid = []
    url = []
    i = 0
    f = 0

    while i < len(lines):
        if RADIO in lines[i]:
            if ARD in lines[i+2] or ZDF in lines[i+2]:

                service_id, \
                    dvb_namespace, \
                    transport_stream_id, \
                    original_network_id, \
                    _, _ = lines[i].split(':', 5)

                url_string = [
                    'http://',
                    host,
                    '/web/epgservice?sRef=1:0:1:',
                    service_id + ':',
                    transport_stream_id + ':',
                    original_network_id + ':',
                    dvb_namespace,
                    ':0:0:0:'
                    ]

                url.append(''.join(url_string))
                sid.append(service_id)
                channel.append(
                    (lines[i+1].strip().replace('.', '')))
                alias.append(replacechars(channel[f]))

                f += 1
        i += 1

    return channel, alias, sid, url


def add_db_entries(channel, alias, sid, url):

    with closing(MySQLdb.connect(
            login.DB_HOST, login.DB_USER,
            login.DB_PASSWORD, login.DB_DATABASE, charset='utf8')) as connection:
        with closing(connection.cursor()) as cursor:

            cursor.execute('TRUNCATE TABLE lamedb')
            connection.commit()

            i = 0
            while i < len(channel):
                cursor.execute(
                    'INSERT INTO lamedb (channel, alias, sid, url) \
                    VALUES (%s,%s,%s,%s)',
                    ((channel[i].decode('utf-8')), (alias[i]), (sid[i]), (url[i]))
                    )
                i += 1
            connection.commit()


def main():

    host = get_host()
    lamedb_remote = 'root@' + host + ':/etc/enigma2/lamedb'
    status = ping(host)
    if status[1]:
        exit()

    fetch_lamedb(lamedb_remote)

    with open(LAMEDB_LOCAL, 'r') as f:
        lines = f.readlines()

    channel, alias, sid, url = parse_lamedb(lines, host)

    add_db_entries(channel, alias, sid, url)


if __name__ == '__main__':
    main()
