# Coding:uft-8
import os
import re
import sys
import math
import time
import requests
import threading


class AudioSpider:
#数据太大时print不出来，但是不影响操作
########################################
    headers  = {"User-Agent":"Spider/0.0.0 AudioSpider/0.0.0"}
    categoURL = "http://www.ximalaya.com/revision/getRankCluster"
    subcatURL = "http://www.ximalaya.com/revision/category/detailCategoryPageInfo?category=%s"
    albumsURL = "http://www.ximalaya.com/revision/category/queryCategoryPageAlbums?sort=0&category=%s&subcategory=%s&meta=%s&page=%d&perPage=%d"
    alInfoURL = "http://www.ximalaya.com/revision/album?albumId=%s"
    audiosURL = "http://www.ximalaya.com/revision/play/album?sort=0&albumId=%s&pageNum=%d&pageSize=%d"
    tracksURL = "http://www.ximalaya.com/revision/album/getTracksList?albumId=%s&pageNum=1&sort=1"

    def __init__(self,argument = ("AudioSpider",True)):

        threading.Thread.__init__(self)

        self.name = argument[0]

        self.checkOld = argument[1]


    def category(self):
        try:
            response = requests.get(self.categoURL, headers = self.headers).json()

            return response["data"]["list"]
        
        except KeyboardInterrupt:

            sys.exit()

        except:
            
            print("\n获取专辑分类失败")

            return False
    
    def subCategory(self, Category):
        try:
            response = requests.get(self.subcatURL%(Category), headers = self.headers).json()

            return (response["data"]["metadata"],response["data"]["subcategories"])
        
        except KeyboardInterrupt:

            sys.exit()

        except:
            
            print("\n获取专辑分类失败")

            return False
        
    def albumsList(self,category, page = 1, size = 0):

        arguments = []
        arguments.extend(category)
        arguments.extend((page,size))

        #取得专辑列表
        response = requests.get(self.albumsURL%tuple(arguments), headers = self.headers).json()

        if response["ret"] != 0:
            #获取专辑失败
            return False

        if size <= 0:
            #如果页大小为0则
            #按专辑总数重新设置
            page = 1

            size = response["data"]["total"]

            return self.albumsList(category,page, size)
        
        return response["data"]


    def trackList(self, album, page = 1, size = 0):
        #取得音频列表
    
        response = requests.get(self.tracksURL%(album), headers = self.headers).json()

        if response["ret"] != 0:

            #获取专辑失败

            return False
        
        trackCount = response["data"]["trackTotalCount"]

        if size <= 0:
            #如果页大小为0则
            #按专辑总数重新设置

            if trackCount <= 1000:
                #目测每页最多1000条，否则出错

                page = 1

                size = trackCount

                return self.trackList(album, page , size)

            else:

                pages = math.ceil(trackCount / 1000)

                track = []
                
                for p in range(1,pages + 1):

                    response = self.trackList(album, p , 1000)

                    track.extend(response["track"])

                return {"trackCount": trackCount, "track" : track} 

        else:
            

            response = requests.get(self.audiosURL%(album,page,size), headers = self.headers).json()

        if response["ret"] != 0:
            #获取专辑失败

            with open ("FailLog.txt","a",encoding='utf-8') as f:

                f.write("%s\n"%(self.audiosURL%(album,page,size)))
        
            return False

        

        return {"trackCount": trackCount, "track" : response["data"]["tracksAudioPlay"]} 
        

    def albumInfo(self, album):
        try:
            response = requests.get(self.alInfoURL%(str(album)), headers = self.headers).json()

            data={
                "albumId": response["data"]["albumId"],
                "title": response["data"]["mainInfo"]["albumTitle"],
                "coverPath": response["data"]["mainInfo"]["cover"],
                "anchorName": response["data"]["anchorInfo"]["anchorName"],
                "uid": response["data"]["anchorInfo"]["anchorId"],
                "isPaid": response["data"]["mainInfo"]["isPaid"],
                "isFinished": response["data"]["mainInfo"]["isFinished"],
                "link": "/youshengshu/%s/"%(album),
                "playCount": response["data"]["mainInfo"]["playCount"]
            }
            
            return data

        except KeyboardInterrupt:

            sys.exit()

        except:
            
            return False
        
        
    def download(self, resource, filePath = ".", fileName = ""):
        
        tempName = self.getFileName(resource)

        #没有指定文件名则使用默认文件名                    
        if fileName == "":

            fileName = tempName[0]

        #去掉非法字符
        for char in '\/':
            fileName = fileName.replace(char,"_")

        for char in ':*?"|':
            filePath = filePath.replace(char,"_")
            fileName = fileName.replace(char,"_")

        #文件不存在则开始下载
        if self.checkOld:
            curName = self.isExists(filePath, fileName)

        else:
            curName = os.path.exists(fileName)
            
        if not curName:

            fileName = "%s/%s"%(filePath,fileName)

            if not os.path.exists(fileName):

                #多层创建目录
                if not os.path.exists(filePath):

                    os.makedirs(filePath)

                if self.delTempFile(fileName + ".tmp"):
                        
                    response = requests.get(resource, headers = self.headers, stream=True)

                    fd = os.open(fileName + ".tmp", os.O_RDWR|os.O_CREAT)

                    fo = os.fdopen(fd, "wb")

                    for chunk in response.iter_content(chunk_size=512):

                        fo.write(chunk)
                    
                    os.close(fd)

                    os.rename(fileName + ".tmp",fileName)
        else:
            if self.checkOld:

                oldName = "%s/%s"%(filePath,curName)
                
                newName = "%s/%s"%(filePath,fileName)

                if oldName != newName:

                    os.rename(oldName, newName)



    def delTempFile(self, filePath,fileName = ""):

        try:

            if fileName:

                filePath = "%s/%s"%(filePath, fileName)

            os.remove(filePath)

            return True

        except FileNotFoundError as Err:

            return True    

        except PermissionError as Err:

            if Err.errno == 13:#raise(Err)

                return False
        

    def isExists(self, filePath, fileName):

        try:

            if not os.path.exists(filePath):

                return False

            fileLists = []
            
            for file in os.listdir(filePath):

                if not os.path.isdir(file):

                    fileLists.append(file)

            fileIndex = re.findall(r'^\[(\d*?)\]',fileName)[0]

            fileIndex = re.sub(r'^0*', '', fileIndex)
            
            oldName = re.sub(r'^\[\d*?\]', '', fileName)

            ruler = r'^\[0*?' + fileIndex + '\]' + oldName + "$"

            oldName = re.findall(ruler,"\n".join(fileLists),re.M)[0]

            return oldName;

        except KeyboardInterrupt:

            sys.exit()
            
        except Exception as err:

            return False
    
    def getFileName(self, filename):

        tempfilename = filename.split("/");

        extension = tempfilename[-1].split(".");

        return tempfilename[-1],"".join(extension[:-1]),".%s"%extension[-1]


