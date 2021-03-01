#!/usr/bin/env python3

#%% <-- For Jupyter debugging
import platform
from decimal import Decimal
import math
import os
import time
import tkinter as tk
#from tkinter.font import Font # https://www.youtube.com/watch?v=JIqE3RMCMFE
from tkinter import colorchooser as tkcolorchooser
from tkinter import filedialog as tkfiledialog
from tkinter import messagebox as tkmessagebox
#from tkinter import scrolledtext as st
from tkinter import ttk
import threading

#
# Credits:
#
# Most of this code was made possible via videos from the Youtube channel at
#   https://www.youtube.com/c/Codemycom/videos
#
#

# TODO:
#    Finish special dialogs related to the purpose of this app (Mostly done)
#       Make the Minimize button disappear or nonfunctional
#    Finish backend functionality for many of the dialogs
#       Flesh out Sort, Filter, Options dialogs (almost done)
#       Add a Replace All function
#       Add Goto Line # (From Filter dialog)
#       Add file encoding option to the Options dialog
#       Re-Find info about tkinter config files that I saw once.
#           This will allow me to finish options dialog
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
        path_slash = os.sep
        # The Windows registry is authoritative for the HOSTS file location.
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
def dlgDismiss(dlgWindow=None, widget=None):
    global searchStart
    searchStart = "1.0"
    if widget:
        widget.grab_release()
        widget.destroy()
    else:
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
            fileMainFilename = tkfiledialog.askopenfilename(
                initialdir=init_dir, title="Open System HOSTS")
    else:
        fileMainFilename = hosts_file
    if fileMainFilename != "" and fileMainFilename != ():
        try:
            try: # Not all files are UTF-8; This needs a better solution.
                text_file = open(fileMainFilename, "r")
                hosts_contents = text_file.read()
            except UnicodeDecodeError:
                text_file = open(fileMainFilename, "r", encoding='ISO-8859-1')
                hosts_contents = text_file.read()
            editor_text.delete(1.0, tk.END)
            editor_text.insert(tk.END, hosts_contents)
            text_file.close()
            fileUnsavedChanges = False
            editor_text.edit_modified(False)
            editor_text.mark_set(tk.INSERT, "1.0") # Move cursor to top
            editor_text.edit_reset() # Clear the undo stack
            init_dir = str(fileMainFilename).rpartition(os.sep)[0]
            statusBarFile.config(text=fileMainFilename)
        except Exception as exp:
            tkmessagebox.showerror("ERROR", exp)

def mnuFileOpen(e=None):
    global fileUnsavedChanges, fileMainFilename, init_dir
    try:
        #fileMainFilename = tkfiledialog.askopenfilename(
        #    initialdir=init_dir, title="Open a Hosts file")
        fileMainFilename = tkfiledialog.askopenfilename(
            title="Open a Hosts file")
        if fileMainFilename == "" or fileMainFilename == ():
            return
        try: # Not all files are UTF-8; This needs a better solution.
            text_file = open(fileMainFilename, "r")
            hosts_contents = text_file.read()
        except UnicodeDecodeError:
            text_file = open(fileMainFilename, "r", encoding='ISO-8859-1')
            hosts_contents = text_file.read()
        editor_text.delete(1.0, tk.END)
        editor_text.insert(tk.END, hosts_contents)
        text_file.close()
        fileUnsavedChanges = False
        editor_text.edit_modified(False)
        editor_text.mark_set(tk.INSERT, "1.0") # Move cursor to top
        editor_text.edit_reset() # Clear the undo stack
        init_dir = str(fileMainFilename).rpartition(os.sep)[0]
        statusBarFile.config(text=fileMainFilename)
    except Exception as exp:
        tkmessagebox.showerror("ERROR", exp)

def mnuFileMerge(e=None):
    global fileUnsavedChanges
    try:
        fileMainFilename = tkfiledialog.askopenfilename(initialdir=init_dir, title="Merge Hosts file")
        if fileMainFilename == "" or fileMainFilename == ():
            return
        # text_file.readlines(), list(sorted())
        try: # Not all files are UTF-8; This needs a better solution.
            text_file = open(fileMainFilename, "r")
            hosts_contents = text_file.read()
        except UnicodeDecodeError:
            text_file = open(fileMainFilename, "r", encoding='ISO-8859-1')
            hosts_contents = text_file.read()
        editor_text.insert(tk.END, "\r\n")
        editor_text.insert(tk.END, hosts_contents)
        text_file.close()
        fileUnsavedChanges = True
        editor_text.see(tk.INSERT) # Move cursor into view
    except Exception as exp:
        tkmessagebox.showerror("ERROR", exp)

# Resides under the Edit menu (and Sort/Merge option)
def mnuInsertFile(e=None, mergefile="", targetpos="", title="Insert a file"):
    global fileUnsavedChanges, init_dir
    try:
        if mergefile == "" or mergefile == " ":
            fileMainFilename = tkfiledialog.askopenfilename(
                initialdir=init_dir, title=title)
        else:
            fileMainFilename = mergefile
        if mergefile == " ":
            return fileMainFilename
        if fileMainFilename == "" or fileMainFilename == ():
            return ""
        try: # Not all files are UTF-8; This needs a better solution.
            text_file = open(fileMainFilename, "r")
            hosts_contents = text_file.read()
        except UnicodeDecodeError:
            text_file = open(fileMainFilename, "r", encoding='ISO-8859-1')
            hosts_contents = text_file.read()
        if targetpos == "":
            curpos = editor_text.index(tk.INSERT)
        else:
            curpos = targetpos
        editor_text.insert(curpos, hosts_contents)
        text_file.close()
        fileUnsavedChanges = True
        editor_text.see(tk.INSERT) # Move cursor into view
        if mergefile == "":
            init_dir = str(fileMainFilename).rpartition(os.sep)[0]
        return fileMainFilename
    except Exception as exp:
        tkmessagebox.showerror("ERROR", exp)
        return ""

