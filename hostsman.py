#!/usr/bin/env python3

#%% <-- For Jupyter debugging
import platform
import re
from tkinter import *
from tkinter import colorchooser
from tkinter import filedialog
from tkinter import font
from tkinter.font import Font # https://www.youtube.com/watch?v=JIqE3RMCMFE
from tkinter import messagebox
#from tkinter import scrolledtext as st
from tkinter import ttk
#from ttkthemes import ThemedTk, THEMES
#from style import *
#import sqlite3
import threading

#
# Credits:
#
# Most of this code was made possible via the videos from the Youtube channel at
#   https://www.youtube.com/c/Codemycom/videos
#
#

# TODO: 
#        Handle Read/Write file exceptions
#        Detect when editor_text.get() changes (partially done)
#        Detect when the cursor position changes in editor_text (partially done)
#        Finish special dialogs related to the purpose of this app
#           Make the Minimize button disappear
#        Perform the backend logic on editor_text with said dialogs
#        Finish backend functionality for many of the dialogs
#           Flesh out Sort, Filter, Options dialogs

root = Tk()
#root = ThemedTk()
root.title("Hosts File Manager")
#root.iconbitmap("/path/to/file.ico")

app_width = 800
app_height = 600
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
app_top = int((screen_width - app_width) / 2)
app_left = int((screen_height - app_height) / 2)
root.geometry(f"{app_width}x{app_height}+{app_top}+{app_left}")


# Utility functions
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
            import winreg
            hivekey = winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE)
            subkey = winreg.OpenKey(hivekey, r"SYSTEM\CurrentControlSet\Services\Tcpip\Parameters")
            keyval = winreg.QueryValueEx(subkey, "DataBasePath")[0]
            hosts_path = winreg.ExpandEnvironmentStrings(keyval)
            hosts_file = hosts_path + r"\HOSTS"
            hivekey.Close()
        except Exception:
            # If there is any reason for the above code block to fail
            # fallback to the standard default location and path
            hosts_path = r"C:\Windows\System32\drivers\etc"
            hosts_file = hosts_path + r"\HOSTS"
    init_dir = hosts_path

def center_window(curwind, dlg_width=200, dlg_height=200):
    # This needs refactoring since it doesn't work quite right for systems with 2+ screens
    global screen_width, screen_height, app_top, app_left, app_width, app_height
    dlg_top = int((screen_width - dlg_width) / 2)
    dlg_left = int((screen_height - dlg_height) / 2)
    curwind.geometry(f"{dlg_width}x{dlg_height}+{dlg_top}+{dlg_left}")

def dlgDismiss(dlgWindow):
    dlgWindow.grab_release()
    dlgWindow.destroy()


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

# Menu and related functions
def mnuFileNew(e):
    global fileUnsavedChanges, fileMainFilename
    if fileUnsavedChanges:
        root.bell()
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

def mnuFileMerge2():    # Custom dialog version (TODO)
    global fileUnsavedChanges
    center_window(dlgFileMerge)
    #fileMainFilename = filedialog.askopenfilename(initialdir=init_dir, title="Merge Hosts file")
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
    text_file.write(editor_text.get(1.0, END))
    fileUnsavedChanges = False
    statusBarFile.config(text=f"Saved: {fileMainFilename}")

def mnuFileSaveAs():
    global fileUnsavedChanges, fileMainFilename
    fileMainFilename = filedialog.asksaveasfilename(initialdir=init_dir, title="Save File As...")
    text_file = open(fileMainFilename, "w+")
    text_file.write(editor_text.get(1.0, END))
    fileUnsavedChanges = False
    statusBarFile.config(text=f"Saved As: {fileMainFilename}")

def mnuFileRevert():
    global fileUnsavedChanges, fileMainFilename, init_dir
    if fileMainFilename == "":
        fileMainFilename = filedialog.askopenfilename(initialdir=init_dir, title="Revert Changes to file")
    text_file = open(fileMainFilename, "r+")
    hosts_contents = text_file.read()
    editor_text.delete(1.0, END)
    editor_text.insert(END, hosts_contents)
    text_file.close()
    fileUnsavedChanges = False
    statusBarFile.config(text=fileMainFilename)

