import os, re, sys, time
import xbmc
import xbmcaddon
import xbmcvfs

__addon__ = xbmcaddon.Addon()
__profile__ = xbmc.translatePath( __addon__.getAddonInfo('profile') ).decode("utf-8")
getTitle=''

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

class AutoSubsPlayer(xbmc.Player):
	def __init__(self, *args, **kwargs):
		xbmc.Player.__init__(self)

	def onPlayBackStarted(self):
		global getTitle
		if xbmc.Player().isPlayingVideo():
			vTag = xbmc.Player().getVideoInfoTag()
			getTitle = vTag.getTitle().strip()
			if getTitle != '':
				getYear = vTag.getYear()
				if getYear > 0: getTitle = getTitle + " (" + str(getYear) + ")"
		else: getTitle = "NOTVIDEO"
				
	def onPlayBackStopped(self):
		if getTitle != "NOTVIDEO":
			xbmc.log("------getTitle '%s'" % getTitle, 3)
			time.sleep(0.5)
			try:
				db = openDB()
				cursor = db.cursor()
				cursor.execute('SELECT idfile, strhash, files.dateadded FROM files INNER JOIN path on files.idpath=path.idpath Order By lastPlayed desc LIMIT 1')
				for row in cursor.fetchall():
					if row[1] is None:
						xbmc.log("-----------id '%s'" % row[0], 3)
						sql = "UPDATE files SET dateadded='%s' where idfile=%s" % (getTitle, row[0])
						cursor = db.cursor()
						cursor.execute(sql)
						db.commit()
			except:
				pass

player_monitor = AutoSubsPlayer()

while not xbmc.abortRequested:
	xbmc.sleep(1000)

del player_monitor