def mnuFileSave(e=None):
    global fileUnsavedChanges, fileMainFilename, init_dir
    try:
        if fileMainFilename == "" or not os.access(fileMainFilename, os.W_OK):
            fileMainFilename = tkfiledialog.asksaveasfilename(
                initialdir=init_dir,
                initialfile="hosts-custom.txt",
                title="Save Hosts file")
            if fileMainFilename != () and fileMainFilename != "":
                init_dir = str(fileMainFilename).rpartition(os.sep)[0]
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
    global fileUnsavedChanges, fileMainFilename, init_dir
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
        init_dir = str(fileMainFilename).rpartition(os.sep)[0]
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
    # Don't prompt to quit if key binding was used
    # unless there are unsaved changes
    if e:
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
    txtFind = tk.Entry(dlgEditReplace) #, textvariable=cursel_text
    lblReplace = tk.Label(dlgEditReplace, text="Replace:")
    txtReplace = tk.Entry(dlgEditReplace)
    lblMatchCase = tk.Label(dlgEditReplace, text="Match Case:")
    chkMatchCase = tk.Checkbutton(dlgEditReplace, variable=boolMatchCase,
        offvalue=False, onvalue=True)
    chkMatchCase.deselect() # Start out unchecked
    btnReplaceFindAll = tk.Button(dlgEditReplace, text="Mark All",
        command=mnuEditFindFindAll)

    btnReplaceFind = tk.Button(dlgEditReplace, text="Find",
        command=mnuEditReplaceFind)
    btnEditReplaceNext = tk.Button(dlgEditReplace, text="Replace",
        command=mnuEditReplaceNext)
    btnEditReplaceCancel = tk.Button(dlgEditReplace, text="Cancel",
        command=mnuEditReplaceCancel)
    lblFind.grid(column=0, row=0, padx=10, pady=10, sticky=tk.E)
    txtFind.grid(column=1, row=0, columnspan=2, pady=10)
    lblReplace.grid(column=0, row=1, padx=10, pady=5)
    txtReplace.grid(column=1, row=1, columnspan=2, pady=5, sticky=tk.E)
    lblMatchCase.grid(column=0, row=2, padx=10, pady=5, sticky=tk.E)
    chkMatchCase.grid(column=1, row=2, sticky=tk.W)
    btnReplaceFindAll.grid(column=2, row=2, sticky=tk.E)
    btnReplaceFind.grid(column=0, row=3)
    btnEditReplaceNext.grid(column=1, row=3, pady=5, sticky=tk.W)
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
    selected_index = "1.0"
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
        cur_end = editor_text.index(tk.END)
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

def mnuAddBrowse(e=None, fileName="", insertPos=""):
    browseTitle = "Select a file to merge"
    if fileName.strip() == "":
        fileName = " "
    fileName = mnuInsertFile(None, fileName, insertPos, browseTitle)
    e.delete(0, tk.END)
    e.insert(0, fileName)
def mnuAddFromPos(e=None, insertPos=""):
    if e.get().strip() == "":
        mnuAddBrowse(e, "")
    curFile = e.get().strip()
    if curFile == "": # 2 chances before we abort.
        return;
    if insertPos == "": # Default to cursor position
        insertPos = editor_text.index(tk.INSERT)
    if txtMergeTag.get().startswith("#"):
        mergeTag = txtMergeTag.get()
        try:
            try: # Not all files are UTF-8; This needs a better solution.
                text_file = open(curFile, "r")
                merge_contents = text_file.readlines()
            except UnicodeDecodeError:
                text_file = open(curFile, "r", encoding='ISO-8859-1')
                merge_contents = text_file.readlines()
            for idx, curLine in enumerate(merge_contents):
                if not curLine.endswith("\n"): curLine += "\n"
                curListTest = curLine.splitlines()
                if curListTest: # Sometimes it is an empty list!
                    curList = curListTest[0].split(" ", 2)
                    if len(mergeTag) > 1 and \
                        (curList[0] == "0.0.0.0" or curList[0] == "127.0.0.1"):
                        curList[0] = "0.0.0.0"
                        if len(curList) == 2:
                            curList.append(mergeTag)
                        elif len(curList) > 2 and mergeTag not in curList[2]:
                            curList[2] = " ".join([mergeTag, curList[2]])
                    curLine = " ".join(curList)
                    merge_contents[idx] = curLine
            editor_text.insert(insertPos, "\n".join(merge_contents))
            editor_text.mark_set(tk.INSERT, insertPos)
        except Exception as exp:
            tkmessagebox.showerror("ERROR", exp)
            return
    else:
        mnuInsertFile(None, curFile, insertPos, "Add a Hosts file")
def spinMax(e=None, maxline=-1):
    e.config(to=maxline)
def spinMin(e=None, minline=1):
    e.config(from_=minline)