def mnuFileExit(e):
    global fileUnsavedChanges, fileMainFilename
    quitMsg = "Are you sure you want to quit?"
    menuBarUsed = True
    if e:   # Don't prompt to quit if key binding was used unless there are unsaved changes
        menuBarUsed = False
    if fileUnsavedChanges:
        quitMsg = "You have UNSAVED changes, are you sure you want to quit?"
    if menuBarUsed or fileUnsavedChanges:
        response = messagebox.askyesno("Quit?", quitMsg)
        if response != 1:
            return
    root.quit()
    # Exit app

def mnuEditUndo(e):
    mnuEdit.entryconfig("Undo", state="disabled")
    mnuEdit.entryconfig("Redo", state="normal")
    editor_text.edit_undo()

def mnuEditRedo(e):
    mnuEdit.entryconfig("Undo", state="normal")
    mnuEdit.entryconfig("Redo", state="disabled")
    editor_text.edit_redo()

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
    global dlgEditFind
    dlgEditFind = Toplevel(root)
    dlgEditFind.title("Find Text...")
    center_window(dlgEditFind, 255, 85)
    lblFind = Label(dlgEditFind, text="Find:")
    lblFind.grid(column=0, row=0, padx=10, pady=10, sticky=E)
    txtFind = Entry(dlgEditFind)
    txtFind.grid(column=1, row=0, columnspan=2, pady=10)
    btnEditFindNext = Button(dlgEditFind, text="Find Next", command=lambda: mnuEditFindNext(txtFind.get()))
    btnEditFindNext.grid(column=1, row=1, sticky=W)
    btnEditFindCancel = Button(dlgEditFind, text="Cancel", command=mnuEditFindCancel)
    btnEditFindCancel.grid(column=2, row=1, sticky=E)
    txtFind.focus()
    dlgEditFind.resizable(False, False)
    #dlgEditFind.attributes('-toolwindow', True)
    #dlgEditFind.overrideredirect(True)
    dlgEditFind.protocol("WM_DELETE_WINDOW",
        lambda: dlgDismiss(dlgEditFind)) # intercept close button
    dlgEditFind.transient(root)   # dialog window is related to main
    # Still need to remove min/max buttons and keep the X button
    dlgEditFind.wait_visibility() # can't grab until window appears, so we wait
    dlgEditFind.grab_set()        # ensure all input goes to our window
    dlgEditFind.wait_window()     # block until window is destroyed
def mnuEditFindNext(searchstr):
    global dlgEditFind, editor_text
    #editor_text.insert(END, dlgEditFind.children.get("Find Next"))
    curpos = editor_text.index(INSERT)
    text_file = editor_text.get(1.0, END)
    #posFound = text_file.find(searchstr, int(curpos))
    #if (posFound == -1):
    #    return      # Not found
    #editor_text.tag_add("sel", str(posFound))
    #print(posFound)

    # Search for the text in txtFind.get() and highlight the first instance
    # starting from editor_text.index(INSERT)
    #dlgDismiss(dlgEditFind)
def mnuEditFindCancel():
    global dlgEditFind
    dlgDismiss(dlgEditFind)

