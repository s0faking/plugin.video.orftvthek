#!/usr/bin/python
# -*- coding: utf-8 -*-

import urllib,urllib2,re,xbmcplugin,xbmcgui,sys,xbmcaddon,base64,socket,datetime,time,os,os.path,urlparse,json
import CommonFunctions as common

from resources.lib.base import *
from resources.lib.helpers import *
from resources.lib.serviceapi import *
from resources.lib.htmlscraper import *

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
useSubtitles = settings.getSetting("useSubtitles") == "true"
videoQuality = settings.getSetting("videoQuality")

try:
    videoQuality = video_quality_list[int(videoQuality)]
except:
    videoQuality = video_quality_list[2]
    


#init scrapers
jsonScraper = serviceAPI(xbmc,settings,pluginhandle,videoQuality,videoProtocol,videoDelivery,defaultbanner,defaultbackdrop,useSubtitles,defaultViewMode)
htmlScraper = htmlScraper(xbmc,settings,pluginhandle,videoQuality,videoProtocol,videoDelivery,defaultbanner,defaultbackdrop,useSubtitles,defaultViewMode)


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
    listCallback(False,thumbViewMode,pluginhandle)
    
    
def listCallback(sort,viewMode,pluginhandle):
    xbmcplugin.setContent(pluginhandle,'episodes')
    if sort:
        xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_VIDEO_TITLE)
    xbmcplugin.endOfDirectory(pluginhandle)
    if forceView:
        xbmc.executebuiltin(viewMode)

def addDirectory(title,banner,description,link,mode):
    parameters = {"link" : link,"title" : cleanText(title),"banner" : banner,"backdrop" : defaultbackdrop, "mode" : mode}
    u = sys.argv[0] + '?' + urllib.urlencode(parameters)
    createListItem(title,banner,description,'','','',u,'false',True,translation,defaultbackdrop,pluginhandle,None)
	
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
    listCallback(True,defaultViewMode,pluginhandle)
		
def search():
    addDirectory((translation(30007)).encode("utf-8")+" ...",defaultbanner,' ',"","searchNew")
    cache.table_name = "searchhistory"
    some_dict = cache.get("searches").split("|")
    for str in reversed(some_dict):
        if str.strip() != '':
            addDirectory(str.encode('UTF-8'),defaultbanner," ",str.replace(" ","+"),"searchNew")
    listCallback(False,defaultViewMode,pluginhandle)
	
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
    listCallback(False,defaultViewMode,pluginhandle)
				
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
    listCallback(False,defaultViewMode,pluginhandle)
    	
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
    listCallback(False,defaultViewMode,pluginhandle)
elif mode == 'getSendungen':
    if useServiceAPI:
        jsonScraper.getCategories()
    else:
        htmlScraper.getCategories()
    listCallback(True,thumbViewMode,pluginhandle)
elif mode == 'getAktuelles':
    if useServiceAPI:
        jsonScraper.getTableResults(jsonScraper.serviceAPIHighlights)
    else:
        htmlScraper.getRecentlyAdded(htmlScraper.base_url)
    listCallback(False,defaultViewMode,pluginhandle)
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
    listCallback(False,defaultViewMode,pluginhandle)
elif mode == 'getNewShows':
    if useServiceAPI:
        jsonScraper.getTableResults(jsonScraper.serviceAPIRecent)
    else:
        htmlScraper.getTableResults(htmlScraper.recent_url)
    listCallback(False,defaultViewMode,pluginhandle)
elif mode == 'getMostViewed':
    if useServiceAPI:
        jsonScraper.getTableResults(jsonScraper.serviceAPIViewed)
    else:
        htmlScraper.getTableResults(htmlScraper.mostviewed_url)
    listCallback(False,defaultViewMode,pluginhandle)
elif mode == 'getThemen':
    if useServiceAPI:
        jsonScraper.getThemen()
    else:
        htmlScraper.getThemen()
    listCallback(True,defaultViewMode,pluginhandle)
elif mode == 'getSendungenDetail':
    htmlScraper.getCategoriesDetail(link,banner)
    listCallback(False,defaultViewMode,pluginhandle)
elif mode == 'getThemenDetail':
    htmlScraper.getThemenDetail(link)
    listCallback(False,defaultViewMode,pluginhandle)
elif mode == 'playList':
    playFile()
elif mode == 'getArchiv':
    if useServiceAPI:
        jsonScraper.getArchiv()
    else:
        htmlScraper.getArchiv(htmlScraper.schedule_url)
    listCallback(False,defaultViewMode,pluginhandle)
elif mode == 'getArchivDetail':
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
    listCallback(False,defaultViewMode,pluginhandle)
elif mode == 'openProgram':
    jsonScraper.getProgram(link,playlist)
    listCallback(False,defaultViewMode,pluginhandle)
elif mode == 'openTopic':
    jsonScraper.getTopic(link)
    listCallback(False,defaultViewMode,pluginhandle)
elif mode == 'openEpisode':
    jsonScraper.getEpisode(link,playlist)
    listCallback(False,defaultViewMode,pluginhandle)
elif mode == 'openSegment':
    jsonScraper.getSegment(link, params.get('segmentID'))
    listCallback(False,defaultViewMode,pluginhandle)
elif mode == 'liveStreamNotOnline':
    jsonScraper.getLiveNotOnline(link)
    listCallback(False,defaultViewMode,pluginhandle)
else:
    getMainMenu()