def mnuToolSort(e=None):
    global dlgToolSort, spinStart, spinStop, sortProgress, btnToolSort
    global txtFileMerge, txtMergeTag
    dlgToolSort = tk.Toplevel(root)
    dlgToolSort.title("Sort/Merge Hosts")
    center_window(dlgToolSort, 650, 210)
    # Figure out how many lines the currently loaded file is
    cur_end = editor_text.index(tk.END)
    lastline = int(cur_end.split(".", 1)[0]) # "int" may be too small
    start_line = tk.IntVar()
    stop_line = tk.IntVar()
    start_line.set(1)
    stop_line.set(lastline)
    spinStart = None
    spinStop = None
    lblWarning = tk.Label(dlgToolSort,
        text="WARNING: All nonfunctional lines will be deleted!")
    curfont = lblWarning["font"]
    lblWarning.config(font=(curfont, 18), fg="red")
    lblSortRoot = tk.Label(dlgToolSort)
    lblSortStartLine = tk.Label(lblSortRoot, text="Start sort at Line: ")
    lblSortEndLine = tk.Label(lblSortRoot, text="Stop sort at Line: ")
    # Now to create the dependent spinboxes
    try:
        spinStart = tk.Spinbox(lblSortRoot, increment=1,
            from_=1, to=int(stop_line.get()),
            textvariable=start_line, justify=tk.RIGHT,
            command=lambda:spinMin(spinStop, start_line.get()))
        spinStop = tk.Spinbox(lblSortRoot, increment=1,
            from_=int(start_line.get()), to=int(lastline),
            textvariable=stop_line, justify=tk.RIGHT,
            command=lambda:spinMax(spinStart, stop_line.get()))
    except Exception as exp:
        pass
    btnToolSortBeautify = tk.Button(lblSortRoot, text="Beautify",
        command=lambda: hostsBeautify(
        spinStop, "%s.0" % (spinStart.get()), "%s.0" % (spinStop.get())))
    btnToolSort = tk.Button(lblSortRoot, text="Sort Hosts", state="disabled",
        command=lambda: threading.Thread(mypySort(
        spinStop, "%s.0" % (spinStart.get()), "%s.0" % (spinStop.get())
        )).start())
    lblMergeTag = tk.Label(lblSortRoot, text="Merge tag:")
    txtMergeTag = tk.Entry(lblSortRoot)

    lblMergeRoot = tk.Label(dlgToolSort)
    lblMergeFile = tk.Label(lblMergeRoot, text="Add file: ")
    txtFileMerge = tk.Entry(lblMergeRoot)
    btnFileBrowse = tk.Button(lblMergeRoot, text="Browse",
        command=lambda: mnuAddBrowse(txtFileMerge, " "))
    lblMergeBtnRoot = tk.Label(dlgToolSort)
    lblAddFrom = tk.Label(lblMergeBtnRoot, text="Add to where?:")
    btnAddFromTop = tk.Button(lblMergeBtnRoot, text="Top",
        command=lambda: mnuAddFromPos(txtFileMerge, "1.0"))
    btnAddFromStart = tk.Button(lblMergeBtnRoot, text="Start",
       command=lambda:mnuAddFromPos(txtFileMerge, "%s.0" % (spinStart.get())))
    btnAddFromCursor = tk.Button(lblMergeBtnRoot, text="Cursor",
        command=lambda: mnuAddFromPos(txtFileMerge))
    btnAddFromStop = tk.Button(lblMergeBtnRoot, text="Stop",
        command=lambda: mnuAddFromPos(txtFileMerge, "%s.0" % (spinStop.get())))
    btnAddFromBottom = tk.Button(lblMergeBtnRoot, text="Bottom",
        command=lambda: mnuAddFromPos(txtFileMerge, tk.END))

    sortProgress = ttk.Progressbar(dlgToolSort, orient=tk.HORIZONTAL,
        mode="determinate")

    # Handle the layout all at once:
    lblWarning.pack(padx=10, pady=5, side=tk.TOP, fill=tk.X)

    lblSortRoot.pack(padx=10)
    lblSortStartLine.grid(row=0, column=0, pady=5, sticky=tk.E)
    lblSortEndLine.grid(row=1, column=0, pady=5, sticky=tk.E)
    spinStart.grid(row=0, column=1, pady=5, sticky=tk.W)
    spinStop.grid(row=1, column=1, pady=5, sticky=tk.W)
    btnToolSortBeautify.grid(row=0, column=3, padx=10)
    btnToolSort.grid(row=1, column=3, padx=10)
    lblMergeTag.grid(row=0, column=4, sticky=tk.W)
    txtMergeTag.grid(row=1, column=4, sticky=tk.W+tk.E)

    # Add weights before adding items to the layout
    tk.Grid.columnconfigure(lblMergeRoot, 1, weight=1)
    lblMergeRoot.pack(padx=10, fill=tk.X)
    lblMergeFile.grid(column=0, row=0, padx=10, pady=5, sticky=tk.W+tk.E)
    txtFileMerge.grid(column=1, row=0, sticky=tk.W+tk.E)
    btnFileBrowse.grid(column=2, row=0, padx=10, sticky=tk.W+tk.E)

    lblMergeBtnRoot.pack(padx=10, fill=tk.X)
    lblAddFrom.grid(column=0, row=0, padx=5)
    btnAddFromTop.grid(column=1, row=0, padx=5)
    btnAddFromStart.grid(column=2, row=0, padx=5)
    btnAddFromCursor.grid(column=3, row=0, padx=5)
    btnAddFromStop.grid(column=4, row=0, padx=5)
    btnAddFromBottom.grid(column=5, row=0, padx=5)

    sortProgress.pack(padx=5, pady=5, side=tk.BOTTOM, fill=tk.X)

    dlgToolSort.resizable(False, False)
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
    sortProgress["value"] = 0
    match_length = tk.IntVar()
    cur_end = editor_text.index(tk.END)
    if (Decimal(cur_end) > Decimal(end_index)):
        cur_end = str(Decimal(end_index))
    cur_index = str(Decimal(start_index))
    cur_pindex = Decimal(start_index)
    cur_pend = Decimal(end_index)
    combined_regexp = r"[ \t][ \t]+|^[ \t]]+|[ \t]+$|^\#.*$|^\r?\n"
    while Decimal(cur_index) <= Decimal(cur_end):
        dlgToolSort.update_idletasks()
        root.update_idletasks()
        try:
            cur_index = editor_text.search(combined_regexp, cur_index,
                count=match_length, regexp=True,
                nocase=1, stopindex=cur_end)
        except Exception as exp0:
            break
        if not cur_index or match_length.get() == 0: break
        cur_pindex = Decimal(start_index)
        next_index = "%s+%sc" % (cur_index, match_length.get())
        found_text = editor_text.get(cur_index, next_index)
        editor_text.delete(cur_index, next_index)
        # One space is fine but not more than 1
        if found_text == " " or found_text == "\t":
            pass # This isn't a duplicate so it must be leading or trailing
        elif found_text.startswith(" ") or found_text.startswith("\t"):
            editor_text.insert(cur_index, " ")
        elif found_text == "\n":
            cur_pend -= Decimal(1.0)
            cur_end = str(cur_pend)
        editor_text.see(cur_index)
        sortProgress["value"] = (Decimal(cur_pindex) / Decimal(cur_pend) * 100)
    # Done with all searches
    sortProgress["value"] = 100
    editor_text.see(tk.INSERT)
    # If the amount of lines change, we have a new EOF/max lines
    oldEnd = int(math.floor(Decimal(end_index)))
    newEnd = int(math.floor(Decimal(editor_text.index(tk.END))))
    if oldEnd >= newEnd:
        spinMax(e, newEnd)
    btnToolSort.config(state=tk.NORMAL)

