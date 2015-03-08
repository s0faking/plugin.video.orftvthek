#!/usr/bin/python
# -*- coding: utf-8 -*-
import xbmcplugin,xbmcgui

def createListItem(title,banner,description,duration,date,channel,videourl,playable,folder,translation,backdrop,pluginhandle,subtitles=None): 
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
    liz.setProperty('fanart_image',backdrop)
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