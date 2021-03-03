# HostsManager
GUI application to manage merging various different sources of HOSTS files

Developing this on Ubuntu Linux using VSCode.  This project uses Avalonia MVVM/ReactiveUI.
The goal of this project is to design an app that can import several HOSTS lists so as to combat ads.

The hostsman.py included here is a way for me to rapid prototype the C# app.  For now, this is the only really fully functional version.  MVVM makes my head spin.  If someone wants to teach that to me in relation to a C# Editor project, I'm willing to go 1 on 1 with them (English only).

Common locations for Hosts file lists:

https://pgl.yoyo.org/adservers/
https://winhelp2002.mvps.org/hosts.htm
https://github.com/StevenBlack/hosts

URLs suitable for importing into the Sort/Merge feature for the above:
https://pgl.yoyo.org/adservers/serverlist.php?hostformat=hosts&showintro=1&mimetype=plaintext
https://winhelp2002.mvps.org/hosts.txt
https://raw.githubusercontent.com/StevenBlack/hosts/master/alternates/gambling-porn/hosts
