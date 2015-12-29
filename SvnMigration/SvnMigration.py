#!/usr/bin/python
# -*- coding: UTF-8 -*-

#
# @filename:     SvnMigration.py
# @description:  Download source code from a svn repository and migration to anothor repository.
# @author:       timeng at outlook.com
# @created:      2015-09-21 22:52:54
# @version:      0.1
#

import time
import subprocess
import sys
import signal
import os
import shutil
import stat
import ConfigParser
import hashlib

def usage():

    print('''\

SvnMigration.py  Version 0.1

Download source code from a svn repository and migration to anothor repository.

A configuration file 'conf/svn.cnf' must be existed, options as follows:
[from]
url = http://example.com/svn/branches/url1
username = usera
password = 111111
 
[to]
url = http://example.com/svn/branches/url2
username = usera
password = 111111

EOF

Usage:
    python SvnMigration.py 
''')

copyFileCounts = 0
oldSvn = None
newSvn = None


class Svn:
    """svn entity"""
    def __init__(self, url=None, username=None, password=None):
        self.__url = url
        self.__username = username
        self.__password = password

    def getUrl(self):
        return self.__url

    def getUserName(self):
        return self.__username

    def getPassWord(self):
        return self.__password


def read_conf():
    try:
        cf = ConfigParser.ConfigParser()
        confDir = os.path.join(os.curdir, 'conf')
        confPath = os.path.join(confDir, 'svn.cnf')
        cf.read(confPath)

        global oldSvn
        global newSvn

        fromUrl = cf.get("from", "url")
        fromUsername = cf.get("from", "username")
        fromPassword = cf.get("from", "password")
        oldSvn = Svn(fromUrl, fromUsername, fromPassword)

        toUrl = cf.get("to", "url")
        toUsername = cf.get("to", "username")
        toPassword = cf.get("to", "password")
        newSvn = Svn(toUrl, toUsername, toPassword)
        
    except Exception, e:
        print('read conf/svn.cnf error')
        usage()
        sys.exit(-2)


def printProcess(p):
    """
    print subprocess stdout
    """
    r = p.stdout.read()
    lines = r.split("\n")
    for t in lines:
        print(t)


def on_rm_error(func, path, exc_info):
    # path contains the path of the file that couldn't be removed
    # let's just assume that it's read-only and unlink it.
    os.chmod(path, stat.S_IWRITE)
    os.unlink(path)


def removeDir(targetDir):
    """
    recursion delete    
    """
    if os.path.isdir(targetDir):
        shutil.rmtree(targetDir, onerror=on_rm_error)
        print "dir " + targetDir + " removed"


def download(url, username, password, targetDir):
    """
    download from svn url
    """
    #osvn = 'svn export --force --username=1 --password=1 http://example.com/svn/branches/url1'
    osvn = 'svn export --force '
    if username is not None:
        osvn = osvn + '--username=' + username + ' '
    if password is not None:
        osvn = osvn + '--password=' + password + ' '
    osvn = osvn + url + ' ' + targetDir
    # print(osvn)
    p = subprocess.Popen(osvn, shell=True, stdout=subprocess.PIPE)
    print('----------- start download... --------')
    printProcess(p)
    print('----------- download done! -----------')


def checkout(url, username, password, targetDir):
    """
    checkout from svn url
    """
    #osvn = 'svn co --force --username=1 --password=1 http://example.com/svn/branches/url2'
    osvn = 'svn co --force '
    if username is not None:
        osvn = osvn + '--username=' + username + ' '
    if password is not None:
        osvn = osvn + '--password=' + password + ' '
    osvn = osvn + url + ' ' + targetDir
    p = subprocess.Popen(osvn, shell=True, stdout=subprocess.PIPE)
    print('----------- start checkout new repository... --------')
    printProcess(p)
    print('----------- checkout new repository done! -----------')


