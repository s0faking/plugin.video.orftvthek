#!/usr/bin/python
# -*- coding: utf-8 -*-

import urllib,urllib2,re,xbmcplugin,xbmcgui,sys,xbmcaddon,base64,socket,datetime,time,os,os.path,urlparse
from BeautifulSoup import BeautifulSoup 

try:
   import StorageServer
except:
   import storageserverdummy as StorageServer
   
cache = StorageServer.StorageServer("plugin.video.orftvthek", 999999)

version = "0.2.0"
plugin = "ORF-TVthek-" + version
author = "sofaking"
 


socket.setdefaulttimeout(30)
settings = xbmcaddon.Addon(id='plugin.video.orftvthek') 
pluginhandle = int(sys.argv[1])
basepath = settings.getAddonInfo('path')


base_url="http://tvthek.orf.at"

if xbmc.getSkinDir() == 'skin.confluence':
   defaultViewMode = 'Container.SetViewMode(503)'
else:
   defaultViewMode = 'Container.SetViewMode(518)'

defaultbackdrop = os.path.join(basepath,"fanart.jpg")
defaultbanner = "http://goo.gl/FG03G"
defaultlogo = "http://goo.gl/FRLJK"

forceView = settings.getSetting("forceView") == "true"

opener = urllib2.build_opener()
opener.addheaders = [('User-agent', 'Mozilla/5.0')]
playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO) 

def parameters_string_to_dict(parameters):
        paramDict = {}
        if parameters:
            paramPairs = parameters[1:].split("&")
            for paramsPair in paramPairs:
                paramSplits = paramsPair.split('=')
                if (len(paramSplits)) == 2:
                    paramDict[paramSplits[0]] = paramSplits[1]
        return paramDict

def createListItem(name,banner,summary,runtime,backdrop,videourl,playable,folder):
        if backdrop == '':
               backdrop = defaultbackdrop
        if banner == '':
               banner = defaultbanner
        liz=xbmcgui.ListItem(name, iconImage=banner, thumbnailImage=banner)
        liz.setInfo( type="Video", infoLabels={ "Title": name } )
        liz.setInfo( type="Video", infoLabels={ "Plot": summary } )
        liz.setInfo( type="Video", infoLabels={ "Plotoutline": summary } )
        liz.setInfo( type="Video", infoLabels={ "tvshowtitle": name } )
        liz.setInfo( type="Video", infoLabels={ "Runtime": runtime } )
        liz.setProperty('fanart_image',backdrop)
        liz.setProperty('IsPlayable', playable)
        xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=videourl, listitem=liz, isFolder=folder)


def addFile(name,videourl,banner,summary,runtime,backdrop):
        createListItem(name,banner,summary,runtime,backdrop,videourl,'true',False)

def addDirectory(title,banner,backdrop,link,mode):
        parameters = {"link" : link,"title" : title,"banner" : banner,"backdrop" : backdrop, "mode" : mode}
        u = sys.argv[0] + '?' + urllib.urlencode(parameters)
        createListItem(title,banner,title,title,backdrop,u,'false',True)

def getLinks(url):
    url = urllib.unquote(url)
    arrayReg = re.compile("{.*?}")
    html = opener.open(url)
    html = html.read()
    soup = BeautifulSoup(html)
    videobox = soup.find('div',{'class':'player_viewport'})
    data = videobox.findAll('div')
    videoUrls = []
    array = arrayReg.findall(str(data[len(data)-2]))
	#Get Links from JS div
    for item in array:
        split = item.replace("{","").replace("}","").replace(",","").replace(":","").replace("\/","/").split('"')
        if split[0] == "quality":
            print "BOOM"
        if split[1] == "quality" and split[3] == "Q6A":
            if len(split) > 13 and split[21] == "protocol" and split[23] == "http":
                if split[9] == "src":
                    path = urlparse.urlparse(split[11]).path
                    ext = os.path.splitext(path)[1]
                    if ext == ".mp4":
                        videoUrls.append(str(split[11]).replace("http//",'http://'))
    descbox = soup.find('div',{'class':'base_list_wrapper mod_playlist'})
    if descbox != None:
        videoDescs = []
        details = descbox.findAll('div',{'class':'details'})
        for detail in details:
            videoDescs.append(detail.text.encode('UTF-8'))
        videoTitles = []
        titles = descbox.findAll('h4',{'class':'base_list_item_headline'})
        for title in titles:
	        videoTitles.append(title.text.encode('UTF-8'))
        i = 0
        for url in videoTitles:
            addFile(videoTitles[i],videoUrls[i],"",videoDescs[i],"",defaultbackdrop)
            i = i + 1
    else:
        title = soup.find('h3',{'class':'video_headline'}).text.encode('UTF-8')
        desc = soup.find('div',{'class':'details_description'}).text.encode('UTF-8')
        link = videoUrls[0]
        addFile(title,link,"",desc,"",defaultbackdrop)
    xbmcplugin.setContent(pluginhandle,'episodes')
    xbmcplugin.endOfDirectory(pluginhandle)
    if forceView:
       xbmc.executebuiltin(defaultViewMode)
    

