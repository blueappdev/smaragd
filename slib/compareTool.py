#!/usr/bin/env python
#
# requires python 2.7

import os, sys
import string, StringIO
import getopt
import difflib
import json
import Tkinter as tk
from collections import OrderedDict
import slib.UI as ui
import Configuration

class CompareComponentFrame(tk.Frame):
    def addToolbarButton(self, toolbar, text, command):
        button = tk.Button(toolbar, text = text, command = command)
        button.pack(side = tk.LEFT, padx = 2, pady = 2)
    
    def createToolbar(self):        
        toolbar = tk.Frame(self)
        self.addToolbarButton(toolbar, "Paste", self.onPasteToFrame)
        self.addToolbarButton(toolbar, "JSON", self.onFormatJSON)
        toolbar.pack(side = tk.TOP, fill = tk.X)
    
    def onPasteToFrame(self, event = None):
        self.setText(self.getClipboardContents())
        self.mainApp.updateResults()

    def setText(self, aString):
        self.text.delete('1.0', tk.END)
        self.text.insert(tk.END, aString, None)
       
    def getClipboardContents(self):
        return self.master.clipboard_get()

    def getText(self):
        return self.text.get('1.0', tk.END)

    def onFormatJSON(self, event = None):
        rawJson = json.loads(self.getText(), object_pairs_hook=OrderedDict)
        prettyJson = json.dumps(rawJson, indent = 2)
        self.setText(prettyJson)

