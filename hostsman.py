from tkinter import *
from tkinter import filedialog
from tkinter import messagebox
from tkinter import scrolledtext as st
import sqlite3

root = Tk()
root.title("Hosts File Manager")
#root.iconbitmap("/path/to/file.ico")
root.geometry("800x600")

def mnuFileOpen():
    root.fileopen = filedialog.askopenfilename(initialdir="/", title="Open a Hosts file") # filetypes=(("file type name", "*"))

    # fileOpen.destroy()

def mnuFileMerge():
    root.fileopen = filedialog.askopenfilename(initialdir="/", title="Merge Hosts file") # filetypes=(("file type name", "*"))

    # fileOpen.destroy()

def mnuFileSave():
    root.filesafe = filedialog.asksaveasfilename(initialdir="/", title="Save Hosts file") # filetypes=(("file type name", "*"))
    # SaveFile via hostsBox.get()

def mnuFileExit():
    response = messagebox.askyesno("Quit?", "Are you sure you want to quit?")
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
mnuFile.add_command(label="Open", command=mnuFileOpen)
mnuFile.add_command(label="Merge", command=mnuFileMerge)
mnuFile.add_command(label="Save", command=mnuFileSave)
mnuFile.add_separator()
mnuFile.add_command(label="Exit", command=mnuFileExit)

mnuEdit = Menu(myMenu)
myMenu.add_cascade(label="Edit", menu=mnuEdit)
mnuEdit.add_cascade(label="Cut", command=mnuEditCut)
mnuEdit.add_cascade(label="Copy", command=mnuEditCopy)
mnuEdit.add_cascade(label="Paste", command=mnuEditPaste)

mainEditor = PanedWindow(bd=4, relief="sunken", bg="gray")

hostsBox = st.ScrolledText(root, wrap="word") #, anchor="nsew")
hostsBox.pack() #anchor="center")








# Status bar (label)
statusBar = Label(root, text="Status Bar", padx=5, pady=5, bd=1, relief=SUNKEN)
statusBar.pack(anchor=S)

sqdb.commit()
sqdb.close()

# Icon file?

root.mainloop()

# Message boxes
# showinfo, showwarning, showerror, askquestion, askokcancel, askyesno