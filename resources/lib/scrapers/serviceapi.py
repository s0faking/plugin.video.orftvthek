#!/usr/bin/python
# -*- coding: utf-8 -*-
import urllib,urllib2,re,xbmcplugin,xbmcgui,sys,xbmcaddon,base64,socket,datetime,time,os,os.path,urlparse,json
import CommonFunctions as common

    
class serviceAPI:
    # serviceAPI Settings
    serviceAPItoken    = 'ef97318c84d4e8'

    serviceAPIEpisode  = 'http://tvthek.orf.at/service_api/token/%s/episode/%s/'
    serviceAPIDate     = 'http://tvthek.orf.at/service_api/token/%s/episodes/by_date/%s?page=0&entries_per_page=1000'
    serviceAPIDateFrom = 'http://tvthek.orf.at/service_api/token/%s/episodes/from/%s0000/till/%s0000?page=0&entries_per_page=1000'
    serviceAPIProgram  = 'http://tvthek.orf.at/service_api/token/%s/episodes/by_program/%s'
    serviceAPISearch   = 'http://tvthek.orf.at/service_api/token/%s/search/%s?page=0&entries_per_page=1000'
    servieAPITopic     = 'http://tvthek.orf.at/service_api/token/%s/topic/%s/'

    serviceAPIPrograms = 'http://tvthek.orf.at/service_api/token/%s/programs?page=0&entries_per_page=1000'
    serviceAPITopics   = 'http://tvthek.orf.at/service_api/token/%s/topics?page=0&entries_per_page=1000'
    serviceAPITrailers = 'http://tvthek.orf.at/service_api/token/%s/episodes/trailers?page=0&entries_per_page=1000'

    serviceAPILive     = 'http://tvthek.orf.at/service_api/token/%s/livestreams/from/%s/till/%s/detail?page=0&entries_per_page=%i'
    serviceAPITip      = 'http://tvthek.orf.at/service_api/token/%s/teaser_content/recommendations'
    serviceAPIHighlights      = 'http://tvthek.orf.at/service_api/token/%s/teaser_content/highlights'
    serviceAPIRecent   = 'http://tvthek.orf.at/service_api/token/%s/teaser_content/newest'
    serviceAPIViewed   = 'http://tvthek.orf.at/service_api/token/%s/teaser_content/most_viewed'

    
    def __init__(self,xbmc,settings,pluginhandle,quality,protocol,delivery):
        self.translation = settings.getLocalizedString
        self.xbmc = xbmc
        self.videoQuality = quality
        self.videoDelivery = delivery
        self.videoProtocol = protocol
        self.pluginhandle = pluginhandle
        self.xbmc.log(msg='Using ServiceAPI', level=xbmc.LOGDEBUG);
        
    def getTableResults(self, urlAPI):
        list = []
        urlAPI = urlAPI % self.serviceAPItoken
        try:
            response = urllib2.urlopen(urlAPI)
            responseCode = response.getcode()
        except urllib2.HTTPError, error:
            responseCode = error.getcode()
            pass

        if responseCode == 200:
            global time

            jsonData = json.loads(response.read())
            if 'teaserItems' in jsonData:
                results = jsonData['teaserItems']
            else:
                results = jsonData['episodeShorts']

            for result in results:
                title       = result.get('title').encode('UTF-8')
                image       = self.JSONImage(result.get('images'))
                if image == '':
                    image = self.JSONImage(result.get('images'), 'logo')
                description = self.JSONDescription(result.get('descriptions'))
                duration    = result.get('duration')
                date        = time.strptime(result.get('date'), '%d.%m.%Y %H:%M:%S')

                description = '%s %s\n\n%s' % ((self.translation(30009)).encode("utf-8"), time.strftime('%A, %d.%m.%Y - %H:%M Uhr', date), description)

                parameters = {'mode' : 'openEpisode', 'link': result.get('episodeId')}
                u = sys.argv[0] + '?' + urllib.urlencode(parameters)
                # Direcotory should be set to False, that the Duration is shown.
                # But then there is an error with the Pluginhandle
                dict = {}
                dict['title'] = title
                dict['image'] = image
                dict['desc'] = description
                dict['link'] = result.get('episodeId')
                dict['mode'] = 'openEpisode'
                list.append(dict)
            return list
        else:
            self.xbmc.log(msg='ServiceAPI no available ... switch back to HTML Parsing in the Addon Settings', level=xbmc.LOGDEBUG);
            
            
    # Useful  Methods for JSON Parsing
    def JSONEpisode2ListItem(self,JSONEpisode, ignoreEpisodeType = None):
        title        = JSONEpisode.get('title').encode('UTF-8')
        image        = JSONImage(JSONEpisode.get('images'))
        description  = JSONDescription(JSONEpisode.get('descriptions'))
        duration     = JSONEpisode.get('duration')
        date         = time.strptime(JSONEpisode.get('date'), '%d.%m.%Y %H:%M:%S')
        link         = JSONEpisode.get('episodeId')

        if JSONEpisode.get('episodeType') == ignoreEpisodeType:
            return None

        parameters = {'mode' : 'openEpisode', 'link': link}
        u = sys.argv[0] + '?' + urllib.urlencode(parameters)
        # Direcotory should be set to False, that the Duration is shown.
        # But then there is an error with the Pluginhandle
        return createListItem(title, image, description, duration, time.strftime('%Y-%m-%d', date), '', u, 'false', True)


    def JSONSegment2ListItem(self,JSONSegment, date):
        title        = JSONSegment.get('title').encode('UTF-8')
        image        = JSONImage(JSONSegment.get('images'))
        description  = JSONDescription(JSONSegment.get('descriptions'))
        duration     = JSONSegment.get('duration')
        streamingURL = JSONStreamingURL(JSONSegment.get('videos'))
        if JSONSegment.get('subtitlesSrtFileUrl'):
            subtitles = [JSONSegment.get('subtitlesSrtFileUrl')]
        else:
            subtitles = None
        return [streamingURL, createListItem(title, image, description, duration, time.strftime('%Y-%m-%d', date), '', streamingURL, 'true', False, subtitles)]

    def JSONDescription(self,jsonDescription):
        desc = ''
        for description in jsonDescription:
            if description.get('text') != None:
                if len(description.get('text')) > len(desc):
                    desc = description.get('text')
                if description.get('fieldName') == 'description':
                    return description.get('text').encode('UTF-8')
        return desc.encode('UTF-8')

    def JSONImage(self,jsonImages, name = 'image_full'):
        logo = ''
        for image in jsonImages:
            if image.get('name') == name:
                return image.get('url')
            elif image.get('name') == 'logo':
                logo = image.get('url')
        return logo

    def JSONStreamingURL(self,jsonVideos):
        for streamingURL in jsonVideos:
            streamingURL = streamingURL.get('streamingUrl')
            if 'http' in streamingURL and 'mp4/playlist.m3u8' in streamingURL:
                return streamingURL.replace('Q4A', self.videoQuality)
        return ''
    
    # list all Categories
    def getCategories(self):
        list = []
        try:
            response = urllib2.urlopen(self.serviceAPIPrograms % self.serviceAPItoken)
            responseCode = response.getcode()
        except urllib2.HTTPError, error:
            responseCode = error.getcode()
            pass

        if responseCode == 200:
            for result in json.loads(response.read())['programShorts']:
                title       = result.get('name').encode('UTF-8')
                image       = self.JSONImage(result.get('images'), 'logo')
                description = ''
                link        = result.get('programId')

                if result.get('episodesCount') == 0:
                    continue

                dict = {}
                dict['title'] = title
                dict['image'] = image
                dict['desc'] = description
                dict['link'] = link
                dict['mode'] = 'openProgram'
                list.append(dict)
        return list
        
    
    # list all Episodes for the given Date
    def getDate(self, date, dateFrom = None):
        if dateFrom == None:
            url = serviceAPIDate % (serviceAPItoken, date)
        else:
            url = serviceAPIDateFrom % (serviceAPItoken, dateFrom, date)
        response = urllib2.urlopen(url)

        if dateFrom == None:
            episodes = json.loads(response.read())['episodeShorts']
        else:
            episodes = reversed(json.loads(response.read())['episodeShorts'])

        for episode in episodes:
            JSONEpisode2ListItem(episode)

        listCallback(False)


    # list all Entries for the given Topic
    def getTopic(self,topicID):
        url = self.servieAPITopic % (self.serviceAPItoken, topicID)
        response = urllib2.urlopen(url)

        for entrie in json.loads(response.read())['topicDetail'].get('entries'):
            title       = entrie.get('title').encode('UTF-8')
            image       = JSONImage(entrie.get('images'))
            description = JSONDescription(entrie.get('descriptions'))
            duration    = entrie.get('duration')
            date        = time.strptime(entrie.get('date'), '%d.%m.%Y %H:%M:%S')

            if entrie.get('teaserItemType') == 'episode':
                parameters = {'mode' : 'openEpisode', 'link': entrie.get('episodeId')}
            elif entrie.get('teaserItemType') == 'segment':
                parameters = {'mode' : 'openSegment', 'link': entrie.get('episodeId'), 'segmentID': entrie.get('segmentId')}
            else:
                continue

            u = sys.argv[0] + '?' + urllib.urlencode(parameters)
            # Direcotory should be set to False, that the Duration is shown.
            # But then there is an error with the Pluginhandle
            self.createListItem(title, image, description, duration, time.strftime('%Y-%m-%d', date), '', u, 'false', True)

        


    # list all Episodes for the given Broadcast
    def getProgram(self,programID):
        url = self.serviceAPIProgram % (self.serviceAPItoken, programID)
        response = urllib2.urlopen(url)
        responseCode = response.getcode()

        if responseCode == 200:
            episodes = json.loads(response.read())['episodeShorts']
            if len(episodes) == 1:
                for episode in episodes:
                    getEpisode(episode.get('episodeId'))
                    return

            for episode in episodes:
                self.JSONEpisode2ListItem(episode, 'teaser')

            


    # listst all Segments for the Episode with the given episodeID
    # If the Episode only contains one Segment, that get played instantly.
    def getEpisode(self,episodeID,playlist):
        playlist.clear()

        url = self.serviceAPIEpisode % (self.serviceAPItoken, episodeID)
        response = urllib2.urlopen(url)
        result = json.loads(response.read())['episodeDetail']

        title       = result.get('title').encode('UTF-8')
        image       = self.JSONImage(result.get('images'))
        description = self.JSONDescription(result.get('descriptions'))
        duration    = result.get('duration')
        date        = time.strptime(result.get('date'), '%d.%m.%Y %H:%M:%S')

        referenceOtherEpisode = False
        for link in result.get('links'):
            if link.get('identifier') == 'program':
                referenceOtherEpisode = True
                addDirectory(link.get('name').encode('UTF-8'), '', '', link.get('id'), 'openProgram')

        if referenceOtherEpisode:
            listCallback(False)
            return

        if len(result.get('segments')) == 1:
            for segment in result.get('segments'):
                image        = self.JSONImage(segment.get('images'))
                streamingURL = self.JSONStreamingURL(segment.get('videos'))
                if segment.get('subtitlesSrtFileUrl'):
                    subtitles = [segment.get('subtitlesSrtFileUrl')]
                else:
                    subtitles = None

            listItem = self.createListItem(title, image, description, duration, time.strftime('%Y-%m-%d', date), '', streamingURL, 'true', False, subtitles)
            playlist.add(streamingURL, listItem)
            self.xbmc.Player().play(playlist)

        else:
            parameters = {'mode' : 'playList'}
            u = sys.argv[0] + '?' + urllib.urlencode(parameters)
            createListItem('[ '+(translation(30015)).encode('UTF-8')+' ]', image, '%s\n%s' % ((translation(30015)).encode('UTF-8'), description), duration, time.strftime('%Y-%m-%d', date), '', u, 'false', False)

            for segment in result.get('segments'):
                listItem = JSONSegment2ListItem(segment, date)
                playlist.add(listItem[0], listItem[1])

            listCallback(False)


    # Plays the given Segment, if it is included in the given Episode
    def getSegment(self,episodeID, segmentID):
        playlist.clear()

        url = self.serviceAPIEpisode % (self.serviceAPItoken, episodeID)
        response = urllib2.urlopen(url)
        responseCode = response.getcode()

        if responseCode == 200:
            result = json.loads(response.read())['episodeDetail']
            date = time.strptime(result.get('date'), '%d.%m.%Y %H:%M:%S')
            for segment in result.get('segments'):
                if segment.get('segmentId') == int(segmentID):
                    listItem = self.JSONSegment2ListItem(segment, date)
                    playlist.add(listItem[0], listItem[1])
                    xbmc.Player().play(playlist)
                    return

    def createListItem(self,title,banner,description,duration,date,channel,videourl,playable,folder,subtitles=None): 
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

        xbmcplugin.addDirectoryItem(handle=self.pluginhandle, url=videourl, listitem=liz, isFolder=folder)
        return liz
                    
                    
    # list all Trailers for further airings
    def getTrailers(self):
        url = serviceAPITrailers % serviceAPItoken
        response = urllib2.urlopen(url)

        for episode in json.loads(response.read())['episodeShorts']:
            self.JSONEpisode2ListItem(episode)

        listCallback(False)