def bubbleSort(e=None, start_index="1.0", end_index=tk.END, max_passes=20):
    # Variable prep:
    startInt = math.floor(Decimal(start_index))
    stopInt = math.floor(Decimal(end_index)) - 1
    if stopInt - startInt > max_passes:
        max_passes = stopInt - startInt
    if (startInt >= stopInt):
        return # Not enough lines to sort ( >= 3+ )
    # Time to do the actual sort:
    #for outerLoop in range(startInt, stopInt):
    for outerLoop in range(startInt, startInt+max_passes):
        lineSwap = False # Prepare to short circuit sorting
        statusBar.config(
            text=f"Pass {outerLoop-startInt+1} of {stopInt-startInt+1}")
        statusBar.update_idletasks()
        for innerLoop in range(startInt, stopInt):
            nextPos = innerLoop + 1
            editor_text.see(f"{nextPos}.0")
            dlgToolSort.update_idletasks()
            root.update_idletasks()
            try:
                curLine = editor_text.get(f"{innerLoop}.0", f"{nextPos}.0")
                nextLine = editor_text.get(f"{nextPos}.0", f"{nextPos+1}.0")
                curList = curLine.splitlines()[0].split(" ", 2)
                nextListTest = nextLine.splitlines()
                if nextListTest: # Sometimes it is an empty list!
                    nextList = nextLine.splitlines()[0].split(" ", 2)
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
        if not lineSwap: # If already sorted, skip further iterations.
            break
    # If the amount of lines change, we have a new EOF/max lines
    oldEnd = int(math.floor(Decimal(end_index)))
    newEnd = int(math.floor(Decimal(editor_text.index(tk.END))))
    if oldEnd >= newEnd:
        spinMax(e, newEnd)

def linekey(entry):
    if entry is None or len(entry) < 2:
        return ""
    return entry[1]
def mypySort(e=None, start_index="1.0", end_index=tk.END, max_passes=20):
    # Variable prep:
    sortProgress["value"] = 0
    startInt = math.floor(Decimal(start_index))
    stopInt = math.floor(Decimal(end_index)) - 1
    if stopInt - startInt > max_passes:
        max_passes = stopInt - startInt
    if (startInt >= stopInt):
        return # Not enough lines to sort ( >= 3+ )
    list2sort = [None] * (stopInt+1)
    # Read all of the lines into lists:
    for innerLoop in range(startInt, stopInt+1):
        dlgToolSort.update_idletasks()
        nextPos = innerLoop + 1
        try:
            curLine = editor_text.get(f"{innerLoop}.0", f"{nextPos}.0")
            # Sometimes the last line doesn't have a newline:
            if not curLine.endswith("\n"): curLine += "\n"
            curListTest = curLine.splitlines()
            if curListTest: # Sometimes it is an empty list!
                curList = curListTest[0].split(" ", 2)
            else: # Design feature: Blank lines will cause sorting to stop
                break
        except Exception:
            break
        list2sort[innerLoop] = curList
        sortProgress["value"] = ((innerLoop / (stopInt+1)) * 45)
    # Time to do the actual (fast) sort:
    sortedLines = sorted(list2sort, key=linekey)
    sortProgress["value"] = 55
    list2sort = None # Empty unsorted list
    # Now check for duplicates:
    for innerLoop in range(startInt, stopInt):
        dlgToolSort.update_idletasks()
        nextPos = innerLoop + 1
        if innerLoop >= len(sortedLines) or nextPos >= len(sortedLines):
            break
        if len(sortedLines[innerLoop]) <2 or len(sortedLines[nextPos]) <2 or \
                sortedLines[innerLoop][0] != sortedLines[nextPos][0] or \
                sortedLines[innerLoop] is None or sortedLines[nextPos] is None:
            continue
        if sortedLines[innerLoop][1] == sortedLines[nextPos][1]:
            # Try to preserve end of line comments
            if len(sortedLines[innerLoop])==2 and len(sortedLines[nextPos])>2:
                sortedLines.pop(innerLoop)
            elif len(sortedLines[innerLoop])>= 2 and \
                    len(sortedLines[nextPos])==2:
                sortedLines.pop(nextPos)
            elif len(sortedLines[innerLoop])>2 and len(sortedLines[nextPos])>2:
                # Consolidate the comments between the 2 lines, min dupes
                if sortedLines[innerLoop][2] not in sortedLines[nextPos][2] and \
                  sortedLines[nextPos][2] not in sortedLines[innerLoop][2]:
                    allComments = " ".join([sortedLines[innerLoop][2],
                        sortedLines[nextPos][2]])
                elif sortedLines[innerLoop][2] in sortedLines[nextPos][2]:
                    allComments = sortedLines[nextPos][2]
                elif sortedLines[nextPos][2] in sortedLines[innerLoop][2]:
                    allComments = sortedLines[innerLoop][2]
                sortedLines[innerLoop][2] = allComments
                sortedLines.pop(nextPos)
        sortProgress["value"] = (55 + ((innerLoop / stopInt) * 45))
    sortedList = [None] * (stopInt+1)
    if len(sortedLines) < stopInt:
        stopInt = len(sortedLines)
    # Now put it back into the editor_text:
    for innerLoop in range(startInt, stopInt+1):
        if innerLoop < len(sortedLines):
            sortedList[innerLoop] = " ".join(sortedLines[innerLoop])
    sortedLines = sortedList[startInt:stopInt+1]
    sortedList = [elem for elem in sortedLines if elem is not None]
    sortedLines = None
    editor_text.delete(start_index, end_index)
    if start_index == "1.0":
        editor_text.insert(start_index, "\n".join(sortedList))
    else:
        editor_text.insert(start_index, "\n" + "\n".join(sortedList))
    sortProgress["value"] = 100
    dlgToolSort.update_idletasks()
    # If the amount of lines change, we have a new EOF/max lines
    oldEnd = int(math.floor(Decimal(end_index)))
    newEnd = int(math.floor(Decimal(editor_text.index(tk.END))))
    if oldEnd >= newEnd:
        spinMax(e, newEnd)

