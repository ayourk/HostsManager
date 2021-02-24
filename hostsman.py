#!/usr/bin/env python3

#%% <-- For Jupyter debugging
import platform
from decimal import Decimal
import math
import os
#from tkinter import *
import tkinter as tk
#from tkinter.font import Font # https://www.youtube.com/watch?v=JIqE3RMCMFE
from tkinter import colorchooser as tkcolorchooser
from tkinter import filedialog as tkfiledialog
from tkinter import messagebox as tkmessagebox
#from tkinter import scrolledtext as st
from tkinter import ttk
#import sqlite3
import threading

#
# Credits:
#
# Most of this code was made possible via videos from the Youtube channel at
#   https://www.youtube.com/c/Codemycom/videos
#
#

# TODO:
#    Finish special dialogs related to the purpose of this app (in progress)
#       Make the Minimize button disappear or nonfunctional
#    Perform the backend logic on editor_text with said dialogs
#    Finish backend functionality for many of the dialogs
#       Flesh out Sort, Filter, Options dialogs (in progress)
#    Add Line numbering feature (as an option) from:
# https://stackoverflow.com/questions/16369470/tkinter-adding-line-number-to-text-widget

root = tk.Tk()
root.title("Hosts File Manager")
#root.iconbitmap("/path/to/file.ico")


# Utility functions
def detectHosts():
    # "Linux", "Darwin", "Java", "Windows"
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
            import winreg
            hivekey = winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE)
            subkey = winreg.OpenKey(hivekey, r"SYSTEM\CurrentControlSet\Services\Tcpip\Parameters")
            keyval = winreg.QueryValueEx(subkey, "DataBasePath")[0]
            hosts_path = winreg.ExpandEnvironmentStrings(keyval)
            hivekey.Close()
        except Exception:
            # If there is any reason for the above code block to fail
            # fallback to the standard default location and path
            hosts_path = r"C:\Windows\System32\drivers\etc"
        hosts_file = hosts_path + r"\HOSTS"
    init_dir = hosts_path

def center_window(curwind, dlg_width=200, dlg_height=200, appCenter=True):
    # Needs a rewrite since it fails for some systems with 2+ screens
    #curwind.update_idletasks() # Make sure geometries are up to date
    # (can cause flicker)
    app_top = root.winfo_rooty()
    app_left = root.winfo_rootx()
    app_width = root.winfo_width()
    app_height = root.winfo_height()
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    dlg_left = int((screen_width/2) - (dlg_width/2))
    dlg_top = int((screen_height/2) - (dlg_height/2))
    dlgapp_left = int(app_left + ((app_width/2) - (dlg_width/2)))
    dlgapp_top = int(app_top + ((app_height/2) - (dlg_height/2)))
    dlgapp_top -= 35   # On my system, the top is biased +59
    geometry_text = f"{dlg_width}x{dlg_height}+{dlg_left}+{dlg_top}"
    if appCenter:   # Center on root window
        geometry_text = f"{dlg_width}x{dlg_height}+{dlgapp_left}+{dlgapp_top}"
    curwind.geometry(geometry_text)

# Tried to use single dispatch, but it didn't go over too well.
# https://docs.python.org/3/library/functools.html#functools.singledispatch
def dlgDismiss(dlgWindow=None):
    global searchStart
    searchStart = "1.0"
    dlgWindow.grab_release()
    dlgWindow.destroy()
def dlgDismissEvent(e=None):
    dlgDismiss(e.widget)


# File menu globals
init_dir = ""
hosts_path = ""
hosts_file = ""
path_slash = "/"
fileMainFilename = ""
fileUnsavedChanges = False
# Edit menu globals
selected_text = ""
selected_font = ""
# Dialog box globals; https://www.youtube.com/watch?v=tpwu5Zb64lQ
dlgFileMerge = False
dlgEditFind = False
dlgEditReplace = False
dlgToolSort = False
dlgToolFilter = False
dlgToolColor = False
dlgToolOptions = False
dlgHelpAbout = False
boolMatchCase = tk.BooleanVar()
stopNOW = tk.BooleanVar()

# Menu and related functions
def mnuFileNew(e=None):
    global fileUnsavedChanges, fileMainFilename
    if fileUnsavedChanges:
        root.bell()
        quitMsg = "You have UNSAVED changes, are you sure you want to erase everything?"
        response = tkmessagebox.askyesno("Start anew?", quitMsg)
        if response != 1:
            return
    fileMainFilename = ""
    statusBarFile.config(text="(Untitled)")
    fileUnsavedChanges = False
    editor_text.edit_modified(False)
    editor_text.delete(1.0, tk.END)

def mnuFileOpenSys(e=None):
    global fileUnsavedChanges, fileMainFilename, init_dir
    if hosts_file == "":
        response = tkmessagebox.askyesno("HOSTS Not Found",
            "Unable to find HOSTS file or detect Operating System\n\n" +
            "Do you want to browse for the HOSTS file?")
        if response == 1:
            fileMainFilename = tkfiledialog.askopenfilename(initialdir=init_dir, title="Open System HOSTS")
    else:
        fileMainFilename = hosts_file
    if fileMainFilename != "" and fileMainFilename != ():
        try:
            text_file = open(fileMainFilename, "r")
            hosts_contents = text_file.read()
            editor_text.delete(1.0, tk.END)
            editor_text.insert(tk.END, hosts_contents)
            text_file.close()
            fileUnsavedChanges = False
            editor_text.edit_modified(False)
            editor_text.mark_set(tk.INSERT, "1.0") # Move cursor to top
            editor_text.edit_reset() # Clear the undo stack
            statusBarFile.config(text=fileMainFilename)
        except Exception as exp:
            tkmessagebox.showerror("ERROR", exp)

def mnuFileOpen(e=None):
    global fileUnsavedChanges, fileMainFilename
    try:
        #fileMainFilename = tkfiledialog.askopenfilename(initialdir=init_dir, title="Open a Hosts file")
        fileMainFilename = tkfiledialog.askopenfilename(title="Open a Hosts file")
        if fileMainFilename == "" or fileMainFilename == ():
            return
        text_file = open(fileMainFilename, "r")
        hosts_contents = text_file.read()
        editor_text.delete(1.0, tk.END)
        editor_text.insert(tk.END, hosts_contents)
        text_file.close()
        fileUnsavedChanges = False
        editor_text.edit_modified(False)
        editor_text.mark_set(tk.INSERT, "1.0") # Move cursor to top
        editor_text.edit_reset() # Clear the undo stack
        statusBarFile.config(text=fileMainFilename)
    except Exception as exp:
        tkmessagebox.showerror("ERROR", exp)

def mnuFileMerge(e=None):
    global fileUnsavedChanges
    try:
        fileMainFilename = tkfiledialog.askopenfilename(initialdir=init_dir, title="Merge Hosts file")
        if fileMainFilename == "" or fileMainFilename == ():
            return
        text_file = open(fileMainFilename, "r")
        hosts_contents = text_file.read()   # text_file.readlines(), list(sorted())
        editor_text.insert(tk.END, "\r\n")
        editor_text.insert(tk.END, hosts_contents)
        text_file.close()
        fileUnsavedChanges = True
        editor_text.see(tk.INSERT) # Move cursor into view
    except Exception as exp:
        tkmessagebox.showerror("ERROR", exp)