class CompareFrame(tk.Frame):
    def __init__(self, master):
        self.initializeCompareMode()
        self.initializeWrapMode()

        self.horizontalScrollbarUpdateInfo = 10
        self.verticalScrollbarUpdateInfo = 10
        self.navigationList = []
        self.navigationIndex = None
        tk.Frame.__init__(self, master = master)
        master.compareFrame = self
        self.master.title("Compare Tool")
        self.master.protocol("WM_DELETE_WINDOW", self.master.destroy)

        # Send explicitly the unpost context menu, 
        # whenever the mouse button is pressed
        # (The context menu does not disappear on Unix, 
        # when clicked outside the context menu.) 
        self.master.bind("<Button-1>", self.unpostContextMenus)

        self.pack()
        self.createMainToolbar()

        self.mainFrame=tk.Frame(
                self.master, 
                width = 1200, 
                height = 800)

        self.createLeftFrame()
        self.createRightFrame()
        self.createPopupMenus()
        self.mainFrame.pack(fill=tk.BOTH,expand=1)
        
        self.leftText.tag_config("red", foreground="red")
        self.leftText.tag_raise(tk.SEL)  # SEL overrides all other tags
        self.leftText.tag_config(tk.SEL, background="black", foreground="white")
        self.leftText.insert(tk.END, "Please paste the text to compare into both windows", None)

        self.rightText.tag_config("red", foreground="red")
        self.rightText.tag_raise(tk.SEL)  # SEL overrides all other tags
        self.rightText.tag_config(tk.SEL, background="black", foreground="white")
        self.rightText.insert(tk.END, "Please paste the text to compare into both windows", None)
        
        # Update according to initialized modes.
        self.compareModeChanged()
        self.wrapModeChanged()

    def createMainToolbar(self):
        self.buttonFrame=tk.Frame(self.master)
        tk.Radiobutton(self.buttonFrame,
              text="Lines",
              #padx = 20,
              variable=self.compareMode,
              value='lines').pack(side=tk.LEFT)
        tk.Radiobutton(self.buttonFrame, 
              text="Words",
              #padx = 20, 
              variable=self.compareMode, 
              value='words').pack(side=tk.LEFT)
        tk.Radiobutton(self.buttonFrame, 
                text="Characters",
                #padx = 20, 
                variable=self.compareMode, 
                value='characters').pack(side=tk.LEFT)
        tk.Checkbutton(self.buttonFrame, 
                text = "Wrap", 
                variable = self.wrapMode, 
                onvalue = tk.WORD,
                offvalue = tk.NONE).pack(side=tk.LEFT)
        self.buttonFirstDiff=tk.Button(
                self.buttonFrame,
                text="First",
                state=tk.DISABLED,
                command=self.navigateToFirstDiff)
        self.buttonFirstDiff.pack(side=tk.LEFT, padx=2, pady=2)
        self.buttonPreviousDiff=tk.Button(
                self.buttonFrame,
                text="Previous",
                state=tk.DISABLED,
                command=self.navigateToPreviousDiff)
        self.buttonPreviousDiff.pack(side=tk.LEFT, padx=2, pady=2)
        self.buttonNextDiff=tk.Button(
                self.buttonFrame,
                text="Next",
                state=tk.DISABLED,
                command=self.navigateToNextDiff)
        self.buttonNextDiff.pack(side=tk.LEFT, padx=2, pady=2)
        self.buttonLastDiff=tk.Button(
                self.buttonFrame,
                text="Last",
                state=tk.DISABLED,
                command=self.navigateToLastDiff)
        self.buttonLastDiff.pack(side=tk.LEFT, padx=2, pady=2)

        self.buttonFrame.pack(side=tk.TOP, fill=tk.X)
        
    def createLeftFrame(self):
        self.leftFrame = CompareComponentFrame(self.mainFrame)
        self.leftFrame.mainApp = self  # hack
        self.leftFrame.createToolbar()

        self.leftVerticalScrollbar = tk.Scrollbar(
                self.leftFrame, 
                orient = tk.VERTICAL)
        self.leftHorizontalScrollbar=tk.Scrollbar(
                self.leftFrame, 
                orient = tk.HORIZONTAL)
        self.leftText = tk.Text(self.leftFrame,
                bg="white",
                xscrollcommand=self.leftxset,
                yscrollcommand=self.leftyset)
        self.leftFrame.text = self.leftText
        self.leftText.config(font = self.textFont())
        self.leftText.config(wrap = tk.NONE)
        self.leftVerticalScrollbar.pack(side = tk.RIGHT, fill=tk.Y)
        self.leftHorizontalScrollbar.pack(side = tk.BOTTOM, fill=tk.X)
        self.leftText.pack(fill=tk.BOTH,expand = 1)
        #self.leftFrame.pack(side=tk.LEFT,fill=tk.BOTH,expand=1)
        #self.leftFrame.grid(row=0,column=0,stick=tk.NSEW,expand=1)
        self.leftFrame.place(relwidth = 0.5,width = -7, relheight = 1)

        self.leftText.bind("<Key>", self.filterKey)
        self.leftText.bind("<Button-2>", self.popupLeftMenu) # button 2 for Mac
        self.leftText.bind("<Button-3>", self.popupLeftMenu)

        # Connect scrollbars with widgets.
        self.leftVerticalScrollbar.config(command = self.yview)
        self.leftHorizontalScrollbar.config(command = self.xview)    

    def createRightFrame(self):
        self.rightFrame = CompareComponentFrame(self.mainFrame)
        self.rightFrame.mainApp = self  # hack
        self.rightFrame.createToolbar()
    
        self.rightVerticalScrollbar = tk.Scrollbar(
                self.rightFrame, 
                orient = tk.VERTICAL)
        self.rightHorizontalScrollbar = tk.Scrollbar(
                self.rightFrame, 
                orient = tk.HORIZONTAL)
        self.rightText = tk.Text(
                self.rightFrame,
                bg = "white",
                xscrollcommand = self.rightxset,
                yscrollcommand = self.rightyset)
        self.rightFrame.text = self.rightText
        self.rightText.config(font = self.textFont())
        self.rightText.config(wrap = tk.NONE)
        self.rightVerticalScrollbar.pack(side = tk.RIGHT, fill=tk.Y)
        self.rightHorizontalScrollbar.pack(side = tk.BOTTOM, fill=tk.X)
        self.rightText.pack(fill = tk.BOTH, expand = 1)
        self.rightFrame.place(
                relx = 0.5, 
                x = -7, 
                width = -7, 
                relwidth = 0.5, 
                relheight = 1)

        self.rightText.bind("<Key>", self.filterKey)
        self.rightText.bind("<Button-2>", self.popupRightMenu) # button 2 for Mac
        self.rightText.bind("<Button-3>", self.popupRightMenu)

        # Connect scrollbars with widgets.
        self.rightVerticalScrollbar.config(command = self.yview)
        self.rightHorizontalScrollbar.config(command = self.xview)
        
    def textFont(self):
        return ("Tahoma", 7)
        
    def initializeCompareMode(self):
        self.compareMode = tk.StringVar()
        self.compareMode.set("words")
        self.compareMode.trace("w", self.compareModeChanged)
        
    def compareModeChanged(self, *unusedArguments):
        #print "compareModeChanged", self.compareMode.get()
        self.updateResults()
        
    def initializeWrapMode(self):
        self.wrapMode = tk.StringVar(name = "wrapMode")
        self.wrapMode.set(tk.WORD)
        self.wrapMode.trace("w", self.wrapModeChanged)
        
    def wrapModeChanged(self, *unusedArguments):
        #print "wrapModeChanged", self.wrapMode.get()
        self.leftText.config(wrap = self.wrapMode.get())
        self.rightText.config(wrap = self.wrapMode.get())

    def leftxset(self,a,b):
        if self.horizontalScrollbarUpdateInfo==40:
            self.horizontalScrollbarUpdateInfo=0
            self.leftHorizontalScrollbar.set(a,b)
            self.rightHorizontalScrollbar.set(a,b)
        elif self.horizontalScrollbarUpdateInfo==0:
            pass
        elif self.horizontalScrollbarUpdateInfo==20:
            self.leftHorizontalScrollbar.set(a,b)
            self.rightHorizontalScrollbar.set(a,b)
        elif self.horizontalScrollbarUpdateInfo==10:
            self.horizontalScrollbarUpdateInfo=0
            self.leftHorizontalScrollbar.set(a,b)
            self.rightHorizontalScrollbar.set(a,b)
            self.leftText.xview("moveto",a)
            self.rightText.xview("moveto",a)
            self.mainFrame.update_idletasks()
            self.horizontalScrollbarUpdateInfo=10
        else:
            assert(0)

    def rightxset(self,a,b):
        self.leftxset(a,b)

    def leftyset(self,a,b):
        if self.verticalScrollbarUpdateInfo==40:
            self.verticalScrollbarUpdateInfo=0
            self.leftVerticalScrollbar.set(a,b)
            self.rightVerticalScrollbar.set(a,b)
        elif self.verticalScrollbarUpdateInfo==0:
            pass
        elif self.verticalScrollbarUpdateInfo==20:
            self.leftVerticalScrollbar.set(a,b)
            self.rightVerticalScrollbar.set(a,b)
        elif self.verticalScrollbarUpdateInfo==10:
            self.verticalScrollbarUpdateInfo=0
            self.leftVerticalScrollbar.set(a,b)
            self.rightVerticalScrollbar.set(a,b)
            self.leftText.yview("moveto",a)
            self.rightText.yview("moveto",a)
            self.mainFrame.update_idletasks()
            self.verticalScrollbarUpdateInfo=10
        else:
            assert(0)

    def rightyset(self,a,b):
        self.leftyset(a,b)

    def xview(self,*a):
        self.horizontalScrollbarUpdateInfo=20
        if len(a)==2:
            self.leftText.xview(a[0],a[1])
            self.rightText.xview(a[0],a[1])
        elif len(a)==3:
            self.leftText.xview(a[0],a[1],a[2])
            self.rightText.xview(a[0],a[1],a[2])
        else:
            assert(0)
        self.mainFrame.update_idletasks()
        self.horizontalScrollbarUpdateInfo=10

    def yview(self,*a):
        self.verticalScrollbarUpdateInfo=20
        if len(a)==2:
            self.leftText.yview(a[0],a[1])
            self.rightText.yview(a[0],a[1])
        elif len(a)==3:
            self.leftText.yview(a[0],a[1],a[2])
            self.rightText.yview(a[0],a[1],a[2])
        else:
            assert(0)
        self.mainFrame.update_idletasks()
        self.verticalScrollbarUpdateInfo=10
  
    def navigateToFirstDiff(self):
        self.buttonFirstDiff.focus()
        if (self.navigationIndex is None) and (len(self.navigationList) != 0):
            self.navigationIndex=0
        if self.navigationIndex>0:
            self.navigationIndex=0
        self.navigateToIndex(-1)

    def navigateToPreviousDiff(self):
        self.buttonPreviousDiff.focus()
        if self.navigationIndex>0:
            self.navigationIndex=self.navigationIndex-1
        self.navigateToIndex(-1)

    def navigateToNextDiff(self):
        self.buttonNextDiff.focus()
        if (self.navigationIndex is None):
            self.navigationIndex=0
        else:
            if self.navigationIndex < len(self.navigationList)-1:
                self.navigationIndex=self.navigationIndex+1
        self.navigateToIndex(1)

    # navigate to the next green or red difference (insertionsi or removals)
    # but skip all blue differences (changes)
    def navigateToNextRedGreenDiff(self):
        self.buttonNextRedGreenDiff.focus()
        backupNavigationIndex=self.navigationIndex
        if (self.navigationIndex is None):
            self.navigationIndex = 0
        else:
            self.navigationIndex = self.navigationIndex + 1
        # find the next red/green navigation index
        while self.navigationIndex < len(self.navigationList):
            a,b,colorTag=self.navigationList[self.navigationIndex]
            #print a,b,colorTag,self.navigationIndex
            if colorTag == "red" or colorTag == "green":
                self.navigateToIndex(1)
                return
            self.navigationIndex = self.navigationIndex + 1
        self.navigationIndex = backupNavigationIndex 
           
    def navigateToLastDiff(self):
        self.buttonLastDiff.focus()
        if (self.navigationIndex is None) or (self.navigationIndex < len(self.navigationList) - 1):
            self.navigationIndex = len(self.navigationList) - 1
        self.navigateToIndex(1)

    def navigateToIndex(self,direction=1):
        if self.navigationIndex is None:
            self.buttonFirstDiff.config(state=tk.DISABLED)
            self.buttonPreviousDiff.config(state=tk.DISABLED)
            if len(self.navigationList)==0:
                self.buttonLastDiff.config(state=tk.DISABLED)
                self.buttonNextDiff.config(state=tk.DISABLED)
            else:
                self.buttonLastDiff.config(state=tk.NORMAL)
                self.buttonNextDiff.config(state=tk.NORMAL)
        else:
            a,b,colorTag=self.navigationList[self.navigationIndex]
 
            n=self.leftText.tag_names("%d.0" % a)
            n=filter(lambda x: x != "sel" and x != "highlight",n)
            if len(n)!=1:
                print n
                assert(len(n)==1)
            t="dark" + n[0]
            if t == "darkbluediffchar":
                t="darkblue"

            self.leftText.tag_config("highlight",background=t,foreground="white")
            self.rightText.tag_config("highlight",background=t,foreground="white")

            self.leftText.tag_remove("highlight",1.0,tk.END)
            self.rightText.tag_remove("highlight",1.0,tk.END)
        
            self.leftText.tag_add("highlight","%d.0" % a,"%d.0" % b)
            self.rightText.tag_add("highlight","%d.0" % a,"%d.0" % b)

            x = 0  
            y = 0
            if t == "darkblue":
                leftString = leftData[a-1][0]
                rightString = rightData[a-1][0]
                xdleft,ydleft,xdright,ydright = onelinediff(leftString,rightString)
                x = xdleft
                y = ydleft

            if self.leftText.bbox("%d.%d" % (b,x)) is None or self.leftText.bbox("%d.%d" % (a,x)) is None:
                self.verticalScrollbarUpdateInfo=40
                self.horizontalScrollbarUpdateInfo=40
                if direction == 1:
                    self.leftText.see("%d.%d" % (min(b+10000,self.totalLines),x))
                    self.rightText.see("%d.%d" % (min(b+10000,self.totalLines),x))
                    self.leftText.see("%d.%d" % (a,x))
                    self.rightText.see("%d.%d" % (a,x))
                elif direction == -1:
                    self.leftText.see("%d.%d" % (max(a-10000,0),x))
                    self.rightText.see("%d.%d" % (max(a-10000,0),x))
                    self.leftText.see("%d.%d" % (b,x))
                    self.rightText.see("%d.%d" % (b,x))
                self.mainFrame.update_idletasks()
                self.verticalScrollbarUpdateInfo = 10
                self.horizontalScrollbarUpdateInfo = 10

            if self.navigationIndex == 0:
                self.buttonFirstDiff.config(state = tk.DISABLED)
                self.buttonPreviousDiff.config(state = tk.DISABLED)
            else:
                self.buttonFirstDiff.config(state = tk.NORMAL)
                self.buttonPreviousDiff.config(state = tk.NORMAL)

            if self.navigationIndex>=len(self.navigationList)-1:
                self.buttonLastDiff.config(state = tk.DISABLED)
                self.buttonNextDiff.config(state = tk.DISABLED)
            else:
                self.buttonLastDiff.config(state = tk.NORMAL)
                self.buttonNextDiff.config(state = tk.NORMAL)

    def createPopupMenus(self):
        self.leftPopupMenu = tk.Menu(tearoff = 0)
        self.rightPopupMenu = tk.Menu(tearoff = 0)
        self.leftPopupMenu.add_command(label="Paste from clipboard", command=self.leftFrame.onPasteToFrame)
        self.rightPopupMenu.add_command(label="Paste from clipboard", command=self.rightFrame.onPasteToFrame)

    def popupLeftMenu(self, anEvent):
        self.unpostContextMenus()
        self.leftPopupMenu.post(anEvent.x_root, anEvent.y_root)

    def popupRightMenu(self, anEvent):
        self.unpostContextMenus()
        self.rightPopupMenu.post(anEvent.x_root, anEvent.y_root)

    def unpostContextMenus(self, anEvent=None):
        self.leftPopupMenu.unpost()
        self.rightPopupMenu.unpost()

    def filterKey(self,ev):
        # filter all keys which might modify the text

        #print "sym=<"+ev.keysym+">, code=<"+str(ev.keycode)+">, chr=<"+ev.char+">, state= <"+str(ev.state)+">"

        controlKeyDown = ev.state & 4
        
        if ev.keysym in [ "Left", "Right", "Up", "Down",
                          "Prior", "Next", "Home", "End",
                          "Escape", "F3" ]:
            return

        if controlKeyDown and ev.keysym in [ "f", "c", "x" ]:
            return
        
        # The event ev is considered as representing a key,
        # which would modify the text, which is not desired.
        return "break"

    def readFile(self, filename):
        stream = open(filename)
        contents = stream.read()
        stream.close()
        return contents

    def clearText(self):
        self.leftText.delete('1.0', tk.END)
        self.rightText.delete('1.0', tk.END)
            
    def fillText(self):
        a = self.readFile("testdata/a")
        b = self.readFile("testdata/b")
        matcher = difflib.SequenceMatcher(None, a, b)
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            #print ("%7s a[%d:%d] (%s) b[%d:%d] (%s)" %
            #    (tag, i1, i2, a[i1:i2], j1, j2, b[j1:j2]))
            if tag == "equal":
                tag = None
            else:
                tag = "red"

        self.updateResults()

    def splitIntoLines(self, aString):
        result = []
        line = StringIO.StringIO()
        for ch in aString:
            if ch == '\n':
                line.write(ch)
                result.append(line.getvalue())
                line = StringIO.StringIO()
            else:
                line.write(ch)
        result.append(line.getvalue())
        return result

    def categorizeCharacter(self, aCharacter):
        if aCharacter.isalnum():
            return 'alpha'
        if aCharacter.isspace():
            return 'white'
        return 'special'
        
    def splitIntoWords(self, aString):
        result = []
        word = StringIO.StringIO()
        previousCategory = 'unknown'
        for ch in aString:
            newCategory = self.categorizeCharacter(ch)
            if newCategory == previousCategory:
                word.write(ch)
            else:
                result.append(word.getvalue())
                word = StringIO.StringIO()
                word.write(ch)
                previousCategory = newCategory
        result.append(word.getvalue())
        return result

    def updateResults(self):
        #print "update results", self.compareMode.get()
        mode = self.compareMode.get()
        a = self.leftText.get('1.0', tk.END)
        b = self.rightText.get('1.0', tk.END)
        self.clearText()
        if mode == "lines":
            a = self.splitIntoLines(a)
            b = self.splitIntoLines(b)
            matcher = difflib.SequenceMatcher(None, a, b)
            for tag, i1, i2, j1, j2 in matcher.get_opcodes():
                #print ("%7s a[%d:%d] (%s) b[%d:%d] (%s)" %
                #    (tag, i1, i2, a[i1:i2], j1, j2, b[j1:j2]))
                if tag == "equal":
                    tag = None
                else:
                    tag = "red"
                for each in a[i1:i2]:
                    self.leftText.insert(tk.END, each, tag)
                for each in b[j1:j2]:
                    self.rightText.insert(tk.END, each, tag)
        elif mode == "words":
            a = self.splitIntoWords(a)
            b = self.splitIntoWords(b)
            matcher = difflib.SequenceMatcher(None, a, b)
            for tag, i1, i2, j1, j2 in matcher.get_opcodes():
                #print ("%7s a[%d:%d] (%s) b[%d:%d] (%s)" %
                #    (tag, i1, i2, a[i1:i2], j1, j2, b[j1:j2]))
                if tag == "equal":
                    tag = None
                else:
                    tag = "red"
                for each in a[i1:i2]:
                    self.leftText.insert(tk.END, each, tag)
                for each in b[j1:j2]:
                    self.rightText.insert(tk.END, each, tag)
        elif mode == "characters":
            matcher = difflib.SequenceMatcher(None, a, b)
            for tag, i1, i2, j1, j2 in matcher.get_opcodes():
                #print ("%7s a[%d:%d] (%s) b[%d:%d] (%s)" %
                #    (tag, i1, i2, a[i1:i2], j1, j2, b[j1:j2]))
                if tag == "equal":
                    tag = None
                else:
                    tag = "red"
                self.leftText.insert(tk.END, a[i1:i2], tag)
                self.rightText.insert(tk.END, b[j1:j2], tag)
        else:
            self.error("unsupported compare mode")

class CompareWindow(tk.Toplevel):
    def __init__(self, root):
        tk.Toplevel.__init__(self, root)
        CompareFrame(self)
                        
if __name__ == "__main__":
    root = tk.Tk()
    CompareFrame(root)
    try:
        root.mainloop()
    except KeyboardInterrupt:
       pass



