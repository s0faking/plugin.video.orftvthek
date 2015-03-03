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
videoProtocol = "http"
videoDelivery = "progressive"
video_quality_list = ["Q1A", "Q4A", "Q6A"]

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
videoQuality = settings.getSetting("videoQuality")
try:
    videoQuality = video_quality_list[int(videoQuality)]
except:
    videoQuality = video_quality_list[2]

#init scrapers
jsonScraper = serviceAPI(xbmc,settings);
htmlScraper = htmlScraper(xbmc,settings);


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


def getArchiv(url):
    useServiceAPI = True
    if useServiceAPI:
        for x in xrange(9):
            date  = datetime.datetime.now() - datetime.timedelta(days=x)
            title = '%s' % (date.strftime('%A, %d.%m.%Y'))
            parameters = {'mode' : 'openDate', 'link': date.strftime('%Y%m%d')}
            if x == 8:
                title = 'älter als %s' % title
                parameters = {'mode' : 'openDate', 'link': date.strftime('%Y%m%d'), 'from': (date - datetime.timedelta(days=150)).strftime('%Y%m%d')}
            u = sys.argv[0] + '?' + urllib.urlencode(parameters)
            createListItem(title, '', title, '', date.strftime('%Y-%m-%d'), '', u, 'False', True)

    else:
        html = common.fetchPage({'link': url})
        articles = common.parseDOM(html.get("content"),name='a',attrs={'class': 'day_wrapper'})
        articles_href = common.parseDOM(html.get("content"),name='a',attrs={'class': 'day_wrapper'},ret="href")
        i = 0
        
        for article in articles:
            link = articles_href[i]
            i = i+1

            day = common.parseDOM(article,name='strong',ret=False)
            if len(day) > 0:
                day = day[0].encode("utf-8")
            else:
                day = ''
            
            date = common.parseDOM(article,name='small',ret=False)
            if len(date) > 0:
                date = date[0].encode("utf-8")
            else:
                date = ''
            
            title = day + " - " + date
            
            addDirectory(title,defaultbanner,date,link,"openArchiv")

    listCallback(False)
	
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
    
def getCategoryList(category,banner):
    url =  urllib.unquote(category)
    banner =  urllib.unquote(banner)
    
    html = common.fetchPage({'link': url})
	
    try:
        show = common.parseDOM(html.get("content"),name='h3',attrs={'class': 'video_headline'})
        showname = common.replaceHTMLCodes(show[0]).encode("utf-8")
    except:
        showname = ""
    playerHeader = common.parseDOM(html.get("content"),name='header',attrs={'class': 'player_header'})
    bcast_info = common.parseDOM(playerHeader,name='div',attrs={'class': 'broadcast_information'})
    
    try:
        current_duration = common.parseDOM(bcast_info,name='span',attrs={'class': 'meta.meta_duration'})
        
        current_date = common.parseDOM(bcast_info,name='span',attrs={'class': 'meta meta_date'})
        if len(current_date) > 0:
            current_date = current_date[0].encode("utf-8")
        else:
            current_date = ""
            
        current_time = common.parseDOM(bcast_info,name='span',attrs={'class': 'meta meta_time'})
        current_link = url
        current_title = "%s - %s" % (showname,current_date)       
        try:
            current_desc = (translation(30009)).encode("utf-8")+' %s - %s\n'+(translation(30011)).encode("utf-8")+': %s' % (current_date,current_time,current_duration)
        except:
            current_desc = translation(30008).encode('UTF-8');
        addDirectory(current_title,banner,current_desc,current_link,"openSeries")
    except:
        addDirectory((translation(30014)).encode("utf-8"),defaultbanner,"","","")
	
    itemwrapper = common.parseDOM(html.get("content"),name='div',attrs={'class': 'base_list_wrapper.mod_latest_episodes'})
    if len(itemwrapper) > 0:
        items = common.parseDOM(itemwrapper,name='li',attrs={'class': 'base_list_item'})
        feedcount = len(items)
        i = 0
        for item in items:
            i = i+1
            duration = common.parseDOM(item,name='span',attrs={'class': 'meta.meta_duration'})
            date = common.parseDOM(item,name='span',attrs={'class': 'meta.meta_date'})
            date = date[0].encode("utf-8")
            time = common.parseDOM(item,name='span',attrs={'class': 'meta.meta_time'})
            title = common.replaceHTMLCodes(common.parseDOM(item, name='a',ret="title")[0]).encode("utf-8").replace('Sendung ', '')
            title = "%s - %s" % (title,date)
            link = common.parseDOM(item,name='a',ret="href");
            try:
                desc = (translation(30009)).encode("utf-8")+" %s - %s\n"+(translation(30011)).encode("utf-8")+": %s" % (date,time,duration)
            except:
                desc = translation(30008).encode('UTF-8');
            addDirectory(title,banner,desc,link[0],"openSeries")
    listCallback(False)