def mnuFileMerge2(e=None):    # Custom dialog version (TODO)
    global fileUnsavedChanges
    center_window(dlgFileMerge)
    # TODO:
    #fileMainFilename = tkfiledialog.askopenfilename(initialdir=init_dir, title="Merge Hosts file")
    if fileMainFilename == "" or fileMainFilename == ():
        return
    text_file = open(fileMainFilename, "r")
    hosts_contents = text_file.read()   # text_file.readlines(), list(sorted())
    editor_text.insert(tk.END, "\r\n")
    editor_text.insert(tk.END, hosts_contents)
    text_file.close()
    fileUnsavedChanges = True

def mnuInsertFile(e=None):   # Resides under the Edit menu
    global fileUnsavedChanges
    try:
        fileMainFilename = tkfiledialog.askopenfilename(initialdir=init_dir, title="Insert a file")
        if fileMainFilename == "" or fileMainFilename == ():
            return
        text_file = open(fileMainFilename, "r")
        hosts_contents = text_file.read()
        curpos = editor_text.index(tk.INSERT)
        editor_text.insert(curpos, hosts_contents)
        text_file.close()
        fileUnsavedChanges = True
        editor_text.see(tk.INSERT) # Move cursor into view
    except Exception as exp:
        tkmessagebox.showerror("ERROR", exp)

def mnuFileSave(e=None):
    global fileUnsavedChanges, fileMainFilename, init_dir
    try:
        if fileMainFilename == "":
            fileMainFilename = tkfiledialog.asksaveasfilename(
                initialdir=init_dir,
                initialfile="hosts-custom.txt",
                title="Save Hosts file")
        if fileMainFilename == "" or fileMainFilename == ():
            return
        text_file = open(fileMainFilename, "w+")
        text_file.write(editor_text.get(1.0, tk.END))
        fileUnsavedChanges = False
        editor_text.edit_modified(False)
        statusBarFile.config(text=f"Saved: {fileMainFilename}")
    except Exception as exp:
        tkmessagebox.showerror("ERROR", exp)

def mnuFileSaveAs(e=None):
    global fileUnsavedChanges, fileMainFilename
    try:
        fileMainFilename = tkfiledialog.asksaveasfilename(
            initialdir=init_dir,
            initialfile="hosts-custom.txt",
            title="Save File As...")
        if fileMainFilename == "" or fileMainFilename == ():
            return
        text_file = open(fileMainFilename, "w+")
        text_file.write(editor_text.get(1.0, tk.END))
        fileUnsavedChanges = False
        editor_text.edit_modified(False)
        statusBarFile.config(text=f"Saved As: {fileMainFilename}")
    except Exception as exp:
        tkmessagebox.showerror("ERROR", exp)

def mnuFileRevert(e=None):
    global fileUnsavedChanges, fileMainFilename, init_dir
    try:
        if fileMainFilename == "":
            fileMainFilename = tkfiledialog.askopenfilename(
                initialdir=init_dir, title="Revert Changes to file")
        if fileMainFilename == "" or fileMainFilename == ():
            return
        text_file = open(fileMainFilename, "r")
        hosts_contents = text_file.read()
        editor_text.delete(1.0, tk.END)
        editor_text.insert(tk.END, hosts_contents)
        text_file.close()
        fileUnsavedChanges = False
        editor_text.edit_modified(False)
        statusBarFile.config(text=fileMainFilename)
        editor_text.see(tk.INSERT) # Move cursor into view
    except Exception as exp:
        tkmessagebox.showerror("ERROR", exp)

def mnuFileExit(e=None):
    global fileUnsavedChanges
    quitMsg = "Are you sure you want to quit?"
    menuBarUsed = True
    if e:   # Don't prompt to quit if key binding was used unless there are unsaved changes
        menuBarUsed = False
    if fileUnsavedChanges:
        quitMsg = "You have UNSAVED changes, are you sure you want to quit?"
    if menuBarUsed or fileUnsavedChanges:
        response = tkmessagebox.askyesno("Quit?", quitMsg)
        if response != 1:
            return
    root.quit()
    # Exit app

def mnuEditUndo(e=None):
    mnuEdit.entryconfig("Undo", state="disabled")
    mnuEdit.entryconfig("Redo", state="normal")
    editor_text.edit_undo()

def mnuEditRedo(e=None):
    mnuEdit.entryconfig("Undo", state="normal")
    mnuEdit.entryconfig("Redo", state="disabled")
    editor_text.edit_redo()

def mnuEditCut(e=None):
    global selected_text
    if e:
        selected_text = root.clipboard_get()
    elif editor_text.selection_get():
        selected_text = editor_text.selection_get()
        editor_text.delete("sel.first", "sel.last")
        root.clipboard_clear()
        root.clipboard_append(selected_text)

def mnuEditCopy(e=None):
    global selected_text
    if e:
        selected_text = root.clipboard_get()
    if editor_text.selection_get():
        selected_text = editor_text.selection_get()
        root.clipboard_clear()
        root.clipboard_append(selected_text)

def mnuEditPaste(e=None):
    global selected_text
    curpos = editor_text.index(tk.INSERT)
    if e:
        selected_text = root.clipboard_get()
    elif selected_text:
        editor_text.insert(curpos, selected_text)

