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
# *** Variable naming convention in this file is not correct
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
if(len(sys.argv) >= 2):
    vote_target = sys.argv[1]
else:
    vote_target = None
gameVar = game(statusFile,actionFile, vote_target)

# Make directory for output data
Path("MafiaHelper Out").mkdir(exist_ok=True)
Path("MafiaHelper Out\\" + gameVar.filename + "\\").mkdir(exist_ok=True)
Path("MafiaHelper Out\\" + gameVar.filename + "\\" + "Night " + str(gameVar.night_num) + "\\").mkdir(exist_ok=True)
savePath = str(Path.cwd()) + "\\MafiaHelper Out\\" + gameVar.filename + "\\" + "Night " + str(gameVar.night_num) + "\\"
#print(savePath)
#evaledXMLFile = open(savePath + gameVar.filename + gameVar.night_num + " evaled status.xml",'w')
# *** Do I need to somehow specify that the file should be overwritten?
notificationsFile = open(savePath + gameVar.filename + " " + "Night " + str(gameVar.night_num) + " notifications.txt",'w')
gameVar.writeNotifications(notificationsFile)

# write to eval'd status XML file
gameElement = ET.Element(gameVar.filename)
gameTree = ET.ElementTree(gameElement)

nightElement = ET.Element("Night")
nightElement.text = str(gameVar.night_num)
gameElement.append(nightElement)

num_players = len(gameVar.players)
for i in range(num_players):
    slotElement = ET.Element(gameVar.categories[i].slot_name)
    gameElement.append(slotElement)

    roleElement = ET.Element("Role")
    slotElement.append(roleElement)
    roleElement.text = gameVar.categories[i].role_name

    playerNameElement = ET.Element("Player")
    slotElement.append(playerNameElement)
    playerNameElement.text = gameVar.players[i].player_name

    perpetuatedElements = ET.Element("Perpetuated")
    slotElement.append(perpetuatedElements)

    #initStatusFile.write(gameVar.categories[i].slot_name + " " + gameVar.categories[i].role_name + " " + gameVar.players[i].player_name)

    for key, value in gameVar.players[i].perpetuated.items():
        #initStatusFile.write("\n" + str(gameVar.players[i].role.perpetuated_labels[j]) + ": " + str(gameVar.players[i].role.perpetuated_info[j]))
        #dataElement = ET.Element(str(gameVar.players[i].role.perpetuated_labels[j]))

        #dataElement.text = (str(gameVar.players[i].role.perpetuated_info[j]))
        dataElement = ET.Element(key)
        dataElement.text = str(value)
        perpetuatedElements.append(dataElement)

# *** Add construction of remainder of game tree here or wherever else really
ET.indent(gameTree,'    ')
gameTree.write(savePath + gameVar.filename + " evaled status.xml", method = 'xml') 

# write to notifications file
# *** Add writing to notifications file
notificationsFile.close()