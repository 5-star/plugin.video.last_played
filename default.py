# -*- coding: utf-8 -*-
import os, time
import json
import ssl
import xbmc
import xbmcaddon
import xbmcvfs

try:
    from urllib.parse import quote, unquote
    import urllib.request
    python="3"
except ImportError:
    from urllib import quote, unquote
    import urllib2
    python="2"

addon = xbmcaddon.Addon()
enable_debug = addon.getSetting('enable_debug')
if addon.getSetting('custom_path_enable') == "true" and addon.getSetting('custom_path') != "":
    txtpath = addon.getSetting('custom_path')
else:
    txtpath = xbmcvfs.translatePath(addon.getAddonInfo('profile'))
    if not os.path.exists(txtpath):
        os.makedirs(txtpath)
txtfile = txtpath + "lastPlayed.json"
starmovies = addon.getSetting('starmovies')
lang = addon.getLocalizedString

class LP:
    title = ""
    year = ""
    thumbnail = ""
    fanart = ""
    showtitle = ""
    season = ""
    episode = ""
    DBID = ""
    type = ""
    file=""
    video=""
    artist=""
    vidPos=1
    vidTot=1000

lp=LP()

player_monitor = xbmc.Monitor()

def getRequest2(url):
    try:
        context = ssl._create_unverified_context()
        request = urllib2.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        response = urllib2.urlopen(request, context=context)
        return response
    except:
        pass

def getRequest3(url):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            return(response.read())
    except:
        pass
        
# Builds JSON request with provided json data
def buildRequest(method, params, jsonrpc='2.0', rid='1'):
    request = { 'jsonrpc' : jsonrpc, 'method' : method, 'params' : params, 'id' : rid }
    return request

# Checks JSON response and returns boolean result
def checkReponse(response):
    result = False
    if ( ('result' in response) and ('error' not in response) ):
        result = True
    return result

# Executes JSON request and returns the JSON response
def JSexecute(request):
    request_string = json.dumps(request)
    response = xbmc.executeJSONRPC(request_string)
    if ( response ):
        response = json.loads(response)
    return response

# Performs single JSON query and returns result boolean, data dictionary and error string
def JSquery(request):
    result = False
    data = {}
    error = ''
    if ( request ):
        response = JSexecute(request)
        if ( response ):
            result = checkReponse(response)
            if ( result ):
                data = response['result']
            else: error = response['error']
    return (result, data, error)