def mnuEditReplace(e):
    global dlgEditReplace
    dlgEditReplace = Toplevel(root)
    dlgEditReplace.title("Find & Replace Text...")
    center_window(dlgEditReplace, 285, 125)
    lblFindR = Label(dlgEditReplace, text="Find:")
    lblFindR.grid(column=0, row=0, padx=10, pady=10, sticky=E)
    txtFindR = Entry(dlgEditReplace)
    txtFindR.grid(column=1, row=0, columnspan=2, pady=10)
    lblReplace = Label(dlgEditReplace, text="Replace:")
    lblReplace.grid(column=0, row=1, padx=10, pady=5)
    txtReplace = Entry(dlgEditReplace)
    txtReplace.grid(column=1, row=1, columnspan=2, pady=5, sticky=E)
    btnReplaceSkip = Button(dlgEditReplace, text="Skip", command=lambda:
        mnuEditReplaceNext(txtFindR.get()))
    btnReplaceSkip.grid(column=0, row=2)
    btnEditReplaceNext = Button(dlgEditReplace, text="Replace",
        command=mnuEditReplaceNext)
    btnEditReplaceNext.grid(column=1, row=2, pady=5, sticky=W)
    btnEditReplaceCancel = Button(dlgEditReplace, text="Cancel",
        command=mnuEditReplaceCancel)
    btnEditReplaceCancel.grid(column=2, row=2, pady=5, sticky=E)
    txtFindR.focus()
    dlgEditReplace.resizable(False, False)
    #dlgEditReplace.attributes('-toolwindow', True)
    #dlgEditReplace.overrideredirect(True)
    dlgEditReplace.protocol("WM_DELETE_WINDOW",
        lambda: dlgDismiss(dlgEditReplace)) # intercept close button
    dlgEditReplace.transient(root)   # dialog window is related to main
    # Still need to remove min/max buttons and keep the X button
    dlgEditReplace.wait_visibility() # can't grab until window appears, so we wait
    dlgEditReplace.grab_set()        # ensure all input goes to our window
    dlgEditReplace.wait_window()     # block until window is destroyed
def mnuEditReplaceSkip():
    global dlgEditReplace
    dlgDismiss(dlgEditReplace)
def mnuEditReplaceNext():
    global dlgEditReplace
    dlgDismiss(dlgEditReplace)
def mnuEditReplaceCancel():
    global dlgEditReplace
    dlgDismiss(dlgEditReplace)

def mnuSelectAll(e):
    editor_text.tag_add("sel", "1.0", "end")

def mnuToolSort():
    global dlgToolSort
    dlgToolSort = Toplevel(root)
    dlgToolSort.title("Sort Hosts")
    center_window(dlgToolSort, 300, 500)

    #txtFindR.focus()
    #dlgToolSort.resizable(False, False)
    #dlgToolSort.attributes('-toolwindow', True)
    #dlgToolSort.overrideredirect(True)
    dlgToolSort.protocol("WM_DELETE_WINDOW",
        lambda: dlgDismiss(dlgToolSort)) # intercept close button
    dlgToolSort.transient(root)   # dialog window is related to main
    # Still need to remove min/max buttons and keep the X button
    dlgToolSort.wait_visibility() # can't grab until window appears, so we wait
    dlgToolSort.grab_set()        # ensure all input goes to our window
    dlgToolSort.wait_window()     # block until window is destroyed

def mnuToolFilter():
    global dlgToolFilter
    dlgToolFilter = Toplevel(root)
    dlgToolFilter.title("Filter Hosts")
    center_window(dlgToolFilter, 300, 250)

    #txtFindR.focus()
    #dlgToolFilter.resizable(False, False)
    #dlgToolFilter.attributes('-toolwindow', True)
    #dlgToolFilter.overrideredirect(True)
    dlgToolFilter.protocol("WM_DELETE_WINDOW",
        lambda: dlgDismiss(dlgToolFilter)) # intercept close button
    dlgToolFilter.transient(root)   # dialog window is related to main
    # Still need to remove min/max buttons and keep the X button
    dlgToolFilter.wait_visibility() # can't grab until window appears, so we wait
    dlgToolFilter.grab_set()        # ensure all input goes to our window
    dlgToolFilter.wait_window()     # block until window is destroyed

def mnuToolWrap():
    # TODO: Allow switching between none, char, word
    pass

def fontChanged(curfont):
    editor_text.config(font=curfont)
