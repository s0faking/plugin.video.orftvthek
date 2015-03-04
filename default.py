#!/usr/bin/python
# -*- coding: utf-8 -*-

import urllib,urllib2,re,xbmcplugin,xbmcgui,sys,xbmcaddon,base64,socket,datetime,time,os,os.path,urlparse,json
import CommonFunctions as common

from resources.lib.scrapers.serviceapi import *
from resources.lib.scrapers.htmlscraper import *

try:
   import StorageServer
except:
   import storageserverdummy as StorageServer

socket.setdefaulttimeout(30) 
cache = StorageServer.StorageServer("plugin.video.orftvthek", 999999)

version = "0.3.3"
plugin = "ORF-TVthek-" + version
author = "sofaking"

#initial
common.plugin = plugin
settings = xbmcaddon.Addon(id='plugin.video.orftvthek') 
pluginhandle = int(sys.argv[1])
basepath = settings.getAddonInfo('path')
translation = settings.getLocalizedString

current_skin = xbmc.getSkinDir();

if 'confluence' in current_skin:
   defaultViewMode = 'Container.SetViewMode(503)'
else:
   defaultViewMode = 'Container.SetViewMode(518)'

thumbViewMode = 'Container.SetViewMode(500)'
smallListViewMode = 'Container.SetViewMode(51)'
playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO) 
 
#hardcoded
video_quality_list = ["Q1A", "Q4A", "Q6A"]
videoProtocol = "http"
videoDelivery = "progressive"

#media resources
resource_path = os.path.join( basepath, "resources" )
media_path = os.path.join( resource_path, "media" )
defaultbanner =  os.path.join(media_path,"default_banner.jpg")
news_banner =  os.path.join(media_path,"news_banner.jpg")
recently_added_banner =  os.path.join(media_path,"recently_added_banner.jpg")
shows_banner =  os.path.join(media_path,"shows_banner.jpg")
topics_banner =  os.path.join(media_path,"topics_banner.jpg")
live_banner =  os.path.join(media_path,"live_banner.jpg")
tips_banner =  os.path.join(media_path,"tips_banner.jpg")
most_popular_banner =  os.path.join(media_path,"most_popular_banner.jpg")
archive_banner =  os.path.join(media_path,"archive_banner.jpg")
search_banner =  os.path.join(media_path,"search_banner.jpg")
trailer_banner =  os.path.join(media_path,"trailer_banner.jpg")
defaultbackdrop = os.path.join(media_path,"fanart_top.png")

#load settings
forceView = settings.getSetting("forceView") == "true"
useServiceAPI = settings.getSetting("useServiceAPI") == "true"
autoPlay = settings.getSetting("autoPlay") == "true"
videoQuality = settings.getSetting("videoQuality")
try:
    videoQuality = video_quality_list[int(videoQuality)]
except:
    videoQuality = video_quality_list[2]
    


#init scrapers
jsonScraper = serviceAPI(xbmc,settings,pluginhandle,videoQuality,videoProtocol,videoDelivery,defaultbanner,defaultbackdrop)
htmlScraper = htmlScraper(xbmc,settings,pluginhandle,videoQuality,videoProtocol,videoDelivery,defaultbanner,defaultbackdrop)


def getMainMenu():
    addDirectory((translation(30000)).encode("utf-8"),recently_added_banner,"","","getNewShows")
    addDirectory((translation(30001)).encode("utf-8"),news_banner,"","","getAktuelles")
    addDirectory((translation(30002)).encode("utf-8"),shows_banner,"","","getSendungen")
    addDirectory((translation(30003)).encode("utf-8"),topics_banner,"","","getThemen")
    addDirectory((translation(30004)).encode("utf-8"),live_banner,"","","getLive")
    addDirectory((translation(30005)).encode("utf-8"),tips_banner,"","","getTipps")
    addDirectory((translation(30006)).encode("utf-8"),most_popular_banner,"","","getMostViewed")
    addDirectory((translation(30018)).encode("utf-8"),archive_banner,"","","getArchiv")
    addDirectory((translation(30007)).encode("utf-8"),search_banner,"","","searchPhrase")
    addDirectory((translation(30027)).encode("utf-8"),trailer_banner,"","","openTrailers")
    listCallback(False,thumbViewMode)