def send2starmovies(line):
    if enable_debug	== "true": xbmc.log("<<<plugin.video.last_played (starmovies) "+str(line), 3)
    if LP.vidPos/LP.vidTot<0.8: return
    wid = 0
    if line["id"]!="": wid = int(line["id"])
    if line["type"]=="movie": typ="M"
    elif line["type"]=="episode": typ="S"
    elif line["type"]=="song": typ="P"
    else: typ="V"
    if enable_debug	== "true": xbmc.log("<<<plugin.video.last_played (starmovies) "+str(addon.getSetting('smovies')), 3)

    if typ=="M" and addon.getSetting('smovies') != "true": return
    if typ=="S" and addon.getSetting('stv') != "true": return
    if typ=="V" : return
    if typ=="P" : return

    imdbId = ""
    tvdbId = ""
    orgTitle = ""
    showTitle = line["show"]
    season = line["season"]
    episode = line["episode"]
    thumbnail = line["thumbnail"]
    fanart = line["fanart"]

    if enable_debug	== "true": xbmc.log("<<<plugin.video.last_played (starmovies) "+str(wid), 3)
    if wid>0:
        if typ=="M":
            request = buildRequest('VideoLibrary.GetMovieDetails', {'movieid' : wid, 'properties' : ['imdbnumber', 'originaltitle']})
            result, data = JSquery(request)[:2]
            if ( result and 'moviedetails' in data ):
                imdbId = data['moviedetails']["imdbnumber"]
                orgTitle = data['moviedetails']["originaltitle"]
        elif typ=="S":
            request = buildRequest('VideoLibrary.GetEpisodeDetails', {'episodeid' : wid, 'properties' : ['tvshowid', 'season', 'episode']})
            result, data = JSquery(request)[:2]
            if ( result and 'episodedetails' in data ):
                season = data['episodedetails']["season"]
                episode = data['episodedetails']["episode"]
                request = buildRequest('VideoLibrary.GetTvShowDetails', {'tvshowid' : data['episodedetails']["tvshowid"], 'properties' : ['imdbnumber', 'originaltitle']})
                result, data = JSquery(request)[:2]
                if ( result and 'tvshowdetails' in data ):
                    showTitle = data['tvshowdetails']["label"]
                    orgTitle = data['tvshowdetails']["originaltitle"]
                    tvdbId = data['tvshowdetails']["imdbnumber"]

    xvideo = line["file"]
    if "video" in line and line["video"]!="": xvideo = line["video"]
    url = "https://www.starmovies.org/WebService.asmx/kodiWatch?tmdbId="
    url = url + "&tvdbId=" + tvdbId
    url = url + "&imdbId=" + imdbId
    url = url + "&kodiId=" + str(wid)
    url = url + "&title=" + quote(line["title"].encode("utf-8"))
    url = url + "&orgtitle=" + quote(orgTitle.encode("utf-8"))
    url = url + "&year=" + str(line["year"])
    url = url + "&source=" + quote(line["source"].encode("utf-8"))
    url = url + "&type=" + typ
    url = url + "&usr=" + quote(addon.getSetting('TMDBusr').encode("utf-8"))
    url = url + "&pwd=" + addon.getSetting('TMDBpwd')
    url = url + "&link=" + quote(xvideo.encode("utf-8"))
    url = url + "&thumbnail=" + quote(line["thumbnail"].encode("utf-8"))
    url = url + "&fanart=" + quote(line["fanart"].encode("utf-8"))
    url = url + "&showtitle=" + quote(showTitle.encode("utf-8"))
    url = url + "&season=" + str(season)
    url = url + "&episode=" + str(episode)
    url = url + "&version=1.22"
    url = url + "&date=" + line["date"]
    if enable_debug	== "true": xbmc.log("<<<plugin.video.last_played (starmovies) "+url, 3)
    if python=="3":
        response = getRequest3(url)
    else:
        response = getRequest2(url)
    if enable_debug	== "true": xbmc.log("<<<plugin.video.last_played (starmovies) response:"+str(response), 3)

