#!/usr/bin/env python
# -*- coding: utf8 -*-

import os
import socket
import sys
import re
from glob import glob
import MySQLdb
from contextlib import closing
import subprocess
import datetime
import time
from email.utils import formatdate

from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1, TALB, USLT, TYER, APIC

import login
import podcast


DIR_FROM = '/home/pi/dreamberry/recordings/finished/'
DIR_TO = '/var/www/dreamberry/recordings/'
STAMP = 'processing_'
DATE_TIME_FORMAT = '%Y-%m-%d_%H-%M'
ID3_TIME_FORMAT = '%d.%m.%Y, %H:%M'
PODCAST_PATH = '/var/www/dreamberry/podcast/'
PODCAST_IMG_PATH = '/var/www/dreamberry/img/podcast/'
HOST_NAME = 'http://' + socket.gethostname()



def stamp(f):

    os.rename(f, DIR_FROM + STAMP + os.path.basename(f))

    return DIR_FROM + STAMP + os.path.basename(f)


def metadata(f):

    with open(f, 'r') as meta:
        lines = meta.readlines()
        timestamp = lines[3].strip()
        sid = lines[0].split(':')[3]

    return sid, timestamp


def epgdata(sid, timestamp):

    with closing(MySQLdb.connect(
            login.DB_HOST, login.DB_USER,
            login.DB_PASSWORD, login.DB_DATABASE)) as connection:
        with closing(connection.cursor()) as cursor:

            cursor.execute(
                'SELECT channel, alias FROM lamedb WHERE sid = (%s)', (sid))
            channel, alias = cursor.fetchone()


            cursor.execute(
                'SELECT alias, title, teaser, summary \
                FROM epg WHERE alias = (%s) AND time <= (%s) \
                ORDER BY time DESC',
                (alias, timestamp))
            epg = cursor.fetchone()

    return epg, channel


def transcode (audio_file, timestamp, epg):

    title = re.compile('[^a-zA-Z0-9]').sub('', epg[1].lower())
    alias = epg[0]
    out_dir = os.path.join(DIR_TO, alias, title)
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    out_file = out_dir + '/' + datetime.datetime.fromtimestamp(
        int(timestamp)).strftime(DATE_TIME_FORMAT) + '_' + epg[0] + '.mp3'

    avconv = [
        'avconv',
        '-i',
        audio_file,
        '-vn',
        '-acodec',
        'libmp3lame',
        '-ab',
        '256k',
        out_file,
    ]
    subprocess.call(avconv)

    return out_file


def id3tag(audio_file, timestamp, channel, epg):

    podcast_img = PODCAST_IMG_PATH + epg[0] + '.jpg'
    if not os.path.isfile(podcast_img):
        podcast_img = PODCAST_IMG_PATH + 'default.jpg'
    if epg[2] == "":
        description = epg[3]
    else:
        description = (epg[2] + '\n\n' + epg[3])

    audio = ID3()
    audio.save(audio_file)
    audio = ID3(audio_file)
    audio.add(TIT2(
            encoding=3, text=epg[1].decode('latin-1')
            + ' ('
            + datetime.datetime.fromtimestamp(int(timestamp)).strftime(
                ID3_TIME_FORMAT)
            + ' Uhr)'
            )
    )
    audio.add(TPE1(encoding=3, text=channel.decode('latin-1')))
    audio.add(TALB(encoding=3, text=epg[1].decode('latin-1')))
    audio.add(USLT(encoding=3, text=description.decode('latin-1')))
    audio.add(TYER(encoding=3,text=datetime.datetime.fromtimestamp(
        int(timestamp)).strftime('%Y')))
    audio.add(APIC(
            encoding = 3,
            mime = 'image/jpeg',
            type = 3,
            desc = u'Cover',
            data = open(podcast_img).read()
            )
    )

    audio.save(v2_version=3)


def audiolength(out_file):

    length = str(
        datetime.timedelta(seconds=int((MP3(out_file)).info.length))
    )
    length_bytes = os.path.getsize(out_file)

    return length, length_bytes


def database(timestamp, channel, epg, out_file):

    rec_date = datetime.datetime.fromtimestamp(
        int(timestamp)).strftime('%Y.%m.%d')
    rec_time = datetime.datetime.fromtimestamp(
        int(timestamp)).strftime('%H:%M')
    pubdate = formatdate(time.time(), True)
    title = epg[1]
    if epg[2] == '':
        description = epg[3]
    else:
        description = epg[2] + '\n\n' + epg[3]
    audiofile = os.path.basename(out_file)
    length, length_bytes = audiolength(out_file)

    with closing(MySQLdb.connect(
            login.DB_HOST, login.DB_USER,
            login.DB_PASSWORD, login.DB_DATABASE)) as connection:
        with closing(connection.cursor()) as cursor:

            cursor.execute('INSERT INTO recordings \
            (date, time, channel, title, description, audiofile, timestamp, \
            length, bytes, pubdate) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',
                    (rec_date, rec_time, channel, title, description,
                     audiofile, timestamp, length, length_bytes, pubdate))

            connection.commit()


def main():

    for f in glob(DIR_FROM + '*'):

        if not STAMP in f:
            extension = f.rsplit('.', 1)[1]

            if extension == 'ts':

                metafile = DIR_FROM + os.path.basename(f) + '.meta'
                sid, timestamp = metadata(metafile)
                epg, channel = epgdata(sid.lower(), timestamp)

                corresponding_files = []
                for c in glob(f.rstrip(extension) + '*'):
                    corresponding_files.append(c)

                i = 0
                while i < len(corresponding_files):
                    corresponding_files[i] = stamp(corresponding_files[i])
                    extension = corresponding_files[i].rsplit('.', 1)[1]
                    if extension == 'ts':
                        audio_file = corresponding_files[i]
                    i += 1

                out_file = transcode(audio_file, timestamp, epg)
                id3tag(out_file, timestamp, channel, epg)
                database(timestamp, channel, epg, out_file)

                for c in corresponding_files:
                    os.remove(c)
                podcast.main(epg[0])


if __name__ == '__main__':
    main()