def addSvn(targetDir):
    # add
    print('----------- add file to svn --------')
    for parent, dirnames, filenames in os.walk(targetDir):
        # 3 params：1.parent folder 2.all folders（no path split '/'） 3. all
        # files name
        for dirname in dirnames:
            filepath = os.path.join(parent, dirname)
            if '.svn' in filepath:
                #print  ("dirname is" + filepath )
                pass
            else:
                addsvn = 'svn add ' + filepath + '/*'
                p = subprocess.Popen(
                    addsvn, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                r = p.stdout.read()
                lines = r.split("\n")
                for t in lines:
                    if (t.startswith('A')):
                        print(t)  # only print file has been added
    print('----------- add done! -----------')


def commit(username, password, targetDir):
    """
    commit to new svn
    """
    #osvn = 'svn commit -m "add test file for my test" '
    osvn = 'svn commit '
    if username is not None:
        osvn = osvn + '--username=' + username + ' '
    if password is not None:
        osvn = osvn + '--password=' + password + ' '
    osvn = osvn + '-m "commit by SvnMigration.py" ' + targetDir + '/*'
    # print(osvn)
    p = subprocess.Popen(osvn, shell=True, stdout=subprocess.PIPE)
    print('----------- start commit new repository... --------')
    printProcess(p)
    print('----------- commit done! -----------')


def getFileMd5(filename):
    """
    #get md5 by file
    """
    if not os.path.isfile(filename):
        return
    myhash = hashlib.md5()
    f = file(filename,'rb')
    while True:
        b = f.read(8096)
        if not b :
            break
        myhash.update(b)
    f.close()
    return myhash.hexdigest()


def copyFiles(sourceDir, targetDir):
    global copyFileCounts
    print sourceDir
    print u"%s dealing folder is :%s ,has processed %s files" % (time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())), sourceDir, copyFileCounts)
    for f in os.listdir(sourceDir):
        sourceF = os.path.join(sourceDir, f)
        targetF = os.path.join(targetDir, f)

        if os.path.isfile(sourceF):
            # mkdir
            if not os.path.exists(targetDir):
                os.makedirs(targetDir)
            copyFileCounts += 1

            # if file existed ,but file size is not equal
            if not os.path.exists(targetF) or (os.path.exists(targetF) and (getFileMd5(targetF) != getFileMd5(sourceF))):
                # binary file
                open(targetF, "wb").write(open(sourceF, "rb").read())
                print u"%s %s copy done" % (time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())), targetF)
            else:
                pass
        if os.path.isdir(sourceF):
            copyFiles(sourceF, targetF)


def signal_handler(signal, frame):
    print('Exit!')
    sys.exit(0)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    # read conf
    read_conf()
    workDir = os.path.join(os.curdir, 'work')
    oldFolder = os.path.join(workDir, 'from', oldSvn.getUrl().split('/')[-1])
    newFolder = os.path.join(workDir, 'to', newSvn.getUrl().split('/')[-1])

    # export old svn
    print('\nold svn will export to this folder: ' + oldFolder)
    removeDir(oldFolder)
    download(oldSvn.getUrl(), oldSvn.getUserName(),
             oldSvn.getPassWord(), oldFolder)

    # checkout new svn
    print('\nnew svn will checkout to this folder: ' + newFolder)
    removeDir(newFolder)
    checkout(newSvn.getUrl(), newSvn.getUserName(),
             newSvn.getPassWord(), newFolder)

    print('----------- copy to new svn repository ! -----------')
    copyFiles(oldFolder, newFolder)
    print('----------- copy done ! -----------')

    # add to svn
    addSvn(newFolder)

    # commit
    print(
        '\n' + newFolder + ' will be commited in 15s, press CTRL + C to stop it')
    count = 0
    while (count < 15):
        ncount = 15 - count
        print ncount
        time.sleep(1)
        count += 1
    commit(newSvn.getUserName(), newSvn.getPassWord(), newFolder)