class MyThread(threading.Thread):

    def __init__(self,argument):

        threading.Thread.__init__(self)

        self.name = argument[0]

        self.category = argument[1]

        self.page = argument[2]

        if argument[2] <= 0:
            #页码小于0时
            #第三个参数是列表
            self.albums = argument[3]
        else:
            self.count = argument[3]

    def run(self):

        print ("%s：任务开始"%self.name)
        
        try:
            #实例化一只蜘蛛
            Spider = AudioSpider(("AudioSpider",True))

            if self.page > 0:
                #页码D大于0时爬取指定专辑
                try:
                    
                    albumsList = Spider.albumsList(self.category,self.page,self.count)

                    if not albumsList:
                        #获取专辑失败，强制异常
                        raise Exception("albums List is Null") 

                except KeyboardInterrupt:

                    sys.exit()
                    
                except Exception as err:

                    with open ("ErrorLog.txt","a",encoding='utf-8') as f:

                        f.write("%s|%s|%s|page：%s|count：%s\n"%(self.localTime(),self.name,str(err),self.page,self.count))

                    print ("%s：异常结束"%self.name)

                    return
            else:
                #页码小于0时爬取指定专辑
                albumsList = {"albums":self.albums}
                
                
            for album in albumsList["albums"]:

                print("%s：正在爬取专辑《%s》\n"%(self.name,album["title"]))

                try:
                    trackList = Spider.trackList(album["albumId"])

                    if not trackList:
                        #获取专辑失败，强制异常
                        raise Exception("track List is Null")

                    for track in trackList["track"]:
                        
                        if track["hasBuy"] == True:

                            #已购买（或者免费）

                            print("%s：正在下载文件《%s》\n"%(self.name,track["trackName"]))

                            filePath = "%s/[%s]%s"%("./AudioSpider", str(album["albumId"]),album["title"])
                            
                            trackIndex = str(track["index"]).zfill(len(str(len(trackList["track"]))))

                            fileName = "[%s]%s%s"%(trackIndex,track["trackName"], Spider.getFileName(track["src"])[2])

                            Spider.download(track["src"], filePath, fileName)
                        else:
                            #未购买
                            #track["src"]值为null，无法下载
                            print("%s：没有下载权限《%s》\n"%(self.name,track["trackName"]))

                    print("%s：爬取专辑《%s》完成\n"%(self.name,album["title"]))

                except KeyboardInterrupt:

                    sys.exit()

                except Exception as err:

                    with open ("FailLog.txt","a",encoding='utf-8') as f:

                        f.write("%s|%s|%s|albums：%s|track：%s\n"%(self.localTime(),self.name,str(err),track["albumId"],track["trackId"]))

                    print("%s：爬取专辑《%s》失败\n"%(self.name,album["title"]))

            print ("%s：任务完成"%self.name)

        except KeyboardInterrupt:

            sys.exit()
                    
        except Exception as err:

            with open ("ErrorLog.txt","a",encoding='utf-8') as f:

                f.write("%s|%s|%s|albums：%s|track：%s\n"%(self.localTime(),self.name,str(err),track["albumId"],track["trackId"]))

            print ("%s：异常结束"%self.name)

    def localTime(self):

        return time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))