def mnuEditGotoLine(e=None):
    global dlgEditGotoLine, spinGoto
    dlgEditGotoLine = tk.Toplevel(root)
    dlgEditGotoLine.title("Goto Line #")
    center_window(dlgEditGotoLine, 240, 80)
    # TODO:
    start_gline = tk.IntVar()
    start_gline.set(1)
    lastline = int(editor_text.index(tk.END).split(".", 1)[0])

    lblGotoLine = tk.Label(dlgEditGotoLine, text="Goto Line #:")
    try:
        spinGoto = tk.Spinbox(dlgEditGotoLine, increment=1, width=10,
            from_=1, to=lastline,
            textvariable=start_gline, justify=tk.RIGHT,
            command=lambda:spinMax(spinGoto, lastline))
    except Exception as exp:
        pass
    #txtGotoLine = tk.Entry(dlgEditGotoLine)
    btnGotoLine = tk.Button(dlgEditGotoLine, text="Go",
        command=lambda: mnuGotoLine(None, "%s.0" % spinGoto.get()))
    lblGotoLine.grid(column=0, row=0, padx=10, pady=10, sticky=tk.E)
    #txtGotoLine.grid(column=1, row=0, pady=10, sticky=tk.W)
    spinGoto.grid(column=1, row=0, pady=10, sticky=tk.W)
    btnGotoLine.grid(column=1, row=2, sticky=tk.W)

    #txtGotoLine.focus()
    spinGoto.focus()
    #dlgEditGotoLine.resizable(False, False)
    spinGoto.bind("<Escape>", lambda x: dlgDismiss(x, dlgEditGotoLine))
    dlgEditGotoLine.bind("<Return>", mnuGotoLineSpin)
    dlgEditGotoLine.bind("<Escape>", dlgDismissEvent)
    #dlgEditGotoLine.overrideredirect(True)
    dlgEditGotoLine.protocol("WM_DELETE_WINDOW",
        lambda: dlgDismiss(dlgEditGotoLine)) # intercept close button
    dlgEditGotoLine.transient(root)   # dialog window is related to main
    # Still need to remove min/max buttons and keep the X button
    dlgEditGotoLine.wait_visibility() # can't grab until window appears, so we wait
    #dlgEditGotoLine.grab_set()        # ensure all input goes to our window
    dlgEditGotoLine.wait_window()     # block until window is destroyed

def mnuGotoLine(e=None, jumpline=""):
    if jumpline == "":
        pass
    else:
        editor_text.see(jumpline)
        editor_text.mark_set(tk.INSERT, jumpline)
        editorUpdate()
def mnuGotoLineSpin(e=None, jumpline=""):
    global spinGoto
    row = spinGoto.get()
    mnuGotoLine(None, f"{row[0]}.0")
def mnuGotoLineTree(e=None, jumpline=""):
    row = treeComments.selection()
    mnuGotoLine(None, f"{row[0]}.0")
def mnuToolFilterComments(e=None, start_index="1.0", end_index=tk.END):
    # Variable prep:
    filterProgress["value"] = 0
    startInt = math.floor(Decimal(start_index))
    stopInt = math.floor(Decimal(end_index))
    if (startInt >= stopInt):
        return # Not enough lines to filter ( >= 3+ )
    # Make sure our Treeview is empty:
    for record in e.get_children():
        e.delete(record)
    # Read all of the lines into the Treeview:
    for innerLoop in range(startInt, stopInt+1):
        dlgToolFilter.update_idletasks()
        nextPos = innerLoop + 1
        try:
            curLine = editor_text.get(f"{innerLoop}.0", f"{nextPos}.0")
            # Sometimes the last line doesn't have a newline:
            if not curLine.endswith("\n"): curLine += "\n"
            curListTest = curLine.splitlines()
            if curListTest: # Sometimes it is an empty list!
                curList = curListTest[0].split(" ", 2)
            else: # Design feature: Blank lines should cause filtering to stop
                break
        except Exception:
            break
        if len(curList) > 2 and curList[2].startswith("#"):
            e.insert(parent="", index="end",
                iid=innerLoop, text=innerLoop, values=tuple(curList))
        filterProgress["value"] = ((innerLoop / (stopInt+1)) * 100)
    filterProgress["value"] = 100