def getMainMenu():
    addDirectory("Neuste Sendungen",defaultbanner,defaultbackdrop,"","getNewShows")
    addDirectory("Aktuell",defaultbanner,defaultbackdrop,"","getAktuelles")
    addDirectory("Sendungen",defaultbanner,defaultbackdrop,"","getSendungen")
    addDirectory("Themen",defaultbanner,defaultbackdrop,"","getThemen")
    addDirectory("Live",defaultbanner,defaultbackdrop,"","getLive")
    addDirectory("ORF Tipps",defaultbanner,defaultbackdrop,"","getTipps")
    addDirectory("Meist gesehen",defaultbanner,defaultbackdrop,"","getMostViewed")
    #addDirectory("Sendung verpasst?",defaultbanner,defaultbackdrop,"","getArchiv")
    addDirectory("Suchen",defaultbanner,defaultbackdrop,"","searchPhrase")
    xbmcplugin.setContent(pluginhandle,'episodes')
    xbmcplugin.endOfDirectory(pluginhandle)
    if forceView:
       xbmc.executebuiltin(defaultViewMode)
    xbmcplugin.setPluginFanart(int(sys.argv[1]), defaultbackdrop, color2='0xFFFF3300')

def getCategoryList(category):
    progressbar = xbmcgui.DialogProgress()
    progressbar.create('Ladevorgang' )
    progressbar.update(0)

    url =  urllib.unquote(category)
    html = opener.open(url)
    html = html.read()
    soup = BeautifulSoup(html)
	
	
    showname = soup.find('h3',{'class':'video_headline'}).text.encode('UTF-8')
    new = soup.find('header',{'class':'player_header'}).find('div',{'class':'broadcast_information'})
    new_duration = new.find('span',{'class':'meta meta_duration'}).text.encode('UTF-8')
    new_date = new.find('span',{'class':'meta meta_date'}).text.encode('UTF-8')
    new_time = new.find('span',{'class':'meta meta_time'}).text.encode('UTF-8')
    new_link = url
    new_title = "%s - %s %s (%s)" % (showname,new_date,new_time,new_duration)
	

    addDirectory(new_title,defaultbanner,defaultbackdrop,new_link,"openSeries")
	
    progressbar.update(15)
    latest = soup.find('div',{'class':'base_list_wrapper mod_latest_episodes'})
    if latest != None:
      latestbox = latest.findAll('li',{'class':'base_list_item'})
      feedcount = len(latestbox)
      i = 1
      for item in latestbox:
        i = i+1
        percent = i*100/feedcount
        progressbar.update(percent)
        duration = item.find('span',{'class':'meta meta_duration'}).text.encode('UTF-8')
        date = item.find('span',{'class':'meta meta_date'}).text.encode('UTF-8')
        time = item.find('span',{'class':'meta meta_time'}).text.encode('UTF-8')
        title = "%s - %s %s (%s)" % (showname,date,time,duration)
        link = item.find('a')['href']
		
        addDirectory(title,defaultbanner,defaultbackdrop,link,"openSeries")
    xbmcplugin.setContent(pluginhandle,'episodes')
    xbmcplugin.endOfDirectory(pluginhandle)
    if forceView:
       xbmc.executebuiltin(defaultViewMode)


