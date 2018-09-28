#!/usr/bin/env python
#
# UI.py
#
# requires python 2.7

import Tkinter as tk
import tkFont
from Kernel import *
import Configuration

class BasicFrame(tk.Frame, Object):
    def __init__(self, master, parentApplication=None):
        tk.Frame.__init__(self, master = master)
        self.parentApplication = parentApplication

    def getFont(self):
        return Configuration.globalConfiguration.getFont()

class ApplicationFrame(BasicFrame):
    def __init__(self, master, parentApplication=None):
        BasicFrame.__init__(self, master = master, parentApplication=parentApplication)
        self.master.protocol("WM_DELETE_WINDOW", self.quit)
        self.installMenubar()

    def installMenubar(self):
        menubar = tk.Menu()
        self.buildMenubar(menubar)
        self.master.config(menu = menubar)

    def buildMenubar(self, menubar):
        pass

    def addMenu(self, parentMenu, label):
        newMenu = tk.Menu(parentMenu, tearoff=0, font = self.getFont())
        parentMenu.add_cascade(
                label = label,
                menu = newMenu)
        return newMenu

    def addMenuItem(self, menu, label, command):
        newMenuItem = menu.add_command(
                label = label,
                command = command,
                font=self.getFont())

    def openTopLevelFrame(self, aFrameClass):
        newWindow = tk.Toplevel(self.master)
        newFrame = aFrameClass(newWindow, self)

class BetterListbox(BasicFrame):
    def __init__(self, master):
        BasicFrame.__init__(self, master)
        self.displayStringFunction = None
        self.displayColorFunction = None
        self.values = []
        self.__listbox = tk.Listbox(
                self,
                selectmode=tk.EXTENDED,
                activestyle=tk.DOTBOX,
                font=self.getFont())
        self.__listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)
        scroll = tk.Scrollbar(self, command=self.__listbox.yview)
        self.__listbox.configure(yscrollcommand = scroll.set)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        #self.listboxFrame.pack(fill=tk.BOTH, expand=1, pady=5, padx=5)

    def clear(self):
        self.__listbox.delete(0, tk.END)
        self.values = []

    def append(self, anObject):
        if self.displayStringFunction is None:
            representation = str(anObject)
        else:
            representation = self.displayStringFunction(anObject)
        self.__listbox.insert(tk.END, representation)
        self.values.append(anObject)
        assert self.__listbox.size() == len(self.values)
        if self.displayColorFunction is not None:
            color = self.displayColorFunction(anObject)
            self.__listbox.itemconfig(len(self.values)-1, foreground=color)

    def getSelectedItems(self):
        assert self.__listbox.size() == len(self.values)
        return [self.values[int(i)] for i in self.__listbox.curselection()]

    def bind(self, eventName, callback):
        self.__listbox.bind(eventName, callback)

class BetterText(tk.Frame):
    def __init__(self, master):
        tk.Frame.__init__(self, master)
        self.realWidget = tk.Text(
                self,
                font=Configuration.globalConfiguration.getFont(),
                wrap=tk.WORD,
                spacing1=2,
                spacing2=2,
                spacing3=2)
        self.realWidget.pack(side=tk.LEFT, fill=tk.BOTH, expand = 1)
        font = tkFont.Font(font=self.realWidget['font'])  # get font associated with Text widget
        tab_width = font.measure(' ' * 8)  # compute desired width of tabs
        self.realWidget.config(tabs=(tab_width,))

    def clear(self):
        self.realWidget.delete("1.0", tk.END)

    def setText(self, aString):
        self.clear()
        self.realWidget.insert(tk.END, aString)

    def replaceSelection(self, aString):
        if self.realWidget.tag_ranges(tk.SEL):
            self.realWidget.delete(tk.SEL_FIRST, tk.SEL_LAST)
        self.realWidget.insert(tk.INSERT, aString)

class SmalltalkText(BetterText):
    def __init__(self, master):
        BetterText.__init__(self, master)
        self.realWidget.bind("<Control-F>", self.onControlShiftF)
        self.realWidget.bind("<Control-T>", self.onControlShiftT)
        #self.realWidget.bind("<Tab", self.onTab)

    def onControlShiftT(self, anEvent):
        self.replaceSelection("ifTrue:")

    def onControlShiftF(self, anEvent):
        self.replaceSelection("ifFalse:")
        
        import Tkinter as tk

"""

For scrollbar stuff
        root = tk.Tk()

textContainer = tk.Frame(root, borderwidth=1, relief="sunken")
text = tk.Text(textContainer, width=24, height=13, wrap="none", borderwidth=0)
textVsb = tk.Scrollbar(textContainer, orient="vertical", command=text.yview)
textHsb = tk.Scrollbar(textContainer, orient="horizontal", command=text.xview)
text.configure(yscrollcommand=textVsb.set, xscrollcommand=textHsb.set)

text.grid(row=0, column=0, sticky="nsew")
textVsb.grid(row=0, column=1, sticky="ns")
textHsb.grid(row=1, column=0, sticky="ew")

textContainer.grid_rowconfigure(0, weight=1)
textContainer.grid_columnconfigure(0, weight=1)

textContainer.pack(side="top", fill="both", expand=True)

root.mainloop()
"""