def createListItem(title,banner,description,duration,date,channel,videourl,playable,folder,subtitles=None): 
    if banner == '':
        banner = defaultbanner
    if description == '':
        description = (translation(30008)).encode("utf-8")
    liz=xbmcgui.ListItem(title, iconImage=banner, thumbnailImage=banner)
    liz.setInfo( type="Video", infoLabels={ "Title": title } )
    liz.setInfo( type="Video", infoLabels={ "Tvshowtitle": title } )
    liz.setInfo( type="Video", infoLabels={ "Sorttitle": title } )
    liz.setInfo( type="Video", infoLabels={ "Plot": description } )
    liz.setInfo( type="Video", infoLabels={ "Plotoutline": description } )
    liz.setInfo( type="Video", infoLabels={ "Aired": date } )
    liz.setInfo( type="Video", infoLabels={ "Studio": channel } )
    liz.setProperty('fanart_image',defaultbackdrop)
    liz.setProperty('IsPlayable', playable)
    
    if not folder:
        try:
            liz.addStreamInfo('video', { 'codec': 'h264','duration':int(duration) ,"aspect": 1.78, "width": 640, "height": 360})
        except:
            liz.addStreamInfo('video', { 'codec': 'h264',"aspect": 1.78, "width": 640, "height": 360})
        liz.addStreamInfo('audio', {"codec": "aac", "language": "de", "channels": 2})
        if subtitles != None:
            liz.addStreamInfo('subtitle', {"language": "de"})
            liz.setSubtitles(subtitles)        

    xbmcplugin.addDirectoryItem(handle=pluginhandle, url=videourl, listitem=liz, isFolder=folder)
    return liz
    
def parameters_string_to_dict(parameters):
    paramDict = {}
    if parameters:
        paramPairs = parameters[1:].split("&")
        for paramsPair in paramPairs:
            paramSplits = paramsPair.split('=')
            if (len(paramSplits)) == 2:
                paramDict[paramSplits[0]] = paramSplits[1]
    return paramDict

def cleanText(string):
    string = string.replace('\\n', '').replace("&#160;"," ").replace("&quot;","'").replace('&amp;', '&').replace('&#039;', '´')
    return string
    
def addItemDirectories(list):
    for item in list:
        addDirectory(item['title'],item['image'],item['desc'],item['link'],item['mode'])
     

def addFile(name,videourl,banner,summary,runtime,backdrop):
    createListItem(name,banner,summary,runtime,'','',videourl,'true',False,'')

def addDirectory(title,banner,description,link,mode):
    parameters = {"link" : link,"title" : cleanText(title),"banner" : banner,"backdrop" : defaultbackdrop, "mode" : mode}
    u = sys.argv[0] + '?' + urllib.urlencode(parameters)
    createListItem(title,banner,description,'','','',u,'false',True)
	
def listCallback(sort,viewMode=defaultViewMode):
    xbmcplugin.setContent(pluginhandle,'episodes')
    if sort:
        xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_VIDEO_TITLE)
    xbmcplugin.endOfDirectory(pluginhandle)
    if forceView:
        xbmc.executebuiltin(viewMode)



	
