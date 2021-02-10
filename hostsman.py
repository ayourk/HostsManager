#!/usr/bin/env python3
#%%
import platform
from tkinter import *
from tkinter import colorchooser
from tkinter import filedialog
from tkinter import font
from tkinter import messagebox
#from tkinter import scrolledtext as st
from tkinter import ttk
#from style import *
#import sqlite3
import threading

root = Tk()
root.title("Hosts File Manager")
#root.iconbitmap("/path/to/file.ico")
root.geometry("800x600")


def detectHosts():
    # 'Linux', 'Darwin', 'Java', 'Windows'
    global hosts_path, hosts_file, path_slash, init_dir
    curopsys = platform.system()
    if str(curopsys) == "Linux":
        hosts_path = "/etc"
        hosts_file = hosts_path + "/hosts"
    elif curopsys == "Darwin":
        hosts_path = "/private/etc"
        hosts_file = hosts_path + "/hosts"
    elif curopsys == "Windows":
        path_slash = "\\"
        # The Windows registry is the authoritative source for the location of the HOSTS file.
        try:
            hkey = winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE)
            subkey = winreg.OpenKey(hkey, r"SYSTEM\CurrentControlSet\Services\Tcpip\Parameters")
            kval = winreg.QueryValueEx(subkey, "DataBasePath")[0]
            hosts_path = winreg.ExpandEnvironmentStrings(kval)
            hosts_file = hosts_path + r"\HOSTS"
            hkey.Close()
        except:
            pass
    init_dir = hosts_path

hosts_path = ""
hosts_file = ""
path_slash = "/"
fileMainFilename = ""
fileUnsavedChanges = False
init_dir = ""
selected_text = ""

# Menu and related functions
def mnuFileNew(e):
    global fileUnsavedChanges, fileMainFilename
    if fileUnsavedChanges:
        quitMsg = "You have UNSAVED changes, are you sure you want to erase everything?"
        response = messagebox.askyesno("Start anew?", quitMsg)
        if response != 1:
            return
    fileMainFilename = ""
    statusBarFile.config(text="(Untitled)")
    fileUnsavedChanges = False
    editor_text.delete(1.0, END)

def mnuFileOpenSys():
    global fileUnsavedChanges, fileMainFilename, init_dir
    if hosts_file == "":
        response = messagebox.askyesno("HOSTS Not Found",
            "Unable to find HOSTS file or detect Operating System\n\n" +
            "Do you want to browse for the HOSTS file?")
        if response == 1:
            fileMainFilename = filedialog.askopenfilename(initialdir=init_dir, title="Open System HOSTS")
    else:
        fileMainFilename = hosts_file
    if fileMainFilename != "":
        text_file = open(fileMainFilename, "r")
        hosts_contents = text_file.read()
        editor_text.delete(1.0, END)
        editor_text.insert(END, hosts_contents)
        text_file.close()
        fileUnsavedChanges = False
        statusBarFile.config(text=fileMainFilename)

def mnuFileOpen(e):
    global fileUnsavedChanges, fileMainFilename
    fileMainFilename = filedialog.askopenfilename(initialdir=init_dir, title="Open a Hosts file")
    text_file = open(fileMainFilename, "r+")
    hosts_contents = text_file.read()
    editor_text.delete(1.0, END)
    editor_text.insert(END, hosts_contents)
    text_file.close()
    fileUnsavedChanges = False
    statusBarFile.config(text=fileMainFilename)

def mnuFileMerge():
    global fileUnsavedChanges
    fileMainFilename = filedialog.askopenfilename(initialdir=init_dir, title="Merge Hosts file")
    text_file = open(fileMainFilename, "r+")
    hosts_contents = text_file.read()
    editor_text.insert(END, "\r\n")
    editor_text.insert(END, hosts_contents)
    text_file.close()
    fileUnsavedChanges = True

def mnuInsertFile(e):   # Resides under the Edit menu
    global fileUnsavedChanges
    fileMainFilename = filedialog.askopenfilename(initialdir=init_dir, title="Insert a file")
    text_file = open(fileMainFilename, "r")
    hosts_contents = text_file.read()
    curpos = editor_text.index(INSERT)
    editor_text.insert(curpos, hosts_contents)
    text_file.close()
    fileUnsavedChanges = True