def videoEnd():
    retry=1
    xsource=''
    while xsource=='' and retry<50:
        xsource = xbmc.getInfoLabel('ListItem.Path')
        retry=retry+1
        time.sleep(0.1)

    if xsource=='': xsource="player"
    xtitle = lp.title
    xyear = lp.year
    xartist = lp.artist
    xid = lp.DBID
    xtype = lp.type
    xfanart = unquote(lp.fanart).replace("image://","").rstrip("/")
    xthumb = unquote(lp.thumbnail).replace("image://","").rstrip("/")	
    if ".jpg" not in xthumb.lower(): xthumb=xfanart
    xfile = lp.file.strip()
    xvideo = lp.video.strip()

    try:
        xshow = lp.showtitle
        xseason = lp.season
        xepisode = lp.episode
    except:
        pass

    if xid!="" and int(xid)>0:
        if xtype=="movie": xsource=lang(30002)
        elif xtype=="episode": xsource=lang(30003)
        elif xtype=="musicvideo": xsource=lang(30004)
        else: xsource=xtype
    else:
        ads = xsource.split("/")
        if len(ads) > 2: xsource = ads[2]

    # if source is on blacklist, do not keep
    if xtype=="movie" and addon.getSetting('movies') != "true": return
    if xtype=="episode" and addon.getSetting('tv') != "true": return
    if xtype=="song" and addon.getSetting('music') != "true": return
    if xtype!="movie" and xtype!="episode" and xtype!="song" and addon.getSetting('videos') != "true": return

    # if source is on blacklist, do not keep
    if addon.getSetting('blackadddon').lower().find(xsource.lower())>=0: return
    if addon.getSetting('blackfolder')!="":
        for dir in addon.getSetting('blackfolder').lower().split(","):
            if xsource.lower().find(dir)>=0: return
    if addon.getSetting('blackvideo')!="":
        for vid in addon.getSetting('blackvideo').lower().split(","):
            if xtitle.lower().find(vid)>=0: return
    
    if enable_debug	== "true": xbmc.log("<<<plugin.video.last_played (end source) "+xsource, 3)
    if xbmcvfs.exists(txtfile):
        f = xbmcvfs.File(txtfile)
        try: lines = json.load(f)
        except: lines = []
        f.close()
    else: lines = []

    replay = "N"
    for line in lines:
        if xfile!="" and xfile==line["file"]: replay = "S"
        if replay == "S":
            lines.remove(line)
            line.update({"date": time.strftime("%Y-%m-%d")})
            line.update({"time": time.strftime("%H:%M:%S")})
            lines.insert(0, line)
            replay = "S"
            if enable_debug	== "true": xbmc.log("<<<plugin.video.last_played (end final replay) "+str(line), 3)
            if starmovies	== "true": send2starmovies(line)
            break

    if replay=="N":
        newline = {"source":xsource, "title":xtitle, "year":xyear, "artist":xartist, "file":xfile, "video":xvideo, "id":xid, "type":xtype,"thumbnail":xthumb, "fanart":xfanart, "show":xshow, "season":xseason, "episode":xepisode, "date":time.strftime("%Y-%m-%d"), "time":time.strftime("%H:%M:%S") }
        lines.insert(0, newline)
        if enable_debug	== "true": xbmc.log("<<<plugin.video.last_played (end final play) "+str(newline), 3)
        if starmovies	== "true": send2starmovies(newline)
        if len(lines)>100:
            del lines[len(lines)-1]

    if len(lines)>0:
        f = xbmcvfs.File(txtfile, 'w')
        json.dump(lines, f)
        f.close()
          
class KodiPlayer(xbmc.Player):
    def __init__(self, *args, **kwargs):
        kplayer=xbmc.Player.__init__(self)

    @classmethod
    def onPlayBackEnded(self):
        videoEnd()

    @classmethod
    def onPlayBackStopped(self):
        videoEnd()

    def onPlayBackStarted(self):
        if xbmc.getCondVisibility('Player.HasMedia'):
            lp.video = self.getPlayingFile()
            request = {"jsonrpc": "2.0", "method": "Player.GetItem", "params": { "properties": ["title", "year", "thumbnail", "fanart", "showtitle", "season", "episode", "file"], "playerid": 1 }, "id": "VideoGetItem"}
            result, data = JSquery(request)[:2]
            if(len(data)==0):
                request = {"jsonrpc": "2.0", "method": "Player.GetItem", "params": { "properties": ["title", "album", "artist", "duration", "thumbnail", "file", "fanart", "streamdetails"], "playerid": 0 }, "id": "AudioGetItem"}
                result, data = JSquery(request)[:2]
            if len(data)>0:
                item=data["item"]
                if enable_debug	== "true": xbmc.log("<<<plugin.video.last_played (start play) "+str(item), 3)
                if "title" in item: lp.title = item["title"]
                if lp.title=="" and "label" in item: lp.title = item["label"]		
                if "year" in item: lp.year = item["year"]
                if "thumbnail" in item: lp.thumbnail = item["thumbnail"]
                if "fanart" in item: lp.fanart = item["fanart"]
                if "showtitle" in item: lp.showtitle = item["showtitle"]
                if "season" in item and item["season"]>0: lp.season = item["season"]
                if "episode" in item and item["episode"]>0: lp.episode = item["episode"]
                if "id" in item: lp.DBID = item["id"]
                if "type" in item: lp.type = item["type"]
                if "file" in item: lp.file = item["file"]
                if "artist" in item: lp.artist = item["artist"]

class KodiRunner:
    player = KodiPlayer()

    while not player_monitor.abortRequested():
        if player.isPlaying():
            LP.vidPos=player.getTime()
            LP.vidTot=player.getTotalTime()
        player_monitor.waitForAbort(1)

    del player