def mnuEditFind(e=None): # Used to be mnuEditReplace
    cursel_text = tk.StringVar()
    cursel_text.set("")
    try:
        # For some reason, no text is selected by the time we come here.
        cursel_text.set(editor_text.selection_get())
    except Exception:
        pass

    # Based on https://www.geeksforgeeks.org/create-find-and-replace-features-in-tkinter-text-widget/
    global dlgEditReplace, txtFind, txtReplace, searchStart, boolMatchCase
    dlgEditReplace = tk.Toplevel(root)
    searchStart = "1.0"
    dlgEditReplace.title("Find & Replace Text...")
    center_window(dlgEditReplace, 310, 160)
    lblFind = tk.Label(dlgEditReplace, text="Find:")
    lblFind.grid(column=0, row=0, padx=10, pady=10, sticky=tk.E)
    txtFind = tk.Entry(dlgEditReplace, textvariable=cursel_text)
    txtFind.grid(column=1, row=0, columnspan=2, pady=10)
    lblReplace = tk.Label(dlgEditReplace, text="Replace:")
    lblReplace.grid(column=0, row=1, padx=10, pady=5)
    txtReplace = tk.Entry(dlgEditReplace)
    txtReplace.grid(column=1, row=1, columnspan=2, pady=5, sticky=tk.E)
    lblMatchCase = tk.Label(dlgEditReplace, text="Match Case:")
    lblMatchCase.grid(column=0, row=2, padx=10, pady=5, sticky=tk.E)
    chkMatchCase = tk.Checkbutton(dlgEditReplace, variable=boolMatchCase,
        offvalue=False, onvalue=True)
    chkMatchCase.deselect() # Start out unchecked
    chkMatchCase.grid(column=1, row=2, sticky=tk.W)
    btnReplaceFindAll = tk.Button(dlgEditReplace, text="Mark All",
        command=mnuEditFindFindAll)
    btnReplaceFindAll.grid(column=2, row=2, sticky=tk.E)

    btnReplaceFind = tk.Button(dlgEditReplace, text="Find",
        command=mnuEditReplaceFind)
    btnReplaceFind.grid(column=0, row=3)
    btnEditReplaceNext = tk.Button(dlgEditReplace, text="Replace",
        command=mnuEditReplaceNext)
    btnEditReplaceNext.grid(column=1, row=3, pady=5, sticky=tk.W)
    btnEditReplaceCancel = tk.Button(dlgEditReplace, text="Cancel",
        command=mnuEditReplaceCancel)
    btnEditReplaceCancel.grid(column=2, row=3, pady=5, sticky=tk.E)

    if cursel_text != "":
        #txtFind.insert(0, cursel_text)
        txtFind.select_range(0, tk.END)

    txtFind.focus()
    dlgEditReplace.resizable(False, False)
    # See http://tkinter.programujte.com/tkinter-dialog-windows.htm
    dlgEditReplace.bind("<Return>", mnuEditReplaceFind)
    dlgEditReplace.bind("<Escape>", mnuEditReplaceCancel)
    dlgEditReplace.protocol("WM_DELETE_WINDOW",
        lambda: dlgDismiss(dlgEditReplace)) # intercept close button
    dlgEditReplace.transient(root)   # dialog window is related to main
    # Still need to remove min/max buttons and keep the X button
    dlgEditReplace.wait_visibility() # can't grab until window appears, so we wait
    dlgEditReplace.wait_window()     # block until window is destroyed
def mnuEditReplaceFind(e=None):
    global dlgEditReplace, txtFind, searchStart
    # Remove tag "found" from index 1 to tk.END
    editor_text.tag_remove(tk.SEL, "1.0", tk.END)
    search_text = txtFind.get()
    if (search_text):
        cur_index = searchStart
        # searches for desired string from index searchStart
        cur_index = editor_text.search(search_text, cur_index,
            nocase=boolMatchCase, stopindex=tk.END)
        if cur_index:
            editor_text.see(cur_index) # Move found text into view
            # Last index sum of current index and length of editor_text
            next_index = "% s+% dc" % (cur_index, len(search_text))
            # Move cursor to end of selected text
            editor_text.mark_set(tk.INSERT, next_index)
            txtFind.select_range(0, tk.END)
            txtFind.focus_set()
            editor_text.focus_set() # Set focus before selecting
            # Mark located string as "selected"
            editor_text.tag_add(tk.SEL, cur_index, next_index)
            searchStart = next_index
        else: # Not found so prepare to search again from the top
            searchStart = "1.0" # Allow search to wrap around
            txtFind.focus_set() # Set focus before selecting
            txtFind.select_range(0, tk.END)
    else: # Search empty so start from the top
        searchStart = "1.0"
        txtFind.focus_set()
def mnuEditReplaceNext(e=None):
    global dlgEditReplace, txtFind, txtReplace, searchStart
    cursel_text = tk.StringVar()
    cursel_text.set("")
    try:
        # For some reason, no text is selected by the time we come here.
        selected_index = editor_text.index(tk.SEL_FIRST)
        cursel_text.set(editor_text.selection_get())
    except Exception:
        try:
            selected_index = txtFind.index(tk.SEL_FIRST)
            cursel_text.set(txtFind.selection_get())
        except Exception:
            pass
    if (cursel_text != ""):
        # Allow replacing of currently selected editor_text
        searchStart = selected_index
    # Remove tag "found" from index 1 to tk.END
    editor_text.tag_remove(tk.SEL, "1.0", tk.END)
    search_text = txtFind.get()
    replace_text = txtReplace.get()
    if (search_text): # replace_text can be empty to do mass deletes
        cur_index = searchStart
        # Searches for desired string from index searchStart
        cur_index = editor_text.search(search_text, cur_index,
            nocase=boolMatchCase, stopindex=tk.END)
        if cur_index:
            editor_text.see(cur_index) # Move found text into view
            # last index sum of current index and length of editor_text
            next_index = "% s+% dc" % (cur_index, len(search_text))
            editor_text.delete(cur_index, next_index)
            editor_text.insert(cur_index, replace_text)
            # overwrite "Found" at cur_index
            next_index = "% s+% dc" % (cur_index, len(replace_text))
            txtReplace.focus_set() # Set focus before selecting
            txtFind.select_range(0, tk.END)
            txtReplace.select_range(0, tk.END)
            editor_text.focus_set() # Set focus before selecting
            # mark located string as "selected"
            editor_text.tag_add(tk.SEL, cur_index, next_index)
            searchStart = next_index
        else: # Not found so prepare to search again from the top
            searchStart = "1.0" # Allow search to wrap around
            txtFind.focus_set() # Set focus before selecting
            txtFind.select_range(0, tk.END)
            txtReplace.select_range(0, tk.END)
            editor_text.focus_set()
    else: # Search empty so start from the top
        searchStart = "1.0"
        txtFind.focus_set()
def mnuEditFindFindAll(e=None):
    global dlgEditReplace, txtFind
    # remove tag "found" from index 1 to tk.END
    editor_text.tag_remove("found", "1.0", tk.END)
    search_text = txtFind.get()
    if (search_text):
        cur_index = "1.0"
        cur_cursor = editor_text.index(tk.INSERT)
        cur_end = editor_text(tk.END)
        while True:
            # searches for desired string from index 1
            cur_index = editor_text.search(search_text, cur_index,
                nocase=boolMatchCase, stopindex=tk.END)
            if not cur_index: break
            editor_text.see(cur_index)
            # last index sum of current index and length of editor_text
            next_index = "% s+% dc" % (cur_index, len(search_text))
            # overwrite "Found" at cur_index
            editor_text.tag_add("found", cur_index, next_index)
            # Move cursor to end of text
            editor_text.mark_set(tk.INSERT, next_index)
            cur_index = next_index
        # mark located string as "selected"
        editor_text.tag_config("found",
            foreground=editor_text["selectforeground"],
            background=editor_text["selectbackground"])
    txtFind.select_range(0, tk.END)
    txtFind.focus_set()
    editor_text.focus_set()
def mnuEditReplaceCancel(e=None):
    global searchStart
    searchStart = "1.0"
    editor_text.tag_remove("found", "1.0", tk.END)
    dlgDismiss(dlgEditReplace)

def mnuSelectAll(e=None):
    editor_text.tag_add(tk.SEL, "1.0", tk.END)

def spinStartMax(e=None, maxline=-1):
    e.config(to=maxline)
