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
        self.shadowClass = self.findShadowClass(self.domain)
        self.initializeSide()
        self.master.title("[CB] " + self.domain.getBrowserDescription())
        self.master.protocol("WM_DELETE_WINDOW", self.master.destroy)
        self.pack(fill=tk.BOTH, expand=1)
        self.panedWindow = tk.PanedWindow(self, orient=tk.VERTICAL,  sashpad=4, sashrelief=tk.RAISED)
        self.panedWindow.pack(fill=tk.BOTH, expand=1)
        self.buildTopFrame()
        self.buildBottomFrame()
        self.updateMethodProtocols()

    def initializeSide(self):
        if self.domain.getAllMethods() == [] and self.domain.metaClass.getAllMethods() != []:
            newSide = "class"
        else:
            newSide = "instance"
        self.side = tk.StringVar()
        self.side.set(newSide)
        self.side.trace("w", self.sideChanged)

    def buildTopFrame(self):
        self.topWindow = tk.PanedWindow(
                self.panedWindow,
                orient=tk.HORIZONTAL,
                sashpad=4,
                sashrelief=tk.RAISED)
        self.panedWindow.add(self.topWindow)
        self.buildTopLeftFrame()
        self.buildMethodsFrame()

    def buildTopLeftFrame(self):
        self.topLeftFrame = tk.Frame(self.topWindow)
        self.methodProtocolsListbox = ui.BetterListbox(self.topLeftFrame)
        self.methodProtocolsListbox.bind("<<ListboxSelect>>", self.methodProtocolsSelectionChanged)
        self.methodProtocolsListbox.pack(fill=tk.BOTH, expand=1)
        self.radioButtonFrame = tk.Frame(self.topLeftFrame)
        tk.Radiobutton(self.radioButtonFrame,
              text="Instance",
              #padx = 20,
              variable=self.side,
              value='instance').pack(side=tk.LEFT)
        tk.Radiobutton(self.radioButtonFrame,
              text="Class",
              #padx = 20,
              variable=self.side,
              value='class').pack(side=tk.LEFT)
        self.radioButtonFrame.pack(fill=tk.BOTH, expand=1)
        self.topWindow.add(self.topLeftFrame)

    def buildMethodsFrame(self):
        self.methodsListbox = ui.BetterListbox(self.topWindow)
        self.methodsListbox.displayStringFunction = lambda m: m.selector
        self.methodsListbox.displayColorFunction = lambda m: self.displayColorForMethod(m)
        self.methodsListbox.bind("<<ListboxSelect>>", self.methodsSelectionChanged)
        self.topWindow.add(self.methodsListbox)

    def compareMethod(self, aMethod):
        if self.shadowClass is None:
            return "missing"
        shadowMethod = self.shadowClass.methodsDictionary.get(aMethod.selector, None)
        if shadowMethod is None:
            return "missing"
        if aMethod.source == shadowMethod.source:
            return "equal"
        # tokensAsString should be changed to bytecode comparision
        if aMethod.tokensAsStrings() == shadowMethod.tokensAsStrings():
            return "sameEffect"
        return "different"

    def displayColorForMethod(self, aMethod):
        result = self.compareMethod(aMethod)
        if result == "equal":
            return "darkgreen"
        if result == "different":
            return "blue"
        if result == "sameEffect":
            return "#FF0000"
        return None

    def findShadowClass(self, aClass):
        shadowImage = None
        if aClass.image == self.parentApplication.image1:
            shadowImage = self.parentApplication.image2
        if aClass.image == self.parentApplication.image2:
            shadowImage = self.parentApplication.image1
        return shadowImage.findClassNamed(aClass.name, ignoreNamespaces = True)

    def buildBottomFrame(self):
        self.buildEditorFrame()

    def buildEditorFrame(self):
        self.editor = ui.SmalltalkText(self.panedWindow)
        self.panedWindow.add(self.editor)

    def methodProtocolsSelectionChanged(self, *unused):
        self.updateMethods()

    def methodsSelectionChanged(self, *unused):
        self.updateEditor()

    def sideChanged(self, *unused):
        self.updateMethodProtocols()

    def getSelectedMethodProtocols(self):
        return self.methodProtocolsListbox.getSelectedItems()

    def getMethodCategories(self):
        return self.getDomainSide().getAllMethodCategories()

    def getDomainSide(self):
        side = self.side.get()
        if side == "instance":
            return self.domain
        if side == "class":
            return self.domain.metaClass
        self.error("Unsupported side", side)

    def getMethods(self):
        methods = []
        selectedMethodProtocols = self.getSelectedMethodProtocols()
        for each in self.getDomainSide().getAllMethods():
            if selectedMethodProtocols == [] or each.category in selectedMethodProtocols:
                methods.append(each)
        return methods

    def updateMethodProtocols(self):
        self.methodProtocolsListbox.clear()
        for each in self.getMethodCategories():
            self.methodProtocolsListbox.append(each)
        self.methodProtocolsSelectionChanged()

    def updateMethods(self):
        self.methodsListbox.clear()
        for each in self.getMethods():
            self.methodsListbox.append(each)
        self.methodsSelectionChanged()

    def updateEditor(self):
        selectedItems = self.methodsListbox.getSelectedItems()
        if selectedItems == []:
            self.editor.setText(self.domain.getClassDefinition())
        else:
            self.editor.setText(selectedItems[0].source)











