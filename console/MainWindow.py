# -*- coding: utf-8 -*-

import os
import xml.etree.ElementTree as ET

from config.util import PyConfigFile

# noinspection PyUnresolvedReferences
import newevent
# noinspection PyUnresolvedReferences
import wx


# noinspection PyBroadException,PyUnusedLocal,PyMethodMayBeStatic,PyAttributeOutsideInit
class MainWindow(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self)

        if not self.xrc_load_frame():
            raise RuntimeError("Cannot create main window from XRC file")

        usable = wx.GetClientDisplayRect()
        w = max(int(usable.width * 0.5), 750)
        h = int(usable.height * 0.75)
        self.SetSize(w, h)
        self.Centre(wx.BOTH)

        self.configs = {}
        self.create_panels()

    def xrc_load_frame(self):
        res = wx.XmlResource.Get()
        res.InitAllHandlers()

        if res.Load(u"MainWindow.xrc"):
            if res.LoadFrame(self, None, u"main_window"):
                self.SetIcon(wx.Icon(u"Icon.ico", wx.BITMAP_TYPE_ICO))
                self.xrc_bind()

                return True

        return False

    def xrc_bind(self):
        res = wx.XmlResource.Get()

        raw = open("MainWindow.xrc").read()
        raw = raw.replace("xmlns", "_xmlns", 1)

        from StringIO import StringIO
        root = ET.parse(StringIO(raw)).getroot()

        for node in root.iter("object"):
            if "name" not in node.attrib:
                continue

            cls = node.attrib["class"]
            name = node.attrib["name"].decode()
            xid = res.GetXRCID(name)

            if cls.startswith("wxMenu"):
                if cls == "wxMenuItem":
                    target = self
                    name = name[:-3]
                else:
                    continue
            else:
                win = self.FindWindow(xid)

                cvt = getattr(wx.XRC, "To_" + cls)
                target = cvt(win)
                setattr(self, name, target)

            event_type = wx.XRC.GetDefaultEventType(cls)
            if event_type != 0:
                handler = getattr(self, "on_" + name, None)
                if handler is not None:
                    target.Bind(event_type, handler, xid)

    def on_exit(self, event):
        self.Close()

    def on_close(self, event):
        event.Skip(True)

    def on_about(self, event):
        wx.MessageBox(u"~~(*^_^*)~~", u"About",
                      wx.OK | wx.ICON_INFORMATION,
                      self)

    def create_panels(self):
        listctrl_width = -1

        folder = "../config/"
        for f in os.listdir(folder):
            if ".sample" in f or f in ("__init__.py", "util.py",):
                continue

            if f.endswith(".py"):
                style = (wx.LC_NO_SORT_HEADER |
                         wx.LC_REPORT |
                         wx.LC_SINGLE_SEL)

                lc = wx.ListCtrl(self.notebook, wx.ID_ANY, style=style)
                lc.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.on_item_activated)

                self.notebook.AddPage(lc, f.decode())

                if listctrl_width == -1:
                    listctrl_width = lc.GetSize().GetX()
                    listctrl_width -= wx.SystemSettings.GetMetric(wx.SYS_VSCROLL_X, self)

                lc.AppendColumn(u"Attribute", width=int(listctrl_width * 0.3))
                lc.AppendColumn(u"Value", width=int(listctrl_width * 0.7))

                config = PyConfigFile(folder + f)
                self.configs[f] = config

                for key, val in config.attrib:
                    index = lc.GetItemCount()
                    lc.InsertItem(index, key.decode())
                    lc.SetItem(index, 1, val.value.decode())

    def on_item_activated(self, event):
        index = event.GetIndex()
        print index