def getLiveStreams():
    url = "http://tvthek.orf.at/live"
    liveurls = {}
    liveurls['ORF1'] = "http://apasfiisl.apa.at/ipad/orf1_q4a/orf.sdp/playlist.m3u8";
    liveurls['ORF2'] = "http://apasfiisl.apa.at/ipad/orf2_q6a/orf.sdp/playlist.m3u8";
    liveurls['ORF3'] = "http://apasfiisl.apa.at/ipad/orf2e_q6a/orf.sdp/playlist.m3u8";
    liveurls['ORFS'] = "http://apasfiisl.apa.at/ipad/orfs_q6a/orf.sdp/playlist.m3u8";
	
    html = opener.open(url)
    html = html.read()
    soup = BeautifulSoup(html)
	
    epg = soup.find('ul',{'class':'base_list epg'})
    epgbox = epg.findAll('li',{'class':re.compile(r'\bbase_list_item program\b')})
    for item in epgbox:
        program = item.get('class', []).split(" ")[2].encode('UTF-8').upper()
        
        title = item.find('h4').text.encode('UTF-8')
        time = item.find('div',{'class':'broadcast_information'}).find('span').text.encode('UTF-8').replace("Uhr","").replace(".",":").strip()
        link = liveurls[program]
        
        title = "[%s] %s (%s)" % (program,title,time)
        addFile(title,link,"","","",defaultbackdrop)
    xbmcplugin.setContent(pluginhandle,'episodes')
    xbmcplugin.endOfDirectory(pluginhandle)
    if forceView:
       xbmc.executebuiltin(defaultViewMode)

def getRecentlyAdded():
    progressbar = xbmcgui.DialogProgress()
    progressbar.create('Ladevorgang' )
    progressbar.update(0)
    html = opener.open(base_url)
    html = html.read()
    soup = BeautifulSoup(html)
    teaserbox = soup.findAll('a',{'class':'item_inner'})
    feedcount = len(teaserbox)
    i = 0
    for teasers in teaserbox:
        if progressbar.iscanceled() :
            xbmcplugin.endOfDirectory(pluginhandle)
            progressbar.close()
            break
        i = i+1
        percent = i*100/feedcount
        progressbar.update(percent)
        title = teasers.find('h3',{'class':'item_title'}).text.encode('UTF-8')
        desc = teasers.find('div',{'class':'item_description'}).text.encode('UTF-8')
        image = teasers.find('img')['src']
        link = teasers['href'] 
        backdrop = ""
        backdropFile = os.path.join(backdroppath, "%s.jpg" % title.replace(" ","."))
        if os.path.isfile(backdropFile):
                  backdrop = backdropFile
        parameters = {"link" : link,"title" : title,"banner" : image,"backdrop" : backdrop, "mode" : "openSeries"}
        u = sys.argv[0] + '?' + urllib.urlencode(parameters)
        createListItem(title,image,desc,title,backdrop,u,'false',True)
    xbmcplugin.setContent(pluginhandle,'episodes')
    xbmcplugin.endOfDirectory(pluginhandle)
    if forceView:
       xbmc.executebuiltin(defaultViewMode)


def getThemenListe(url):
    progressbar = xbmcgui.DialogProgress()
    progressbar.create('Ladevorgang' )
    progressbar.update(0)
    url = urllib.unquote(url)
    html = opener.open(url)
    html = html.read()
    soup = BeautifulSoup(html)
	
    content = soup.find('section',{'class':'mod_container_list'})
    topics = soup.findAll('article',{'class':'item'})
	
    i = 1
    feedcount = len(topics)
    for topic in topics:
        if progressbar.iscanceled() :
            xbmcplugin.endOfDirectory(pluginhandle)
            progressbar.close()
            break
        i = i+1
        percent = i*100/feedcount
        progressbar.update(percent)
            
        title = topic.find('h4',{'class':'item_title'}).text.encode('UTF-8')
        link = topic.find('a')['href'].encode('UTF-8')
        image = topic.find('img')
        if image != None:
            image = image['src'].encode('UTF-8')
        else:
            image = ''
        desc = topic.find('div',{'class':'item_description'})
        if desc != None:
            desc = desc.text.encode('UTF-8')
        else:
            desc = 'Keine Beschreibung verfügbar'
        date = topic.find('time').text.encode('UTF-8')
        time = topic.find('span',{'class':'meta meta_duration'}).text.encode('UTF-8')
		
        desc = "Datum: %s \nDauer: %s \n\n%s" % (date,time,desc)
		
        parameters = {"link" : link,"title" : title,"banner" : image,"backdrop" : defaultbackdrop, "mode" : "openSeries"}
        u = sys.argv[0] + '?' + urllib.urlencode(parameters)
        createListItem(title,image,desc,title,backdrop,u,'false',True)
    xbmcplugin.setContent(pluginhandle,'episodes')
    xbmcplugin.endOfDirectory(pluginhandle)
    if forceView:
       xbmc.executebuiltin(defaultViewMode)

