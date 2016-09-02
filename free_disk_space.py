#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from subprocess import Popen, PIPE, call
import MySQLdb
from contextlib import closing
import shutil

import login
from lamedb import replacechars


RECORDING_PATH = '/var/www/dreamberry/recordings/'
BACKUP_PATH = '/media/fritzbox/Radio/'
PROWL_API_KEY = 'c855906554c47633852dcc4e1cb8b7427e11d10f'
MAX_USAGE = 90
RELAX_USAGE = 80


def checkspace():

    used = Popen(['df', '/', '--output=pcent'], stdout=PIPE)
    used = used.communicate()[0]
    used = int(used[len(used)-4:len(used)-2])

    return used


def prowl(usage):

    description = 'Speicherauslastung%20bei%20' + str(usage) + '%'
    url = (
            'https://api.prowlapp.com/publicapi/add/'
            + '?apikey='
            + PROWL_API_KEY
            + '&application=Dreamberry&description='
            + description
        )

    call (['curl', '-s', '-o', 'curl.log', url])


def movelatest():

    with closing(MySQLdb.connect(
            login.DB_HOST, login.DB_USER,
            login.DB_PASSWORD, login.DB_DATABASE)) as connection:
        with closing(connection.cursor()) as cursor:

            cursor.execute(
                'SELECT id, channel, title, audiofile FROM recordings ORDER BY id ASC')
            id, channel, title, audiofile = cursor.fetchone()

            db_request = 'DELETE FROM recordings WHERE id = %s'
            cursor.execute(db_request, (id,))
            connection.commit()

    channel = replacechars(channel.decode('latin-1').encode('utf-8'))
    title = replacechars(title.decode('latin-1').encode('utf-8'))
    origin = os.path.join(RECORDING_PATH, channel, title, audiofile)
    destination = os.path.join(BACKUP_PATH, channel, title, audiofile)
    destination_path = os.path.join(BACKUP_PATH, channel, title)

    if not os.path.exists(destination_path):
        os.makedirs(destination_path)
    shutil.move(origin, destination)


def main():

    usage = checkspace()

    prowl(usage)

    if usage >= MAX_USAGE:
        call('kill $(pidof -x watchdog)', shell=True)
        while 1:
            movelatest()
            if checkspace() <= RELAX_USAGE:
                call('setsid /home/pi/dreamberry/watchdog >/dev/null 2>&1 < /dev/null &', shell=True)
                break


if __name__ == '__main__':
    main()
