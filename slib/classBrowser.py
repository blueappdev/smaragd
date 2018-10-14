#!/usr/bin/env python
#
# requires python 2.7

import Tkinter as tk
import UI as ui
from compareTool import CompareWindow
import scmd

class ClassBrowser(ui.ApplicationFrame):
    def __init__(self, master, parentApplication, aClass):
        ui.ApplicationFrame.__init__(self, master = master, parentApplication = parentApplication)
        self.currentClass = aClass
        self.initializeSide()
        self.initializeCommentMode()
        self.master.title("[CB] " + self.currentClass.getBrowserDescription())
        self.master.protocol("WM_DELETE_WINDOW", self.master.destroy)
        self.pack(fill=tk.BOTH, expand=1)
        self.panedWindow = tk.PanedWindow(self, orient=tk.VERTICAL,  sashpad=4, sashrelief=tk.RAISED)
        self.panedWindow.pack(fill=tk.BOTH, expand=1)
        self.buildTopFrame()
        self.buildBottomFrame()
        self.initialUpdate()

    def initialUpdate(self):
        self.updatePackages()
        self.updateMethodProtocols()

    def buildMenubar(self, menubar):
        self.buildClassMenu(menubar)

    def buildClassMenu(self, parentMenu):
        newMenu = self.addMenu(parentMenu, "Class")
        self.addMenuItem(newMenu, "Compare with shadow class", self.onCompareWithShadowClass)

    def initializeSide(self):
        if self.currentClass.getAllMethods() == [] and self.currentClass.metaClass.getAllMethods() != []:
            newSide = "class"
        else:
            newSide = "instance"
        self.side = tk.StringVar()
        self.side.set(newSide)
        self.side.trace("w", self.sideChanged)

    def initializeCommentMode(self):
        self.commentMode = tk.BooleanVar()
        self.commentMode.set(False)
        self.commentMode.trace("w", self.commentModeChanged)

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
        self.packagesListbox = ui.BetterListbox(self.topLeftFrame)
        self.packagesListbox.displayStringFunction = lambda aPackage: aPackage.name
        self.packagesListbox.bind("<<ListboxSelect>>", self.packagesSelectionChanged)
        self.packagesListbox.pack(fill=tk.BOTH, expand=1)
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
        tk.Checkbutton(self.radioButtonFrame,
              text="Comment",
              #padx = 20,
              variable=self.commentMode).pack(side=tk.LEFT)
        self.radioButtonFrame.pack(fill=tk.BOTH, expand=1)
        self.topWindow.add(self.topLeftFrame)

    def buildMethodsFrame(self):
        self.methodsListbox = ui.BetterListbox(self.topWindow)
        self.methodsListbox.displayStringFunction = lambda aMethod: aMethod.selector
        self.methodsListbox.displayColorFunction = lambda aMethod: self.displayColorForMethod(aMethod)
        self.methodsListbox.bind("<<ListboxSelect>>", self.methodsSelectionChanged)
        self.topWindow.add(self.methodsListbox)
        self.popupMenu = tk.Menu(self.methodsListbox, tearoff=0)
        self.addMenuItem(self.popupMenu, "Compare with shadow method", self.onCompareWithShadowMethod)
        self.methodsListbox.bind("<Button-3>", self.popup)
        self.bind("<Button-2>", self.popup) #Aqua

    def popup(self, event):
        try:
            self.popupMenu.tk_popup(event.x_root, event.y_root, 0)
        finally:
            self.popupMenu.grab_release()

    def onCompareWithShadowMethod(self):
        method = self.methodsListbox.getSelectedItems()[0]
        compareTool = CompareWindow(self.master)
        compareFrame = compareTool.compareFrame
        compareFrame.leftFrame.setText(method.source)
        compareFrame.rightFrame.setText(method.getShadowMethod().source)
        compareFrame.updateResults()

    def compareMethod(self, aMethod):
        shadowMethod = aMethod.getShadowMethod()
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
            return "#006F00"
        if result == "different":
            return "#0000FF"
        if result == "sameEffect":
            return "#7F6F00"
        return None

    def buildBottomFrame(self):
        self.buildEditorFrame()

    def buildEditorFrame(self):
        self.editor = ui.SmalltalkText(self.panedWindow)
        self.panedWindow.add(self.editor)

    def packagesSelectionChanged(self, *unused):
        self.updateMethods()

    def methodProtocolsSelectionChanged(self, *unused):
        self.updateMethods()

    def methodsSelectionChanged(self, *unused):
        self.updateEditor()

    def sideChanged(self, *unused):
        self.initialUpdate()

    def commentModeChanged(self, *unused):
        self.updateEditor()

    def getSelectedPackages(self):
        return self.packagesListbox.getSelectedItems()

    def getSelectedMethodProtocols(self):
        return self.methodProtocolsListbox.getSelectedItems()

    def getMethodCategories(self):
        return self.getClassSide().getAllMethodCategories()

    def getClassSide(self):
        side = self.side.get()
        if side == "instance":
            return self.currentClass
        if side == "class":
            return self.currentClass.metaClass
        self.error("Unsupported side", side)

    def getVisibleMethods(self):
        methods = []
        selectedPackages = self.getSelectedPackages()
        selectedMethodProtocols = self.getSelectedMethodProtocols()
        for each in self.getClassSide().getAllMethods():
            if selectedPackages == [] or each.package in selectedPackages:
                if selectedMethodProtocols == [] or each.category in selectedMethodProtocols:
                    methods.append(each)
        return methods

    def updatePackages(self):
        self.packagesListbox.clear()
        for each in self.getClassSide().getAllPackages():
            self.packagesListbox.append(each)

    def updateMethodProtocols(self):
        self.methodProtocolsListbox.clear()
        for each in self.getMethodCategories():
            self.methodProtocolsListbox.append(each)
        self.methodProtocolsSelectionChanged()

    def updateMethods(self):
        self.methodsListbox.clear()
        for each in self.getVisibleMethods():
            self.methodsListbox.append(each)
        self.methodsSelectionChanged()

    def updateEditor(self):
        if self.commentMode.get():
            self.showClassComment()
        else:
            selectedItems = self.methodsListbox.getSelectedItems()
            if selectedItems == []:
                self.showClassDefinition()
            else:
                #print "Method package", selectedItems[0].package.name
                self.editor.setText(selectedItems[0].source)

    def showClassComment(self):
        self.editor.setText(self.currentClass.comment)

    def showClassDefinition(self):
        self.editor.setText(self.currentClass.getClassDefinition())

    def onCompareWithShadowClass(self):
        print "Compare with shadow class", self.currentClass.name











