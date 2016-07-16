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

	def onPlayBackStarted(self):
		request = self._buildRequest('Player.GetItem', {'playerid' : 1, 'properties' : ['file', 'title', 'year', 'thumbnail', 'fanart']})
		result, data = self._query(request)[:2]
		if ( result and 'item' in data and data['item'] ):
			item = data['item']
			pu=xbmc.Player().getVideoInfoTag().getPictureURL()
			if pu=='' and item['type']!='musicvideo':
				xbmc.log("#############item '%s'" % str(item), 3)
				getTitle=xbmc.Player().getVideoInfoTag().getTitle().strip()
				if getTitle=='': getTitle=item['title']
				if getTitle=='': getTitle=item['label']
				if getTitle != '':
					getYear = item['year']
					if getYear > 0: getTitle = getTitle + " (" + str(getYear) + ")"
					txtfile = profile + "list.txt"
				if item['thumbnail']=='': img = item['fanart'].strip()
				else: img = item['thumbnail'].strip()
				img = img.rstrip('/').replace('image://','')
				img = urllib.unquote(img)
				if not os.path.exists(profile):
					os.makedirs(profile)
				if xbmcvfs.exists(txtfile):
					with open(txtfile) as f:
						lines = f.readlines()
				else: lines = {}
				with open(txtfile, 'w') as f:
					url=item['file'].strip()
					list_count=1
					f.write(getTitle+chr(9)+url+chr(9)+img+chr(10))
					for line in lines:
						lin = line.split(chr(9))
						if len(lin)>2 and list_count<(list_size+20):
							#xbmc.log("#############item[file] '%s'" % item['file'].strip(), 3)
							if lin[1]!=url:
								f.write(line)
								list_count=list_count+1

player_monitor = KodiPlayer()

while not xbmc.abortRequested:
	xbmc.sleep(1000)

del player_monitor
