#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys, os
import re
import socket
import urllib
import json
import datetime, time

import xbmcplugin
import xbmcgui
import xbmcaddon

import CommonFunctions as common

try:
   import StorageServer
except:
   import storageserverdummy as StorageServer
 
socket.setdefaulttimeout(30) 
cache = StorageServer.StorageServer("plugin.video.orftvthek", 999999)

version = "0.2.3"
plugin = "ORF-TVthek-%s" % version
author = "sofaking"

common.plugin = plugin

settings = xbmcaddon.Addon(id='plugin.video.orftvthek') 
pluginhandle = int(sys.argv[1])
basepath = settings.getAddonInfo('path')

translation = settings.getLocalizedString
base_url="http://tvthek.orf.at"
live_url = "http://apasfiisl.apa.at/ipad/%(channel)s%(special)s_%(quality)s/orf.sdp/playlist.m3u8"

video_qualities = ["q1a", "q4a", "q6a"]

forceView = settings.getSetting("forceView") == "true"
videoProtocol = "http"
videoQuality = settings.getSetting("videoQuality")
try:
    videoQuality = video_qualities[int(videoQuality)]
except:
    videoQuality = video_qualities[2]
livestreamInfo = settings.getSetting("livestreamInfo")

if xbmc.getSkinDir() == 'skin.confluence':
   defaultViewMode = 'Container.SetViewMode(503)'
else:
   defaultViewMode = 'Container.SetViewMode(518)'

defaultbackdrop = os.path.join(basepath, "fanart.jpg")
defaultbanner = "http://goo.gl/FG03G"


channels = {
    'ORF1': {
        "short": "orf1",
        "title": "ORF eins",
        "banner": "http://tvthek.orf.at/dynamic/get_asset_resized.php?width=278&path=orf_channels%252Flogo_color%252F6779277.png&percent=100&quality=100&x1=0&x2=204&y1=0&y2=43"
    },
    'ORF2': {
        "short": "orf2",
        "title": "ORF 2",
        "banner": "http://tvthek.orf.at/dynamic/get_asset_resized.php?width=278&path=orf_channels%252Flogo_color%252F6779281.png&percent=100&quality=100&x1=0&x2=145&y1=0&y2=43"
    },
    'ORF3': {
        "short": "orf3",
        "title": "ORF III",
        "banner": "http://tvthek.orf.at/dynamic/get_asset_resized.php?width=278&path=orf_channels%252Flogo_color%252F6779305.png&percent=100&quality=100&x1=0&x2=153&y1=0&y2=60"
    },
    'ORFS': {
        "short": "orfs",
        "title": "ORF Sport+",
        "banner": "http://tvthek.orf.at/dynamic/get_asset_resized.php?width=278&path=orf_channels%252Flogo_color%252F6779307.png&percent=100&quality=100&x1=0&x2=284&y1=0&y2=43"
    }
}

playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO) 

def parameterEncode(parameter):
    return parameter.replace("&", "AMPSIGN").replace("=", "EQUALSIGN").replace("?", "QUESTIONMARK")
    
def parameterDecode(parameter):
    return urllib.unquote(parameter.replace("AMPSIGN", "&").
            replace("EQUALSIGN", "=").
            replace("QUESTIONMARK", "?"))

def parseDate(date_string, strftime):
    return datetime.datetime(*(time.strptime(date_string, strftime)[0:6]))

def parseDuration(duration):
    duration = duration.split(" ")[0]
    if duration[1] == "Std.": # convert from HH:MM to seconds
        duration = int(duration.split(":")[0])*60*60 + int(duration.split(":")[1])*60
    else:  # convert from MM:SS to seconds
        duration = int(duration.split(":")[0])*60 + int(duration.split(":")[1])
    return duration

def playFile(item=None):
    player = xbmc.Player()
    if not item:
        item = playlist
    player.play(item)
    if not player.isPlayingVideo():
        d = xbmcgui.Dialog()
        d.ok('VIDEO QUEUE EMPTY', 'The XBMC video queue is empty.','Add more links to video queue.')