def getLiveStreams():
    liveurls = {}
    liveurls['ORF1'] = "http://apasfiisl.apa.at/ipad/orf1_"+videoQuality.lower()+"/orf.sdp/playlist.m3u8";
    liveurls['ORF2'] = "http://apasfiisl.apa.at/ipad/orf2_"+videoQuality.lower()+"/orf.sdp/playlist.m3u8";
    liveurls['ORF3'] = "http://apasfiisl.apa.at/ipad/orf2e_"+videoQuality.lower()+"/orf.sdp/playlist.m3u8";
    liveurls['ORFS'] = "http://apasfiisl.apa.at/ipad/orfs_"+videoQuality.lower()+"/orf.sdp/playlist.m3u8";

    url = serviceAPILive % (serviceAPItoken, datetime.datetime.now().strftime('%Y%m%d%H%M'), (datetime.datetime.now() + datetime.timedelta(days=1)).strftime('%Y%m%d%H%M'), 25)
    try: 
        response = urllib2.urlopen(url)
        responseCode = response.getcode()
    except urllib2.HTTPError, error:
        responseCode = error.getcode()
        pass

    if responseCode == 200:
        global time

        bannerurls = {}
        bannerurls['ORF1'] = 'http://tvthek.orf.at/assets/1326810345/orf_channels/logo_color/6779277.png'
        bannerurls['ORF2'] = 'http://tvthek.orf.at/assets/1326810345/orf_channels/logo_color/6779281.png'
        bannerurls['ORF3'] = 'http://tvthek.orf.at/assets/1326810345/orf_channels/logo_color/6779305.png'
        bannerurls['ORFS'] = 'http://tvthek.orf.at/assets/1326810345/orf_channels/logo_color/6779307.png'

        results = json.loads(response.read())['episodeDetails']
        for result in results:

            description     = JSONDescription(result.get('descriptions'))
            program         = result.get('channel').get('reel').upper()
            programName     = result.get('channel').get('name')
            programName     = programName.strip()
            livestreamStart = time.strptime(result.get('livestreamStart'), '%d.%m.%Y %H:%M:%S')
            livestreamEnd   = time.strptime(result.get('livestreamEnd'),   '%d.%m.%Y %H:%M:%S')

            # already playing
            if livestreamStart < time.localtime():
                duration = time.mktime(livestreamEnd) - time.mktime(time.localtime())
                state = (translation(30019)).encode("utf-8")
                state_short = 'Online'

            else:
                duration = time.mktime(livestreamEnd) - time.mktime(livestreamStart)
                state = (translation(30020)).encode("utf-8")
                state_short = 'Offline'
                link = sys.argv[0] + '?' + urllib.urlencode({'mode': 'liveStreamNotOnline', 'link': result.get('episodeId')})

            # find the livestreamStreamingURLs
            livestreamStreamingURLs = []
            for streamingURL in result.get('livestreamStreamingUrls'):
                if '.m3u' in streamingURL.get('streamingUrl'):
                    livestreamStreamingURLs.append(streamingURL.get('streamingUrl'))

            livestreamStreamingURLs.sort()
            link = livestreamStreamingURLs[len(livestreamStreamingURLs) - 1].replace('q4a', videoQuality.lower())

            title = "[%s] %s (%s)" % (programName, result.get('title'), time.strftime('%H:%M', livestreamStart))

            if program in bannerurls:
                banner = bannerurls[program]
            else:
                banner = ''

            createListItem(title, banner, description, duration, time.strftime('%Y-%m-%d', livestreamStart), program, link, 'True', False)

    else:
        html = common.fetchPage({'link': live_url})
        wrapper = common.parseDOM(html.get("content"),name='div',attrs={'class': 'base_list_wrapper.*mod_epg'})
        items = common.parseDOM(wrapper[0],name='li',attrs={'class': 'base_list_item.program.*?'})
        items_class = common.parseDOM(wrapper[0],name='li',attrs={'class': 'base_list_item.program.*?'},ret="class")
        i = 0
        for item in items:
            #program = common.parseDOM(item,ret="class")
            program = items_class[i].split(" ")[2].encode('UTF-8').upper()

            i += 1
            
            banner = common.parseDOM(item,name='img',ret="src")
            banner = common.replaceHTMLCodes(banner[0]).encode('UTF-8')
            
            title = common.parseDOM(item,name='h4')
            title = common.replaceHTMLCodes(title[0]).encode('UTF-8')
            
            time = common.parseDOM(item,name='span',attrs={'class': 'meta.meta_time'})
            time = common.replaceHTMLCodes(time[0]).encode('UTF-8').replace("Uhr","").replace(".",":").strip()

            if getBroadcastState(time):
                state = (translation(30019)).encode("utf-8")
                state_short = "Online"
            else:
                state = (translation(30020)).encode("utf-8")
                state_short = "Offline"

            link = liveurls[program]
            
            title = "[%s] - %s (%s)" % (program,title,time)
            createListItem(title,banner,state,time,program,program,link,'true',False)

    listCallback(False,smallListViewMode)

