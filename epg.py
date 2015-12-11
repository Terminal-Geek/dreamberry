#!/usr/bin/env python
# -*- coding: utf-8 -*-

import MySQLdb
from contextlib import closing
import subprocess
import urllib
try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET

import login
from lamedb import ping


TIME = 'e2eventstart'
DURATION = 'e2eventduration'
TITLE = 'e2eventtitle'
TEASER = 'e2eventdescription'
SUMMARY = 'e2eventdescriptionextended'


def check_online(connection, cursor):

    cursor.execute('SELECT host FROM enigma_host WHERE id="1"')
    host = cursor.fetchone()[0]
    status = ping(host)
    if status[1]:
        exit()


def retrieve_epg(connection, cursor, db_result):

    epg = []

    for db_record in db_result:

        alias = db_record[0]
        url = db_record[1]
        f = urllib.urlopen(url)
        epg.append(f.read())

    return epg


def parse_epg(epg):

    time = []
    duration = []
    title = []
    teaser = []
    summary = []

    root = ET.fromstring(epg)

    for element in root.iter(TIME):
        time.append(element.text)
    for element in root.iter(DURATION):
        duration.append(element.text)
    for element in root.iter(TITLE):
        title.append(element.text)
    for element in root.iter(TEASER):
        teaser.append(element.text)
    for element in root.iter(SUMMARY):
        summary.append(element.text)

    return time, duration, title, teaser, summary


def add_to_db(connection, cursor,
              alias, time, duration, title, teaser, summary):

    i = 0

    while i < len(time):

        if not teaser[i]:
            teaser[i] = ''
        if not summary[i]:
            summary[i] = ''
        summary[i] = summary[i].replace(u'\x8a', u'\n')
        summary[i] = summary[i].replace(u'\x26', u'und')

        cursor.execute('INSERT INTO epg \
        (alias, title, teaser, summary, time, duration) \
        VALUES (%s,%s,%s,%s,%s,%s)',
                       (alias, title[i], teaser[i],
                        summary[i], time[i], duration[i]))

        i += 1

    connection.commit()


def main():

    with closing(MySQLdb.connect(
            login.DB_HOST, login.DB_USER,
            login.DB_PASSWORD, login.DB_DATABASE, charset='utf8')) as connection:
        with closing(connection.cursor()) as cursor:

            check_online(connection, cursor)

            cursor.execute('TRUNCATE TABLE epg')
            connection.commit()
            cursor.execute('SELECT alias, url FROM lamedb')
            db_result = cursor.fetchall()

            epg = retrieve_epg(connection, cursor, db_result)

            i = 0

            for db_record in db_result:

                alias = db_record[0]
                time, duration, title, teaser, summary = parse_epg(epg[i])
                add_to_db(connection, cursor,
                          alias, time, duration, title, teaser, summary)

                i += 1


if __name__ == '__main__':
    main()
