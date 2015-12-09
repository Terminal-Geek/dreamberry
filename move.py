#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from glob import glob
import time

DIR_FROM = '/home/pi/dreamberry/recordings/'
DIR_TO = '/home/pi/dreamberry/recordings/finished/'


def mtime(filename):
    return int(os.path.getmtime(filename))


def main():

    now = int(time.time())
    for f in glob(DIR_FROM+'*.*'):
        if mtime(f)+60 < now:
            os.rename(DIR_FROM + os.path.basename(f),
                      DIR_TO + os.path.basename(f))


if __name__ == '__main__':
    main()