def getBroadcastState(time):
    time_probe = time.split(":")
        
    current_hour = datetime.datetime.now().strftime('%H')
    current_min = datetime.datetime.now().strftime('%M')
    if time_probe[0] == current_hour and time_probe[1] >= current_min:
        return False
    elif time_probe[0] > current_hour:
        return False
    else:
        return True
    


def getThemenListe(url):
    url = urllib.unquote(url)
    html = common.fetchPage({'link': url})
    html_content = html.get("content")
	
    content = common.parseDOM(html_content,name='section',attrs={'class':'mod_container_list'})
    topics = common.parseDOM(content,name='article',attrs={'class':'item.*?'})

    for topic in topics:
        title = common.parseDOM(topic,name='h4',attrs={'class': 'item_title'})
        title = common.replaceHTMLCodes(title[0]).encode('UTF-8')
        
        link = common.parseDOM(topic,name='a',ret="href")
        link = common.replaceHTMLCodes(link[0]).encode('UTF-8')
        
        image = common.parseDOM(topic,name='img',ret="src")
        if len(image) > 0:
            image = common.replaceHTMLCodes(image[0]).encode('UTF-8')
        else:
            image = defaultbanner
            
        desc = common.parseDOM(topic,name='div',attrs={'class':'item_description'})
        if len(desc) > 0:
            desc = common.replaceHTMLCodes(desc[0]).encode('UTF-8')
        else:
            desc = translation(30008).encode('UTF-8')

        date = common.parseDOM(topic,name='time')
        date = common.replaceHTMLCodes(date[0]).encode('UTF-8')

        time = common.parseDOM(topic,name='span',attrs={'class':'meta.meta_duration'})
        time = common.replaceHTMLCodes(time[0]).encode('UTF-8')

        desc = "%s - (%s) \n%s" % (str(date),str(time).strip(),str(desc))
        
        addDirectory(title,image,desc,link,"openSeries")
    listCallback(False)

def playFile():
    player = xbmc.Player()
    player.play(playlist)
    if not player.isPlayingVideo():
        d = xbmcgui.Dialog()
        d.ok('VIDEO QUEUE EMPTY', 'The XBMC video queue is empty.','Add more links to video queue.')

