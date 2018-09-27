#!/usr/bin/env python
#
# requires python 2.7

import os, sys
import string, fnmatch
import Tkinter as tk
from Kernel import *
import UI as ui
import classBrowser

class ClassWrapper:
    def __init__(self, aClass):
        self.value = aClass

    def __repr__(self):
        return self.value.getBrowserDescription()

class ClassFinderFrame(ui.ApplicationFrame):
    def __init__(self, master, parentApplication):
        ui.ApplicationFrame.__init__(self, master = master, parentApplication = parentApplication)
        self.master.title("Find Class")
        self.master.protocol("WM_DELETE_WINDOW", self.master.destroy)
        self.pack()
        self.mainFrame=tk.Frame(self.master)
        self.buildEntry()
        self.buildSearchResultsListbox()
        self.buildButtons()
        self.mainFrame.pack(fill=tk.BOTH, expand=1)
        self.initializeWrappers()
        self.classNameChanged()
        self.selectionChanged()

    def getFont(self):
        return Configuration.globalConfiguration.getFont()

    def buildEntry(self):
        self.methodNameVar = tk.StringVar()
        self.methodNameVar.trace("w", self.classNameChanged)
        self.entryLabel = tk.Label(
                self.mainFrame,
                text="Find:",
                font=self.getFont())
        self.entryLabel.pack(
                side=tk.TOP,
                pady=0,
                padx=5,
                anchor=tk.W)
        self.entry = tk.Entry(
                self.mainFrame,
                textvariable=self.methodNameVar,
                font=self.getFont())
        self.entry.pack(side=tk.TOP, fill=tk.X, pady=5, padx=5)

    def buildSearchResultsListbox(self):
        self.listboxLabel = tk.Label(
                self.mainFrame,
                text="Classes:",
                font=self.getFont())
        self.listboxLabel.pack(side=tk.TOP, pady=0, padx=5, anchor=tk.W)
        self.listboxFrame = tk.Frame(self.mainFrame)
        self.listbox = tk.Listbox(
                self.listboxFrame,
                selectmode=tk.BROWSE,
                width = 70,
                height = 30,
                font=self.getFont())
        self.listbox.bind("<<ListboxSelect>>", self.selectionChanged)
        self.listbox.bind('<Double-Button-1>', self.onDoubleClick)
        scroll = tk.Scrollbar(self.listboxFrame, command=self.listbox.yview)
        self.listbox.configure(yscrollcommand = scroll.set)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.listboxFrame.pack(fill=tk.BOTH, expand=1, pady=5, padx=5)

    def selectionChanged(self, event=None):
        if len(self.listbox.curselection()) == 0:
            self.buttonOK.config(state="disabled")
        else:
            self.buttonOK.config(state="normal")

    def buildButtons(self):
        self.buttonsFrame = tk.Frame(self.mainFrame)
        self.buttonCancel = tk.Button(
                self.buttonsFrame,
                text="Cancel",
                width=10,
                font=self.getFont(),
                command = self.onCancel)
        self.buttonCancel.pack(side=tk.RIGHT, pady=5, padx=5)
        self.buttonOK = tk.Button(
                self.buttonsFrame,
                text="OK",
                width=10,
                font=self.getFont(),
                command=self.onOK)
        self.buttonOK.pack(side=tk.RIGHT, pady=5, padx=5)
        self.buttonsFrame.pack(side=tk.BOTTOM, fill=tk.X)

    def classNameChanged(self, *unused):
        self.updateListbox(pattern = self.methodNameVar.get())

    def getAllClassWrappers(self):
        wrappers = []
        for each in self.parentApplication.getAllClasses():
            wrappers.append(ClassWrapper(each))
        wrappers.sort(key=lambda each: each.value.getUnqualifiedName())
        return wrappers

    def initializeWrappers(self):
        result = []
        for each in self.getAllClassWrappers():
            result.append(each)
        self.wrappers = result

    def updateListbox(self, pattern):
        self.listbox.delete(0, tk.END)
        for each in self.wrappers:
            if fnmatch.fnmatch(each.value.getUnqualifiedName(), pattern + "*"):
                self.listbox.insert(tk.END, each)

    def findClassForSelectedString(self, aString):
        for each in self.wrappers:
            if repr(each) == aString:
                return each.value
        self.error("selection not found")

    def onDoubleClick(self, event):
        self.onOK()

    def onOK(self):
        selectedString =  self.listbox.get(self.listbox.curselection())
        selectedClass = self.findClassForSelectedString(selectedString)
        newWindow = tk.Toplevel(self.parentApplication.master)
        newWindow.title(selectedClass.name)
        reload(classBrowser)
        classBrowser.ClassBrowser(
                newWindow,
                parentApplication = self.parentApplication,
                domain=selectedClass)
        self.master.destroy()

    def onCancel(self):
        self.master.destroy()


                        