def listCallback():
    xbmcplugin.setContent(pluginhandle,'episodes')
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_VIDEO_SORT_TITLE)
    xbmcplugin.endOfDirectory(pluginhandle)
    
    if forceView:
        xbmc.executebuiltin(defaultViewMode)

def createListItem(title, description=None,
        banner=None, backdrop=None, 
        duration=None, date=None, channel="",
        videourl="", playable="true",
        folder=False,
        sorttitle=None, count=None):
    
    if count is not None:
        sorttitle = str(count)
    
    if sorttitle is None:
        sorttitle = title
    
    if not description:
        description = translation(30008)
    
    if not banner:
        banner = defaultbanner
    else:
        banner = re.sub(r"height=[0-9.]*&amp;", r"", banner)
        banner = re.sub(r"width=[0-9.]*&amp;", r"", banner)
    
    if not backdrop:
        backdrop = defaultbackdrop
    else:
        backdrop = re.sub(r"height=[0-9.]*&amp;", r"", backdrop)
        backdrop = re.sub(r"width=[0-9.]*&amp;", r"", backdrop)
    
    title = common.replaceHTMLCodes(title)
    sorttitle = common.replaceHTMLCodes(sorttitle)
    description = common.replaceHTMLCodes(description)
    banner = common.replaceHTMLCodes(banner)
    backdrop = common.replaceHTMLCodes(backdrop)
    videourl = common.replaceHTMLCodes(videourl)
    
    liz = xbmcgui.ListItem(label=title, label2=channel,
        iconImage=banner, thumbnailImage=banner)
    liz.setInfo(type="video", infoLabels={
        "title": title,
        "sorttitle": sorttitle,
        "plot": description,
        "plotoutline": description,
        "tvshowtitle": channel
    })
    liz.addStreamInfo("video", {
        "codec": "aac",
        "language": "de",
        "channels": 2
    })
    liz.addStreamInfo("audio", {
        "codec": "aac",
        "language": "de",
        "channels": 2
    })
    if count is not None:
        liz.setInfo(type="video", infoLabels={
            "count": count
        })
    if date is not None:
        liz.setInfo(type="video", infoLabels={
            "dateadded": date.strftime("%Y-%m-%d %H:%M:%S"),
            "aired": date.strftime("%Y-%m-%d")
        })
    if duration is not None:
        liz.addStreamInfo("video", {
            'duration': duration
        })
    liz.setArt({
        'thumb': banner,
        'poster': backdrop,
        'banner': banner,
        'fanart': backdrop,
        'clearart': backdrop,
        'clearlogo': banner,
        'landscape': backdrop
    })
    liz.setProperty('IsPlayable', playable)
    
    xbmcplugin.addDirectoryItem(handle=pluginhandle, url=videourl, listitem=liz, isFolder=folder)
    return liz

def addDirectory(title, description=None,
        banner=None, backdrop=None,
        duration=None, date=None, channel=None,
        link=None, mode=None,
        sorttitle=None, count=None):
    parameters = {}
    if banner:
        parameters['banner'] = common.replaceHTMLCodes(parameterEncode(banner))
    if backdrop:
        parameters['backdrop'] = common.replaceHTMLCodes(parameterEncode(backdrop))
    if link:
        parameters['link'] = common.replaceHTMLCodes(parameterEncode(link))
    if mode:
        parameters['mode'] = mode
    if channel:
        parameters['channel'] = channel
    
    videourl = sys.argv[0] + '?' + urllib.urlencode(parameters)
    createListItem(title=title, description=description,
        banner=banner, backdrop=backdrop,
        duration=duration, date=date, channel=channel,
        videourl=videourl, playable='false',
        folder=True,
        sorttitle=sorttitle, count=count)