def spinStopMin(e=None, minline=1):
    e.config(from_=minline)
def fullStop():
    global stopNOW;
    stopNOW = True
def mnuToolSort(e=None):
    global dlgToolSort, spinStart, spinStop, stopNOW
    dlgToolSort = tk.Toplevel(root)
    dlgToolSort.title("Sort Hosts")
    center_window(dlgToolSort, 650, 300)
    # TODO:
    lblWarning = tk.Label(dlgToolSort,
        text="WARNING: All nonfunctional lines will be deleted!")
    curfont = lblWarning["font"]
    lblWarning.config(font=(curfont, 18), fg="red")
    lblWarning.grid(row=0, column=0, padx=10, pady=5, sticky=tk.E,
        columnspan=20)
    lblSortStartLine = tk.Label(dlgToolSort, text="Start sort at Line: ")
    lblSortStartLine.grid(row=1, column=0, pady=5, sticky=tk.E)
    lblSortEndLine = tk.Label(dlgToolSort, text="End sort at Line: ")
    lblSortEndLine.grid(row=2, column=0, pady=5, sticky=tk.E)
    lblSortPasses = tk.Label(dlgToolSort, text="Sorting Passes: ")
    lblSortPasses.grid(row=3, column=0, pady=5, sticky=tk.E)
    # Figure out how many lines the currently loaded file is
    cur_cursor = editor_text.index(tk.INSERT)
    cur_end = editor_text.index(tk.END)
    lastline = int(cur_end.split(".", 1)[0]) # "int" may be too small
    # Now to create the dependent spinboxes
    start_line = tk.IntVar()
    stop_line = tk.IntVar()
    pass_line = tk.IntVar()
    start_line.set(1)
    stop_line.set(lastline)
    pass_line.set(lastline)
    spinStart = None
    spinStop = None
    try:
        spinStart = tk.Spinbox(dlgToolSort, increment=1,
            from_=1, to=int(stop_line.get()),
            textvariable=start_line,
            command=lambda:spinStopMin(spinStop, start_line.get()))
        spinStop = tk.Spinbox(dlgToolSort, increment=1,
            from_=int(start_line.get()), to=int(lastline),
            textvariable=stop_line,
            command=lambda:spinStartMax(spinStart, stop_line.get()))
        spinPasses = tk.Spinbox(dlgToolSort, increment=1,
            from_=int(start_line.get()), to=int(lastline),
            textvariable=pass_line)
        spinStart.grid(row=1, column=1, pady=5, sticky=tk.W,
            columnspan=2)
        spinStop.grid(row=2, column=1, pady=5, sticky=tk.W,
            columnspan=2)
        spinPasses.grid(row=3, column=1, pady=5, sticky=tk.W,
            columnspan=2)
    except Exception as exp:
        pass
    #beauThread = threading.Thread(target=hostsBeautify(
    #    spinStop, "%s.0" % (spinStart.get()), "%s.0" % (spinStop.get())))
    #beauThread = threading.Thread(target=bubbleSort(
    #    spinStop, "%s.0" % (spinStart.get()), "%s.0" % (spinStop.get())))
    btnToolSortBeautify = tk.Button(dlgToolSort, text="Beautify",
        command=lambda: hostsBeautify(
        spinStop, "%s.0" % (spinStart.get()), "%s.0" % (spinStop.get())))
    btnToolSortBeautify.grid(row=1, column=4)
    btnToolSortBeautify = tk.Button(dlgToolSort, text="Bubble Sort",
        command=lambda: threading.Thread(bubbleSort(
        spinStop, "%s.0" % (spinStart.get()), "%s.0" % (spinStop.get()),
        pass_line.get())).start())
    btnToolSortBeautify.grid(row=2, column=4)
    btnToolSortBeautify = tk.Button(dlgToolSort, text="Cancel Sort",
        command=lambda: stopNOW.set(True))
    btnToolSortBeautify.grid(row=2, column=6)

    #dlgToolSort.resizable(False, False)
    dlgToolSort.bind("<Escape>", dlgDismissEvent)
    #dlgToolSort.overrideredirect(True)
    dlgToolSort.protocol("WM_DELETE_WINDOW",
        lambda: dlgDismiss(dlgToolSort)) # intercept close button
    dlgToolSort.transient(root)   # dialog window is related to main
    # Still need to remove min/max buttons and keep the X button
    dlgToolSort.wait_visibility() # can't grab until window appears, so we wait
    #dlgToolSort.grab_set()        # ensure all input goes to our window
    dlgToolSort.wait_window()     # block until window is destroyed

def hostsBeautify(e=None, start_index="1.0", end_index=tk.END):
    match_length = tk.IntVar()
    cur_end = editor_text.index(tk.END)
    if (Decimal(cur_end) > Decimal(end_index)):
        cur_end = str(Decimal(end_index))
    cur_index = str(Decimal(start_index))
    while Decimal(cur_index) <= Decimal(cur_end):
        dlgToolSort.update_idletasks()
        root.update_idletasks()
        try: # Consecutive spaces/tabs
            cur_index = editor_text.search(r"[ \t][ \t]+", cur_index,
                count=match_length, regexp=True,
                nocase=1, stopindex=cur_end)
        except Exception as exp0:
            break
        if not cur_index or match_length.get() == 0: break
        # We don't want to delete all spaces so offset by -1
        next_index = "%s+%sc" % (cur_index, match_length.get()-1)
        editor_text.delete(cur_index, next_index)
    cur_index = str(Decimal(start_index))
    while Decimal(cur_index) <= Decimal(cur_end):
        dlgToolSort.update_idletasks()
        root.update_idletasks()
        try: # Leading spaces/tabs
            cur_index = editor_text.search(r"^[ \t]]+", cur_index,
                count=match_length, regexp=True,
                nocase=1, stopindex=cur_end)
        except Exception as exp1:
            break
        if not cur_index or match_length.get() == 0: break
        next_index = "%s+%sc" % (cur_index, match_length.get())
        editor_text.delete(cur_index, next_index)
    cur_index = str(Decimal(start_index))
    while Decimal(cur_index) <= Decimal(cur_end):
        dlgToolSort.update_idletasks()
        root.update_idletasks()
        try: # Trailing spaces/tabs
            cur_index = editor_text.search(r"[ \t]+$", cur_index,
                count=match_length, regexp=True,
                nocase=1, stopindex=cur_end)
        except Exception as exp2:
            break
        if not cur_index or match_length.get() == 0: break
        next_index = "%s+%sc" % (cur_index, match_length.get())
        editor_text.delete(cur_index, next_index)
    cur_index = str(Decimal(start_index))
    while Decimal(cur_index) <= Decimal(cur_end):
        dlgToolSort.update_idletasks()
        root.update_idletasks()
        try: # Comment lines
            cur_index = editor_text.search(r"^\#.*$", cur_index,
                count=match_length, regexp=True,
                nocase=1, stopindex=cur_end)
        except Exception as exp3:
            break
        if not cur_index or match_length.get() == 0: break
        next_index = "%s+%sc" % (cur_index, match_length.get())
        editor_text.delete(cur_index, next_index)
    # Windows = "^\r\n"
    # Linux/Unix/BSD/MacBSD = "^\n"
    # MacOS = "^\r" (can be this)
    #blank_lines = r"^\r?\n" # Not perfect but does the job most of the time.
    cur_index = str(Decimal(start_index))
    while Decimal(cur_index) <= Decimal(cur_end):
        dlgToolSort.update_idletasks()
        root.update_idletasks()
        try: # Blank lines
            cur_index = editor_text.search(r"^\r?\n", cur_index,
                count=match_length, regexp=True,
                nocase=1, stopindex=cur_end)
        except Exception as exp4:
            break
        if not cur_index or match_length.get() == 0: break
        next_index = "%s+%sc" % (cur_index, (match_length.get()))
        editor_text.delete(cur_index, next_index)
    # Done with all searches
    editor_text.see(tk.INSERT)
    # If the amount of lines change, we have a new EOF/max lines
    oldEnd = int(math.floor(Decimal(end_index)))
    newEnd = int(math.floor(Decimal(editor_text.index(tk.END))))
    if oldEnd >= newEnd:
        spinStartMax(e, newEnd)