def getCategory():
    #实例化一只蜘蛛
    Spider = AudioSpider()

    print("\n请选择你要下载的分类：")

    categorys = Spider.category()

    if not categorys:

        return False

    category = showCategory(categorys, "title")
        
    return category["name"]


def subCategory(category):
    #实例化一只蜘蛛
    Spider = AudioSpider()

    categorys = Spider.subCategory(category)

    if not categorys:

        return False

    metadatas = categorys[0]

    categorys = categorys[1]

    metaList = []

    category = showCategory(categorys, "displayValue", True)

    if category and type(category) == bool:

        subCateStr = ""
    else:

        subCateStr = category["code"]

        metaList = getMetas(category["metas"])
        
    metaList.extend(getMetas(metadatas))

    metaString = "-".join(metaList)

    return (subCateStr, metaString)

def getMetas(metadatas):

    metaList = []
        
    for meta in metadatas:

        print("\n请选择你要下载的%s："%(meta["name"]))
        
        subMeta = showCategory(meta["metaValues"], "displayName", True)

        if subMeta and type(subMeta) == bool:

            continue

        metaList.append("%d_%d"%(meta["id"],subMeta["id"]))

        if len(subMeta["metas"]) > 0:

            metaList.extend(getMetas(subMeta["metas"]))

    return metaList

def showCategory(categorys, field ,allowAll = False):

    index = 0

    print("-"*20)

    if allowAll:
        print(str(index).rjust(2),"│", "全部")
    for cate in categorys:
        index += 1
        print(str(index).rjust(2),"│", cate[field])
        
    print("-"*20)

    while True:

        index = input("\n请输入一个ID：")

        try:
            index = int(index)
        except ValueError:
            continue

        if (index <= len(categorys) and index > 0) \
           or (allowAll and index == 0):

            break
        
    if index == 0:
        
        print("\n已经选择：","全部")

        return True

    print("\n已经选择：",categorys[index - 1][field])

    return categorys[index - 1]
    

