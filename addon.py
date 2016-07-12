import sys, os, re
import json
import urllib
import urlparse
import xbmc
import xbmcplugin
import xbmcaddon
import xbmcvfs
from xbmcgui import ListItem
from xbmcplugin import addDirectoryItem, endOfDirectory

addon = xbmcaddon.Addon()
addon_handle = int(sys.argv[1])
args = urlparse.parse_qs(sys.argv[2][1:])
menu = args.get('menu', None)
list_size = int(addon.getSetting('list_size'))
show_addons = addon.getSetting('show_addons')
lang = addon.getLocalizedString
	
def openDB():	
	dbType = 'sqlite'	
	dbName = 'MyVideos'
	kodiVer = xbmc.getInfoLabel( "System.BuildVersion" )[:2]
	dbVersion = '99'
	if kodiVer==13: dbVersion = '75'
	if kodiVer==14: dbVersion = '90'
	if kodiVer==15: dbVersion = '93'
	advPath = xbmc.translatePath(os.path.join('special://profile','advancedsettings.xml'))
	if xbmcvfs.exists(advPath):
		f = open(advPath, "r")
		advSettings = f.read()
		wrk = re.compile('<videodatabase>(.+?)</videodatabase>', re.DOTALL).findall(advSettings)
		if len(wrk) != 0:
			dbSection = wrk[0]
		wrk = re.compile('<type>(.+?)</type>', re.DOTALL).findall(dbSection)
		if len(wrk) != 0: dbType = wrk[0]
		wrk = re.compile('<name>(.+?)</name>', re.DOTALL).findall(dbSection)
		if len(wrk) != 0: dbName = wrk[0]
		wrk = re.compile('<host>(.+?)</host>', re.DOTALL).findall(dbSection)
		if len(wrk) != 0: dbHost = wrk[0]
		wrk = re.compile('<port>(.+?)</port>', re.DOTALL).findall(dbSection)
		if len(wrk) != 0: dbPort = wrk[0]
		wrk = re.compile('<user>(.+?)</user>', re.DOTALL).findall(dbSection)
		if len(wrk) != 0: dbUser = wrk[0]
		wrk = re.compile('<pass>(.+?)</pass>', re.DOTALL).findall(dbSection)
		if len(wrk) != 0: dbPass = wrk[0]
	if dbType=='mysql':
		import mysql.connector as database
		db = database.connect(db = dbName+dbVersion, user = dbUser, passwd = dbPass, host = dbHost)
	else:
		from sqlite3 import dbapi2 as database
		dbPath = xbmc.translatePath('special://database/' + dbName + dbVersion + '.db')
		db = database.connect(dbPath)
		db.row_factory = database.Row
	return db

def url(pQuery):
	return sys.argv[0] + '?' + urllib.urlencode(pQuery)

def jsonrpc(query):
	return json.loads(xbmc.executeJSONRPC(json.dumps(query, encoding='utf-8')))

def list_items(items, type):
	xbmcplugin.setContent(addon_handle, type)
	for item in items:
		if type=='movies': dbid = item['movieid']
		elif type=='episodes': dbid = item['episodeid']
		elif type=='musicvideos': dbid = item['musicvideoid']
		elif type=='songs': dbid = item['songid']
		li = ListItem(label=item['title'])
		li.setInfo(type="Video", infoLabels={"mediatype": 'episode'})
		li.setProperty("type", "episode")
		li.setProperty("dbid", str(dbid))
		addDirectoryItem(addon_handle, item['file'], li, False, len(items))
	endOfDirectory(addon_handle)
	
def get_items(pMethod, pResult):
	query = { "jsonrpc": "2.0", "method": pMethod, "id": 1, "params": { "properties": ["title", "file" ], "sort": { "order": "descending", "method": "lastplayed" },  "limits": {"start" : 0, "end" : list_size } } }
	items = jsonrpc(query)['result'].get(pResult, [])
	return items
	
def list_others():
	try:
		db = openDB()
		cursor = db.cursor()
		cursor.execute('SELECT strFilename, strpath, files.dateadded, lastplayed FROM files INNER JOIN path on files.idpath=path.idpath where strhash is null Order By lastPlayed desc LIMIT ' + str(list_size))
		for row in cursor.fetchall():
			title = row[2]
			if title=='' or title=='None' or title is None: title=row[3]
			li = ListItem(label=title)
			li.setInfo(type="Video", infoLabels={ "Title": title})
			li.setProperty('IsPlayable', 'true')
			addDirectoryItem(addon_handle, row[1]+row[0], li, False)
		endOfDirectory(addon_handle)
	except: 
		pass

if menu is None:
	xbmcplugin.setContent(addon_handle, "menu")
	imgPath=xbmc.translatePath(xbmcaddon.Addon().getAddonInfo('path')).decode('utf-8')
	addDirectoryItem(addon_handle, url({'menu': 'movies'}), ListItem(lang(30002), iconImage=imgPath+'/resources/movies.png'), True)
	addDirectoryItem(addon_handle, url({'menu': 'episodes'}), ListItem(lang(30003), iconImage=imgPath+'/resources/episodes.png'), True)
	addDirectoryItem(addon_handle, url({'menu': 'musicvideos'}), ListItem(lang(30004), iconImage=imgPath+'/resources/musicvideos.png'), True)
	addDirectoryItem(addon_handle, url({'menu': 'songs'}), ListItem(lang(30005), iconImage=imgPath+'/resources/songs.png'), True)
	if show_addons == "true":
		addDirectoryItem(addon_handle, url({'menu': 'others'}), ListItem(lang(30006), iconImage=imgPath+'/resources/others.png'), True)
	endOfDirectory(addon_handle)
elif menu[0] == 'movies':
	list_items(get_items("VideoLibrary.GetMovies","movies"),'movies')
elif menu[0] == 'episodes':
	list_items(get_items("VideoLibrary.GetEpisodes","episodes"),"episodes")
elif menu[0] == 'musicvideos':
	list_items(get_items("VideoLibrary.GetMusicVideos","musicvideos"),"musicvideos")
elif menu[0] == 'songs':
	list_items(get_items("AudioLibrary.GetSongs","songs"),"songs")
else:
	list_others()