# -*- coding: utf-8 -*-

import os
import sys

sys.path += os.environ["PYWX"].split(';')
# noinspection PyUnresolvedReferences
import wx


# noinspection PyMethodMayBeStatic
class App(wx.PyApp):
    def __init__(self):
        wx.PyApp.__init__(self)
        wx.SetProcessDPIAware()
        self._BootstrapApp()

    def OnInit(self):
        win = MyFrame()
        win.Show()

        return True


# noinspection PyUnusedLocal
class MyFrame(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None, wx.ID_ANY, u"Platform and technology categorizer",
                          size=wx.DefaultSize)

        usable = wx.GetClientDisplayRect()
        self.SetSize(int(usable.width * 0.5), int(usable.height * 0.75))
        self.Centre(wx.BOTH)

        self.Bind(wx.EVT_CLOSE_WINDOW, self.OnClose)
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_KEY_UP, self.OnKeyUp)

        self.platech = []
        for line in open("platech.txt"):
            line = line.strip()
            self.platech.append(line.decode("utf-8"))

        self.categories = []
        for line in open("cat.txt"):
            line = line.strip()
            self.categories.append(line.decode("utf-8"))

        if os.path.exists("result.txt"):
            self.result = [n.strip() for n in open("result.txt")]
        else:
            self.result = []

        self.curr = len(self.result)

    def OnClose(self, event):
        self.Save()
        self.Destroy()

    def Save(self):
        with open("result.txt", "w") as outf:
            outf.write('\n'.join(self.result))

    def OnPaint(self, event):
        dc = wx.PaintDC(self)

        font = self.GetFont()
        font.SetFaceName(u"Consolas")
        font.SetPointSize(18)
        dc.SetFont(font)
        dc.SetTextForeground(wx.WHITE)

        x = 50
        y = 50

        if self.curr >= len(self.platech):
            dc.DrawText(u"DONE!", x, y)
            return

        charHeight = dc.GetTextExtent(u"pbH").y
        padding = int(charHeight * 0.1)
        height = charHeight + padding * 2

        pt = self.platech[self.curr]
        dc.DrawText(pt, x, y + padding)
        y += height

        for index, cat in enumerate(self.categories):
            dc.DrawText(("%X: " % (index + 1)) + cat, x, y + padding)
            y += height

    def OnKeyUp(self, event):
        key = event.GetKeyCode()
        if key < 256:
            if chr(key).upper() == 'S':
                self.Save()
                return
            elif chr(key).upper() == 'Q':
                self.OnClose(None)
                return
            elif chr(key).upper() == 'P' and self.curr > 0:
                self.result.pop()
                self.curr -= 1
            else:
                cat = int(chr(key), 16)
                if cat <= 0 or cat > len(self.categories):
                    return

                self.result.append(str(cat))
                self.curr += 1

            self.Refresh()


if __name__ == "__main__":
    app = App()
    app.MainLoop()
