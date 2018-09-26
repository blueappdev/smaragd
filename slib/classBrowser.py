#!/usr/bin/env python
#
# requires python 2.7

import os, sys
import string, fnmatch
import Tkinter as tk
from Kernel import *
import UI as ui
import Configuration

class ClassBrowser(ui.ApplicationFrame):
    def __init__(self, master, parentApplication, domain):
        ui.ApplicationFrame.__init__(self, master = master, parentApplication = parentApplication)
        self.domain = domain
        self.master.title("[CB] " + self.domain.name)
        self.master.protocol("WM_DELETE_WINDOW", self.master.destroy)
        self.pack(fill=tk.BOTH, expand=1)
        self.panedWindow = tk.PanedWindow(self, orient=tk.VERTICAL,  sashpad=4, sashrelief=tk.RAISED)
        self.panedWindow.pack(fill=tk.BOTH, expand=1)

        self.buildTopFrame()
        self.buildBottomFrame()

        self.updateEditor()


    def buildTopFrame(self):
        self.topWindow = tk.PanedWindow(
                self.panedWindow,
                orient=tk.HORIZONTAL,
                sashpad=4,
                sashrelief=tk.RAISED)
        self.panedWindow.add(self.topWindow)
        self.buildMethodProtocolsFrame()
        self.buildMethodsFrame()

    def buildMethodProtocolsFrame(self):
        self.methodProtocolsListbox = ui.BetterListbox(self.topWindow)
        self.methodProtocolsListbox.bind("<<ListboxSelect>>", self.methodProtocolsSelectionChanged)
        self.topWindow.add(self.methodProtocolsListbox)
        self.updateMethodProtocols()

    def buildMethodsFrame(self):
        self.methodsListbox = ui.BetterListbox(self.topWindow)
        self.methodsListbox.displayStringFunction = lambda m: m.selector
        self.methodsListbox.bind("<<ListboxSelect>>", self.methodsSelectionChanged)
        self.topWindow.add(self.methodsListbox)
        self.updateMethods()

    def buildBottomFrame(self):
        self.buildEditorFrame()

    def buildEditorFrame(self):
        self.editor = ui.SmalltalkText(self.panedWindow)
        self.panedWindow.add(self.editor)

    def methodProtocolsSelectionChanged(self, event):
        self.updateMethods()
        self.updateEditor()

    def getSelectedMethodProtocols(self):
        return self.methodProtocolsListbox.getSelectedItems()

    def getMethodCategories(self):
        #Should take class/instance flag into account.
        return self.domain.getAllMethodCategories()

    def getMethods(self):
        # Should take class/instance flag into account.
        methods = []
        selectedMethodProtocols = self.getSelectedMethodProtocols()
        for each in self.domain.getAllMethods():
            if selectedMethodProtocols == [] or each.category in selectedMethodProtocols:
                methods.append(each)
        return methods

    def updateMethodProtocols(self):
        for each in self.getMethodCategories():
            self.methodProtocolsListbox.append(each)

    def updateMethods(self):
        self.methodsListbox.clear()
        for each in self.getMethods():
            self.methodsListbox.append(each)

    def methodsSelectionChanged(self, anEvent):
        self.updateEditor()

    def updateEditor(self):
        selectedItems = self.methodsListbox.getSelectedItems()
        if selectedItems == []:
            self.editor.setText(self.domain.getClassDefinition())
        else:
            self.editor.setText(selectedItems[0].source)