def mnuToolFont():
    # Tkinter has not yet added a convenient way to use this font dialog,
    # so I have to use the Tcl API directly. You can see the latest work
    # towards a proper Python API and download code at [Issue#28694].
    # On macOS, if you don't provide a font via the font configuration option,
    # your callbacks won't be invoked so always provide an initial font
    curfont = editor_text["font"]
    dlgToolFont = root.tk.call('tk', 'fontchooser', 'configure',
        '-font', f"{curfont} 10", '-command', root.register(fontChanged))
    root.tk.call('tk', 'fontchooser', 'show')

def dlgColorChange(self, editcolor):
    # https://www.youtube.com/watch?v=NDCirUTTrhg
    newcolor = colorchooser.askcolor(initialcolor=editor_text[editcolor])[1]
    if newcolor == None:
        pass
    else:
        self.config(bg=newcolor, activebackground=newcolor)
        editor_text[editcolor] = newcolor
def mnuToolColor():
    global dlgToolColor
    dlgToolColor = Toplevel(root)
    dlgToolColor.title("Editor Colors")
    center_window(dlgToolColor, 250, 260)
    # insertbackground needs to equal fg
    # colorchooser.askcolor(initialcolor='#ff0000')
    lblColorColorFg = Label(dlgToolColor, text="Foreground Color:")
    lblColorColorBg = Label(dlgToolColor, text="Background Color:")
    btnColorColorFg = Button(dlgToolColor, width=5,
        activebackground=editor_text["fg"], bg=editor_text["fg"],
        command=lambda: dlgColorChange(btnColorColorFg, "fg"))
    btnColorColorBg = Button(dlgToolColor, width=5,
        activebackground=editor_text["bg"], bg=editor_text["bg"],
        command=lambda: dlgColorChange(btnColorColorBg, "bg"))
    lblColorCursorBg = Label(dlgToolColor, text="Cursor BG Color:")
    btnColorCursorBg = Button(dlgToolColor, width=5,
        activebackground=editor_text["insertbackground"], bg=editor_text["insertbackground"],
        command=lambda: dlgColorChange(btnColorCursorBg, "insertbackground"))
    lblColorHiliteFg = Label(dlgToolColor, text="Highlight FG Color:")
    lblColorHiliteBg = Label(dlgToolColor, text="Highlight BG Color:")
    btnColorHiliteFg = Button(dlgToolColor, width=5,
        activebackground=editor_text["selectforeground"], bg=editor_text["selectforeground"],
        command=lambda: dlgColorChange(btnColorHiliteFg, "selectforeground"))
    btnColorHiliteBg = Button(dlgToolColor, width=5,
        activebackground=editor_text["selectbackground"], bg=editor_text["selectbackground"],
        command=lambda: dlgColorChange(btnColorHiliteBg, "selectbackground"))
    lblColorColorFg.grid(column=0, row=0, padx=(10,5), pady=10, sticky=E)
    lblColorColorBg.grid(column=0, row=1, padx=(10,5), pady=10, sticky=E)
    lblColorCursorBg.grid(column=0, row=3, padx=(10,5), pady=10, sticky=E)
    lblColorHiliteFg.grid(column=0, row=4, padx=(10,5), pady=10, sticky=E)
    lblColorHiliteBg.grid(column=0, row=5, padx=(10,5), pady=10, sticky=E)
    btnColorColorFg.grid(column=1, row=0, padx=(5,10), pady=10, sticky=W)
    btnColorColorBg.grid(column=1, row=1, padx=(5,10), pady=10, sticky=W)
    btnColorCursorBg.grid(column=1, row=3, padx=(5,10), pady=10, sticky=W)
    btnColorHiliteFg.grid(column=1, row=4, padx=(5,10), pady=10, sticky=W)
    btnColorHiliteBg.grid(column=1, row=5, padx=(5,10), pady=10, sticky=W)

    dlgToolColor.resizable(False, False)
    #dlgToolColor.attributes('-toolwindow', True)
    #dlgToolColor.overrideredirect(True)
    dlgToolColor.protocol("WM_DELETE_WINDOW",
        lambda: dlgDismiss(dlgToolColor)) # intercept close button
    dlgToolColor.transient(root)   # dialog window is related to main
    # Still need to remove min/max buttons and keep the X button
    dlgToolColor.wait_visibility() # can't grab until window appears, so we wait
    dlgToolColor.grab_set()        # ensure all input goes to our window
    dlgToolColor.wait_window()     # block until window is destroyed

