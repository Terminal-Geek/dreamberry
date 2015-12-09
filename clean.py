#!/usr/bin/env python
# -*- coding: utf-8 -*-

import MySQLdb
from contextlib import closing
from glob import glob
import os

import login
from lamedb import replacechars


PATH_RECORDINGS = '/var/www/dreamberry/recordings'


def filelist():

    mp3 = []
    fullpath = []
    for dirs in os.walk(PATH_RECORDINGS):
        for files in dirs[2]:
            mp3.append(files)
            fullpath.append(os.path.join(dirs[0], files))

    return mp3, fullpath


def delete_file_orphans(cursor):

    mp3, fullpath = filelist()
    i = 0

    while i < len(mp3):

        db_request = 'SELECT COUNT(*) FROM recordings WHERE audiofile = %s'
        cursor.execute(db_request, (mp3[i],))
        check = cursor.fetchone()[0]
        if check == 0:
            os.remove(fullpath[i])
        i += 1


def delete_db_orphans(connection, cursor):

    cursor.execute('SELECT * FROM recordings')
    result = cursor.fetchall()

    for db_record in result:

        channel_alias = replacechars(
            db_record[3].decode('latin-1').encode('utf-8')
        )
        title_path = replacechars(
            db_record[4].decode('latin-1').encode('utf-8')
        )
        mp3 = os.path.join(
            PATH_RECORDINGS, channel_alias, title_path, db_record[6]
        )

        check = os.path.isfile(mp3)
        if check is False:
            db_request = 'DELETE FROM recordings WHERE audiofile = %s'
            cursor.execute(db_request, (db_record[6],))
            connection.commit()


def delete_empty_dirs():

    i = 0
    while i < 2:
        for dirs in os.walk(PATH_RECORDINGS):
            if not os.listdir(dirs[0]):
                os.rmdir(dirs[0])
        i += 1


def main():

    with closing(MySQLdb.connect(
            login.DB_HOST, login.DB_USER,
            login.DB_PASSWORD, login.DB_DATABASE
            )) as connection:

        with closing(connection.cursor()) as cursor:

            delete_file_orphans(cursor)
            delete_db_orphans(connection, cursor)
            delete_empty_dirs()


if __name__ == '__main__':
    main()