def playFile():
    player = xbmc.Player(xbmc.PLAYER_CORE_DVDPLAYER)
    player.play(playlist)
    if not player.isPlayingVideo():
        d = xbmcgui.Dialog()
        d.ok('VIDEO QUEUE EMPTY', 'The XBMC video queue is empty.','Add more links to video queue.')




def getThemen():
    progressbar = xbmcgui.DialogProgress()
    progressbar.create('Ladevorgang' )
    progressbar.update(15)
	
    url = "http://tvthek.orf.at/topics"
    html = opener.open(url)
    html = html.read()
    soup = BeautifulSoup(html)
    
    
    content = soup.find('section',{'class':'mod_container_list'})
    topics = soup.findAll('section',{'class':'item_wrapper'})
    feedcount = len(topics)
    i = 1
    for topic in topics:
        if progressbar.iscanceled() :
                xbmcplugin.endOfDirectory(pluginhandle)
                progressbar.close()
                break
        i = i+1
        percent = i*100/feedcount
        progressbar.update(percent)
		
        title = topic.find('h3').text.encode('UTF-8')
        link = topic.find('a',{'class':'more service_link service_link_more'})['href'].encode('UTF-8')
        image = topic.find('img')['src'].replace("width=395","width=500").replace("height=209.07070707071","height=265").encode('UTF-8')
        desc = ""    
        parameters = {"link" : link,"title" : title,"banner" : image,"backdrop" : defaultbackdrop, "mode" : "openTopicPosts"}
        u = sys.argv[0] + '?' + urllib.urlencode(parameters)
        createListItem(title,image,desc,title,defaultbackdrop,u,'false',True)
    xbmcplugin.setContent(pluginhandle,'episodes')
    xbmcplugin.endOfDirectory(pluginhandle)
    if forceView:
        xbmc.executebuiltin(defaultViewMode)

def getCategories():
    html = opener.open(base_url)
    html = html.read()
    soup = BeautifulSoup(html)
    
    slideview = soup.find('div',{'class':'mod_carousel'})
    catbox = slideview.findAll('a',{'class':'carousel_item_link'})
    for cat in catbox:
        link = cat['href']
        title = programUrlTitle(link)
        image = cat.find('img')['src'].replace("height=56.34328358209","height=280").replace("width=100","width=500")
        parameters = {"title" : title.encode('UTF-8'),"mode" : "openCategoryList","category" : link}
        u = sys.argv[0] + '?' + urllib.urlencode(parameters)
        createListItem(title,image,"","",defaultbackdrop,u,'false',True)
    xbmcplugin.setContent(pluginhandle,'episodes')
    xbmcplugin.endOfDirectory(pluginhandle)
    if forceView:
        xbmc.executebuiltin(defaultViewMode)

def programUrlTitle(url):
    title = url.replace(base_url,"").split("/")
    return title[2].replace("-"," ")
		
def search():
    addDirectory("Suchen ...",defaultbanner,defaultbackdrop,"","searchNew")
    cache.table_name = "searchhistory"
    some_dict = cache.get("searches").split("|")
    for str in reversed(some_dict):
        addDirectory(str,defaultbanner,defaultbackdrop,str.replace(" ","+"),"searchNew")
    xbmcplugin.setContent(pluginhandle,'episodes')
    xbmcplugin.endOfDirectory(pluginhandle)
    if forceView:
       xbmc.executebuiltin(defaultViewMode)
    xbmcplugin.setPluginFanart(int(sys.argv[1]), defaultbackdrop, color2='0xFFFF3300')
	
def searchTV():
    keyboard = xbmc.Keyboard('')
    keyboard.doModal()
    if (keyboard.isConfirmed()):
      cache.table_name = "searchhistory"
      keyboard_in = keyboard.getText()
      some_dict = cache.get("searches") + "|"+keyboard_in
      cache.set("searches",some_dict);
      searchurl = "%s/search?q=%s"%(base_url,keyboard_in.replace(" ","+"))
      getTipps(searchurl)
    else:
      addDirectory("Keine Ergebnisse",defaultlogo,defaultbackdrop,"","")
    xbmcplugin.setContent(pluginhandle,'episodes')
    xbmcplugin.endOfDirectory(pluginhandle)
    if forceView:
        xbmc.executebuiltin(defaultViewMode)