def mnuToolOptions():
    global dlgToolOptions
    dlgToolOptions = Toplevel(root)
    dlgToolOptions.title("Editor Options")
    center_window(dlgToolOptions, 300, 500)

    #txtFindR.focus()
    #dlgToolOptions.resizable(False, False)
    #dlgToolOptions.attributes('-toolwindow', True)
    #dlgToolOptions.overrideredirect(True)
    dlgToolOptions.protocol("WM_DELETE_WINDOW",
        lambda: dlgDismiss(dlgToolOptions)) # intercept close button
    dlgToolOptions.transient(root)   # dialog window is related to main
    # Still need to remove min/max buttons and keep the X button
    dlgToolOptions.wait_visibility() # can't grab until window appears, so we wait
    dlgToolOptions.grab_set()        # ensure all input goes to our window
    dlgToolOptions.wait_window()     # block until window is destroyed

def mnuHelpAbout():
    messagebox.showinfo("About", "This program is a text editor designed to help merge multiple HOSTS files together.")

def rightClickMenu(e):
    mnuRightClick.tk_popup(e.x_root, e.y_root)

def editorUpdate(e):    # Check to see if there are unsaved changes
    global statusBar
    # Update status bar with cursor position
    statusBarCursor.config(text=editor_text.index(INSERT))
    # Regardless of e.state, editor_text changes
    if e.keysym == "Return":
        pass
    # If we are at the start of the buffer and BackSpace is pressed,
    # no change is made
    if e.keysym == "BackSpace" and editor_text.index(INSERT) == 1.0:
        pass
    # If we are at the end of the buffer and Delete is pressed,
    # no change is made
    # "KP_Delete" registers as "Delete" when numlock is off or
    # shift is pressed and numlock is on
    # (Num_Lock == ON && KP_Decimal) == Delete ==
    # (Num_Lock == OFF && KP_Delete)
    if e.keysym == "Delete" and editor_text.index(INSERT) == 1.0:
        pass
    statusBar.config(text=f"{e.state} {e.keysym} {e.keycode}")

# I'm Considering storing HOSTS entries in a DB or CSV
#sqdb = sqlite3.connect("hosts.db")
#sqcur = sqdb.cursor()


# Font info:  .metrics("fixed") == 1 - Fixed with fonts only

#
# Main editor window
#
# Scrolling issues: https://www.youtube.com/watch?v=0WafQCaok6g
editor_frame = Frame(root)
# Scroll bars should NOT be part of the tab order (takefocus=0)
vert_scroll = Scrollbar(editor_frame, takefocus=0)
vert_scroll.pack(side=RIGHT, fill=Y)
horiz_scroll = Scrollbar(editor_frame, takefocus=0, orient="horizontal")
horiz_scroll.pack(side=BOTTOM, fill=X)
editor_text = Text(editor_frame, width=20, height=20, wrap="none", undo=True,
    selectbackground="yellow", # Default is Gray
    xscrollcommand=horiz_scroll.set, yscrollcommand=vert_scroll.set)
# Default to Dark Mode
editor_text.config(fg="white", bg="black", insertbackground="white", insertwidth=2)

editor_text.bind("<Button-3>", rightClickMenu)
# Any time the cursor moves in the text box, set cursor pos in the status bar:
#editor_text.bind("<Configure>", editorUpdate) # Doesn't work yet
editor_text.bind("<KeyRelease>", editorUpdate)
#editor_text.pack needs to be added AFTER StatusBar is added

editor_text.pack(expand=TRUE, fill=BOTH) # Must be last to AutoResize properly

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
mnuFile.add_command(label="Open...", command=lambda: mnuFileOpen(0), accelerator="(Ctrl+O)")
mnuFile.add_command(label="Merge", command=mnuFileMerge)
mnuFile.add_command(label="Save", command=lambda: mnuFileSave(0), accelerator="(Ctrl+S)")
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

