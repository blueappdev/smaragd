#!/usr/bin/env python
#
# sdevkit.py
#
# requires python 2.7

import os, sys
import string, StringIO
import getopt
import Tkinter as tk

from scmd import *
import slib
from slib.Kernel import *
import slib.Configuration as Configuration
import slib.UI as ui
from slib.compareTool import *
import slib.classFinder

class LauncherFrame(ui.ApplicationFrame):
    def __init__(self, master):
        ui.ApplicationFrame.__init__(self, master = master)
        
        Image.image1 = None
        Image.image2 = None

        self.createPopupMenus()
        self.horizontalScrollbarUpdateInfo = 10
        self.verticalScrollbarUpdateInfo = 10

        # Send explicitly the unpost context menu, 
        # whenever the mouse button is pressed
        # (The context menu does not disappear on Unix, 
        # when clicked outside the context menu.) 
        self.master.bind("<Button-1>", self.unpostContextMenus)

        self.pack()
        #self.createToolbar()

        self.mainFrame=tk.Frame(
                self.master, 
                width = 800, 
                height = 300)

        self.transcriptFrame = tk.Frame(self.mainFrame)
        #print Configuration.globalConfiguration.getFont()
        self.transcript = tk.Text(self.transcriptFrame,
                #xscrollcommand = self.leftxset,
                #yscrollcommand = self.leftyset,
                font = Configuration.globalConfiguration.getFont(),
                wrap = tk.WORD,
                spacing1 = 2,
                spacing2 = 2,
                spacing3 = 2)
        self.transcriptScrollbar = tk.Scrollbar(
                self.transcriptFrame,
                orient = tk.VERTICAL,
                command=self.transcript.yview)
        self.transcript.configure(yscrollcommand=self.transcriptScrollbar.set)
        self.transcriptScrollbar.pack(side = tk.RIGHT, fill=tk.Y)
        self.transcript.pack(fill=tk.BOTH,expand = 1)
        #self.transcript.grid(row=0, column=0, sticky="nsew")
        #self.transcriptScrollbar.grid(row=0, column=1, sticky="ns")
        #self.transcriptFrame.grid_rowconfigure(0, weight=1)
        #self.transcriptFrame.grid_columnconfigure(0, weight=1)

        self.transcriptFrame.pack(side="top", fill="both", expand=True)

        #self.leftText.bind("<Key>", self.filterKey)
        self.transcript.bind("<Button-3>", self.popupLeftMenu)

        self.mainFrame.pack(fill=tk.BOTH,expand=1)
        
    def buildMenubar(self, menubar):
        self.buildBrowseMenu(menubar)
        self.buildToolsMenu(menubar)

    def buildBrowseMenu(self, parentMenu):
        newMenu = self.addMenu(parentMenu, "Browse")
        self.addMenuItem(newMenu, "Packages...", self.onBrowsePackages)
        self.addMenuItem(newMenu, "Classes...", self.onBrowseClasses)
        self.addMenuItem(newMenu, "Implementors...", self.onBrowseImplementors)
        self.addMenuItem(newMenu, "Load images", self.onLoadImages)

    def buildToolsMenu(self, parentMenu):
        newMenu = self.addMenu(parentMenu, "Tools")
        self.addMenuItem(newMenu, "Compare Tool", self.onOpenCompareTool)

    def onBrowsePackages(self):
        print 'onBrowsePackages'
        self.loadImages()

    def onBrowseClasses(self):
        self.loadImages()
        reload(slib.classFinder)
        self.openTopLevelFrame(slib.classFinder.ClassFinderFrame)

    def onBrowseImplementors(self):
        self.loadImages()
        print 'onBrowseImplementors'
        print self.image.methodsDictionary

    def loadCachedImage(self, aFilename):
        print "Load", aFilename
        stream = open(aFilename, "rb")
        image = pickle.load(stream)
        stream.close()
        image.imageName = os.path.basename(aFilename)
        return image
        
    def loadImages(self): 
        if Image.image1 is None:
            Image.image1 = self.loadCachedImage(Configuration.globalConfiguration.image1)
        if Image.image2 is None:
            Image.image2 = self.loadCachedImage(Configuration.globalConfiguration.image2)

    def onLoadImages(self):
        Image.image1 = None
        Image.image2 = None
        self.loadImages()
        
    def onOpenCompareTool(self):
        CompareWindow(self.master)

    def createPopupMenus(self):
        self.popupMenu = tk.Menu(tearoff=0)
        self.popupMenu.add_command(label="Clear", command=self.onClear)

    def popupLeftMenu(self, anEvent):
        self.unpostContextMenus()
        self.popupMenu.post(anEvent.x_root, anEvent.y_root)

    def unpostContextMenus(self, anEvent=None):
        self.popupMenu.unpost()

    def onClear(self):
        self.transcript.delete('1.0', tk.END)

    def getAllImages(self):
        return [Image.image1, Image.image2]

    def getAllClasses(self):
        allClasses = []
        for each in self.getAllImages():
            allClasses += each.getAllClasses()
        allClasses.sort(key=self.nameOfClass)
        return allClasses

    def nameOfClass(self, aClass):
        return aClass.name

class LauncherApp(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)
        self.title("DevKit")
        tool=LauncherFrame(self)
            
if __name__ == "__main__":
    options, arguments = getopt.getopt(sys.argv[1:], "v")
    for option, value in options:
        if option == "-v":
            Configuration.verboseFlag = True
        else:
            print "Option", option, "not supported."
    try:
        LauncherApp().mainloop()
    except KeyboardInterrupt:
       pass