def getTipps(url):
    url = urllib.unquote(url)
    progressbar = xbmcgui.DialogProgress()
    progressbar.create('Ladevorgang' )
    progressbar.update(0)

    html = opener.open(url)
    html = html.read()
    soup = BeautifulSoup(html)
    tipps = soup.findAll('article',{'class':'item'})
    i = 1
    feedcount = len(tipps)
    for tip in tipps:
        if progressbar.iscanceled() :
            xbmcplugin.endOfDirectory(pluginhandle)
            progressbar.close()
            break
        i = i+1
        percent = i*100/feedcount
        progressbar.update(percent)
        title = tip.find('h4',{'class':'item_title'}).text.encode('UTF-8')
        desc = tip.find('div',{'class':'item_description'})
        if desc != None:
            desc = desc.text.encode('UTF-8')
            date = tip.find('time',{'class':'meta meta_date'}).text.encode('UTF-8')
            time = tip.find('span',{'class':'meta meta_time'}).text.encode('UTF-8')
            title = "%s | %s %s" % (title,date,time)
        else:
            desc = "Keine Beschreibung"
            
        image = tip.find('img')['src'].replace("width=395","width=500").replace("height=209.07070707071","height=265")
        link = tip.find('a')['href']
        parameters = {"link" : link,"title" : title,"banner" : image,"backdrop" : defaultbackdrop, "mode" : "openSeries"}
        u = sys.argv[0] + '?' + urllib.urlencode(parameters)
        createListItem(title,image,desc,title,backdrop,u,'false',True)
    xbmcplugin.setContent(pluginhandle,'episodes')
    xbmcplugin.endOfDirectory(pluginhandle)
    if forceView:
       xbmc.executebuiltin(defaultViewMode)
		
		
def searchTVHistory(link):
    keyboard = xbmc.Keyboard(link)
    keyboard.doModal()
    if (keyboard.isConfirmed()):
      cache.table_name = "searchhistory"
      keyboard_in = keyboard.getText()
      if keyboard_in != link:
           some_dict = cache.get("searches") + "|"+keyboard_in
           cache.set("searches",some_dict);
      searchurl = "%s/search?q=%s"%(base_url,keyboard_in.replace(" ","+"))
      getTipps(searchurl)
    else:
      addDirectory("Keine Ergebnisse",defaultlogo,defaultbackdrop,"","")
    xbmcplugin.setContent(pluginhandle,'episodes')
    xbmcplugin.endOfDirectory(pluginhandle)
    if forceView:
        xbmc.executebuiltin(defaultViewMode)
    
	
#Getting Parameters
params=parameters_string_to_dict(sys.argv[2])
mode=params.get('mode')
title=params.get('title')
link=params.get('link')
logo=params.get('logo')
category=params.get('category')
backdrop=params.get('backdrop')


if mode == 'openSeries':
    getLinks(link)
elif mode == 'openShowList':
    getMoreShows(link,logo,backdrop)
elif mode == 'openCategoryList':
    getCategoryList(category)
elif mode == 'getSendungen':
    getCategories()
elif mode == 'getAktuelles':
    getRecentlyAdded()
elif mode == 'getLive':
    getLiveStreams()
elif mode == 'getTipps':
    getTipps("http://tvthek.orf.at/tips")
elif mode == 'getNewShows':
    getTipps("http://tvthek.orf.at/newest")
elif mode == 'getMostViewed':
    getTipps('http://tvthek.orf.at/most_viewed')
elif mode == 'getThemen':
    getThemen()
elif mode == 'openTopicPosts':
    getThemenListe(link)
elif mode == 'playVideo':
    playFile()
elif mode == 'playList':
    playFile()
elif mode == 'getArchiv':
    getArchiv(schedule_url)
elif mode == 'openArchiv':
    openArchiv(link)
elif mode == 'searchPhrase':
    search()
elif mode == 'searchNew':
    if not link == None:
        searchTVHistory(urllib.unquote(link));
    else:
        searchTV()
	
else:
    getMainMenu()
