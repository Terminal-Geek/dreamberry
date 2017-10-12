#!/usr/bin/env python
# -*- coding: utf-8 -*-

import MySQLdb
from contextlib import closing
from subprocess import call

import login


def main():

    with closing(MySQLdb.connect(
            login.DB_HOST, login.DB_USER,
            login.DB_PASSWORD, login.DB_DATABASE)) as connection:
        with closing(connection.cursor()) as cursor:

            cursor.execute('SELECT * FROM epg')
            results = cursor.fetchone()

            if not results:
                url = (
                        'https://api.prowlapp.com/publicapi/add/'
                        + '?apikey=c855906554c47633852dcc4e1cb8b7427e11d10f'
                        + '&application=DB-Alert&description=Datenbank%20leer!'
                    )

                call (['curl', '-s', '-o', 'curl.log', url])


if __name__ == '__main__':
    main()
