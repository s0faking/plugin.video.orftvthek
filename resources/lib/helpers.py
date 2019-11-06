#!/usr/bin/python
# -*- coding: utf-8 -*-

import xbmc
import xbmcaddon
import sys

try:
    from urllib.parse import unquote, urlencode
    from urllib.request import urlopen as OpenRequest
    from urllib.request import Request as HTTPRequest
    from urllib.error import HTTPError
except ImportError:
    from urllib import unquote, urlencode
    from urllib2 import HTTPError
    from urllib2 import urlopen as OpenRequest
    from urllib2 import Request as HTTPRequest


def unqoute_url(url):
    return unquote(url)


def build_kodi_url(parameters):
    return sys.argv[0] + '?' + encode_parameters(parameters)


def encode_parameters(parameters):
    return urlencode(parameters)


def url_get_request(url, authorization=False):
    if authorization:
        request = HTTPRequest(url)
        request.add_header('Authorization', 'Basic %s' % authorization)
    else:
        request = url
    return OpenRequest(request)


def parameters_string_to_dict(parameters):
    paramDict = {}
    if parameters:
        paramPairs = parameters[1:].split("&")
        for paramsPair in paramPairs:
            paramSplits = paramsPair.split('=')
            if (len(paramSplits)) == 2:
                paramDict[paramSplits[0]] = paramSplits[1]
    return paramDict


def debugLog(message, loglevel=xbmc.LOGDEBUG):
    output = "[ORF TVTHEK] " + message
    xbmc.log(msg=output, level=loglevel)


def notifyUser(message):
    addon = xbmcaddon.Addon()
    name = addon.getAddonInfo('name')
    icon = addon.getAddonInfo('icon')
    xbmc.executebuiltin('Notification(%s, %s, %s, %s)' % (name, message, "", icon))

