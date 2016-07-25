import os, re, sys, time
import json
import urllib
import xbmc
import xbmcgui
import xbmcaddon
import xbmcvfs

addon = xbmcaddon.Addon()
profile = xbmc.translatePath(addon.getAddonInfo('profile')).decode("utf-8")
list_size = int(addon.getSetting('list_size'))
enable_debug = addon.getSetting('enable_debug')
newline="ignore"
lang = addon.getLocalizedString

class KodiPlayer(xbmc.Player):
	def __init__(self, *args, **kwargs):
		xbmc.Player.__init__(self)

	# Checks JSON response and returns boolean result
	def _checkReponse(self, response):
		result = False
		if ( ('result' in response) and ('error' not in response) ):
			result = True
		return result
		
	# Executes JSON request and returns the JSON response
	def _execute(self, request):
		request_string = json.dumps(request)
		response = xbmc.executeJSONRPC(request_string)  
		if ( response ):
			response = json.loads(response)
		return response
    
	# Builds JSON request with provided json data
	def _buildRequest(self, method, params={}, jsonrpc='2.0', rid='1'):
		request = { 'jsonrpc' : jsonrpc, 'method' : method, 'params' : params, 'id' : rid, }
		return request
		
	# Performs single JSON query and returns result boolean, data dictionary and error string
	def _query(self, request):
		result = False
		data = {}
		error = ''
		if ( request ):
			response = self._execute(request)
			if ( response ):
				result = self._checkReponse(response)
				if ( result ):
					data = response['result']
				else: error = response['error']
		return (result, data, error)
	 
	def videoEnd(self):
		global newline
		if enable_debug	== "true": xbmc.log("<<<plugin.video.last_played 56 "+newline, 3)
		if newline != 'ignore':
			retry=1
			addon=''
			while addon=='' and retry<50:
				addon = xbmc.getInfoLabel('ListItem.Path')
				retry=retry+1
				time.sleep(0.1)
			if enable_debug	== "true": xbmc.log("<<<plugin.video.last_played 64 "+addon, 3)
			txtfile = profile + "list.txt"
			if not os.path.exists(profile):
				os.makedirs(profile)
			if xbmcvfs.exists(txtfile):
				with open(txtfile) as f:
					lines = f.readlines()
			else: lines = {}
			with open(txtfile, 'w') as f:
				#line = newline.split(chr(9))
				list_count=1
				if enable_debug	== "true": xbmc.log("<<<plugin.video.last_played 75 "+newline, 3)
				if addon[0:4]=='http':
					addon='plugin://plugin.video.last_played/'
					f.write(newline+chr(9)+addon+chr(10))
				else:
					if addon=='': addon=lang(30012)
					dt=time.strftime("%Y-%m-%d")
					tm=time.strftime("%H:%M:%S")
					f.write(newline+chr(9)+addon+chr(9)+dt+chr(9)+tm+chr(10))
				for line in lines:
					lin = line.split(chr(9))
					if len(lin)>2 and list_count<(list_size+20):
						if lin[1]!=line[1]:
							f.write(line)
							list_count=list_count+1
		newline="ignore"

	def onPlayBackStarted(self):
		request = self._buildRequest('Player.GetItem', {'playerid' : 1, 'properties' : ['file', 'title', 'year', 'thumbnail', 'fanart']})
		result, data = self._query(request)[:2]
		if enable_debug	== "true": xbmc.log("<<<plugin.video.last_played 95 "+str(data), 3)
		global newline
		newline = 'ignore'
		if ( result and 'item' in data and data['item'] ):
			item = data['item']
			if item['file'][0:4]=='http' or item['type']=='unknown':
				getTitle=xbmc.Player().getVideoInfoTag().getTitle().strip()
				if getTitle=='': getTitle=item['title']
				if getTitle=='': getTitle=item['label']
				if getTitle != '':
					getYear = item['year']
					if getYear > 0: getTitle = getTitle + " (" + str(getYear) + ")"
				if item['thumbnail']=='': img = item['fanart'].strip()
				else: img = item['thumbnail'].strip()
				img = img.rstrip('/').replace('image://','')
				img = urllib.unquote(img)
				newline = getTitle+chr(9)+item['file'].strip()+chr(9)+img
				if enable_debug	== "true": xbmc.log("<<<plugin.video.last_played 112 "+newline, 3)

	def onPlayBackEnded(self):
		self.videoEnd()

	def onPlayBackStopped(self):
		self.videoEnd()

player_monitor = KodiPlayer()

while not xbmc.abortRequested:
	xbmc.sleep(1000)

del player_monitor