def bubbleSort(e=None, start_index="1.0", end_index=tk.END, max_passes=20):
    global stopNOW
    # Variable prep:
    startInt = math.floor(Decimal(start_index))
    stopInt = math.floor(Decimal(end_index)) - 1
    if stopInt - startInt > max_passes:
        max_passes = stopInt - startInt
    stopNOW.set(False)
    if (startInt >= stopInt):
        return # Not enough lines to sort ( >= 3+ )
    # Time to do the actual sort:
    #for outerLoop in range(startInt, stopInt):
    for outerLoop in range(startInt, startInt+max_passes):
        lineSwap = False # Prepare to short circuit sorting
        statusBar.config(text=f"Pass {outerLoop-startInt+1} of {stopInt-startInt+1}")
        statusBar.update_idletasks()
        for innerLoop in range(startInt, stopInt):
            nextPos = innerLoop + 1
            editor_text.see(f"{nextPos}.0")
            dlgToolSort.update_idletasks()
            root.update_idletasks()
            try:
                curLine = editor_text.get(f"{innerLoop}.0", f"{nextPos}.0")
                nextLine = editor_text.get(f"{nextPos}.0", f"{nextPos+1}.0")
                curList = curLine.splitlines()[0].split(" ", 3)
                nextListTest = nextLine.splitlines()
                if nextListTest and not stopNOW.get(): # Sometimes it is an empty list!
                    nextList = nextLine.splitlines()[0].split(" ", 3)
                else:
                    break
            except Exception:
                break
            if len(curList) < 2 or len(nextList) < 2 or \
                    curList[0] != nextList[0]:
                continue
            # Only worry about comparing the host names
            if curList[1] > nextList[1]:
                lineSwap = True
                editor_text.delete(f"{innerLoop}.0", f"{nextPos}.0")
                editor_text.insert(f"{nextPos}.0", curLine)
            elif curList[1] == nextList[1]: # Delete duplicate hosts
                # Try to preserve end of line comments
                if len(curList) == 2 and len(nextList) > 2:
                    editor_text.delete(f"{innerLoop}.0", f"{nextPos}.0")
                elif len(curList) >= 2 and len(nextList) == 2:
                    editor_text.delete(f"{nextPos}.0", f"{nextPos+1}.0")
                elif len(curList) > 2 and len(nextList) > 2:
                    # Consolidate the comments between the 2 lines
                    curList.append(nextList[2])
                    curLine = " ".join(curList) + "\n" # os.linesep
                    editor_text.delete(f"{innerLoop}.0", f"{nextPos+1}.0")
                    editor_text.insert(f"{innerLoop}.0", curLine)
        if not lineSwap or stopNOW.get(): # If already sorted, skip further iterations.
            break
    # If the amount of lines change, we have a new EOF/max lines
    oldEnd = int(math.floor(Decimal(end_index)))
    newEnd = int(math.floor(Decimal(editor_text.index(tk.END))))
    if oldEnd >= newEnd:
        spinStartMax(e, newEnd)

def linekey(entry):
    if len(entry) < 2:
        return ""
    return entry[1]
def mypySort(e=None, start_index="1.0", end_index=tk.END, max_passes=20):
    global stopNOW
    # Variable prep:
    startInt = math.floor(Decimal(start_index))
    stopInt = math.floor(Decimal(end_index)) - 1
    if stopInt - startInt > max_passes:
        max_passes = stopInt - startInt
    stopNOW.set(False)
    if (startInt >= stopInt):
        return # Not enough lines to sort ( >= 3+ )
    list2sort = []
    # Read all of the lines into lists:
    for innerLoop in range(startInt, stopInt+1):
        nextPos = innerLoop + 1
        try:
            curLine = editor_text.get(f"{innerLoop}.0", f"{nextPos}.0")
            curListTest = curLine.splitlines()
            if curListTest and not stopNOW.get(): # Sometimes it is an empty list!
                curList = curListTest[0].split(" ", 3)
            else: # Design feature: Blank lines will cause sorting to stop
                break
        except Exception:
            break
        list2sort[innerLoop] = curList
    # Time to do the actual (fast) sort:
    sortedLines = sorted(list2sort, key=linekey)
    list2sort = [] # Empty unsorted list
    # Now check for duplicates:
    for innerLoop in range(startInt, stopInt):
        nextPos = innerLoop + 1
        if len(sortedLines[innerLoop]) <2 or len(sortedLines[nextPos]) <2 or \
                sortedLines[innerLoop][0] != sortedLines[nextPos][0]:
            continue
        if sortedLines[innerLoop][1] == sortedLines[innerLoop][1]:
            # Try to preserve end of line comments
            if len(sortedLines[innerLoop]) == 2 and len(sortedLines[nextPos]) > 2:
                sortedLines.remove(innerLoop)
            elif len(sortedLines[innerLoop]) >= 2 and len(sortedLines[nextPos]) == 2:
                sortedLines.remove(nextPos)
            elif len(sortedLines[innerLoop]) > 2 and len(sortedLines[nextPos]) > 2:
                # Consolidate the comments between the 2 lines
                allComments = " ".join([sortedLines[innerLoop][2], sortedLines[nextPos][2]])
                sortedLines[innerLoop][2] = allComments
                sortedLines.remove(nextPos)
    # Now put it back into the editor_text:
    sortedList = []
    for innerLoop in range(startInt, stopInt):
        sortedList[innerLoop] = " ".join(sortedLines[innerLoop])
    editor_text.delete(f"{startInt}.0", f"{stopInt+1}.0")
    editor_text.insert(f"{startInt}.0", "\n".join(sortedList))
    # If the amount of lines change, we have a new EOF/max lines
    oldEnd = int(math.floor(Decimal(end_index)))
    newEnd = int(math.floor(Decimal(editor_text.index(tk.END))))
    if oldEnd >= newEnd:
        spinStartMax(e, newEnd)