def getMainMenu():
    addDirectory(translation(30001), mode="getNews", count=1)
    addDirectory(translation(30000), mode="getNewShows", count=2)
    addDirectory(translation(30005), mode="getRecommendations", count=3)
    addDirectory(translation(30006), mode="getMostViewed", count=4)
    addDirectory(translation(30002), mode="getShows", count=5)
    addDirectory(translation(30003), mode="getTopics", count=6)
    addDirectory(translation(30004), mode="getLive", count=7)
    addDirectory(translation(30018), mode="getScheduleDays", count=8)
    addDirectory(translation(30029), mode="getArchive", count=9)
    addDirectory(translation(30007), mode="search", count=10)
    
    listCallback()

def getVideoParts(url, backdrop=None):
    # get id at end of url
    videoid = url.split("/")[-1]
    
    html = common.fetchPage({'link': url})
    data = common.parseDOM(html.get("content"),
        name='div',
        attrs={'class': "jsb_ jsb_VideoPlaylist"},
        ret='data-jsb')
    data = data[0]
    data = common.replaceHTMLCodes(data)
    data = json.loads(data)
    
    title = data.get("title")
    if not backdrop:
        backdrop = data.get("preview_image_url")
    
    videos = data.get('playlist', {}).get('videos', [])
    
    # if the videoid matches with a video in the list we only want that video
    filtered = filter(lambda x: x.get("id") == videoid, videos)
    if filtered:
        videos = filtered
    
    count = 0
    for video in videos:
        title = video.get("title")
        description = video.get("description")
        banner = video.get("preview_image_url")
        duration = video.get("duration")
        
        videourl = None
        for source in video.get("sources", []):
            if source.get("quality", "").lower() != videoQuality:
                continue
            if source.get("protocol", "") != videoProtocol:
                continue
            videourl = source.get("src")
        
        # if it is only one video or we want a specific video
        # like with search. play it directly.
        if len(videos) == 1:
            playFile(videourl)
            return
        
        createListItem(title, description=description,
            banner=banner, backdrop=backdrop,
            duration=duration, videourl=videourl,
            count=count)
        count += 1
    
    listCallback()

def getFilteredEpisodes(url, backdrop=None):
    html = common.fetchPage({'link': url})
    
    time_in_title = False
    day_string = common.parseDOM(html.get("content"),
        name='h3',
        attrs={'class': "subheadline"},
        ret=False)
    try:
        day_string = day_string[0].split(" ")[1]
        parseDate(day_string, "%d.%m.%Y")
        time_in_title = True
    except:
        day_string = None
    
    articles = common.parseDOM(html.get("content"),
        name='article',
        attrs={'class': "item.*?"},
        ret=False)
    
    count = 0
    for article in articles:
        title = common.parseDOM(article,
            name='h4',
            attrs={'class': "item_title"},
            ret=False)
        title = title[0]
        description = common.parseDOM(article,
            name='div',
            attrs={'class': "item_description"},
            ret=False)
        if description:
            description = description[0]
            
            meta_date = common.parseDOM(article,
                name='time',
                attrs={'class':'meta meta_date'},
                ret=False)
            if meta_date:
                day_string = meta_date[0].split(" ")[1]
            meta_time = common.parseDOM(article,
                name='span',
                attrs={'class':'meta meta_time'},
                ret=False)
            date_string = "%sT%s" % (day_string, meta_time[0].split(" ")[0])
            date = parseDate(date_string, "%d.%m.%YT%H.%M")
            
            duration = common.parseDOM(article,
                name='span',
                attrs={'class':'meta meta_duration'},
                ret=False)
            duration = duration[0]
            duration = parseDuration(duration)
            
            description = "%s (%s: %s)" % (description,
                translation(30009),
                date.strftime("%Y-%m-%d %H:%M"))
            
            if time_in_title:
                title = "%s (%s)" % (date.strftime("%H:%M"), title)
            else:
                title = "%s (%s)" % (title, date.strftime("%Y-%m-%d"))
        else:
            description = translation(30008)
        
        banner = common.parseDOM(article,
            name='img',
            attrs={},
            ret='src')
        banner = banner[0].split("\"")[0] # dirty hack becase parseDom has some problems...
        link = common.parseDOM(article,
            name='a',
            attrs={},
            ret='href')
        link = link[0].split("\"")[0] # dirty hack becase parseDom has some problems...
        addDirectory(title, description=description,
            banner=banner,
            backdrop=backdrop,
            link=link, mode="getVideoParts",
            count=count)
        count += 1
    listCallback()