def openArchiv(url):
    url =  urllib.unquote(url)
    html = common.fetchPage({'link': url})
    teasers = common.parseDOM(html.get("content"),name='a',attrs={'class': 'item_inner.clearfix'})
    teasers_href = common.parseDOM(html.get("content"),name='a',attrs={'class': 'item_inner.clearfix'},ret="href")

    i = 0
    for teaser in teasers:
        link = teasers_href[i]
        i = i+1
        
        title = common.parseDOM(teaser,name='h4',attrs={'class': "item_title"},ret=False)
        title = common.replaceHTMLCodes(title[0]).encode("utf-8")
        
        time = common.parseDOM(teaser,name='span',attrs={'class': "meta.meta_time"},ret=False)
        time = common.replaceHTMLCodes(time[0]).encode("utf-8")
		
        title = "["+time+"] "+title
		
        description = common.parseDOM(teaser,name='div',attrs={'class': "item_description"},ret=False)
        if len(description) > 0 :
            description = common.replaceHTMLCodes(description[0])
        else:
            description = translation(30008).encode('UTF-8')
            
        banner = common.parseDOM(teaser,name='img',ret='src')
        banner = common.replaceHTMLCodes(banner[1]).encode("utf-8")
        
        banner = common.parseDOM(teaser,name='img',ret='src')
        banner = common.replaceHTMLCodes(banner[1]).encode("utf-8")
		
        addDirectory(title,banner,description,link,"openSeries")
    listCallback(True)

def playFile():
    player = xbmc.Player()
    player.play(playlist)
    if not player.isPlayingVideo():
        d = xbmcgui.Dialog()
        d.ok('VIDEO QUEUE EMPTY', 'The XBMC video queue is empty.','Add more links to video queue.')
		
def search():
    addDirectory((translation(30007)).encode("utf-8")+" ...",defaultbanner,' ',"","searchNew")
    cache.table_name = "searchhistory"
    some_dict = cache.get("searches").split("|")
    for str in reversed(some_dict):
        if str.strip() != '':
            addDirectory(str.encode('UTF-8'),defaultbanner," ",str.replace(" ","+"),"searchNew")
    listCallback(False)
	
def searchTV():
    keyboard = xbmc.Keyboard('')
    keyboard.doModal()
    if (keyboard.isConfirmed()):
      cache.table_name = "searchhistory"
      keyboard_in = keyboard.getText()
      some_dict = cache.get("searches") + "|"+keyboard_in
      cache.set("searches",some_dict);
      searchurl = "%s/search?q=%s"%(base_url,keyboard_in.replace(" ","+").replace("Ö","O").replace("ö","o").replace("Ü","U").replace("ü","u").replace("Ä","A").replace("ä","a"))
      searchurl = searchurl
      getTableResults(searchurl)
    else:
      addDirectory((translation(30014)).encode("utf-8"),defaultbanner,"","","")
    listCallback(False)
				
def searchTVHistory(link):
    keyboard = xbmc.Keyboard(link)
    keyboard.doModal()
    if (keyboard.isConfirmed()):
        cache.table_name = "searchhistory"
        keyboard_in = keyboard.getText()
        if keyboard_in != link:
            some_dict = cache.get("searches") + "|"+keyboard_in
            cache.set("searches",some_dict);
        searchurl = "%s?q=%s"%(search_base_url,keyboard_in.replace(" ","+"))
        getTableResults(searchurl)
    else:
        addDirectory((translation(30014)).encode("utf-8"),defaultbanner,defaultbackdrop,"","")
    listCallback(False)
    	
#parameters
params=parameters_string_to_dict(sys.argv[2])
mode=params.get('mode')
title=params.get('title')
link=params.get('link')
banner=params.get('banner')
backdrop=params.get('backdrop')

#modes
if mode == 'openSeries':
    playlist = htmlScraper.getLinks(link,banner,playlist,autoPlay)
    if autoPlay and playlist != None:
        xbmc.Player().play(playlist)
    listCallback(False)
elif mode == 'getSendungen':
    if useServiceAPI:
        jsonScraper.getCategories()
    else:
        htmlScraper.getCategories()
    listCallback(True,thumbViewMode)
elif mode == 'getAktuelles':
    if useServiceAPI:
        jsonScraper.getTableResults(jsonScraper.serviceAPIHighlights)
    else:
        htmlScraper.getRecentlyAdded(htmlScraper.base_url)
    listCallback(False)
elif mode == 'getLive':
    if useServiceAPI:
        jsonScraper.getLiveStreams()
    else:
        htmlScraper.getLiveStreams()
    listCallback(False,smallListViewMode)