def mnuToolFilter(e=None):
    global dlgToolFilter, filterProgress, treeComments
    dlgToolFilter = tk.Toplevel(root)
    dlgToolFilter.title("Filter Hosts")
    center_window(dlgToolFilter, 650, 450)
    cur_end = editor_text.index(tk.END)
    lastline = int(cur_end.split(".", 1)[0]) # "int" may be too small
    start_fline = tk.IntVar()
    stop_fline = tk.IntVar()
    start_fline.set(1)
    stop_fline.set(lastline)
    spinFStart = None
    spinFStop = None
    lblFilterRoot = tk.Label(dlgToolFilter)
    lblFilterStartLine = tk.Label(lblFilterRoot, text="Start filter at Line: ")
    lblFilterEndLine = tk.Label(lblFilterRoot, text="Stop filter at Line: ")
    # Now to create the dependent spinboxes
    try:
        spinFStart = tk.Spinbox(lblFilterRoot, increment=1,
            from_=1, to=int(stop_fline.get()),
            textvariable=start_fline, justify=tk.RIGHT,
            command=lambda:spinMin(spinFStop, start_fline.get()))
        spinFStop = tk.Spinbox(lblFilterRoot, increment=1,
            from_=int(start_fline.get()), to=int(lastline),
            textvariable=stop_fline, justify=tk.RIGHT,
            command=lambda:spinMax(spinFStart, stop_fline.get()))
    except Exception as exp:
        pass
    btnToolFilter = tk.Button(lblFilterRoot,
        text="Show Hosts with Comments",
        command=lambda: threading.Thread(mnuToolFilterComments(
            treeComments, "%s.0" % (spinFStart.get()), "%s.0" % (spinFStop.get())
        )).start())
    frameComments = tk.Frame(dlgToolFilter)
    treeVScroll = tk.Scrollbar(frameComments, takefocus=0)
    treeHScroll = tk.Scrollbar(frameComments, takefocus=0, orient="horizontal")
    treeComments = ttk.Treeview(frameComments, selectmode="browse",
        xscrollcommand=treeHScroll.set, yscrollcommand=treeVScroll.set)
    treeVScroll.config(command=treeComments.yview)
    treeHScroll.config(command=treeComments.xview)
    filterProgress = ttk.Progressbar(dlgToolFilter, orient=tk.HORIZONTAL,
        mode="determinate")

    treeStyle = ttk.Style()
    treeStyle.theme_use("default")
    treeStyle.configure("Treeview",
        foreground=editor_text["foreground"],
        background=editor_text["background"],
        fieldbackground=editor_text["background"]
    )
    treeStyle.map("Treeview",
        foreground=[("selected", editor_text["selectforeground"])],
        background=[("selected", editor_text["selectbackground"])]
    )

    treeComments["columns"] = ("IP", "Hostname", "Comments")
    # First column is the Phantom/"icon" column
    treeComments.column("#0", anchor=tk.E, width=70,
        minwidth=25, stretch=tk.NO)
    treeComments.column("IP", anchor=tk.CENTER, width=80, stretch=tk.NO)
    treeComments.column("Hostname", anchor=tk.W, width=200, stretch=tk.NO)
    treeComments.column("Comments", anchor=tk.W)

    treeComments.heading("#0", text="Line", anchor=tk.CENTER)
    treeComments.heading("IP", text="IP", anchor=tk.CENTER)
    treeComments.heading("Hostname", text="Hostname", anchor=tk.CENTER)
    treeComments.heading("Comments", text=" Comments", anchor=tk.W)

    treeComments.tag_configure("host", font=editor_text["font"],
        foreground=editor_text["foreground"],
        background=editor_text["background"])
    treeComments.bind("<ButtonRelease-1>", mnuGotoLineTree)

    lblFilterRoot.pack(padx=10, side=tk.TOP)
    lblFilterStartLine.grid(row=0, column=0, pady=5, sticky=tk.E)
    lblFilterEndLine.grid(row=1, column=0, pady=5, sticky=tk.E)
    spinFStart.grid(row=0, column=1, pady=5, sticky=tk.W)
    spinFStop.grid(row=1, column=1, pady=5, sticky=tk.W)
    btnToolFilter.grid(row=0, column=3, rowspan=2, padx=10)

    filterProgress.pack(padx=5, pady=5, side=tk.BOTTOM, fill=tk.X)
    frameComments.pack(padx=10, pady=(10,0), expand=True, fill=tk.BOTH)
    # Always add scroll bars before the scrolled widget
    treeVScroll.pack(side=tk.RIGHT, fill=tk.Y)
    treeHScroll.pack(side=tk.BOTTOM, fill=tk.X)
    treeComments.pack(expand=True, fill=tk.BOTH)

    #dlgToolFilter.resizable(False, False)
    dlgToolFilter.bind("<Escape>", dlgDismissEvent)
    #dlgToolFilter.overrideredirect(True)
    dlgToolFilter.protocol("WM_DELETE_WINDOW",
        lambda: dlgDismiss(dlgToolFilter)) # intercept close button
    dlgToolFilter.transient(root)   # dialog window is related to main
    # Still need to remove min/max buttons and keep the X button
    dlgToolFilter.wait_visibility() # can't grab until window appears, so we wait
    #dlgToolFilter.grab_set()        # ensure all input goes to our window
    dlgToolFilter.wait_window()     # block until window is destroyed

def mnuToolWrapSet(curwrap):
    editor_text["wrap"] = curwrap
    statusBarWrap["text"] = f"Wrap: {curwrap.capitalize()}"

def fontChanged(curfont):
    # Font info:  .metrics("fixed") == 1 - Fixed with fonts only
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

# By default, some menu items don't make sense to have enabled
# when editor_text is empty
def mnuDisableWhenEmpty():
    global mnuFile, mnuEdit, mnuTool
    # Enable when editor_text.get() != ""
    mnuFile.entryconfig("New", state="disabled")
    mnuFile.entryconfig("Save", state="disabled")
    mnuFile.entryconfig("Save As...", state="disabled")
    if fileMainFilename == "":
        # Enable when fileMainFilename != ""
        #mnuFile.entryconfig("Merge", state="disabled")
        # Enable when fileMainFilename != ""
        mnuFile.entryconfig("Revert", state="disabled")
    # Enable when editor_text.get() != ""
    mnuEdit.entryconfig("Select All", state="disabled")
    mnuEdit.entryconfig("Cut", state="disabled")
    mnuEdit.entryconfig("Copy", state="disabled")
    mnuEdit.entryconfig("Find & Replace...", state="disabled")
    mnuEdit.entryconfig("Go To Line #", state="disabled")
    mnuTool.entryconfig("Sort/Merge Hosts", state="disabled")
    mnuTool.entryconfig("Filter Hosts", state="disabled")

