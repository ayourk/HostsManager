# HostsManager
GUI application to manage merging various different sources of HOSTS files

Developing this on Ubuntu Linux using VSCode.  This project uses Avalonia MVVM/ReactiveUI.
The goal of this project is to design an app that can import several HOSTS lists so as to combat ads.

The hostsman.py included here is a way for me to rapid prototype the C# app.  For now, this is the only really fully functional version.  MVVM makes my head spin.  If someone wants to teach that to me in relation to a C# Editor project, I'm willing to go 1 on 1 with them (English only).

Common locations for Hosts file lists:

https://pgl.yoyo.org/adservers/<br>
https://winhelp2002.mvps.org/hosts.htm<br>
https://github.com/StevenBlack/hosts

URLs suitable for importing into the Sort/Merge feature for the above:<br>
https://pgl.yoyo.org/adservers/serverlist.php?hostformat=hosts&showintro=1&mimetype=plaintext<br>
https://winhelp2002.mvps.org/hosts.txt<br>
https://raw.githubusercontent.com/StevenBlack/hosts/master/alternates/gambling-porn/hosts

This program allows you to import, merge, and sort different sources of HOSTS lists and trim out duplicates.  This program is a text editor first and HOSTS file manager second.  There may still be a few bugs but I use this app without issue for my needs.