def mnuToolFilter(e=None):
    global dlgToolFilter
    dlgToolFilter = tk.Toplevel(root)
    dlgToolFilter.title("Filter Hosts")
    center_window(dlgToolFilter, 300, 250)
    # TODO:

    #txtFindR.focus()
    #dlgToolFilter.resizable(False, False)
    #dlgToolFilter.bind("<Return>", mnuEditReplaceFind)
    dlgToolFilter.bind("<Escape>", dlgDismissEvent)
    #dlgToolFilter.attributes("-toolwindow", True)
    #dlgToolFilter.overrideredirect(True)
    dlgToolFilter.protocol("WM_DELETE_WINDOW",
        lambda: dlgDismiss(dlgToolFilter)) # intercept close button
    dlgToolFilter.transient(root)   # dialog window is related to main
    # Still need to remove min/max buttons and keep the X button
    dlgToolFilter.wait_visibility() # can't grab until window appears, so we wait
    dlgToolFilter.grab_set()        # ensure all input goes to our window
    dlgToolFilter.wait_window()     # block until window is destroyed

def mnuToolWrapSet(curwrap):
    editor_text["wrap"] = curwrap
    statusBarWrap["text"] = f"Wrap: {curwrap.capitalize()}"

def fontChanged(curfont):
    editor_text.config(font=curfont)
def mnuToolFont(e=None):
    # Tkinter has not yet added a convenient way to use this font dialog,
    # so I have to use the Tcl API directly. You can see the latest work
    # towards a proper Python API and download code at [Issue#28694].
    # On MacOS, if you don't provide a font via the font configuration option,
    # your callbacks won't be invoked so always provide an initial font
    curfont = editor_text["font"]
    dlgToolFont = root.tk.call("tk", "fontchooser", "configure",
        "-font", f"{curfont} 10", "-command", root.register(fontChanged))
    root.tk.call("tk", "fontchooser", "show")

def dlgColorChange(self, editcolor):
    # https://www.youtube.com/watch?v=NDCirUTTrhg
    newcolor = tkcolorchooser.askcolor(initialcolor=editor_text[editcolor], parent=self)[1]
    if newcolor == None:
        pass
    else:
        self.config(bg=newcolor, activebackground=newcolor)
        editor_text[editcolor] = newcolor
def mnuToolColor(e=None):
    global dlgToolColor
    dlgToolColor = tk.Toplevel(root)
    dlgToolColor.title("Editor Colors")
    center_window(dlgToolColor, 250, 260)
    # insertbackground needs to equal fg
    # colorchooser.askcolor(initialcolor="#ff0000")
    lblColorColorFg = tk.Label(dlgToolColor, text="Foreground Color:")
    lblColorColorBg = tk.Label(dlgToolColor, text="Background Color:")
    btnColorColorFg = tk.Button(dlgToolColor, width=5,
        activebackground=editor_text["fg"], bg=editor_text["fg"],
        command=lambda: dlgColorChange(btnColorColorFg, "fg"))
    btnColorColorBg = tk.Button(dlgToolColor, width=5,
        activebackground=editor_text["bg"], bg=editor_text["bg"],
        command=lambda: dlgColorChange(btnColorColorBg, "bg"))
    lblColorCursorBg = tk.Label(dlgToolColor, text="Cursor BG Color:")
    btnColorCursorBg = tk.Button(dlgToolColor, width=5,
        activebackground=editor_text["insertbackground"], bg=editor_text["insertbackground"],
        command=lambda: dlgColorChange(btnColorCursorBg, "insertbackground"))
    lblColorHiliteFg = tk.Label(dlgToolColor, text="Highlight FG Color:")
    lblColorHiliteBg = tk.Label(dlgToolColor, text="Highlight BG Color:")
    btnColorHiliteFg = tk.Button(dlgToolColor, width=5,
        activebackground=editor_text["selectforeground"], bg=editor_text["selectforeground"],
        command=lambda: dlgColorChange(btnColorHiliteFg, "selectforeground"))
    btnColorHiliteBg = tk.Button(dlgToolColor, width=5,
        activebackground=editor_text["selectbackground"], bg=editor_text["selectbackground"],
        command=lambda: dlgColorChange(btnColorHiliteBg, "selectbackground"))
    lblColorColorFg.grid(column=0, row=0, padx=(10,5), pady=10, sticky=tk.E)
    lblColorColorBg.grid(column=0, row=1, padx=(10,5), pady=10, sticky=tk.E)
    lblColorCursorBg.grid(column=0, row=3, padx=(10,5), pady=10, sticky=tk.E)
    lblColorHiliteFg.grid(column=0, row=4, padx=(10,5), pady=10, sticky=tk.E)
    lblColorHiliteBg.grid(column=0, row=5, padx=(10,5), pady=10, sticky=tk.E)
    btnColorColorFg.grid(column=1, row=0, padx=(5,10), pady=10, sticky=tk.W)
    btnColorColorBg.grid(column=1, row=1, padx=(5,10), pady=10, sticky=tk.W)
    btnColorCursorBg.grid(column=1, row=3, padx=(5,10), pady=10, sticky=tk.W)
    btnColorHiliteFg.grid(column=1, row=4, padx=(5,10), pady=10, sticky=tk.W)
    btnColorHiliteBg.grid(column=1, row=5, padx=(5,10), pady=10, sticky=tk.W)

    dlgToolColor.resizable(False, False)
    dlgToolColor.bind("<Escape>", dlgDismissEvent)
    #dlgToolColor.attributes("-toolwindow", True)
    #dlgToolColor.overrideredirect(True)
    dlgToolColor.protocol("WM_DELETE_WINDOW",
        lambda: dlgDismiss(dlgToolColor)) # intercept close button
    dlgToolColor.transient(root)   # dialog window is related to main
    # Still need to remove min/max buttons and keep the X button
    dlgToolColor.wait_visibility() # can't grab until window appears, so we wait
    dlgToolColor.grab_set()        # ensure all input goes to our window
    dlgToolColor.wait_window()     # block until window is destroyed

def mnuToolOptions(e=None):
    global dlgToolOptions
    dlgToolOptions = tk.Toplevel(root)
    dlgToolOptions.title("Editor Options")
    center_window(dlgToolOptions, 300, 500)
    # TODO:

    #txtFindR.focus()
    #dlgToolOptions.resizable(False, False)
    #dlgToolOptions.bind("<Return>", mnuEditReplaceFind)
    dlgToolOptions.bind("<Escape>", dlgDismissEvent)
    #dlgToolOptions.attributes("-toolwindow", True)
    #dlgToolOptions.overrideredirect(True)
    dlgToolOptions.protocol("WM_DELETE_WINDOW",
        lambda: dlgDismiss(dlgToolOptions)) # intercept close button
    dlgToolOptions.transient(root)   # dialog window is related to main
    # Still need to remove min/max buttons and keep the X button
    dlgToolOptions.wait_visibility() # can't grab until window appears, so we wait
    dlgToolOptions.grab_set()        # ensure all input goes to our window
    dlgToolOptions.wait_window()     # block until window is destroyed

