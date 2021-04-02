# -*- coding: utf-8 -*-
import sys
import json
import xbmc
import xbmcplugin
import xbmcaddon
import xbmcvfs
import xbmcgui
from xbmcplugin import addDirectoryItem, endOfDirectory
try:
    from urllib.parse import parse_qs, urlencode
except ImportError:
    from urlparse import parse_qs
    from urllib import urlencode

addon = xbmcaddon.Addon()
addon_handle = int(sys.argv[1])
args = parse_qs(sys.argv[2][1:])
xbmc.log(str(args),3)
menu = args.get('menu', None)
try: list_size = int(addon.getSetting('list_size'))
except Exception: list_size=0
try: top_size = int(addon.getSetting('top_size'))
except Exception: top_size=0
single_list = addon.getSetting('single_list')
group_by = addon.getSetting('group_by')
show_date = addon.getSetting('show_date')
show_time = addon.getSetting('show_time')
enable_debug = addon.getSetting('enable_debug')
lang = addon.getLocalizedString
if addon.getSetting('custom_path_enable') == "true" and addon.getSetting('custom_path') != "":
    txtpath = addon.getSetting('custom_path')
else:
    txtpath = xbmc.translatePath(addon.getAddonInfo('profile'))
txtfile = txtpath + "lastPlayed.json"
imgPath=xbmc.translatePath(xbmcaddon.Addon().getAddonInfo('path'))
group_by_type=lang(30018)

def url(pQuery):
    return sys.argv[0] + '?' + urlencode(pQuery)

def list_items(selGroup, nbrLines):
    xbmcplugin.setContent(addon_handle, "files")
    if xbmcvfs.exists(txtfile):
        f = xbmcvfs.File(txtfile)
        nbr=0 # nbr of line on screen (selected)
        idx=0 # idx of line on the json file
        try: lines = json.load(f)
        except: lines = []
        for line in lines:
            if nbr>=nbrLines: break
            if group_by == group_by_type: group = line["type"]
            else: group = line["source"]
            if len(line)>3 and (group==selGroup or selGroup=='*'):
                nbr=nbr+1
                desc=''
                if show_date == "true": desc = desc + line["date"].strip() + ' '
                if show_time == "true": desc = desc + line["time"].strip() + ' '
                show = ''
                if 'show' in line: show=line["show"] + " "
                if 'season' in line and line["season"]!='' and str(line["season"])!="-1":
                    if 'episode' in line and line["episode"]!='' and str(line["episode"])!="-1":
                        show = show + str(line["season"])+"x"+str(line["episode"]) + " "
                desc=desc + show + line["title"]
                if 'artist' in line and line["artist"]!='': desc=desc+" - "+str(line["artist"])
                xpath=""
                infolabels={'title': desc, 'year': line['year'], "mediatype": line['type'], 'Top250': line['id']}
                li = xbmcgui.ListItem(label=desc)
                li.setInfo('video', infolabels)
                li.setArt({ "poster" : line["thumbnail"].strip() })
                li.setArt({ "thumbnail" : line["thumbnail"].strip() })
                li.setArt({ "fanart" : line["fanart"].strip() })
                li.setProperty('IsPlayable', 'true')
                command = []
                command.append((lang(30008), "RunPlugin(plugin://plugin.video.last_played?menu=remove&id="+str(idx)+")"))
                if line["file"][:6]=="plugin":
                    command.append((lang(30031)+line["source"], "PlayMedia(" + line["file"] + ")"))
                li.addContextMenuItems(command)
                xurl=line["file"]
                if "video" in line and line["video"]!="": xurl=line["video"]
                addDirectoryItem(addon_handle, xurl, li)
            idx = idx + 1
        f.close()
        if single_list == "true" and nbr == 0:
            li = ListItem(lang(30030))
            li.setProperty('IsPlayable', 'false')
            addDirectoryItem(addon_handle, "", li, isFolder = True)
            
def list_groups():
    if xbmcvfs.exists(txtfile):
        groups = []
        f = xbmcvfs.File(txtfile)
        try:
            lines = json.load(f);
        except Exception:
            lines = []
        for line in lines:
            if len(line)>5:
                if group_by == group_by_type:
                    group = line["type"]
                else:
                    group = line["source"]
                if group not in groups:
                    groups.append(group)
                    if group_by == group_by_type:
                        nm = group
                        ic = imgPath+'/resources/' + group + '.png'
                    else:
                        nm = group
                        ads = group.split("/")
                        if len(ads) > 2: nm = ads[2]
                        if group==lang(30002): ic = imgPath+'/resources/movie.png'
                        elif group==lang(30003): ic = imgPath+'/resources/episode.png'
                        elif group==lang(30004): ic = imgPath+'/resources/musicvideo.png'
                        else:
                            try:
                                la = xbmcaddon.Addon(nm)
                                nm = la.getAddonInfo('name')
                                ic = la.getAddonInfo('icon')
                            except Exception:
                                ic = imgPath+'/resources/addons.png'
                    li = xbmcgui.ListItem(nm)
                    li.setArt({'thumbnail':ic})
                    addDirectoryItem(addon_handle, url({'menu': group}), li, True)
        f.close()

# Menu
if menu is None or menu[0]=="top":
    if single_list == "true":
        list_items("*", list_size)
    else:
        xbmcplugin.setContent(addon_handle, "menu")
        list_items("*", top_size)
        if top_size>0: addDirectoryItem(addon_handle, "", xbmcgui.ListItem(label=""), False)

        list_groups()
    if enable_debug	== "true":
        addDirectoryItem(addon_handle, url({'menu': 'showlist'}), xbmcgui.ListItem(lang(30014)), True)
        if xbmcvfs.exists(txtfile):
            addDirectoryItem(addon_handle, url({'menu': 'deletelist'}), xbmcgui.ListItem(lang(30015)), True)
        else:
            addDirectoryItem(addon_handle, url({'menu': 'deletelist'}), xbmcgui.ListItem(lang(30016)), True)
    endOfDirectory(addon_handle)
elif menu[0] == 'remove':
    lid = args.get('id', None)
    if xbmcvfs.exists(txtfile) and lid is not None:
        f = xbmcvfs.File(txtfile)
        lines = json.load(f)
        f.close()
        osz = len(lines)
        lines.remove(lines[int(lid[0])])
        # to avoid accidental cleaning, update empty file only it had only one line before
        if len(lines)>0 or osz==1:
            f = xbmcvfs.File(txtfile, 'w')
            json.dump(lines, f)
            f.close()
        xbmc.executebuiltin("ActivateWindow(Videos,plugin://plugin.video.last_played?menu=top)")
elif menu[0] == 'showlist':
    if xbmcvfs.exists(txtfile):
        f = xbmcvfs.File(txtfile)
        lines = json.load(f)
        f.close()
        for line in lines:
            addDirectoryItem(addon_handle, url({}), ListItem(str(line)), False)
        endOfDirectory(addon_handle)
elif menu[0] == 'deletelist':
    if xbmcvfs.exists(txtfile):
        lines = []
        f = xbmcvfs.File(txtfile, 'w')
        json.dump(lines, f)
        f.close()
else:
    list_items(menu[0], list_size)
    endOfDirectory(addon_handle)
