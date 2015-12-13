#!/usr/bin/env python
# -*- coding: utf-8 -*-

import MySQLdb
from contextlib import closing

import login
from soco import SoCo


def main():

    with closing(MySQLdb.connect(
            login.DB_HOST, login.DB_USER,
            login.DB_PASSWORD, login.DB_DATABASE)) as connection:
        with closing(connection.cursor()) as cursor:
            cursor.execute('SELECT ip FROM sonos WHERE id="1"')
            ip = cursor.fetchone()[0]

    sonos = SoCo(ip)
    sonos.start_library_update()


if __name__ == '__main__':
    main()