def getEpisodes(url, banner=None, backdrop=None):
    html = common.fetchPage({'link': url})
    
    showname = common.parseDOM(html.get("content"),
        name='h3',
        attrs={'class': "video_headline"},
        ret=False)
    
    if showname:
        showname = showname[0]
    else:
        showname = ""
    
    count = 0
    header = common.parseDOM(html.get("content"),
        name='header',
        attrs={'class': "player_header"},
        ret=False)
    if header:
        date_string = common.parseDOM(header,
            name='time',
            attrs={},
            ret="datetime")
        date_string = date_string[0]
        date = parseDate(date_string, "%Y-%m-%dT%H:%M:%S")
        
        duration = common.parseDOM(header,
            name='span',
            attrs={'class':'meta meta_duration'},
            ret=False)
        duration = duration[0]
        duration = parseDuration(duration)
        
        title = date.strftime("%Y-%m-%d %H:%M")
        
        description = "%s (%s: %s)" % (showname,
            translation(30009),
            date.strftime("%Y-%m-%d %H:%M"))
        
        link = url
        
        addDirectory(title, description=description,
            banner=banner, backdrop=backdrop,
            link=link, mode="getVideoParts",
            count=count)
        count += 1
    
    if not header:
        episodes = []
    else:
        episodes = common.parseDOM(html.get("content"),
            name='div',
            attrs={'class': "base_list_wrapper mod_latest_episodes"},
            ret=False)
    for episode in episodes:
        date_string = common.parseDOM(episode,
            name='time',
            attrs={},
            ret="datetime")
        date_string = date_string[0]
        date = parseDate(date_string, "%Y-%m-%dT%H:%M:%S")
        
        duration = common.parseDOM(episode,
            name='span',
            attrs={'class': 'meta meta_duration'},
            ret=False)
        duration = duration[0]
        duration = parseDuration(duration)
        
        link = common.parseDOM(episode,
            name='a',
            attrs={},
            ret='href')
        link = link[0].split("\"")[0] # dirty hack becase parseDom has some problems...
        
        title = date.strftime("%Y-%m-%d %H:%M")
        description = "%s (%s: %s)" % (showname,
            translation(30009),
            date.strftime("%Y-%m-%d %H:%M"))
        
        addDirectory(title, description=description,
            banner=banner, backdrop=backdrop,
            link=link, mode="getVideoParts",
            count=count)
        count += 1
    
    if header:
        articles = []
    else:
        articles = common.parseDOM(html.get("content"),
            name='article',
            attrs={'class': 'item.*?'},
            ret=False)
    for article in articles:
        title = common.parseDOM(article,
            name='h4',
            attrs={},
            ret=False)
        if not title:
            continue
        title = title[0]
        
        date_string = common.parseDOM(article,
            name='time',
            attrs={},
            ret=False)
        if not date_string:
            continue
        date_string = date_string[0]
        date = parseDate(date_string.split(" ")[1], "%d.%m.%Y")
        
        duration = common.parseDOM(article,
            name='span',
            attrs={'class':'meta meta_duration'},
            ret=False)
        if not duration:
            continue
        duration = duration[0]
        duration = parseDuration(duration)
        
        link = common.parseDOM(article,
            name='a',
            attrs={},
            ret='href')
        if not link:
            continue
        link = link[0].split("\"")[0] # dirty hack becase parseDom has some problems...
        
        article_banner = common.parseDOM(article,
            name='img',
            attrs={},
            ret='src')
        if article_banner:
            article_banner = article_banner[0]
        else:
            article_banner = banner
        
        description = "%s (%s: %s)" % (title,
            translation(30009),
            date.strftime("%Y-%m-%d"))
        title = "%s (%s)" % (title, date.strftime("%Y-%m-%d"))
        
        addDirectory(title, description=description,
            banner=article_banner, backdrop=backdrop,
            link=link, mode="getVideoParts",
            count=count)
        count += 1
    
    listCallback()