def mnuFileSave(e):
    global fileUnsavedChanges, fileMainFilename, init_dir
    if fileMainFilename == "":
        fileMainFilename = filedialog.asksaveasfilename(initialdir=init_dir, title="Save Hosts file")
    text_file = open(fileMainFilename, "w+")
    text_file.write(hostsBox.get(1.0, END))
    fileUnsavedChanges = False
    statusBarFile.config(text=f"Saved: {fileMainFilename}")

def mnuFileSaveAs():
    global fileUnsavedChanges, fileMainFilename
    fileMainFilename = filedialog.asksaveasfilename(initialdir=init_dir, title="Save Hosts file")
    text_file = open(fileMainFilename, "w+")
    text_file.write(hostsBox.get(1.0, END))
    fileUnsavedChanges = False
    statusBarFile.config(text=f"Saved: {fileMainFilename}")

def mnuFileRevert():
    global fileUnsavedChanges, fileMainFilename, init_dir
    if fileMainFilename == "":
        fileMainFilename = filedialog.askopenfilename(initialdir=init_dir, title="Open a Hosts file")
    text_file = open(fileMainFilename, "r+")
    hosts_contents = text_file.read()
    editor_text.delete(1.0, END)
    editor_text.insert(END, hosts_contents)
    text_file.close()
    fileUnsavedChanges = False
    statusBarFile.config(text=fileMainFilename)

def mnuFileExit():
    global fileUnsavedChanges, fileMainFilename
    quitMsg = "Are you sure you want to quit?"
    if fileUnsavedChanges:
        quitMsg = "You have UNSAVED changes, are you sure you want to quit?"
    response = messagebox.askyesno("Quit?", quitMsg)
    if response == 1:
        root.quit()
    # Exit app

def mnuEditUndo(e):
    hostsBox.edit_undo()

def mnuEditRedo(e):
    hostsBox.edit_redo()

def mnuEditCut(e):
    global selected_text
    if e:
        selected_text = root.clipboard_get()
    elif editor_text.selection_get():
        selected_text = editor_text.selection_get()
        editor_text.delete("sel.first", "sel.last")
        root.clipboard_clear()
        root.clipboard_append(selected_text)

def mnuEditCopy(e):
    global selected_text
    if e:
        selected_text = root.clipboard_get()
    if editor_text.selection_get():
        selected_text = editor_text.selection_get()
        root.clipboard_clear()
        root.clipboard_append(selected_text)

def mnuEditPaste(e):
    global selected_text
    curpos = editor_text.index(INSERT)
    if e:
        selected_text = root.clipboard_get()
    elif selected_text:
        editor_text.insert(curpos, selected_text)

def mnuEditFind(e):
    pass

def mnuEditReplace(e):
    pass

def mnuSelectAll(e):
    editor_text.tag_add("sel", "1.0", "end")
    pass

def mnuHelpAbout():
    messagebox.showinfo("About", "This program is to help merge multiple HOSTS files.")

def rightClickMenu():
    pass


# I'm Considering storing HOSTS entries in a DB
#sqdb = sqlite3.connect("hosts.db")
#sqcur = sqdb.cursor()


#
# Main editor window
#
# Scrolling issues: https://www.youtube.com/watch?v=0WafQCaok6g
editor_frame = Frame(root)
vert_scroll = Scrollbar(editor_frame)
vert_scroll.pack(side=RIGHT, fill=Y)
horiz_scroll = Scrollbar(editor_frame, orient="horizontal")
horiz_scroll.pack(side=BOTTOM, fill=X)
editor_text = Text(editor_frame, width=20, height=20, wrap="none", undo=True,
# bg="black", fg="white",
    selectbackground="yellow", xscrollcommand=horiz_scroll.set, yscrollcommand=vert_scroll.set)

editor_text.bind("<Button-3>", rightClickMenu)
# Any time the cursor moves in the text box, set the cursor pos in the status bar:
#editor_text.bind("<Configure>", statusBarCursor.config(text=editor_text.index(INSERT))) # Doesn't work yet
#editor_text.pack needs to be added AFTER StatusBar is added

editor_text.pack(expand=TRUE, fill=BOTH) # Needs to be added last for proper expanding layout behavior

