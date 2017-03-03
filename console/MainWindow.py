# -*- coding: utf-8 -*-

import importlib
import logging
import os
import thread
import xml.etree.ElementTree as ET

from collections import namedtuple

# noinspection PyUnresolvedReferences
import wx
# noinspection PyUnresolvedReferences
import newevent

from config.util import PyConfigFile
import Logger


MyConfigFile = namedtuple("ConfigFile", ("data", "list",))
(WorkerFinishEvent, EVT_WORKER_FIN) = newevent.NewEvent()


class Worker(object):
    def __init__(self, main_window, runnable, done_listener=None):
        self.main_window = main_window
        self.runnable = runnable
        self.done_listener = done_listener

    def start(self):
        thread.start_new_thread(self.run, ())

    def run(self):
        self.runnable()

        event = WorkerFinishEvent()
        event.done_listener = self.done_listener
        wx.PostEvent(self.main_window, event)


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

        self.redirector = Logger.MyRedirector(self)
        self.std_redirector = Logger.RedirectStdStreams(
            stdout=self.redirector, stderr=self.redirector
        )

        self.prepare_logger()

        self.configs = {}
        self.create_panels()

        self.Bind(EVT_WORKER_FIN, self.on_worker_finished)
        self.Bind(wx.EVT_CLOSE_WINDOW, self.on_close)

    def xrc_load_frame(self):
        res = wx.XmlResource.Get()
        res.InitAllHandlers()

        if res.Load(u"console/MainWindow.xrc"):
            if res.LoadFrame(self, None, u"main_window"):
                self.SetIcon(wx.Icon(u"console/Icon.ico", wx.BITMAP_TYPE_ICO))
                self.xrc_bind()

                return True

        return False

    def xrc_bind(self):
        res = wx.XmlResource.Get()

        raw = open("console/MainWindow.xrc").read()
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

        folder = "config/"
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

                attr_width = int(listctrl_width * 0.58)
                lc.AppendColumn(u"Attribute", width=attr_width)
                lc.AppendColumn(u"Value", width=(listctrl_width - attr_width))

                config = PyConfigFile(folder + f)
                my_config = MyConfigFile(config, lc)
                self.configs[f] = my_config

                for key in config.attrib_keys:
                    index = lc.GetItemCount()
                    lc.InsertItem(index, key.decode())
                    lc.SetItem(index, 1, config.attrib[key].value.decode())

    def prepare_logger(self):
        self.logger = Logger.ListBoxLogger(self.logger_ctrl)
        self.Bind(Logger.EVT_LOG, self.on_append_log)

        logging.basicConfig(level=logging.DEBUG,
                            format="[%(levelname)s] %(message)s",
                            stream=self.redirector)

        logging.debug("Hello from RecSys!")

    def on_append_log(self, event):
        self.logger.append(event.log)
        self.logger.go_to_end()

    def get_selected_config_file(self):
        return self.notebook.GetPageText(self.notebook.GetSelection())

    def on_item_activated(self, event):
        fname = self.get_selected_config_file()
        my_config = self.configs[fname]

        index = event.GetIndex()
        key = my_config.list.GetItemText(index, 0)
        val = my_config.list.GetItemText(index, 1)

        if val == u"True":
            new_val = u"False"
        elif val == u"False":
            new_val = u"True"
        elif my_config.data.attrib[key].options is not None:
            new_val = my_config.data.attrib[key].next().decode()
        else:
            dlg = wx.TextEntryDialog(caption=u"Set attribute value",
                                     message=key + u" =",
                                     value=val,
                                     parent=self)
            dlg.ShowModal()
            new_val = dlg.GetValue()
            dlg.Destroy()

        if new_val:
            my_config.data.attrib[key].value = new_val
            my_config.data.save()

            my_config.list.SetItem(index, 1, new_val)

    def enable_console(self, enabled):
        self.notebook.Enable(enabled)
        self.start.Enable(enabled)

    def on_worker_finished(self, event):
        self.enable_console(True)

    def on_start(self, event):
        self.logger.clear()
        self.enable_console(False)

        worker = Worker(self, self.do_start)
        worker.start()

    def do_start(self):
        mod_name = self.get_selected_config_file()[:-3]

        try:
            config_module = importlib.import_module("config." + mod_name)
            reload(config_module)

            m = importlib.import_module(mod_name)
            m.main()
        except:
            logging.exception("Failed to execute script: %s.py", mod_name)

        self.redirector.flush()
