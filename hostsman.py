#!/usr/bin/env python3

import platform
from tkinter import *
from tkinter import filedialog
from tkinter import font
from tkinter import messagebox
from tkinter import scrolledtext as st
from tkinter import ttk
#from style import *
import sqlite3
import threading

global root
global OShosts
global OShostsPath
global PathSlash
global init_dir
global fileUnsavedChanges
global fileMainFilename
global statusBarFile

root = Tk()
fileUnsavedChanges = False # Are they any unsaved changes?
fileMainFilename = ""

# Status bar
statusBarRoot = Label(root, relief=SUNKEN)
statusBar = Label(statusBarRoot, text="Status Bar", padx=5, pady=3, bd=1, relief=SUNKEN)
statusBar.grid(column=0, row=0)
statusBarFile = Label(statusBarRoot, text="CurrentFilename", padx=5, pady=3, bd=1, relief=SUNKEN)
statusBarFile.grid(column=1, row=0, padx=1, sticky=W+E)
statusBarCursor = Label(statusBarRoot, text="Coord", padx=5, pady=3, bd=1, relief=SUNKEN)
statusBarCursor.grid(column=2, row=0, padx=1, sticky=W+E)


root.title("Hosts File Manager")
#root.iconbitmap("/path/to/file.ico")
root.geometry("800x600")
OShosts = ""
OShostsPath = ""
PathSlash = "/"

if str(platform.system) == "Linux":
    OShostsPath = "/etc"
    OShosts = OShostsPath + "/hosts"
    messagebox.showinfo(OShosts)
elif platform.system() == "Darwin":
    OShostsPath = "/private/etc"
    OShosts = OShostsPath + "/hosts"
elif platform.system() == "Windows":
    PathSlash = "\\"
    # The Windows registry is the authoritative source for the location of the HOSTS file.
    try:
        hkey = winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE)
        subkey = winreg.OpenKey(hkey, r"SYSTEM\CurrentControlSet\Services\Tcpip\Parameters")
        kval = winreg.QueryValueEx(subkey, "DataBasePath")[0]
        OShostsPath = winreg.ExpandEnvironmentStrings(kval)
        OShosts = OShostsPath + r"\HOSTS"
        hkey.Close()
    except:
        pass
#    Linux', 'Darwin', 'Java', 'Windows
init_dir = OShostsPath + PathSlash
init_dir = r"/home/mythtv/Documents/Projects/HostsManager"
statusBarFile.config(text=OShosts)

def openHostsFile(fname):
    # Use threading.Thread(function_name).start() to read large files.
    # Iterate through the lines
    text_file = open(fname, "r+")
    hosts_contents = text_file.read()
    hostsBox.insert(END, hosts_contents)
    text_file.close()
    return False

def mnuFileNew():
    global fileUnsavedChanges, fileMainFilename, hostsBox
    if fileUnsavedChanges:
        quitMsg = "You have UNSAVED changes, are you sure you want to erase everything?"
        response = messagebox.askyesno("Start anew?", quitMsg)
        if response != 1:
            return
    fileMainFilename = ""
    statusBarFile.config(text="(Untitled)")
    hostsBox.delete(1.0, END)

def mnuFileOpenSys():
    global OShosts, OShostsPath, fileMainFilename, init_dir
    if OShosts == "":
        response = messagebox.askyesno("HOSTS Not Found",
            "Unable to find HOSTS file or detect Operating System\n\n" +
            "Do you want to browse for the HOSTS file?")
        if response == 1:
            hostsBox.delete(1.0, END)
            root.fileopen = filedialog.askopenfilename(initialdir=init_dir, title="Open System HOSTS")
            statusBarFile.config(text=root.fileopen)
        else:
            return
    else:
        root.fileopen = OShosts
    if openHostsFile(root.fileopen): # detect depending on host type (Win/OSX/Linux)
        fileMainFilename = root.fileopen

def mnuFileOpen():
    root.fileopen = filedialog.askopenfilename(initialdir=init_dir, title="Open a Hosts file")
    if openHostsFile(root.fileopen):
        hostsBox.delete(1.0, END)
        fileMainFilename = root.fileopen
        openHostsFile(root.fileopen)
        statusBarFile.config(text=root.fileopen)


def mnuFileMerge():
    root.fileopen = filedialog.askopenfilename(initialdir=init_dir, title="Merge Hosts file")
    fileUnsavedChanges = True

    # fileOpen.destroy()

