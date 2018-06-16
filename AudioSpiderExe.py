# Coding:uft-8
import os,sys
import AudioSpider

def getalbumList():

    def toInt(string):
        try:
            return int(album)
        except:

            return False
             
    albumList = []
    try:
        #引入命令行参数
        if len(sys.argv) > 1:
            fileName = sys.argv[1]
            
            if os.path.exists(fileName):
                print("导入文件内容：%s"%fileName)
        
                albumList = []
                file = open(fileName) 

                while True:

                    line = file.readline()

                    if not line: break
                            
                    aList = line.split(",")

                    for album in aList:

                        albumID = toInt(album)

                        if type(albumID) == int:

                            albumList.append(int(album))

                file.close()
            else:
                print("没有找到文件")

        else:
            print("请输入专辑ID（多个请使用半角逗号分隔）\n")
            print("下载指定分类全部专辑，请直接按回车键\n")
            aList = input("请输入专辑ID：")
            aList = aList.split(",")
            for album in aList:
                try:
                    albumList.append(int(album))
                except:
                    pass

    except KeyboardInterrupt:

        sys.exit()
        
    except:
       pass
                
    return albumList

if __name__ == "__main__":

    try:
        os.system("Title Audio Spider - 喜马拉雅FM")

        os.system("color 3f")

        downAlbum = getalbumList()

        AudioSpider.main(downAlbum)

        input ("按回车键退出\n")

    except KeyboardInterrupt:

        sys.exit()