def mnuDisableUnReDo():
    if not editor_text.edit_modified():
        # Enabled upon editor_text change; enables Redo
        mnuEdit.entryconfig("Undo", state="disabled")
        # Enabled upon Undo; disabled after use
        mnuEdit.entryconfig("Redo", state="disabled")

def mnuEnableUnReDo():
    if editor_text.edit_modified():
        # Enabled upon editor_text change; enables Redo
        mnuEdit.entryconfig("Undo", state="normal")

def mnuEnable():
    global mnuFile, mnuEdit, mnuTool
    # Enable when editor_text.get() != ""
    mnuFile.entryconfig("New", state="normal")
    mnuFile.entryconfig("Save", state="normal")
    mnuFile.entryconfig("Save As...", state="normal")
    if fileMainFilename != "":
        # Enable when fileMainFilename != ""
        #mnuFile.entryconfig("Merge", state="disabled")
        # Enable when fileMainFilename != ""
        mnuFile.entryconfig("Revert", state="normal")
    # Enable when editor_text.get() != ""
    mnuEdit.entryconfig("Select All", state="normal")
    mnuEdit.entryconfig("Cut", state="normal")
    mnuEdit.entryconfig("Copy", state="normal")
    mnuEdit.entryconfig("Find & Replace...", state="normal")
    mnuEdit.entryconfig("Go To Line #", state="normal")
    mnuTool.entryconfig("Sort/Merge Hosts", state="normal")
    mnuTool.entryconfig("Filter Hosts", state="normal")

def rightClickMenu(e=None):
    mnuRightClick.tk_popup(e.x_root, e.y_root)

def editorUpdate(e=None):
    # Useful info at https://tkdocs.com/shipman/event-handlers.html
    # e.widget = item causing event
    # Update status bar with cursor position
    #editor_text.see(tk.INSERT) # Keep cursor in current view
    cursortxt = "Cursor: " + editor_text.index(tk.INSERT)
    statusBarCursor.config(text=cursortxt)
    if editor_text.compare("end-1c", "==", "1.0"):
        editor_text.edit_modified(False)
        mnuDisableWhenEmpty()
    else:
        mnuEnable()
        mnuEnableUnReDo()
    fileUnsavedChanges = editor_text.edit_modified() # Has anything changed?
    #statusBar.config(text=f"{e.state} {e.keysym} {e.keycode}")
    if fileUnsavedChanges:
        statusBar.config(text="Modified")
        mnuEnableUnReDo()
    else:
        statusBar.config(text="Status Bar")
        mnuDisableUnReDo()

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
editor_text = tk.Text(editor_frame, width=20, height=20,
    wrap="none", undo=True,
    selectbackground="yellow", # Default is Gray
    xscrollcommand=horiz_scroll.set, yscrollcommand=vert_scroll.set)
# Default to Dark Mode
editor_text.config(fg="white", bg="black", insertbackground="white")

editor_text.pack(expand=True, fill=tk.BOTH) # Last for proper AutoResize

# Configure scrollbars
vert_scroll.config(command=editor_text.yview)
horiz_scroll.config(command=editor_text.xview)

# Menu bar
rootMenu = tk.Menu(root)
root.config(menu=rootMenu)

mnuFile = tk.Menu(rootMenu, tearoff=False)
rootMenu.add_cascade(label="File", menu=mnuFile)
mnuFile.add_command(label="New",
    command=lambda: mnuFileNew(0), accelerator="(Ctrl+N)")
mnuFile.add_command(label="Open System Hosts",
    command=mnuFileOpenSys, accelerator="(Ctrl+Shift+O)")
mnuFile.add_command(label="Open...",
    command=lambda: mnuFileOpen(0), accelerator="(Ctrl+O)")
#mnuFile.add_command(label="Merge", command=mnuFileMerge)
mnuFile.add_command(label="Save",
    command=lambda: mnuFileSave(0), accelerator="(Ctrl+S)")
mnuFile.add_command(label="Save As...",
    command=mnuFileSaveAs, accelerator="(Ctrl+Shift+S)")
mnuFile.add_command(label="Revert",
    command=mnuFileRevert)
mnuFile.add_separator()
mnuFile.add_command(label="Exit",
    command=lambda: mnuFileExit(0), accelerator="(Ctrl+Q)")

mnuEdit = tk.Menu(rootMenu, tearoff=False)
rootMenu.add_cascade(label="Edit", menu=mnuEdit)
mnuEdit.add_command(label="Undo",
    command=editor_text.edit_undo, accelerator="(Ctrl+Z)")
mnuEdit.add_command(label="Redo",
    command=editor_text.edit_redo, accelerator="(Ctrl+Y)")
mnuEdit.add_separator()
mnuEdit.add_command(label="Select All",
    command=lambda: mnuSelectAll(0), accelerator="(Ctrl+A)")
mnuEdit.add_command(label="Insert File...",
    command=lambda: mnuInsertFile(0), accelerator="(Ctrl+I)")
mnuEdit.add_command(label="Cut",
    command=lambda: mnuEditCut(0), accelerator="(Ctrl+X)")
mnuEdit.add_command(label="Copy",
    command=lambda: mnuEditCopy(0), accelerator="(Ctrl+C)")
mnuEdit.add_command(label="Paste",
    command=lambda: mnuEditPaste(0), accelerator="(Ctrl+V)")
mnuEdit.add_separator()
mnuEdit.add_command(label="Find & Replace...",
    command=lambda: mnuEditFind(0), accelerator="(Ctrl+F)")
