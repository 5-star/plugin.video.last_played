# -*- coding: utf-8 -*-
import os, time
import json
import urllib, urllib2
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
enable_debug = addon.getSetting('enable_debug')
lang = addon.getLocalizedString

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

def videoEnd():
	retry=1
	xsource=''
	while xsource=='' and retry<50:
		xsource = xbmc.getInfoLabel('ListItem.Path').decode("utf-8")
		retry=retry+1
		time.sleep(0.1)

	if xsource!='':
		xtitle = xbmc.getInfoLabel('ListItem.Title').decode("utf-8").strip()
		xyear = xbmc.getInfoLabel('ListItem.Year')
		xfile = xbmc.getInfoLabel('ListItem.FileNameAndPath').decode("utf-8").strip()
		xid = xbmc.getInfoLabel('ListItem.DBID')
		xtype = xbmc.getInfoLabel('ListItem.DBTYPE')
		xthumb = xbmc.getInfoLabel('ListItem.Art(thumb)').decode("utf-8")
		xfanart = xbmc.getInfoLabel('ListItem.Art(fanart)').decode("utf-8")
		xshow = xbmc.getInfoLabel('ListItem.TVShowTitle').decode("utf-8").strip()
		xseason = xbmc.getInfoLabel('ListItem.Season')
		xepisode = xbmc.getInfoLabel('ListItem.Episode')
		xvideo = player_monitor.video
		
		if int(xid)>0:
			if xtype=="movie": xsource=lang(30002)
			elif xtype=="episode": xsource=lang(30003)
			elif xtype=="musicvideo": xsource=lang(30004)
			else: xsource=lang(30022)
		else:
			ads = xsource.split("/")
			if len(ads) > 2: xsource = ads[2]
	
		if enable_debug	== "true": xbmc.log("<<<plugin.video.last_played (end source) "+xsource, 3)
		if xbmcvfs.exists(txtfile):
			f = xbmcvfs.File(txtfile)
			try: lines = json.load(f)
			except: lines = []
			f.close()
		else: lines = []

		replay = "N"
		for line in lines:
			if xfile==line["file"]: replay = "S"
			if "video" in line and xvideo==line["video"]: replay = "S"
			if replay == "S":
				lines.remove(line)
				line.update({"date": time.strftime("%Y-%m-%d")})
				line.update({"time": time.strftime("%H:%M:%S")})
				lines.insert(0, line)
				replay = "S"
				if enable_debug	== "true": xbmc.log("<<<plugin.video.last_played (end final replay) "+str(line), 3)
				break

		if replay=="N":
			newline = {"source":xsource, "title":xtitle, "year":xyear, "file":xfile, "video": xvideo, "id":xid, "type":xtype,"thumbnail":xthumb, "fanart":xfanart, "show":xshow, "season":xseason, "episode":xepisode, "date":time.strftime("%Y-%m-%d"), "time":time.strftime("%H:%M:%S")}
			lines.insert(0, newline)
			if enable_debug	== "true": xbmc.log("<<<plugin.video.last_played (end final play) "+str(newline), 3)
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
		player_monitor.video = player_monitor.getPlayingFile()
				
player_monitor = KodiPlayer()

while not xbmc.abortRequested:
	xbmc.sleep(1000)

del player_monitor