def mnuHelpAbout(e=None):
    tkmessagebox.showinfo("About", "This program is a text editor designed to help merge multiple HOSTS files together.")

def rightClickMenu(e=None):
    mnuRightClick.tk_popup(e.x_root, e.y_root)

def editorUpdate(e=None):
    # Useful info at https://tkdocs.com/shipman/event-handlers.html
    # e.widget = item causing event
    # Update status bar with cursor position
    #editor_text.see(tk.INSERT) # Keep cursor in current view
    cursortxt = "Cursor: " + editor_text.index(tk.INSERT)
    statusBarCursor.config(text=cursortxt)
    if editor_text.get("1.0", tk.END) == "":
        editor_text.edit_modified(False)
    fileUnsavedChanges = editor_text.edit_modified() # Has anything changed?
    #statusBar.config(text=f"{e.state} {e.keysym} {e.keycode}")
    if fileUnsavedChanges:
        statusBar.config(text="Modified")
    else:
        statusBar.config(text="Status Bar")


# Font info:  .metrics("fixed") == 1 - Fixed with fonts only

#
# Main editor window
#
# Scrolling issues: https://www.youtube.com/watch?v=0WafQCaok6g
editor_frame = tk.Frame(root)
# Scroll bars should NOT be part of the tab order (takefocus=0)
vert_scroll = tk.Scrollbar(editor_frame, takefocus=0)
vert_scroll.pack(side=tk.RIGHT, fill=tk.Y)
horiz_scroll = tk.Scrollbar(editor_frame, takefocus=0, orient="horizontal")
horiz_scroll.pack(side=tk.BOTTOM, fill=tk.X)
editor_text = tk.Text(editor_frame, width=20, height=20, wrap="none", undo=True,
    selectbackground="yellow", # Default is Gray
    xscrollcommand=horiz_scroll.set, yscrollcommand=vert_scroll.set)
# Default to Dark Mode
editor_text.config(fg="white", bg="black", insertbackground="white", insertwidth=2)

editor_text.pack(expand=True, fill=tk.BOTH) # Must be last to AutoResize properly

# Configure scrollbars
vert_scroll.config(command=editor_text.yview)
horiz_scroll.config(command=editor_text.xview)

# Menu bar
rootMenu = tk.Menu(root)
root.config(menu=rootMenu)

mnuFile = tk.Menu(rootMenu, tearoff=False)
rootMenu.add_cascade(label="File", menu=mnuFile, accelerator="(Ctrl+N)")
mnuFile.add_command(label="New", command=lambda: mnuFileNew(0), accelerator="(Ctrl+N)")
mnuFile.add_command(label="Open System Hosts", command=mnuFileOpenSys, accelerator="(Ctrl+Shift+O)")
mnuFile.add_command(label="Open...", command=lambda: mnuFileOpen(0), accelerator="(Ctrl+O)")
mnuFile.add_command(label="Merge", command=mnuFileMerge)
mnuFile.add_command(label="Save", command=lambda: mnuFileSave(0), accelerator="(Ctrl+S)")
mnuFile.add_command(label="Save As...", command=mnuFileSaveAs, accelerator="(Ctrl+Shift+S)")
mnuFile.add_command(label="Revert", command=mnuFileRevert)
mnuFile.add_separator()
mnuFile.add_command(label="Exit", command=lambda: mnuFileExit(0), accelerator="(Ctrl+Q)")

mnuEdit = tk.Menu(rootMenu, tearoff=False)
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
mnuEdit.add_command(label="Find & Replace...", command=lambda: mnuEditFind(0), accelerator="(Ctrl+F)")
#mnuEdit.add_command(label="Replace...", command=lambda: mnuEditReplace(0), accelerator="(Ctrl+H)")

textWrap = tk.StringVar()
textWrap.set(editor_text["wrap"])

mnuTool = tk.Menu(rootMenu, tearoff=False)
mnuToolWrap = tk.Menu(mnuTool, tearoff=False)
rootMenu.add_cascade(label="Tools", menu=mnuTool)
mnuTool.add_command(label="Sort Hosts", command=mnuToolSort)
mnuTool.add_command(label="Filter Hosts", command=mnuToolFilter)
mnuTool.add_cascade(label="Text Wrap", menu=mnuToolWrap) # Radio between [none, char, word]
# See https://blog.tecladocode.com/how-to-add-menu-to-tkinter-app/
mnuToolWrap.add_radiobutton(label="None", value="none", variable=textWrap, command=lambda: mnuToolWrapSet(textWrap.get()))
mnuToolWrap.add_radiobutton(label="Char", value="char", variable=textWrap, command=lambda: mnuToolWrapSet(textWrap.get()))
mnuToolWrap.add_radiobutton(label="Word", value="word", variable=textWrap, command=lambda: mnuToolWrapSet(textWrap.get()))
mnuTool.add_command(label="Text Font", command=mnuToolFont) # blockcursor= ?
mnuTool.add_command(label="Editor Colors", command=mnuToolColor)
mnuTool.add_command(label="Options...", command=mnuToolOptions)

mnuHelp = tk.Menu(rootMenu, tearoff=False)
rootMenu.add_cascade(label="Help", menu=mnuHelp)
mnuHelp.add_command(label="About...", command=mnuHelpAbout)

mnuRightClick = tk.Menu(root, tearoff=False)
mnuRightWrap = tk.Menu(mnuRightClick, tearoff=False)
mnuRightClick.add_command(label="Select All", command=lambda: mnuSelectAll(0), accelerator="(Ctrl+A)")
mnuRightClick.add_command(label="Insert File...", command=lambda: mnuInsertFile(0), accelerator="(Ctrl+Shift+I)")
mnuRightClick.add_command(label="Cut", command=lambda: mnuEditCut(0), accelerator="(Ctrl+X)")
mnuRightClick.add_command(label="Copy", command=lambda: mnuEditCopy(0), accelerator="(Ctrl+C)")
mnuRightClick.add_command(label="Paste", command=lambda: mnuEditPaste(0), accelerator="(Ctrl+V)")
mnuRightClick.add_separator()
mnuRightClick.add_command(label="Find & Replace...", command=lambda: mnuEditFind(0), accelerator="(Ctrl+F)")
#mnuRightClick.add_command(label="Replace...", command=lambda: mnuEditReplace(0), accelerator="(Ctrl+R)")
mnuRightClick.add_cascade(label="Text Wrap", menu=mnuRightWrap) # Radio between [none, char, word]
# Might be a bug that we can't use mnuToolWrap above instead of having to rebuild it below
mnuRightWrap.add_radiobutton(label="None", value="none", variable=textWrap, command=lambda: mnuToolWrapSet(textWrap.get()))
mnuRightWrap.add_radiobutton(label="Char", value="char", variable=textWrap, command=lambda: mnuToolWrapSet(textWrap.get()))
mnuRightWrap.add_radiobutton(label="Word", value="word", variable=textWrap, command=lambda: mnuToolWrapSet(textWrap.get()))
mnuRightClick.add_separator()
mnuRightClick.add_command(label="Exit", command=lambda: mnuFileExit(0), accelerator="(Ctrl+Q)")