def downlAll(maxThread):
    #实例化一只蜘蛛
    Spider = AudioSpider()

    category = getCategory()

    subCateStr, metaString = subCategory(category)

    category = (category,subCateStr,metaString)

    #主要目的是获取专辑数量
    albums = Spider.albumsList(category,1,0)

    total = albums["total"]

    albums = albums["albums"]
  
    print("\n找到以下专辑：\n"+"-"*47)

    for album in albums:

            print("\n%s\t%s"%(str(album["albumId"]).rjust(8),album["title"]))

    print("\n" + "-"*47)

    print("\n%s\t%d"%("Total".rjust(8),total))

    print("\n" + "-"*47)

    input ("按回车键继续\n")

    if total == 0:
        print("\n没有可执行的任务")
        return {"total":0, "category":(), "threadAlbum":0, "instance":0, "threadTask":[]}

    maxThread = 10

    threadAlbum = math.ceil(total / maxThread)

    instance = math.ceil(total / threadAlbum)

    threadTask = []

    for ThreadID in range(0,instance):

        threadTask.append({"page":ThreadID + 1, "album":threadAlbum})

    return {"total":total, "category":category, "threadAlbum":threadAlbum, "instance":instance, "threadTask":threadTask}

def downlList(albums,maxThread):

    #没有指定List则下载全部
    if not albums:
        return downlAll(maxThread)
    
    #实例化一只蜘蛛
    Spider = AudioSpider()

    downAlbum = []

    #已经找到的专辑
    exis = []

    print("\n找到以下专辑：\n"+"-"*47)
    for album in albums:

        albumsInfo = Spider.albumInfo(album)
        
        if albumsInfo:

            exis.append(albumsInfo["albumId"])

            downAlbum.append(albumsInfo)
            
            print("\n%s\t%s"%(str(albumsInfo["albumId"]).rjust(8),albumsInfo["title"]))

    #list求差集，即为没有找到的专辑
    ret_list = list(set(albums)^set(exis))

    total = len(downAlbum)

    print("\n" + "-"*47)

    print("\n%s\t%d"%("Total".rjust(8),total))

    print("\n%s\t%s"%("NotFound".rjust(8),str(ret_list)[1:-1]))

    print("\n" + "-"*47)

    input ("按回车键继续\n")

    if total == 0:
        print("\n没有可执行的任务")
        return {"total":0, "category":(), "threadAlbum":0, "instance":0, "threadTask":[]}

    threadAlbum = math.ceil(total / maxThread)

    instance = math.ceil(total / threadAlbum)

    threadTask = []

    for ThreadID in range(0,instance):

        albumStrat = ThreadID * threadAlbum
        albumEnded = albumStrat + threadAlbum

        threadTask.append({"page":0, "album":downAlbum[albumStrat:albumEnded]})

    return {"total":len(downAlbum), "category":(), "threadAlbum":threadAlbum, "instance":instance, "threadTask":threadTask}


def main(downAlbum):
    try:

        starttime = time.time()
        
        threadTask = downlList(downAlbum,10)

        maxThread = 10
        
        total = threadTask["total"]

        category = threadTask["category"]
        
        threadAlbum = threadTask["threadAlbum"]

        instance = threadTask["instance"]

        threadTask = threadTask["threadTask"]

        Threads = []

        for ThreadID in range(0,instance):

            ThreadName = "Thread_%s"%(str(ThreadID).zfill(len(str(maxThread))))

            Thread = MyThread((ThreadName, category, threadTask[ThreadID]["page"], threadTask[ThreadID]["album"]))

            Threads.append(Thread)

            Thread.start()

        for Thread in Threads:

            while not isinstance(Thread, MyThread):

                time.sleep(1)

            Thread.join()

        endtime = time.time()

        print ("\n" + "-"*17 + "任务结束" + "-"*18 + "\n")
        print ("最大线程数：%s\n"%maxThread)
        print ("任务总数量：%s\n"%total)
        print ("线程处理量：%s\n"%threadAlbum)
        print ("启动线程数：%s\n"%instance)
        print ("运行总耗时：%s\n"%str(endtime - starttime))

    except KeyboardInterrupt:

        sys.exit()

if __name__ == "__main__":

    #空列表下载全部，否则下载指定ID专辑
    downAlbum =[]

    print("请输入专辑ID（多个请使用半角逗号分隔）\n")
    print("下载指定分类全部专辑，请直接按回车键\n")
    aList = input("请输入专辑ID：")
    aList = aList.split(",")
    for album in aList:
        try:
            downAlbum.append(int(album))
        except:
            pass
        
    os.chdir(sys.path[0])

    main(downAlbum)