def getArchive(url):
    html = common.fetchPage({'link': url})
    
    articles = common.parseDOM(html.get("content"),
        name='article',
        attrs={'class': 'item.*?'},
        ret=False)
    count = 0
    for article in articles:
        title = common.parseDOM(article,
            name='h4',
            attrs={'class': "item_title"},
            ret=False)
        title = title[0]
        
        description = common.parseDOM(article,
            name='div',
            attrs={'class': "item_description"},
            ret=False)
        description = description[0]
        
        banner = common.parseDOM(article,
            name='img',
            attrs={},
            ret='src')
        banner = banner[0]
        
        link = common.parseDOM(article,
            name='a',
            attrs={},
            ret='href')
        link = link[0].split("\"")[0] # dirty hack becase parseDom has some problems...
        
        addDirectory(title, description=description,
            banner=banner,
            link=link, mode="getEpisodes",
            count=count)
        count += 1
    
    listCallback()

def getScheduleDays(url):
    html = common.fetchPage({'link': url})
    
    days = common.parseDOM(html.get("content"),
        name='li',
        attrs={'class': 'slider_list_item.*?'},
        ret=False)
    
    count = len(days)
    for day in reversed(days):
        if count == 1:
            title = translation(30030)
        else:
            date_string = common.parseDOM(day,
                name='small',
                attrs={'class': 'date'},
                ret=False)
            date_string = date_string[0]
            date = parseDate(date_string, "%d.%m.%Y")
            title = date.strftime("%Y-%m-%d")
        
        link = common.parseDOM(day,
            name='a',
            attrs={},
            ret='href')
        link = link[0].split("\"")[0] # dirty hack becase parseDom has some problems...
        
        addDirectory(title,
            link=link, mode="getFilteredEpisodes", count=count)
        count -= 1
    
    listCallback()

def getChannelLiveStreams(channel=None, epg=None, show_all=True, callback=True):
    if not epg:
        html = common.fetchPage({'link': "http://tvthek.orf.at/live"})
        epg = common.parseDOM(html.get("content"),
            name='ul',
            attrs={'class': "base_list epg"}, #".*?epg.*?"
            ret=False)
    
    if not channel:
        # get all streams of all channels instead
        for key in channels.keys():
            getChannelLiveStreams(channel=key, epg=epg, show_all=show_all, callback=False)
        listCallback()
        return
    
    channel = channels.get(channel)
    
    livestreams = common.parseDOM(epg,
        name='li',
        attrs={'class': "base_list_item program %s jsb_ jsb_ToggleButton" % channel.get("short")}, #.*?%s.*?"
        ret=False)
    programs = common.parseDOM(livestreams,
        name='a',
        attrs={},
        ret=False)
    
    start_timestamp = 0
    previous_start_timestamp = 0
    for program in programs:
        date = common.parseDOM(program,
            name='span',
            attrs={},
            ret="data-jsb")
        date = date[0]
        date = common.replaceHTMLCodes(date)
        date = json.loads(date)
        start_timestamp = int(date.get("livestream_start_as_timestamp"))
        
        if not show_all and \
                previous_start_timestamp > 0 and \
                previous_start_timestamp < start_timestamp:
            # show only current or next livestream
            # show more than one if start timestamp is equal (e.g. diffrent audio streams)
            break
        
        now = datetime.datetime.now()
        
        start_date = datetime.datetime.fromtimestamp(start_timestamp)
        start_time = start_date.strftime("%H:%M")
        
        end_timestamp = int(date.get("livestream_end_as_timestamp"))
        end_date = datetime.datetime.fromtimestamp(end_timestamp)
        end_time = end_date.strftime("%H:%M")
        
        duration = end_timestamp - start_timestamp
        
        playable = 'false'
        if now >= start_date and now < end_date:
            playable = 'true'
        
        title = common.parseDOM(program,
            name='h4',
            attrs={},
            ret=False)
        title = title[0]
        
        description = "%s - %s (%s - %s)" % (channel.get("title"), title, start_time, end_time)
        title = "%s - %s" % (start_time, title)
        
        banner = channel.get("banner")
        
        special = ""
        if previous_start_timestamp == start_timestamp:
            # same livestream with special option like diffrent audio
            if "(AD)" in title:
                special = "ad"
            else:
                # currently only ad alternatives are supported
                continue
        
        videourl = live_url % {
            'channel': channel.get("short"),
            'special': special,
            'quality': videoQuality
        }
        
        sorttitle = "%s %s" % (start_timestamp, channel.get("short"))
        
        createListItem(title, description=description,
            banner=banner,
            duration=duration, date=start_date,
            channel=channel.get("title"),
            videourl=videourl, playable=playable,
            sorttitle=sorttitle)
        
        previous_start_timestamp = start_timestamp
    
    if callback:
        listCallback()

