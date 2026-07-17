from mafia_helper import *
import collections
import fileinput
import sys
import os.path
from pathlib import Path
import tkinter as tk
from tkinter import filedialog

root = tk.Tk()
root.withdraw()

#gameFile = Path(filedialog.askopenfilename())
#while gameFile.suffix is not ".txt" | gameFile.is_file != True | gameFile is None:
#gameFile = filedialog.askopenfilename(filetypes=[("Text Files", ".txt")])
#if not gameFile:
#    sys.exit
# I think I should either make a UI or just create a file structure, idk
statusFile = filedialog.askopenfilename(filetypes=[("XML Files", ".XML")])
if not statusFile: ## user opts not to select a file
    print("No status file selected. Ending program.")
    sys.exit()

actionFile = filedialog.askopenfilename(filetypes=[("Text Files", ".txt")])
if not actionFile: ## user opts not to select a file
    print("No action file selected. Ending program.")
    sys.exit()

##*** Check if file is formatted properly
# initialize game object, where all data is stored
gameVar = game(statusFile,actionFile)

# Make directory for output data
Path("MafiaHelper Out").mkdir(exist_ok=True)
Path("MafiaHelper Out\\" + gameVar.filename + "\\").mkdir(exist_ok=True)
Path("MafiaHelper Out\\" + gameVar.filename + "\\" + gameVar.night_num + "\\").mkdir(exist_ok=True)
savePath = str(Path.cwd()) + "\\MafiaHelper Out\\" + gameVar.filename + "\\" + gameVar.night_num + "\\"
#print(savePath)
#evaledXMLFile = open(savePath + gameVar.filename + gameVar.night_num + " evaled status.xml",'w')
# *** Do I need to somehow specify that the file should be overwritten?
notificationsFile = open(savePath + gameVar.filename + " " + gameVar.night_num + " notifications.txt",'w')
gameVar.writeNotifications(notificationsFile)

# write to eval'd status XML file
gameElement = ET.Element(gameVar.filename)
gameTree = ET.ElementTree(gameElement)
# *** Add construction of remainder of game tree here or wherever else really
ET.indent(gameTree,'    ')
gameTree.write(savePath + gameVar.filename + " evaled status.xml", method = 'xml') 

# write to notifications file
# *** Add writing to notifications file
notificationsFile.close()