# By default, some menu items don't make sense to have enabled when the editor_text is empty
def mnuDisableWhenEmpty(firstRun):
    global mnuFile, mnuEdit, mnuTool
    mnuFile.entryconfig("New", state="disabled")        # Enable when editor_text.get() != ""
    mnuFile.entryconfig("Save", state="disabled")       # Enable when editor_text.get() != ""
    mnuFile.entryconfig("Save As...", state="disabled") # Enable when editor_text.get() != ""
    if fileMainFilename == "":
        mnuFile.entryconfig("Merge", state="disabled")      # Enable when fileMainFilename != ""
        mnuFile.entryconfig("Revert", state="disabled")     # Enable when fileMainFilename != ""
    mnuEdit.entryconfig("Select All", state="disabled") # Enable when editor_text.get() != ""
    if firstRun:
        mnuEdit.entryconfig("Undo", state="disabled")       # Enabled upon editor_text change; enables Redo
        mnuEdit.entryconfig("Redo", state="disabled")       # Enabled upon Undo; disabled after use
    mnuEdit.entryconfig("Cut", state="disabled")        # Enable when editor_text.get() != ""
    mnuEdit.entryconfig("Copy", state="disabled")       # Enable when editor_text.get() != ""
    mnuEdit.entryconfig("Find...", state="disabled")    # Enable when editor_text.get() != ""
    mnuEdit.entryconfig("Replace...", state="disabled") # Enable when editor_text.get() != ""
    mnuTool.entryconfig("Sort Hosts", state="disabled") # Enable when editor_text.get() != ""
    mnuTool.entryconfig("Filter Hosts", state="disabled") # Enable when editor_text.get() != ""

def mnuEnable(fileOpened=None):
    global mnuFile, mnuEdit, mnuTool
    mnuFile.entryconfig("New", state="normal")        # Enable when editor_text.get() != ""
    mnuFile.entryconfig("Save", state="normal")       # Enable when editor_text.get() != ""
    mnuFile.entryconfig("Save As...", state="normal") # Enable when editor_text.get() != ""
    if fileMainFilename != "":
        mnuFile.entryconfig("Merge", state="normal")      # Enable when fileMainFilename != ""
        mnuFile.entryconfig("Revert", state="normal")     # Enable when fileMainFilename != ""
    mnuEdit.entryconfig("Select All", state="normal") # Enable when editor_text.get() != ""
    mnuEdit.entryconfig("Cut", state="normal")        # Enable when editor_text.get() != ""
    mnuEdit.entryconfig("Copy", state="normal")       # Enable when editor_text.get() != ""
    mnuEdit.entryconfig("Find...", state="normal")    # Enable when editor_text.get() != ""
    mnuEdit.entryconfig("Replace...", state="normal") # Enable when editor_text.get() != ""
    mnuTool.entryconfig("Sort Hosts", state="normal") # Enable when editor_text.get() != ""
    mnuTool.entryconfig("Filter Hosts", state="normal") # Enable when editor_text.get() != ""

# Any time the cursor moves in the text box, set cursor pos in the status bar:
editor_text.bind("<Activate>", editorUpdate)
editor_text.bind("<ButtonRelease>", editorUpdate)
editor_text.bind("<FocusIn>", editorUpdate)
editor_text.bind("<KeyPress>", editorUpdate)
editor_text.bind("<KeyRelease>", editorUpdate)
# Main application key bindings:
root.bind("<Control-Key-n>", mnuFileNew)
root.bind("<Control-Key-o>", mnuFileOpen)
root.bind("<Control-Key-O>", mnuFileOpenSys)
root.bind("<Control-Key-s>", mnuFileSave)
root.bind("<Control-Key-S>", mnuFileSaveAs)
root.bind("<Control-Key-q>", mnuFileExit)
#root.bind("<Control-Key-z>", mnuEditUndo)
#root.bind("<Control-Key-y>", mnuEditRedo)
root.bind("<Control-Key-a>", mnuSelectAll)
root.bind("<Control-Key-I>", mnuInsertFile)
root.bind("<Control-Key-x>", mnuEditCut)
root.bind("<Control-Key-c>", mnuEditCopy)
root.bind("<Control-Key-v>", mnuEditPaste)
root.bind("<Control-Key-f>", mnuEditFind)
#root.bind("<Control-Key-h>", mnuEditReplace)
root.bind("<Button-3>", rightClickMenu)

# Status bar
statusBarRoot = tk.Label(root, relief=tk.SUNKEN)
tk.Grid.columnconfigure(statusBarRoot, 2, weight=1) # Make at least 1 status bar field expand
#statusTheme = ttk.Combobox(statusBarRoot, values=THEMES)
#statusTheme.grid(column=0, row=0, padx=1, sticky=tk.W+tk.E)
statusBarCursor = tk.Label(statusBarRoot, text="Cursor: 0.0", padx=5, pady=3, bd=1, relief=tk.SUNKEN)
statusBarCursor.grid(column=3, row=0, padx=1, sticky=tk.W+tk.E)
statusBarFile = tk.Label(statusBarRoot, text="CurrentFilename", padx=5, pady=3, bd=1, relief=tk.SUNKEN)
statusBarFile.grid(column=2, row=0, padx=1, sticky=tk.W+tk.E)
# Maybe add another status indicator containing a progress bar for file Open/Save?
statusBar = tk.Label(statusBarRoot, text="Status Bar", padx=5, pady=3, bd=1, relief=tk.SUNKEN)
statusBar.grid(column=1, row=0, sticky=tk.W+tk.E)
statusBarWrap = tk.Label(statusBarRoot, text="Wrap: None", padx=5, pady=3, bd=1, relief=tk.SUNKEN)
statusBarWrap.grid(column=4, row=0, sticky=tk.W+tk.E)
statusBarGrip = ttk.Sizegrip(statusBarRoot)
statusBarGrip.grid(column=5, row=0, sticky=tk.W+tk.E, padx=(10,0), pady=(10,0))
#statusBarCursor.config(textvariable=editor_text.index(tk.INSERT)) # Testing stuff

# Now we can add the status bar
statusBarRoot.pack(side=tk.BOTTOM, fill=tk.X)
editor_frame.pack(expand=True, fill=tk.BOTH)

# Now we get to the meat and potatoes!
if __name__ == "__main__":
    searchStart = "1.0"
    center_window(root, 800, 600, False)
    detectHosts()
    #mnuDisableWhenEmpty(True)

    editor_text.focus()
    #editor_text.insert(tk.END, font.families())
    root.mainloop()

# Message boxes
# showinfo, showwarning, showerror, askquestion, askokcancel, askyesno
