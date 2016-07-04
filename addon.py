import sys
#import common
import json
import urllib
import urlparse
import xbmcplugin
import xbmcaddon
from xbmcgui import ListItem
from xbmcplugin import addDirectoryItem, endOfDirectory
import mysql.connector as database

#db_address = common.addon.get_setting('db_address')
#db_port = common.addon.get_setting('db_port')
#if db_port: db_address = '%s:%s' %(db_address,db_port)
#db_user = common.addon.get_setting('db_user')
#db_pass = common.addon.get_setting('db_pass')
#db_name = common.addon.get_setting('db_name')
db_name = "luisvideos99"
db_user = "kodi"
db_pass = "kodi"
db_address = "base"
db = database.connect(db = db_name, user = db_user, passwd = db_pass, host = db_address)

addon = xbmcaddon.Addon()
addon_handle = int(sys.argv[1])
args = urlparse.parse_qs(sys.argv[2][1:])
menu = args.get('menu', None)
list_size = int(addon.getSetting('list_size'))
show_others = addon.getSetting('show_others')
lang = addon.getLocalizedString

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
    query = { "jsonrpc": "2.0", "method": pMethod, "id": 1,
        "params": { "properties": ["title", "file" ], "sort": { "order": "descending", "method": "lastplayed" },  "limits": {"start" : 0, "end" : list_size } }
    }
    items = jsonrpc(query)['result'].get(pResult, [])
    return items
	
def list_others():
    cursor = db.cursor()
    cursor.execute('SELECT strFilename, concat(strpath,strFilename) as video FROM files INNER JOIN path on files.idpath=path.idpath where strhash is null Order By lastPlayed desc LIMIT ' + str(list_size))
    for row in cursor.fetchall():
        li = ListItem(label=row[0])
        li.setInfo(type="Video", infoLabels={ "Title": row[0]})
        li.setProperty('IsPlayable', 'true')
        addDirectoryItem(addon_handle, row[1], li, False)
    endOfDirectory(addon_handle)

if menu is None:
    xbmcplugin.setContent(addon_handle, "menu")
    imgPath=xbmc.translatePath(xbmcaddon.Addon().getAddonInfo('path')).decode('utf-8')
    addDirectoryItem(addon_handle, url({'menu': 'movies'}), ListItem(lang(30002), iconImage=imgPath+'/resources/movies.png'), True)
    addDirectoryItem(addon_handle, url({'menu': 'episodes'}), ListItem(lang(30003), iconImage=imgPath+'/resources/episodes.png'), True)
    addDirectoryItem(addon_handle, url({'menu': 'musicvideos'}), ListItem(lang(30004), iconImage=imgPath+'/resources/musicvideos.png'), True)
    addDirectoryItem(addon_handle, url({'menu': 'songs'}), ListItem(lang(30005), iconImage=imgPath+'/resources/songs.png'), True)
    if show_others:
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