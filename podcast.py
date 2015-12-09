#!/usr/bin/env python
# -*- coding: utf-8 -*-

import MySQLdb
from contextlib import closing
import socket
from email.utils import formatdate
import datetime
import time
import sys
import os
import re

import login
from lamedb import replacechars


HOST_NAME = 'http://' + socket.gethostname()
PODCAST_IMG_PATH = '/var/www/dreamberry/img/podcast/'
PODCAST_PATH = '/var/www/dreamberry/podcast/'
ID3_TIME_FORMAT = '%d.%m.%Y, %H:%M'


def station(connection, channel_alias):

    with closing(connection.cursor()) as cursor:
        cursor.execute(
                'SELECT channel FROM lamedb WHERE alias=%s', (
                channel_alias,)
        )
        row = cursor.fetchone()

        return row[0]


def image(channel_alias):

    podcast_img = PODCAST_IMG_PATH + channel_alias + '.jpg'
    if not os.path.isfile(podcast_img):
        podcast_img = HOST_NAME + '/dreamberry/img/podcast/' + 'default.jpg'
    else:
        podcast_img = HOST_NAME + '/dreamberry/img/podcast/' + channel_alias + '.jpg'

    return podcast_img


def header(channel, last_build_date, podcast_img):

    podcast_header = [
                    '<?xml version=\"1.0\" encoding=\"UTF-8\"?>',
                    '<rss xmlns:itunes=\"http://www.itunes.com/'
                    + 'dtds/podcast-1.0.dtd\" version=\"2.0\">',
                    '<channel>',
                    '<title>Dreamberry - '
                    + channel
                    + '</title>',
                    '<link>'
                    + HOST_NAME
                    + '/dreamberry'
                    + '</link>',
                    '<description>Hier hörst du alle deine Aufnahmen von '
                    + channel
                    +'</description>',
                    '<language>de-de</language>',
                    '<pubDate>'
                    + last_build_date
                    + '</pubDate>',
                    '<lastBuildDate>'
                    + last_build_date
                    + '</lastBuildDate>',
                    '<generator>DreamBerry</generator>',
                    '<category>Society &amp; Culture</category>',
                    '<image>',
                    '<url>'
                    + podcast_img
                    + '</url>',
                    '<title>DreamBerry - '
                    + channel
                    + '</title>',
                    '<link>'
                    + HOST_NAME
                    + '</link>',
                    '</image>',
                    '<itunes:subtitle>Hören, wann du willst!'
                    + '</itunes:subtitle>',
                    '<itunes:author>'
                    + channel
                    + '</itunes:author>',
                    '<itunes:summary>Hier hörst du alle Aufnahmen von '
                    + channel
                    + '</itunes:summary>',
                    '<itunes:image href=\"'
                    + podcast_img
                    + '\" />',
                    '<itunes:category text=\"Society &amp; Culture\" />',
                    '\n'
                    ]

    podcast_header = '\n'.join(podcast_header)

    return podcast_header


def item(title, description, audio_file, length_bytes, guid,
                        pub_date, podcast_img, channel, length):

    podcast_item = [
                    '<item>',
                    '<title>',
                    title.decode('latin-1').encode('utf-8'),
                    '</title>',
                    '<link>'
                    + HOST_NAME
                    + '/dreamberry/recordings/'
                    + audio_file
                    + '</link>',
                    '<description>',
                    description.decode('latin-1').encode('utf-8'),
                    '</description>',
                    '<enclosure url=\"'
                    + HOST_NAME
                    + '/dreamberry/recordings/'
                    + audio_file
                    + '\" length=\"'
                    + str(length_bytes)
                    + '\" type=\"audio/mpeg\" />',
                    '<guid isPermaLink=\"false\">'
                    + guid
                    + '</guid>',
                    '<pubDate>'
                    + pub_date
                    + '</pubDate>',
                    '<image>',
                    '<url>'
                    + podcast_img
                    + '</url>',
                    '<title>DreamBerry - '
                    + channel
                    + '</title>',
                    '<link>'
                    + HOST_NAME
                    + 'dreamberry'
                    + '</link>',
                    '</image>',
                    '<itunes:author>'
                    + channel
                    + '</itunes:author>',
                    '<itunes:subtitle>Hören, wann du willst!'
                    + '</itunes:subtitle>',
                    '<itunes:image href=\"'
                    + podcast_img
                    + '\" />',
                    '<itunes:duration>'
                    + length
                    + '</itunes:duration>',
                    '</item>',
                    '\n'
                    ]

    podcast_item = '\n'.join(podcast_item)

    return podcast_item


def main(channel_alias):

    with closing(MySQLdb.connect(
            login.DB_HOST, login.DB_USER,
            login.DB_PASSWORD, login.DB_DATABASE)) as connection:

        channel = station(connection, channel_alias)
        last_build_date = formatdate(time.time(), True)
        podcast_img = image(channel_alias)
        xml_file = PODCAST_PATH + channel_alias + '.xml'

        feed = open(xml_file, 'w')
        podcast_header = header(channel, last_build_date, podcast_img)
        feed.write(podcast_header)
        feed.close

        feed = open(xml_file, 'a')

        with closing(connection.cursor()) as cursor:
            cursor.execute(
                    'SELECT * FROM recordings WHERE channel=%s', channel,)
            result = cursor.fetchall()
            for db_record in result:

                timestamp = db_record[7]
                title = (
                    db_record[4]
                    + ' ('
                    + datetime.datetime.fromtimestamp(
                        int(timestamp)).strftime(ID3_TIME_FORMAT)
                    + ' Uhr)'
                )
                description = db_record[5]
                title_path = replacechars(
                    db_record[4].decode('latin-1').encode('utf-8')
                )
                audio_file = (
                    channel_alias + '/' + title_path + '/' + db_record[6]
                )
                length_bytes = db_record[9]
                guid = (
                    HOST_NAME
                    + '/dreamberry/podcast/'
                    + channel_alias
                    + '_'
                    + str(db_record[0])
                )
                pub_date = db_record[10]
                length = db_record[8]

                podcast_item = item(title, description, audio_file,
                                    length_bytes, guid, pub_date,
                                    podcast_img, channel, length
                )

                feed.write(podcast_item)

        feed.write('</channel>\n</rss>')

        feed.close


if __name__ == '__main__':
    main(sys.argv[1])