def getLiveChannelDirectories():
    for key, channel in channels.iteritems():
        addDirectory(title="%s Livestreams" % channel.get("title"),
            banner=channel.get("banner"),
            mode="getChannelLiveStreams",
            channel=key, sorttitle=key)
    listCallback()

def getLive():
    if livestreamInfo == "0":
        for key, channel in channels.iteritems():
            title = "%s Livestream" % channel.get("title")
            banner = channel.get("banner")
            createListItem(title=title,
                banner=banner,
                channel=channel.get("title"),
                videourl=channel.get("liveurl"))
        listCallback()
    elif livestreamInfo == "2":
        getChannelLiveStreams(show_all=True)
    elif livestreamInfo == "3":
        getLiveChannelDirectories()
    else:
        getChannelLiveStreams(show_all=False)

def getNews():
    html = common.fetchPage({'link': base_url})
    
    stage = common.parseDOM(html.get("content"),
        name='ul',
        attrs={'class': 'stage_items_list.*?'},
        ret=False)
    articles = common.parseDOM(stage,
        name='article',
        attrs={},
        ret=False)
    count = 0
    for article in articles:
        title = common.parseDOM(article,
            name='h3',
            attrs={'class': "item_title"},
            ret=False)
        title = title[0]
        
        description = common.parseDOM(article,
            name='div',
            attrs={'class': "item_description"},
            ret=False)
        description = description[0]
        
        banner = common.parseDOM(article,
            name='img',
            attrs={},
            ret='src')
        banner = banner[0]
        
        link = common.parseDOM(article,
            name='a',
            attrs={},
            ret='href')
        link = link[0].split("\"")[0] # dirty hack becase parseDom has some problems...
        
        addDirectory(title, description=description,
            banner=banner,
            link=link, mode="getVideoParts",
            count=count)
        count += 1
    
    listCallback()

def getTopics():
    url = "http://tvthek.orf.at/topics"
    html = common.fetchPage({'link': url})
    
    topics = common.parseDOM(html.get("content"),
        name='section',
        attrs={'class': "item_wrapper"},
        ret=False)
    for topic in topics:
        title = common.parseDOM(topic,
            name='h3',
            attrs={},
            ret=False)
        title = title[0]
        link = common.parseDOM(topic,
            name='a',
            attrs={},
            ret='href')
        link = link[-1].split("\"")[0] # dirty hack becase parseDom has some problems...
        addDirectory(title,
            link=link, mode="getEpisodes")
    listCallback()