mnuEdit.add_command(label="Go To Line #",
    command=lambda: mnuEditGotoLine(0), accelerator="(Ctrl+G)")

textWrap = tk.StringVar()
textWrap.set(editor_text["wrap"])

mnuTool = tk.Menu(rootMenu, tearoff=False)
mnuToolWrap = tk.Menu(mnuTool, tearoff=False)
rootMenu.add_cascade(label="Tools", menu=mnuTool)
mnuTool.add_command(label="Sort/Merge Hosts",
    command=mnuToolSort, accelerator="(Ctrl+Shift+M)")
mnuTool.add_command(label="Filter Hosts",
    command=mnuToolFilter, accelerator="(Ctrl+Shift+F)")
# Radio between [none, char, word]
mnuTool.add_cascade(label="Text Wrap", menu=mnuToolWrap)
# See https://blog.tecladocode.com/how-to-add-menu-to-tkinter-app/
mnuToolWrap.add_radiobutton(label="None", value="none", variable=textWrap,
    command=lambda: mnuToolWrapSet(textWrap.get()))
mnuToolWrap.add_radiobutton(label="Char", value="char", variable=textWrap,
    command=lambda: mnuToolWrapSet(textWrap.get()))
mnuToolWrap.add_radiobutton(label="Word", value="word", variable=textWrap,
    command=lambda: mnuToolWrapSet(textWrap.get()))
mnuTool.add_command(label="Text Font", command=mnuToolFont)
mnuTool.add_command(label="Editor Colors", command=mnuToolColor)
mnuTool.add_command(label="Options...", command=mnuToolOptions)

mnuHelp = tk.Menu(rootMenu, tearoff=False)
rootMenu.add_cascade(label="Help", menu=mnuHelp)
mnuHelp.add_command(label="About...", command=mnuHelpAbout)

mnuRightClick = tk.Menu(root, tearoff=False)
mnuRightWrap = tk.Menu(mnuRightClick, tearoff=False)
mnuRightClick.add_command(label="Select All",
    command=lambda: mnuSelectAll(0), accelerator="(Ctrl+A)")
mnuRightClick.add_command(label="Insert File...",
    command=lambda: mnuInsertFile(0), accelerator="(Ctrl+Shift+I)")
mnuRightClick.add_command(label="Cut",
    command=lambda: mnuEditCut(0), accelerator="(Ctrl+X)")
mnuRightClick.add_command(label="Copy",
    command=lambda: mnuEditCopy(0), accelerator="(Ctrl+C)")
mnuRightClick.add_command(label="Paste",
    command=lambda: mnuEditPaste(0), accelerator="(Ctrl+V)")
mnuRightClick.add_separator()
mnuRightClick.add_command(label="Find & Replace...",
    command=lambda: mnuEditFind(0), accelerator="(Ctrl+F)")
# Radio between [none, char, word]
mnuRightClick.add_cascade(label="Text Wrap", menu=mnuRightWrap)
# Might be a bug that we can't use mnuToolWrap above instead of
# having to rebuild it below
mnuRightWrap.add_radiobutton(label="None", value="none", variable=textWrap,
    command=lambda: mnuToolWrapSet(textWrap.get()))
mnuRightWrap.add_radiobutton(label="Char", value="char", variable=textWrap,
    command=lambda: mnuToolWrapSet(textWrap.get()))
mnuRightWrap.add_radiobutton(label="Word", value="word", variable=textWrap,
    command=lambda: mnuToolWrapSet(textWrap.get()))
mnuRightClick.add_separator()
mnuRightClick.add_command(label="Exit",
    command=lambda: mnuFileExit(0), accelerator="(Ctrl+Q)")

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
root.bind("<Control-Key-g>", mnuEditGotoLine)
root.bind("<Control-Key-M>", mnuToolSort)
root.bind("<Control-Key-F>", mnuToolFilter)
root.bind("<Button-3>", rightClickMenu)

# Status bar
statusBarRoot = tk.Label(root, relief=tk.SUNKEN)
statusBar = tk.Label(statusBarRoot, text="Status Bar",
    padx=5, pady=3,bd=1, relief=tk.SUNKEN)
statusBarFile = tk.Label(statusBarRoot, text="CurrentFilename",
    padx=5, pady=3, bd=1, relief=tk.SUNKEN)
# Add another indicator for a progress bar when doing Open/Save?
statusBarCursor = tk.Label(statusBarRoot, text="Cursor: 0.0",
    padx=5, pady=3, bd=1, relief=tk.SUNKEN)
statusBarWrap = tk.Label(statusBarRoot, text="Wrap: None",
    padx=5, pady=3, bd=1, relief=tk.SUNKEN)
statusBarGrip = ttk.Sizegrip(statusBarRoot)

# Make at least 1 status bar field expand
tk.Grid.columnconfigure(statusBarRoot, 2, weight=1)
statusBar.grid(column=1, row=0, sticky=tk.W+tk.E)
statusBarFile.grid(column=2, row=0, padx=1, sticky=tk.W+tk.E)
statusBarCursor.grid(column=3, row=0, padx=1, sticky=tk.W+tk.E)
statusBarWrap.grid(column=4, row=0, sticky=tk.W+tk.E)
statusBarGrip.grid(column=5, row=0, sticky=tk.W+tk.E, padx=(10,0), pady=(10,0))

# Now we can add the status bar
statusBarRoot.pack(side=tk.BOTTOM, fill=tk.X)
editor_frame.pack(expand=True, fill=tk.BOTH)

# Now we get to the meat and potatoes!
if __name__ == "__main__":
    searchStart = "1.0"
    center_window(root, 800, 600, False)
    detectHosts()
    mnuDisableWhenEmpty()

    editor_text.focus()
    #editor_text.insert(tk.END, font.families())
    root.mainloop()
