#!/usr/bin/python
# -*- coding: utf-8 -*-
import urllib,urllib2,re,xbmcplugin,xbmcgui,sys,xbmcaddon,base64,socket,datetime,time,os,os.path,urlparse,json
import CommonFunctions as common

class htmlScraper:
    opener = urllib2.build_opener()
    opener.addheaders = [('User-agent', 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/535.7 (KHTML, like Gecko) Chrome/16.0.912.77 Safari/535.7')]

    base_url="http://tvthek.orf.at" 
    
    schedule_url = 'http://tvthek.orf.at/schedule'
    recent_url = 'http://tvthek.orf.at/newest'
    live_url = "http://tvthek.orf.at/live"
    mostviewed_url = 'http://tvthek.orf.at/most_viewed'
    tip_url = 'http://tvthek.orf.at/tips'
    search_base_url = 'http://tvthek.orf.at/search'
    translation = ""
    xbmc = ""
    
    def __init__(self,xbmc,settings):
        self.translation = settings.getLocalizedString
        self.xbmc = xbmc;
        self.xbmc.log(msg='Using HTML Scraper', level=xbmc.LOGDEBUG);
        
    def doStuff(self):
        self.xbmc.log(msg='doStuff', level=xbmc.LOGDEBUG);
        
        
    def getVideoUrl(self,sources,protocol,delivery,quality):
        for source in sources:
            if source["protocol"].lower() == videoProtocol.lower():
                if source["delivery"].lower() == videoDelivery.lower():
                    if source["quality"].lower() == videoQuality.lower():
                        return source["src"]
        return False
        
    def programUrlTitle(self,url):
        title = url.replace(self.base_url,"").split("/")
        if title[1] == 'index.php':
            return title[3].replace("-"," ")
        else:
            return title[2].replace("-"," ")
    
    def getTableResults(self,url):
        url = urllib.unquote(url)
        html = common.fetchPage({'link': url})
        items = common.parseDOM(html.get("content"),name='article',attrs={'class': "item.*?"},ret=False)
        list = []

        for item in items:
            title = common.parseDOM(item,name='h4',attrs={'class': "item_title"},ret=False)
            title = common.replaceHTMLCodes(title[0]).encode('UTF-8')
            desc = common.parseDOM(item,name='div',attrs={'class': "item_description"},ret=False)
            time = ""
            date = ""
            if desc != None and len(desc) > 0:
                desc = common.replaceHTMLCodes(desc[0]).encode('UTF-8')
                date = common.parseDOM(item,name='time',attrs={'class':'meta.meta_date'},ret=False)
                date = date[0].encode('UTF-8')
                time = common.parseDOM(item,name='span',attrs={'class':'meta.meta_time'},ret=False)
                time = time[0].encode('UTF-8')
                desc = (self.translation(30009)).encode("utf-8")+' %s - %s\n%s' % (date,time,desc)
            else:
                desc = (self.translation(30008)).encode("utf-8")

            image = common.parseDOM(item,name='img',attrs={},ret='src')
            image = common.replaceHTMLCodes(image[0]).encode('UTF-8')
            link = common.parseDOM(item,name='a',attrs={},ret='href')
            link = link[0].encode('UTF-8')
            if date != "":
                title = "%s - %s" % (title,date)
            dict = {}
            dict['title'] = title
            dict['image'] = image
            dict['desc'] = desc
            dict['link'] = link
            dict['mode'] = "openSeries"
            list.append(dict)
        return list
    
    def getRecentlyAdded(self,url):
        html = common.fetchPage({'link': url})
        html_content = html.get("content")
        teaserbox = common.parseDOM(html_content,name='a',attrs={'class': 'item_inner'})
        teaserbox_href = common.parseDOM(html_content,name='a',attrs={'class': 'item_inner'},ret="href")
        list = []

        i = 0
        for teasers in teaserbox:
            link = teaserbox_href[i]
            i = i+1
            title = common.parseDOM(teasers,name='h3',attrs={'class': 'item_title'})
            title = common.replaceHTMLCodes(title[0]).encode('UTF-8')
            
            desc = common.parseDOM(teasers,name='div',attrs={'class': 'item_description'})
            desc = common.replaceHTMLCodes(desc[0]).encode('UTF-8')
            
            image = common.parseDOM(teasers,name='img',ret="src")
            image = common.replaceHTMLCodes(image[0]).encode('UTF-8')
            
            dict = {}
            dict['title'] = title
            dict['image'] = image
            dict['desc'] = desc
            dict['link'] = link
            dict['mode'] = "openSeries"
            list.append(dict)
        return list
    
    # list all Categories
    def getCategories(self):
        html = common.fetchPage({'link': self.base_url})
        html_content = html.get("content")
        
        content = common.parseDOM(html_content,name='div',attrs={'class':'mod_carousel'})
        items = common.parseDOM(content,name='a',attrs={'class':'carousel_item_link'})
        items_href = common.parseDOM(content,name='a',attrs={'class':'carousel_item_link'},ret="href")
        
        list = []
        
        i = 0
        for item in items:
            link = common.replaceHTMLCodes(items_href[i]).encode('UTF-8')
            i = i + 1
            title = self.programUrlTitle(link).encode('UTF-8')
            if title.lower().strip() == "bundesland heute":
                image = common.parseDOM(item,name='img',ret="src")
                image = common.replaceHTMLCodes(image[0]).replace("height=56","height=280").replace("width=100","width=500").encode('UTF-8')
                list = self.getBundeslandHeute(link,image,list)
            if title.lower().strip() == "zib":
                image = common.parseDOM(item,name='img',ret="src")
                image = common.replaceHTMLCodes(image[0]).replace("height=56","height=280").replace("width=100","width=500").encode('UTF-8')
                list = self.getZIB(image,list)
            else:
                image = common.parseDOM(item,name='img',ret="src")
                image = common.replaceHTMLCodes(image[0]).replace("height=56","height=280").replace("width=100","width=500").encode('UTF-8')

                desc = self.translation(30008).encode('UTF-8')

                dict = {}
                dict['title'] = title
                dict['image'] = image
                dict['desc'] = desc
                dict['link'] = link
                dict['mode'] = "openCategoryList"
                list.append(dict)
        return list

        listCallback(True,thumbViewMode)
        
    def getZIB(self,baseimage,list):
        url = 'http://tvthek.orf.at/programs/genre/ZIB/1';
        html = common.fetchPage({'link': url})
        html_content = html.get("content")
        
        content = common.parseDOM(html_content,name='div',attrs={'class':'base_list_wrapper mod_results_list'})
        items = common.parseDOM( content ,name='li',attrs={'class':'base_list_item jsb_ jsb_ToggleButton results_item'})
        
        for item in items:
            title = common.parseDOM(item,name='h4')
            if len(title) > 0:
                title = title[0].encode('UTF-8')
                item_href = common.parseDOM(item,name='a',attrs={'class':'base_list_item_inner.*?'},ret="href")
                image_container = common.parseDOM(item,name='figure',attrs={'class':'episode_image'},ret="href")
                desc = self.translation(30008).encode('UTF-8')
                image = common.parseDOM(item,name='img',attrs={},ret="src")
                if len(image) > 0:
                    image = common.replaceHTMLCodes(image[0]).encode('UTF-8').replace("height=180","height=265").replace("width=320","width=500")
                else:
                    image = baseimage
                link = common.replaceHTMLCodes(item_href[0]).encode('UTF-8')
                dict = {}
                dict['title'] = title
                dict['image'] = image
                dict['desc'] = desc
                dict['link'] = link
                dict['mode'] = "openCategoryList"
                list.append(dict)
        return list
            
     
    def getBundeslandHeute(self,url,image,list):
        html = common.fetchPage({'link': url})
        html_content = html.get("content")
        
        content = common.parseDOM(html_content,name='div',attrs={'class':'base_list_wrapper mod_link_list'})
        items = common.parseDOM(content,name='li',attrs={'class':'base_list_item'})
        items_href = common.parseDOM(items,name='a',attrs={},ret="href")
        items_title = common.parseDOM(items,name='h4')
        
        i = 0
        for item in items:
            link = common.replaceHTMLCodes(items_href[i]).encode('UTF-8')        
            title = items_title[i].encode('UTF-8')
            desc = self.translation(30008).encode('UTF-8')
            dict = {}
            dict['title'] = title
            dict['image'] = image
            dict['desc'] = desc
            dict['link'] = link
            dict['mode'] = "openCategoryList"
            list.append(dict)
            i = i + 1
        return list
    
    def getLinks(self,url,banner):
        videoUrls = []
        
        url = str(urllib.unquote(url))

        if banner != None:
            banner = urllib.unquote(banner)
        
     
        html = common.fetchPage({'link': url})
        data = common.parseDOM(html.get("content"),name='div',attrs={'class': "jsb_ jsb_VideoPlaylist"},ret='data-jsb')
        
        data = data[0]
        data = common.replaceHTMLCodes(data)
        data = json.loads(data)
        
        video_items = data.get("playlist")["videos"]
        
        try:
            current_title_prefix = data.get("selected_video")["title_prefix"]
            current_title = data.get("selected_video")["title"]
            current_desc = data.get("selected_video")["description"].encode('UTF-8')
            current_duration = data.get("selected_video")["duration"]
            current_preview_img = data.get("selected_video")["preview_image_url"]
            if "subtitles" in data.get("selected_video"):
                current_subtitles = []
                for sub in data.get("selected_video")["subtitles"]:
                    current_subtitles.append(sub.get(u'src'))
            else:
                current_subtitles = None
            current_id = data.get("selected_video")["id"]
            current_videourl = getVideoUrl(data.get("selected_video")["sources"]);
        except Exception, e:
            current_subtitles = None

        if len(video_items) > 1:
            parameters = {"mode" : "playList"}
            u = sys.argv[0] + '?' + urllib.urlencode(parameters)
            createListItem("[ "+(translation(30015)).encode("utf-8")+" ]",banner,(translation(30015)).encode("utf-8"),"","","",u,'false',False)
            for video_item in video_items:
                try:
                    title_prefix = video_item["title_prefix"]
                    title = video_item["title"].encode('UTF-8')
                    desc = video_item["description"].encode('UTF-8')
                    duration = video_item["duration"]
                    preview_img = video_item["preview_image_url"]
                    id = video_item["id"]
                    sources = video_item["sources"]
                    if "subtitles" in video_item:
                        subtitles = []
                        for sub in video_item["subtitles"]:
                            subtitles.append(sub.get(u'src'))
                    else:
                        subtitles = None
                    videourl = getVideoUrl(sources);
                    listItem = createListItem(title,preview_img,desc,duration,'','',videourl,'true',False,subtitles)
                    playlist.add(videourl,listItem)
                except Exception, e:
                    continue
        else:
            listItem = createListItem(current_title,current_preview_img,current_desc,current_duration,'','',current_videourl,'true',False,current_subtitles)
            playlist.add(current_videourl,listItem)
        listCallback(False)