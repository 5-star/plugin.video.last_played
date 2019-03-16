# -*- coding: utf-8 -*-
import os, time
import json
import urllib, urllib2
import ssl
import xbmc
import xbmcaddon
import xbmcvfs

addon = xbmcaddon.Addon()
enable_debug = addon.getSetting('enable_debug')
if addon.getSetting('custom_path_enable') == "true" and addon.getSetting('custom_path') != "":
	txtpath = addon.getSetting('custom_path').decode("utf-8")
else:
	txtpath = xbmc.translatePath(addon.getAddonInfo('profile')).decode("utf-8")
	if not os.path.exists(txtpath):
		os.makedirs(txtpath)
txtfile = txtpath + "lastPlayed.json"
starmovies = addon.getSetting('starmovies')
lang = addon.getLocalizedString
vidPos=1
vidTot=1000

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
	if vidPos/vidTot<0.8: return
	wid = 0
	if line["id"]!="": wid = int(line["id"])
	if line["type"]=="movie": typ="M"
	elif line["type"]=="episode": typ="S"
	elif line["type"]=="song": typ="P"
	else: typ="V"

	if typ=="M" and addon.getSetting('smovies') != "true": return
	if typ=="S" and addon.getSetting('stv') != "true": return
	if typ=="V" and addon.getSetting('svideos') != "true": return
	if typ=="P" : return

	imdbId = ""
	tvdbId = ""
	orgTitle = ""
	showTitle = line["show"]
	season = line["season"]
	episode = line["episode"]
	thumbnail = line["thumbnail"]
	fanart = line["fanart"]

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
	url = url + "&title=" + urllib.quote(line["title"].encode("utf-8"))
	url = url + "&orgtitle=" + urllib.quote(orgTitle.encode("utf-8"))
	url = url + "&year=" + str(line["year"])
	url = url + "&source=" + urllib.quote(line["source"].encode("utf-8"))
	url = url + "&type=" + typ
	url = url + "&usr=" + urllib.quote(addon.getSetting('TMDBusr').encode("utf-8"))
	url = url + "&pwd=" + addon.getSetting('TMDBpwd')
	url = url + "&link=" + urllib.quote(xvideo.encode("utf-8"))
	url = url + "&thumbnail=" + urllib.quote(line["thumbnail"].encode("utf-8"))
	url = url + "&fanart=" + urllib.quote(line["fanart"].encode("utf-8"))
	url = url + "&showtitle=" + urllib.quote(showTitle.encode("utf-8"))
	url = url + "&season=" + str(season)
	url = url + "&episode=" + str(episode)
	url = url + "&version=1.22"
	url = url + "&date=" + line["date"]
	if enable_debug	== "true": xbmc.log("<<<plugin.video.last_played (starmovies) "+url, 3)
	try:
		context = ssl._create_unverified_context()
		request = urllib2.Request(url)
		response = urllib2.urlopen(request, context=context)
	except:
		pass

def videoEnd():
	retry=1
	xsource=''
	while xsource=='' and retry<50:
		xsource = xbmc.getInfoLabel('ListItem.Path').decode("utf-8")
		retry=retry+1
		time.sleep(0.1)

	if xsource=='': xsource="player"	
	xtitle = xbmc.getInfoLabel('ListItem.Title').decode("utf-8").strip()
	if xtitle=="" : xtitle = player_monitor.title
	xyear = xbmc.getInfoLabel('ListItem.Year')
	if xyear is None : xyear = player_monitor.year
	xid = xbmc.getInfoLabel('ListItem.DBID')
	if xid=="": xid = player_monitor.DBID
	xtype = xbmc.getInfoLabel('ListItem.DBTYPE')
	if xtype=="": xtype = player_monitor.type
	xthumb = xbmc.getInfoLabel('ListItem.Art(thumb)').decode("utf-8")
	if xthumb=="": xthumb = player_monitor.thumbnail
	xfanart = xbmc.getInfoLabel('ListItem.Art(fanart)').decode("utf-8")
	if xfanart=="": xfanart = player_monitor.fanart
	xshow = xbmc.getInfoLabel('ListItem.TVShowTitle').decode("utf-8").strip()
	xseason = xbmc.getInfoLabel('ListItem.Season')
	xepisode = xbmc.getInfoLabel('ListItem.Episode')
	try:
		if xshow=="": xshow = player_monitor.showtitle
		if xseason=="": xseason = player_monitor.season
		if xepisode=="": xepisode = player_monitor.episode
	except:
		pass
	xvideo = player_monitor.video.decode("utf-8").strip()	
	xfile = xbmc.getInfoLabel('ListItem.FileNameAndPath').decode("utf-8").strip()
	
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
	if xtype=="song" and addon.getSetting('videos') != "true": return
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
		if "video" in line and xvideo==line["video"]: replay = "S"
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
		newline = {"source":xsource, "title":xtitle, "year":xyear, "file":xfile, "video": xvideo, "id":xid, "type":xtype,"thumbnail":xthumb, "fanart":xfanart, "show":xshow, "season":xseason, "episode":xepisode, "date":time.strftime("%Y-%m-%d"), "time":time.strftime("%H:%M:%S") }
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
		xbmc.Player.__init__(self)

	@classmethod
	def onPlayBackEnded(self):
		videoEnd()

	@classmethod
	def onPlayBackStopped(self):
		videoEnd()

	def onPlayBackStarted(self):
		player_monitor.title = ""
		player_monitor.year = ""
		player_monitor.thumbnail = ""
		player_monitor.fanart = ""
		player_monitor.showtitle = ""
		player_monitor.season = ""
		player_monitor.episode = ""
		player_monitor.DBID = ""
		player_monitor.type = ""
		if xbmc.getCondVisibility('Player.HasMedia'):
			player_monitor.video = player_monitor.getPlayingFile()
			request = {"jsonrpc": "2.0", "method": "Player.GetItem", "params": { "properties": ["title", "year", "thumbnail", "fanart", "showtitle", "season", "episode"], "playerid": 1 }, "id": "VideoGetItem"}
			result, data = JSquery(request)[:2]
			if len(data)>0:
				item=data["item"]
				if enable_debug	== "true": xbmc.log("<<<plugin.video.last_played (start play) "+str(item), 3)
				if "title" in item: player_monitor.title = item["title"]
				if player_monitor.title=="" and "label" in item: player_monitor.title = item["label"]		
				if "year" in item: player_monitor.year = item["year"]
				if "thumbnail" in item: player_monitor.thumbnail = item["thumbnail"]
				if "fanart" in item: player_monitor.fanart = item["fanart"]
				if "showtitle" in item: player_monitor.showtitle = item["showtitle"]
				if "season" in item and item["season"]>0: player_monitor.season = item["season"]
				if "episode" in item and item["episode"]>0: player_monitor.episode = item["episode"]
				if "id" in item: player_monitor.DBID = item["id"]
				if "type" in item: player_monitor.type = item["type"]
			
def getPosition():
	global vidPos
	global vidTot
	if player_monitor.isPlaying():
		vidPos=player_monitor.getTime()
		vidTot=player_monitor.getTotalTime()

player_monitor = KodiPlayer()

while not xbmc.abortRequested:
	xbmc.sleep(5000)
	getPosition()

del player_monitor