def mnuFileSave():
    root.filesave = filedialog.asksaveasfilename(initialdir=init_dir, title="Save Hosts file")
    fileUnsavedChanges = False
    text_file = open(root,filesave, w)
    text_file.write(hostsBox.get(1.0, END))
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

def mnuEditUndo():
    hostsBox.edit_undo()

def mnuEditRedo():
    hostsBox.edit_redo()

def mnuEditCut():
    pass

def mnuEditCopy():
    selected = hostsBox.selection_get()

def mnuEditPaste():
    pass

def mnuEditFind():
    pass

def mnuEditReplace():
    pass

def mnuSelectAll():
    pass

def mnuHelpAbout():
    messagebox.showinfo("About", "This program is to help merge multiple HOSTS files.")

def rightClickMenu():
    pass

clicked = StringVar()

sqdb = sqlite3.connect("hosts.db")

sqcur = sqdb.cursor()

myMenu = Menu(root)
root.config(menu=myMenu)

mnuFile = Menu(myMenu, tearoff=False)
myMenu.add_cascade(label="File", menu=mnuFile)
mnuFile.add_command(label="New", command=mnuFileNew)
mnuFile.add_command(label="Open System Hosts", command=mnuFileOpenSys)
mnuFile.add_command(label="Open...", command=mnuFileOpen)
mnuFile.add_command(label="Merge", command=mnuFileMerge)
mnuFile.add_command(label="Save", command=mnuFileSave)
mnuFile.add_command(label="Save As...", command=mnuFileSaveAs)
mnuFile.add_command(label="Revert", command=mnuFileRevert)
mnuFile.add_separator()
mnuFile.add_command(label="Exit", command=mnuFileExit)

mnuEdit = Menu(myMenu, tearoff=False)
myMenu.add_cascade(label="Edit", menu=mnuEdit)
mnuEdit.add_command(label="Undo", command=mnuEditUndo)
mnuEdit.add_command(label="Redo", command=mnuEditRedo)
mnuEdit.add_separator()
mnuEdit.add_command(label="Select All", command=mnuSelectAll)
mnuEdit.add_command(label="Cut", command=mnuEditCut)
mnuEdit.add_command(label="Copy", command=mnuEditCopy)
mnuEdit.add_command(label="Paste", command=mnuEditPaste)
mnuEdit.add_separator()
mnuEdit.add_command(label="Find...", command=mnuEditFind)
mnuEdit.add_command(label="Replace...", command=mnuEditReplace)

#
# Main editor window
#
# Scrolling issues: https://www.youtube.com/watch?v=0WafQCaok6g
#hostsBox = st.ScrolledText(root, wrap="word", bg="black", fg="white", undo=True, selectbackground="yellow")
editor_frame = Frame(root)
vert_scroll = Scrollbar(editor_frame)
vert_scroll.pack(side=RIGHT, fill=Y)
horiz_scroll = Scrollbar(editor_frame, orient="horizontal")
horiz_scroll.pack(side=BOTTOM, fill=X)
hostsBox = Text(editor_frame, width=20, height=20, wrap="word", bg="black", fg="white", undo=True,
    selectbackground="yellow", xscrollcommand=horiz_scroll.set, yscrollcommand=vert_scroll.set)
hostsBox.pack(expand=TRUE, fill=BOTH) # Needs to be added last for proper layout behavior
#hostsBox.pack() # Needs to be added last for proper layout behavior

# Configure sideways scrollbar
vert_scroll.config(command=hostsBox.yview)
horiz_scroll.config(command=hostsBox.xview)

hostsBox.bind("<Button-3>", rightClickMenu)
# Any time the cursor moves in the text box, set the cursor pos in the status bar:
#hostsBox.bind("<Configure>", statusBarCursor.config(text=hostsBox.index(INSERT))) # Doesn't work yet
#hostsBox.pack needs to be added AFTER StatusBar is added



# Now we can add the status bar
statusBarRoot.pack(side=BOTTOM, fill=X)
#hostsBox.pack(expand=TRUE, fill=BOTH) # Needs to be added last for proper layout behavior
editor_frame.pack(expand=TRUE, fill=BOTH)
#editor_frame.pack()

sqdb.commit()
sqdb.close()

# Icon file?

root.mainloop()

# Message boxes
# showinfo, showwarning, showerror, askquestion, askokcancel, askyesno