# Configure scrollbars
vert_scroll.config(command=editor_text.yview)
horiz_scroll.config(command=editor_text.xview)

# Menu bar
rootMenu = Menu(root)
root.config(menu=rootMenu)

mnuFile = Menu(rootMenu, tearoff=False)
rootMenu.add_cascade(label="File", menu=mnuFile, accelerator="(Ctrl+N)")
mnuFile.add_command(label="New", command=lambda: mnuFileNew(0), accelerator="(Ctrl+N)")
mnuFile.add_command(label="Open System Hosts", command=mnuFileOpenSys)
mnuFile.add_command(label="Open...", command=lambda: mnuFileOpen(0), accelerator="(Ctrl+N)")
mnuFile.add_command(label="Merge", command=mnuFileMerge)
mnuFile.add_command(label="Save", command=lambda: mnuFileSave(0), accelerator="(Ctrl+N)")
mnuFile.add_command(label="Save As...", command=mnuFileSaveAs)
mnuFile.add_command(label="Revert", command=mnuFileRevert)
mnuFile.add_separator()
mnuFile.add_command(label="Exit", command=lambda: mnuFileExit(0), accelerator="(Ctrl+Q)")

mnuEdit = Menu(rootMenu, tearoff=False)
rootMenu.add_cascade(label="Edit", menu=mnuEdit)
mnuEdit.add_command(label="Undo", command=editor_text.edit_undo, accelerator="(Ctrl+Z)")
mnuEdit.add_command(label="Redo", command=editor_text.edit_redo, accelerator="(Ctrl+Y)")
mnuEdit.add_separator()
mnuEdit.add_command(label="Select All", command=lambda: mnuSelectAll(0), accelerator="(Ctrl+A)")
mnuEdit.add_command(label="Insert File...", command=lambda: mnuInsertFile(0), accelerator="(Ctrl+I)")
mnuEdit.add_command(label="Cut", command=lambda: mnuEditCut(0), accelerator="(Ctrl+X)")
mnuEdit.add_command(label="Copy", command=lambda: mnuEditCopy(0), accelerator="(Ctrl+C)")
mnuEdit.add_command(label="Paste", command=lambda: mnuEditPaste(0), accelerator="(Ctrl+V)")
mnuEdit.add_separator()
mnuEdit.add_command(label="Find...", command=lambda: mnuEditFind(0), accelerator="(Ctrl+F)")
mnuEdit.add_command(label="Replace...", command=lambda: mnuEditReplace(0), accelerator="(Ctrl+R)")

# Main application key bindings:
root.bind("<Control-Key-n>", mnuFileNew)
root.bind("<Control-Key-o>", mnuFileOpen)
root.bind("<Control-Key-s>", mnuFileSave)
root.bind("<Control-Key-q>", mnuFileExit)
#root.bind("<Control-Key-z>", mnuEditUndo)
#root.bind("<Control-Key-y>", mnuEditRedo)
root.bind("<Control-Key-a>", mnuSelectAll)
root.bind("<Control-Key-i>", mnuInsertFile)
root.bind("<Control-Key-x>", mnuEditCut)
root.bind("<Control-Key-c>", mnuEditCopy)
root.bind("<Control-Key-v>", mnuEditPaste)

# Status bar
statusBarRoot = Label(root, relief=SUNKEN)
statusBar = Label(statusBarRoot, text="Status Bar", padx=5, pady=3, bd=1, relief=SUNKEN)
statusBar.grid(column=0, row=0)
statusBarFile = Label(statusBarRoot, text="CurrentFilename", padx=5, pady=3, bd=1, relief=SUNKEN)
statusBarFile.grid(column=1, row=0, padx=1)
statusBarCursor = Label(statusBarRoot, text="Coord", padx=5, pady=3, bd=1, relief=SUNKEN)
statusBarCursor.grid(column=2, row=0, padx=1, sticky=W+E)

# Now we can add the status bar
statusBarRoot.pack(side=BOTTOM, fill=X)
editor_frame.pack(expand=TRUE, fill=BOTH)

#sqdb.commit()
#sqdb.close()

# Now we get to the meat and potatoes!
detectHosts()

editor_text.focus()
root.mainloop()

# Message boxes
# showinfo, showwarning, showerror, askquestion, askokcancel, askyesno