elif mode == 'getTipps':
    if useServiceAPI:
        jsonScraper.getTableResults(jsonScraper.serviceAPITip)
    else:
        htmlScraper.getTableResults(htmlScraper.tip_url)
    listCallback(False)
elif mode == 'getNewShows':
    if useServiceAPI:
        jsonScraper.getTableResults(jsonScraper.serviceAPIRecent)
    else:
        htmlScraper.getTableResults(htmlScraper.recent_url)
    listCallback(False)
elif mode == 'getMostViewed':
    if useServiceAPI:
        jsonScraper.getTableResults(jsonScraper.serviceAPIViewed)
    else:
        htmlScraper.getTableResults(htmlScraper.mostviewed_url)
    listCallback(False)
elif mode == 'getThemen':
    if useServiceAPI:
        jsonScraper.getThemen()
    else:
        htmlScraper.getThemen()
    listCallback(True)
elif mode == 'getSendungenDetail':
    htmlScraper.getCategoriesDetail(link,banner)
    listCallback(False)
elif mode == 'getThemenDetail':
    htmlScraper.getThemenDetail(link)
    listCallback(False)
elif mode == 'playVideo':
    playFile()
elif mode == 'playList':
    playFile()
elif mode == 'getArchiv':
    if useServiceAPI:
        jsonScraper.getArchiv()
    else:
        htmlScraper.getArchiv(htmlScraper.schedule_url)
    listCallback(False)
elif mode == 'openArchiv':
    openArchiv(link)
elif mode == 'openTrailers':
    getTrailers()
elif mode == 'searchPhrase':
    search()
elif mode == 'searchNew':
    if not link == None:
        searchTVHistory(urllib.unquote(link));
    else:
        searchTV()
elif mode == 'openDate':
    getDate(link, params.get('from'))
elif mode == 'openProgram':
    jsonScraper.getProgram(link,playlist)
    listCallback(False)
elif mode == 'openTopic':
    jsonScraper.getTopic(link)
    listCallback(False)
elif mode == 'openEpisode':
    jsonScraper.getEpisode(link,playlist)
    listCallback(False)
elif mode == 'openSegment':
    getSegment(link, params.get('segmentID'))
elif mode == 'liveStreamNotOnline':
    url = serviceAPIEpisode % (serviceAPItoken, link)
    response = urllib2.urlopen(url)
    result = json.loads(response.read())['episodeDetail']

    title       = result.get('title').encode('UTF-8')
    image       = JSONImage(result.get('images'))
    description = JSONDescription(result.get('descriptions'))
    duration    = result.get('duration')
    date        = time.strptime(result.get('date'), '%d.%m.%Y %H:%M:%S')
    subtitles   = None # result.get('subtitlesSrtFileUrl')

    dialog = xbmcgui.Dialog()
    if dialog.yesno('Livestream noch nicht gestartet', 'Der Livestream startet erst um %s.\nSoll der Livesteam automatisch starten?' % time.strftime('%H:%M', date)):
        sleepTime = int(time.mktime(date) - time.mktime(time.localtime()))
        dialog.notification('Sleep till start', 'Spleeptime: %s' % sleepTime)
        xbmc.sleep(sleepTime * 1000)
        if dialog.yesno('', 'Den Livestream Starten?'):
            xbmc.Player().play(urllib.unquote(link))

            # find the livestreamStreamingURL
            livestreamStreamingURLs = []
            for streamingURL in result.get('livestreamStreamingUrls'):
                if '.m3u' in streamingURL.get('streamingUrl'):
                    livestreamStreamingURLs.append(streamingURL.get('streamingUrl'))

            livestreamStreamingURLs.sort()
            streamingURL = livestreamStreamingURLs[len(livestreamStreamingURLs) - 1].replace('q4a', videoQuality)
            listItem = createListItem(title, image, description, duration, time.strftime('%Y-%m-%d', date), '', streamingURL, 'true', False, subtitles)
            xbmc.Player().play(streamingURL, listItem)
else:
    getMainMenu()
