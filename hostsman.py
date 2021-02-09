#!/usr/bin/env python3

from sys import platform
from tkinter import *
from tkinter import filedialog
from tkinter import messagebox
from tkinter import scrolledtext as st
#from style import *
import sqlite3


fileUnsavedChanges = False # Are they any unsaved changes?
fileMainFilename = ""

root = Tk()
root.title("Hosts File Manager")
#root.iconbitmap("/path/to/file.ico")
root.geometry("800x600")
root.OShosts = ""
root.OShostsPath = ""
root.PathSlash = "/"

def detectOS():
    if platform.system() == "Linux":
        root.OShostsPath = "/etc"
        root.OShosts = root.OShostsPath + "/hosts"
    elif platform.system() == "Darwin":
        root.OShostsPath = "/private/etc"
        root.OShosts = root.OShostsPath + "/hosts"
    elif platform.system() == "Windows":
        root.PathSlash = "\\"
        # The Windows registry is the authoritative source for the location of the HOSTS file.
        try:
            hkey = winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE)
            subkey = winreg.OpenKey(hkey, "SYSTEM\\CurrentControlSet\\Services\\Tcpip\\Parameters")
            kval = winreg.QueryValueEx(subkey, "DataBasePath")[0]
            root.OShostsPath = winreg.ExpandEnvironmentStrings(kval)
            root.OShosts = root.OShostsPath + "\\HOSTS"
            hkey.Close()
        except:
            return
#    Linux', 'Darwin', 'Java', 'Windows
detectOS()
init_dir = root.OShostsPath + root.PathSlash

def openHostsFile(fname):
    # Iterate through the lines
    pass
    return False

def mnuFileOpenSys():
    if root.OShosts == "":
        response = messagebox.askyesno("HOSTS Not Found", 
            "Unable to find HOSTS file or detect Operating System\n\n" +
            "Do you want to browse for the HOSTS file?")
        if response == 1:
            root.fileopen = filedialog.askopenfilename(initialdir=init_dir, title="Open System HOSTS")
        else:
            return
    else:
        root.fileopen = root.OShosts
    if openHostsFile(root.fileopen): # detect depending on host type (Win/OSX/Linux)
        fileMainFilename = root.fileopen

def mnuFileOpen():
    root.fileopen = filedialog.askopenfilename(initialdir=init_dir, title="Open a Hosts file")
    if openHostsFile(root.fileopen):
        fileMainFilename = root.fileopen


def mnuFileMerge():
    root.fileopen = filedialog.askopenfilename(initialdir=init_dir, title="Merge Hosts file")
    fileUnsavedChanges = True

    # fileOpen.destroy()

def mnuFileSave():
    root.filesave = filedialog.asksaveasfilename(initialdir=init_dir, title="Save Hosts file")
    fileUnsavedChanges = False
    # SaveFile via hostsBox.get()

def mnuFileSaveAs():
    root.filesave = filedialog.asksaveasfilename(initialdir=init_dir, title="Save As...")
    fileUnsavedChanges = False
    # SaveFile via hostsBox.get()

def mnuFileRevert():
    fileUnsavedChanges = False
    # SaveFile via hostsBox.get()

def mnuFileExit():
    quitMsg = "Are you sure you want to quit?"
    if fileUnsavedChanges:
        quitMsg = "You have UNSAVED changes, are you sure you want to quit?"
    response = messagebox.askyesno("Quit?", quitMsg)
    if response == 1:
        root.quit()
    # Exit app

def mnuEditCut():
    pass

def mnuEditCopy():
    pass

def mnuEditPaste():
    pass

def mnuHelpAbout():
    messagebox.showinfo("About", "This program is to help merge multiple HOSTS files.")

clicked = StringVar()

sqdb = sqlite3.connect("hosts.db")

sqcur = sqdb.cursor()

myMenu = Menu(root)
root.config(menu=myMenu)

mnuFile = Menu(myMenu)
myMenu.add_cascade(label="File", menu=mnuFile)
mnuFile.add_command(label="Open System Hosts", command=mnuFileOpenSys)
mnuFile.add_command(label="Open...", command=mnuFileOpen)
mnuFile.add_command(label="Merge", command=mnuFileMerge)
mnuFile.add_command(label="Save", command=mnuFileSave)
mnuFile.add_command(label="Save As...", command=mnuFileSaveAs)
mnuFile.add_command(label="Revert", command=mnuFileRevert)
mnuFile.add_separator()
mnuFile.add_command(label="Exit", command=mnuFileExit)

mnuEdit = Menu(myMenu)
myMenu.add_cascade(label="Edit", menu=mnuEdit)
mnuEdit.add_cascade(label="Cut", command=mnuEditCut)
mnuEdit.add_cascade(label="Copy", command=mnuEditCopy)
mnuEdit.add_cascade(label="Paste", command=mnuEditPaste)

#
# Main editor window
#
hostsBox = st.ScrolledText(root, wrap="word", bg="black", fg="white")
#hostsBox.pack needs to be added AFTER StatusBar is added

# Status bar (label)
statusBarRoot = Label(root, relief=SUNKEN)
statusBar = Label(statusBarRoot, text="Status Bar", padx=5, pady=3, bd=1, relief=SUNKEN)
statusBar.grid(column=0, row=0)
statusBar2 = Label(statusBarRoot, text="Status Bar2", padx=5, pady=3, bd=1, relief=SUNKEN)
statusBar2.grid(column=1, row=0, padx=1, sticky=W+E)
statusBarRoot.pack(side=BOTTOM, fill=X)
hostsBox.pack(expand=TRUE, fill=BOTH) # Needs to be added last for proper layout behavior

sqdb.commit()
sqdb.close()

# Icon file?

root.mainloop()

# Message boxes
# showinfo, showwarning, showerror, askquestion, askokcancel, askyesno