mnuTool = Menu(rootMenu, tearoff=False)
rootMenu.add_cascade(label="Tools", menu=mnuTool)
mnuTool.add_command(label="Sort Hosts", command=mnuToolSort)
mnuTool.add_command(label="Filter Hosts", command=mnuToolFilter)
mnuTool.add_command(label="Text Wrap", command=mnuToolWrap) # Radio between [none, char, word]
mnuTool.add_command(label="Text Font", command=mnuToolFont) # blockcursor= ?
mnuTool.add_command(label="Editor Colors", command=mnuToolColor)
mnuTool.add_command(label="Options...", command=mnuToolOptions)

mnuHelp = Menu(rootMenu, tearoff=False)
rootMenu.add_cascade(label="Help", menu=mnuHelp)
mnuHelp.add_command(label="About...", command=mnuHelpAbout)

mnuRightClick = Menu(root, tearoff=False)
mnuRightClick.add_command(label="Select All", command=lambda: mnuSelectAll(0), accelerator="(Ctrl+A)")
mnuRightClick.add_command(label="Insert File...", command=lambda: mnuInsertFile(0), accelerator="(Ctrl+I)")
mnuRightClick.add_command(label="Cut", command=lambda: mnuEditCut(0), accelerator="(Ctrl+X)")
mnuRightClick.add_command(label="Copy", command=lambda: mnuEditCopy(0), accelerator="(Ctrl+C)")
mnuRightClick.add_command(label="Paste", command=lambda: mnuEditPaste(0), accelerator="(Ctrl+V)")
mnuRightClick.add_separator()
mnuRightClick.add_command(label="Find...", command=lambda: mnuEditFind(0), accelerator="(Ctrl+F)")
mnuRightClick.add_command(label="Replace...", command=lambda: mnuEditReplace(0), accelerator="(Ctrl+R)")
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

def mnuEnable(fileOpened):
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

#def quickTheme(theme, e=None):
#    try:
#        root.set_theme(theme)
#    except:
#        pass

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
root.bind("<Control-Key-f>", mnuEditFind)
root.bind("<Control-Key-h>", mnuEditReplace)

# Status bar
statusBarRoot = Label(root, relief=SUNKEN)
Grid.columnconfigure(statusBarRoot, 2, weight=1) # Make at least 1 status bar field expand
#statusTheme = ttk.Combobox(statusBarRoot, values=THEMES)
#statusTheme.grid(column=0, row=0, padx=1, sticky=W+E)
statusBarCursor = Label(statusBarRoot, text="Coord", padx=5, pady=3, bd=1, relief=SUNKEN)
statusBarCursor.grid(column=1, row=0, padx=1, sticky=W+E)
statusBarFile = Label(statusBarRoot, text="CurrentFilename", padx=5, pady=3, bd=1, relief=SUNKEN)
statusBarFile.grid(column=2, row=0, padx=1, sticky=W+E)
# Maybe add another status indicator containing a progress bar for file Open/Save?
statusBar = Label(statusBarRoot, text="Status Bar", padx=5, pady=3, bd=1, relief=SUNKEN)
statusBar.grid(column=3, row=0, sticky=W+E)
#statusBarCursor.config(textvariable=editor_text.index(INSERT)) # Testing stuff

#statusTheme.bind("<<ComboboxSelected>>", lambda e:quickTheme(statusTheme.get()))

# Now we can add the status bar
statusBarRoot.pack(side=BOTTOM, fill=X)
editor_frame.pack(expand=TRUE, fill=BOTH)

#sqdb.commit()
#sqdb.close()

# Now we get to the meat and potatoes!
if __name__ == '__main__':
    detectHosts()
    #mnuDisableWhenEmpty(True)

    editor_text.focus()
    #editor_text.insert(END, font.families())
    root.mainloop()

# Message boxes
# showinfo, showwarning, showerror, askquestion, askokcancel, askyesno