def getThemen():
    try: 
        response = urllib2.urlopen(serviceAPITopics % serviceAPItoken)
        responseCode = response.getcode()
    except ValueError, error:
        responseCode = 404
        pass
    except urllib2.HTTPError, error:
        responseCode = error.getcode()
        pass

    if responseCode == 200:
        for topic in json.loads(response.read())['topicShorts']:
            if topic.get('parentId') != None or topic.get('isArchiveTopic'):
                continue
            title       = topic.get('name').encode('UTF-8')
            image       = JSONImage(topic.get('images'))
            description = topic.get('description')
            link        = topic.get('topicId')

            addDirectory(title, image, description, link, 'openTopic')
        listCallback(False, thumbViewMode)

    else:
        url = "http://tvthek.orf.at/topics"
        html = common.fetchPage({'link': url})
        html_content = html.get("content")
        
        content = common.parseDOM(html_content,name='section',attrs={'class':'mod_container_list'})
        topics = common.parseDOM(content,name='section',attrs={'class':'item_wrapper'})

        for topic in topics:
            title = common.parseDOM(topic,name='h3',attrs={'class':'item_wrapper_headline.subheadline.*?'})
            title = common.replaceHTMLCodes(title[0]).encode('UTF-8')
            
            link = common.parseDOM(topic,name='a',attrs={'class':'more.service_link.service_link_more'},ret="href")
            link = common.replaceHTMLCodes(link[0]).encode('UTF-8')
            
            image = common.parseDOM(topic,name='img',ret="src")
            image = common.replaceHTMLCodes(image[0]).replace("width=395","width=500").replace("height=209.07070707071","height=265").encode('UTF-8')
            
            descs = common.parseDOM(topic,name='h4',attrs={'class':'item_title'})
            description = ""
            for desc in descs:
                description += "* "+common.replaceHTMLCodes(desc).encode('UTF-8') + "\n"
            if description == "":
                description = translation(30008).encode('UTF-8')

            addDirectory(title,image,description,link,"openTopicPosts")
        listCallback(True)
		
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
    htmlScraper.getLinks(link,banner)
elif mode == 'openShowList':
    getMoreShows(link,banner,backdrop)
elif mode == 'openCategoryList':
    getCategoryList(link,banner)
elif mode == 'getSendungen':
    if useServiceAPI:
        list = jsonScraper.getCategories()
        addItemDirectories(list);
    else:
        list = htmlScraper.getCategories()
        addItemDirectories(list);
    listCallback(True,thumbViewMode)
elif mode == 'getAktuelles':
    if useServiceAPI:
        list = jsonScraper.getTableResults(jsonScraper.serviceAPIHighlights)
        addItemDirectories(list);
    else:
        list = htmlScraper.getRecentlyAdded(htmlScraper.base_url)
        addItemDirectories(list);
    listCallback(False)
elif mode == 'getLive':
    getLiveStreams()
elif mode == 'getTipps':
    if useServiceAPI:
        list = jsonScraper.getTableResults(jsonScraper.serviceAPITip)
        addItemDirectories(list);
    else:
        list = htmlScraper.getTableResults(htmlScraper.tip_url)
        addItemDirectories(list);
    listCallback(False)
elif mode == 'getNewShows':
    if useServiceAPI:
        list = jsonScraper.getTableResults(jsonScraper.serviceAPIRecent)
        addItemDirectories(list);
    else:
        list = htmlScraper.getTableResults(htmlScraper.recent_url)
        addItemDirectories(list);
    listCallback(False)
elif mode == 'getMostViewed':
    if useServiceAPI:
        list = jsonScraper.getTableResults(jsonScraper.serviceAPIViewed)
        addItemDirectories(list);
    else:
        list = htmlScraper.getTableResults(htmlScraper.mostviewed_url)
        addItemDirectories(list);
    listCallback(False)
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
    getProgram(link)
elif mode == 'openTopic':
    getTopic(link)
elif mode == 'openEpisode':
    getEpisode(link)
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
