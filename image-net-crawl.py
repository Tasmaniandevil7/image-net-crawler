import requests
from urllib.request import urlopen, urlretrieve
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import os
import json
import pandas as pd
from PIL import Image, ImageChops
import math
import operator
from functools import reduce

# MAIN ID 82127
rooturllist = ['82127']
final_data = pd.read_json('final.json', orient='records', lines=False)
fresh_data = pd.DataFrame()
# saved flickr image that says image not found
verpath = "C:\\Users\Administrator\Documents\Python\imgdata\\ver.jpg"
start_dir = "C:\\Users\\Administrator\\Documents\\Python\\imagedata"


def rmsdiff(im1, im2):
    "Calculate the root-mean-square difference between two images"

    try:
        h = ImageChops.difference(im1, im2).histogram()
        return math.sqrt(reduce(operator.add,
                                map(lambda h, i: h*(i**2), h, range(256))
                                ) / (float(im1.size[0]) * im1.size[1]))
    except:
        #print("images do not match")
        return 10000


def versize(im1):  # checks for size of image > 200x200
    width, height = im1.size
    if(width > 200 and height > 200):
        return 1
    else:
        return 0


def verimg(fname):
    im2 = Image.open(verpath)
    try:
        im1 = Image.open("%s.jpg" % fname)  # checks for broken file
        print("%s.jpg" % fname)
        if(versize(im1) == 1):
            # 0 means image is also flickr not found, 10000 means different
            return(rmsdiff(im1, im2))
        else:
            print("skipped image %s.jpg due to size" % fname)
            return -2
        im1.close()
    except:
        print("Image bytes broken, skipping")
        return -1
    im2.close()


def scrape(rooturl):
    url = 'http://image-net.org/python/tree.py/SubtreeXML?rootid=%s' % rooturl
    print(url)
    global fresh_data
    global final_data
    var1 = True
    while(var1):
        try:
            r = requests.get(url)
            data = r.content
            soup = BeautifulSoup(data, "lxml")
            #soup = BeautifulSoup(open("test.html"),"lxml")
            li = soup.find_all('synset')
            for el in li:
                urlid = el.get('synsetoffset')
                rootid = el.get('synsetid')
                keyword = el.get('words')
                num_child = el.get('num_children')
                dct = {"WNID": urlid,
                       "ROOTID": rootid,
                       "KEYWORD": keyword,
                       }

            if(int(num_child) != 0):
                if(rootid not in rooturllist):
                    rooturllist.append(rootid)
            else:
                # print(type(num_child))
                # print(keyword)
                # print(num_child)
                temp_data = pd.DataFrame.from_dict([dct])
                fresh_data = pd.concat(
                    (fresh_data, temp_data), axis=0, sort=False)
                fresh_data = fresh_data.drop_duplicates()
                final_data = pd.concat(
                    (final_data, fresh_data), axis=0, sort=False)
                final_data = final_data.drop_duplicates()
            var1 = False
        except:
            print("Unable to reach url, trying again")
            pass


def run_scrape():
    global final_data
    for url in rooturllist:
        print(rooturllist)
        scrape(url)
    final_data.to_json('final.json', orient='records', lines=False)


def download(wnid, foldername):
    global start_dir 
    if(not os.path.isdir("%s\\%s" % (start_dir, foldername))):
        os.mkdir(foldername)
        os.chdir(foldername)
    else:
        print("Folder already exists")
        os.chdir(foldername)
    logf = open("%serrorlog.txt" % foldername, "w")

    var1 = True
    while(var1):
        try:
            r = urlopen(
                "http://image-net.org/api/text/imagenet.synset.geturls?wnid=n%s" % wnid)

            print("Url opened succesfully")
            name = 1
            for line in r:
                print(line.decode())
                try:
                    x = urlopen(line.decode())

                    if(x.headers.get_content_maintype() == "image"):
                        path = urlparse(line.decode()).path
                        ext = os.path.splitext(path)[1]
                        urlretrieve(line.decode(), "%s.%s" % (name,ext))
                        retx = verimg(name)
                        if(retx != 0):
                            if(retx == 10000):
                                name += 1
                            elif(retx == -1):
                                print("Image broken, skipping")
                                logf.write("File broken:%s" % line.decode())
                            elif(retx == -2):
                                print("Image dropped due to size")
                                logf.write("Size error:%s" % line.decode())
                            else:
                                print("Image dropped due to similarity")
                                logf.write("File not found:%s" % line.decode())
                        else:
                            print("flickr error dropped")
                            logf.write("Flickr:%s" % line.decode())
                except:
                    print("skipped image due to server error")
                    logf.write("Server:%s" % line.decode())
                    pass

            var1 = False
        except:
            print("Url did not open, trying again")
            pass

    os.chdir(start_dir)
    logf.close()


def run_download():
    to_download = pd.read_json('final.json', orient='records', lines=False)
    count_row = to_download.shape[0]
    to_download_dict = to_download.to_dict(orient='records')
    # print(to_download_dict)
    for x in range(count_row):
        download(to_download_dict[x]["WNID"], to_download_dict[x]["KEYWORD"])


# download url http://image-net.org/api/text/imagenet.synset.geturls?wnid=n
