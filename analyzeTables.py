#!/usr/bin/python
# -*- coding: UTF-8 -*-

#
#
# @filename:     analyzeTables.py
# @description:  Analyze all innodb tables and count time in analyzing.
# @author:       timeng#outlook.com
# @created:      2014-9-22 10:04:22
# @version:      0.2
#
#

import time
import subprocess
import sys
import getopt
import signal


def usage():

    print('''\
analyzeTables  Ver 0.2
Analyze all innodb tables and count time in analyzing.

Usage: analyzeTables OPTIONS

Options and arguments:
    --database=name         : Database name, Without this option, analyze all database and tables.
    -h, --host=name         : Connect to host.
    --help                  : Display this help message.
    -p, --password=name     : Password for connecting to mysql.
    -P, --port=#            : Port number to use for connection(default: 3306)
    -t, --table=name        : Table name, Without this option, analyze all tables in '--database'.
                              Between multiple names separated by ','
                              (The pre-condition to use this option is using '--database')
    -u, --user=name         : User for connecting to mysql.(default: root)
    
Sample:
    python analyzeTables.py -u test -p test -h 127.0.0.1 -P 3306 --database=test --table=t1,t2
''')


# defaults variables
user = 'root'
password = ''
host = '127.0.0.1'
port = '3306'
database = None
table = None


def getoptions():
    if len(sys.argv) < 2:
        usage()
        sys.exit()

    options, args = getopt.getopt(
        sys.argv[1:], "h:u:p:P:t:", ["help", "host", "user=", "password=", "Port=", "database=", "table="])
    for opt, value in options:
        if opt in("-u", "--user"):
            global user
            user = value
        elif opt in ("-p", "--password"):
            global password
            password = value
        elif opt in ("-h", "--host"):
            global host
            host = value
        elif opt in ("-P", "--Port"):
            global port
            port = value
        elif opt in ("--database"):
            global database
            database = value
        elif opt in ("-t", "--table"):
            global table
            table = value
        elif opt in ("--help"):
            usage()
            sys.exit()


def analyze_tables():
    """
    analyze innodb tables
    """
    sql = "select TABLE_SCHEMA,TABLE_NAME from information_schema.tables where engine='innodb' and TABLE_SCHEMA!='mysql'"
    global database
    global table
    if database is not None:
        sql = "%s and TABLE_SCHEMA='%s' " % (sql, database)
        if table is not None:
            tmp = str(table).split(',')
            table_sql = ""
            for i in tmp:
                table_sql = "%s '%s'," % (table_sql, i)
            sql = "%s and TABLE_NAME in (%s) " % (sql, table_sql[:-1])
    sql = "%s ;" % (sql)
    command = prepare_mysql(sql)
    p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
    r = p.stdout.read()
    if r == '':
        print('--- Result is empty! Check the options in command line is correct ---')
        sys.exit()

    lines = r.split("\n")
    # delete column name
    del lines[0]
    # delete blank line
    if(lines[-1] == ''):
        del lines[-1]
    result = {}
    # analyze every table
    total_time = 0
    for t in lines:
        # TABLE_SCHEMA  TABLE_NAME
        spend_time = do_analyze(t.split()[0], t.split()[1])
        total_time = total_time + spend_time
        result['%s.%s' % (t.split()[0], t.split()[1])] = spend_time
    print('Analyze All Tables in  %.3f seconds' % (total_time))
    for k in result:
        print('%-30s : %.3f' % (k, result[k]))


def do_analyze(database, table):
    '''
    analyze table, and count time
    @return spent time in analysis
    '''
    sql = "analyze table %s.%s;" % (database, table)
    command = prepare_mysql(sql)

    start = time.time()
    p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
    p.stdout.read()
    end = time.time()
    return end - start


def prepare_mysql(sql=None):
    global user
    global password
    global host
    global port
    mysql = 'mysql -h%s -u%s -p%s -P%s' % (host, user, password, port)
    command = '%s -e "%s"' % (mysql, sql)
    return command


def signal_handler(signal, frame):
    print('Exit!')
    sys.exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    getoptions()
    analyze_tables()
