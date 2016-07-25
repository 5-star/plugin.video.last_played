import sys, os, re
from datetime import datetime
import json
import urllib
import urlparse
import xbmc
import xbmcplugin
import xbmcaddon
import xbmcvfs
from xbmcgui import ListItem, Window
from xbmcplugin import addDirectoryItem, endOfDirectory

addon = xbmcaddon.Addon()
addon_handle = int(sys.argv[1])
args = urlparse.parse_qs(sys.argv[2][1:])
menu = args.get('menu', None)
list_size = int(addon.getSetting('list_size'))
show_addons = addon.getSetting('show_addons')
group_addons = addon.getSetting('group_addons')
show_date = addon.getSetting('show_date')
show_time = addon.getSetting('show_time')
enable_debug = addon.getSetting('enable_debug')
lang = addon.getLocalizedString
profile = xbmc.translatePath(addon.getAddonInfo('profile')).decode("utf-8")
imgPath=xbmc.translatePath(xbmcaddon.Addon().getAddonInfo('path')).decode('utf-8')
	
def url(pQuery):
	return sys.argv[0] + '?' + urllib.urlencode(pQuery)

def jsonrpc(query):
	return json.loads(xbmc.executeJSONRPC(json.dumps(query, encoding='utf-8')))

def list_items(items, type):
	xbmcplugin.setContent(addon_handle, type)
	for item in items:
		desc=''
		if show_date == "true": desc = desc + item['lastplayed'][0:10] + ' '
		if show_time == "true": desc = desc + item['lastplayed'][11:18] + ' '
		desc=desc + item['title']
		li = ListItem(label=desc)
		li.setInfo(type="Video", infoLabels={"mediatype": 'episode'})
		li.setProperty("type", "episode")
		addDirectoryItem(addon_handle, item['file'], li, False, len(items))
	endOfDirectory(addon_handle)
	
def get_items(pMethod, pResult):
	query = { "jsonrpc": "2.0", "method": pMethod, "id": 1, "params": { "properties": ["title", "file", "lastplayed" ], "sort": { "order": "descending", "method": "lastplayed" },  "limits": {"start" : 0, "end" : list_size } } }
	items = jsonrpc(query)['result'].get(pResult, [])
	return items

def list_addonitems(addon):
	xbmcplugin.setContent(addon_handle, "movies")
	txtfile = profile + "list.txt"
	if xbmcvfs.exists(txtfile):
		with open(txtfile) as f:
			lines = f.readlines()
		nbr=0
		for line in lines:
			item = line.split(chr(9))
			if len(item)>3 and nbr<list_size and (item[3]==addon or addon=='*'):
				desc=''
				if show_date == "true" and len(item)>4 : desc = desc + item[4].strip() + ' '
				if show_time == "true" and len(item)>5: desc = desc + item[5].strip() + ' '
				desc=desc + item[0]
				li = ListItem(label=desc)
				li.setInfo(type="Video", infoLabels={ "Title": desc})
				li.setProperty('IsPlayable', 'true')
				command = []
				command.append((lang(30008), "XBMC.RunPlugin(plugin://plugin.video.last_played?menu=remove&id="+str(nbr)+")"))
				nbr=nbr+1
				li.addContextMenuItems(command)
				li.setArt({ "poster" : item[2].strip() })
				addDirectoryItem(addon_handle, item[1].strip(), li, False)
		endOfDirectory(addon_handle)

def list_addons():
	if group_addons == "true":
		addDirectoryItem(addon_handle, url({'menu': '*'}), ListItem(lang(30006), iconImage=imgPath+'/resources/others.png'), True)
	else:
		txtfile = profile + "list.txt"
		if xbmcvfs.exists(txtfile):
			addons = []
			with open(txtfile) as f:
				lines = f.readlines()
				for line in lines:
					fld = line.split(chr(9))
					if len(fld)>5:
						ad = fld[3]
						ads = ad.split("/")
						if len(ads) > 2: ad = ads[2]
						if ad not in addons:
							addons.append(ad)
							try:
								la = xbmcaddon.Addon(ad)
								nm = la.getAddonInfo('name')
								ic = la.getAddonInfo('icon')
							except:
								nm = ad
								ic = imgPath+'/resources/addons.png'
							addDirectoryItem(addon_handle, url({'menu': fld[3]}), ListItem(nm, iconImage=ic), True)
		
if menu is None:
	xbmcplugin.setContent(addon_handle, "menu")
	addDirectoryItem(addon_handle, url({'menu': 'movies'}), ListItem(lang(30002), iconImage=imgPath+'/resources/movies.png'), True)
	addDirectoryItem(addon_handle, url({'menu': 'episodes'}), ListItem(lang(30003), iconImage=imgPath+'/resources/episodes.png'), True)
	addDirectoryItem(addon_handle, url({'menu': 'musicvideos'}), ListItem(lang(30004), iconImage=imgPath+'/resources/musicvideos.png'), True)
	addDirectoryItem(addon_handle, url({'menu': 'songs'}), ListItem(lang(30005), iconImage=imgPath+'/resources/songs.png'), True)
	if show_addons == "true":
		list_addons()
	if enable_debug	== "true":
		addDirectoryItem(addon_handle, url({'menu': 'showlist'}), ListItem(lang(30014)), True)
		txtfile = profile + "list.txt"
		if xbmcvfs.exists(txtfile):
			addDirectoryItem(addon_handle, url({'menu': 'deletelist'}), ListItem(lang(30015)), True)
		else:
			addDirectoryItem(addon_handle, url({'menu': 'deletelist'}), ListItem(lang(30016)), True)
	endOfDirectory(addon_handle)
elif menu[0] == 'movies':
	list_items(get_items("VideoLibrary.GetMovies","movies"),'movies')
elif menu[0] == 'episodes':
	list_items(get_items("VideoLibrary.GetEpisodes","episodes"),"episodes")
elif menu[0] == 'musicvideos':
	list_items(get_items("VideoLibrary.GetMusicVideos","musicvideos"),"musicvideos")
elif menu[0] == 'songs':
	list_items(get_items("AudioLibrary.GetSongs","songs"),"songs")
elif menu[0] == 'remove':
	lid = args.get('id', None)
	txtfile = profile + "list.txt"
	if xbmcvfs.exists(txtfile) and lid is not None:
		rid = int(lid[0])
		with open(txtfile) as f:
			lines = f.readlines()
			nbr=0
			with open(txtfile, 'w') as f:
				for line in lines:
					item = line.split(chr(9))
					if len(item)>2 and nbr!=rid:
						f.write(line)
					nbr=nbr+1
		xbmc.executebuiltin("ActivateWindow(Videos,plugin://plugin.video.last_played?menu=addons)")
elif menu[0] == 'showlist':
	txtfile = profile + "list.txt"
	if xbmcvfs.exists(txtfile):
		with open(txtfile) as f:
			lines = f.readlines()
			for line in lines:
				addDirectoryItem(addon_handle, url(""), ListItem(str(line)), False)
		endOfDirectory(addon_handle)
elif menu[0] == 'deletelist':
	txtfile = profile + "list.txt"
	if xbmcvfs.exists(txtfile):
		xbmcvfs.delete(txtfile)

else:
	list_addonitems(menu[0])