def programUrlTitle(url):
    title = url.replace(base_url,"").split("/")
    return title[2].replace("-"," ")

def getShows():
    html = common.fetchPage({'link': base_url})
    slideview = common.parseDOM(html.get("content"),
        name='div',
        attrs={'class': "mod_carousel"},
        ret=False)
    links = common.parseDOM(slideview,
        name='a',
        attrs={'class': "carousel_item_link"},
        ret='href')
    catbox = common.parseDOM(slideview,
        name='a',
        attrs={'class': "carousel_item_link"},
        ret=False)
    i = 0
    for cat in catbox:
        link = links[i].split("\"")[0] # dirty hack becase parseDom has some problems...
        title = programUrlTitle(link)
        banner = common.parseDOM(cat,
            name='img',
            attrs={},
            ret='src')
        banner = banner[0].split("\"")[0] # dirty hack becase parseDom has some problems...
        addDirectory(title,
            banner=banner,
            backdrop=banner,
            link=link, mode="getEpisodes")
        i += 1
    
    listCallback()

def newSearch():
    keyboard = xbmc.Keyboard('')
    keyboard.doModal()
    if (keyboard.isConfirmed()):
        cache.table_name = "searchhistory"
        keyboard_in = keyboard.getText()
        some_dict = "%s|%s" % (cache.get("searches"), keyboard_in)
        cache.set("searches", some_dict);
        searchurl = "%s/search?q=%s" % (base_url,keyboard_in.replace(" ", "+"))
        getFilteredEpisodes(searchurl)
    else:
        addDirectory(translation(30014))
        listCallback()

def historySearch(link):
    searchurl = "%s/search?q=%s" % (base_url, link.replace(" ", "+"))
    getFilteredEpisodes(searchurl)

def search():
    addDirectory(translation(30007),
        mode="searchNew")
    
    cache.table_name = "searchhistory"
    some_dict = cache.get("searches").split("|")
    for string in reversed(some_dict):
        link = string.replace(" ", "+")
        addDirectory(string,
            link=link, mode="getSearch")
    listCallback()

if __name__ == "__main__":
    params = common.getParameters(sys.argv[2])
    
    channel = params.get('channel')
    mode = params.get('mode')
    link = params.get('link')
    if link:
        link = parameterDecode(link)
    banner = params.get('banner')
    if banner:
        banner = parameterDecode(banner)
    backdrop = params.get('backdrop')
    if backdrop:
        backdrop = parameterDecode(backdrop)
    
    if mode == 'getVideoParts':
        getVideoParts(link, backdrop=banner)
    elif mode == 'getFilteredEpisodes':
        getFilteredEpisodes(link, backdrop=banner)
    elif mode == 'getEpisodes':
        getEpisodes(link, banner=banner, backdrop=banner)
    elif mode == 'getShows':
        getShows()
    elif mode == 'getNews':
        getNews()
    elif mode == 'getChannelLiveStreams':
        getChannelLiveStreams(channel=channel, show_all=True)
    elif mode == 'getLive':
        getLive()
    elif mode == 'getRecommendations':
        getFilteredEpisodes("http://tvthek.orf.at/tips")
    elif mode == 'getNewShows':
        getFilteredEpisodes("http://tvthek.orf.at/newest")
    elif mode == 'getMostViewed':
        getFilteredEpisodes('http://tvthek.orf.at/most_viewed')
    elif mode == 'getTopics':
        getTopics()
    elif mode == 'getScheduleDays':
        getScheduleDays('http://tvthek.orf.at/schedule')
    elif mode == 'getSchedule':
        getSchedule(link)
    elif mode == 'getArchive':
        getArchive('http://tvthek.orf.at/archive')
    elif mode == 'search':
        search()
    elif mode == 'getSearch':
        if link:
            historySearch(link);
        else:
            newSearch()
    else:
        getMainMenu()
