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

gameFile = filedialog.askopenfilename(filetypes=[("Text Files", ".txt")])
if not gameFile: ## user opts not to select a file
    print("No file selected. Ending program.")
    sys.exit()
#    gameFilePath = Path(gameFile)
#    if gameFilePath.is_file() is False: ## re-prompt user for file that exists
#         print('Error: Choose an existing .txt file')
#    elif gameFilePath.suffix != ".txt": ## re-prompt user for file with .txt extension
#        print('Error: Choose .txt file')
#    else:
#        break
##*** Check if file is formatted properly
# initialize game object, where all data is stored
gameVar = game(gameFile)

# Make directory for output data
Path("MafiaHelper Out").mkdir(exist_ok=True)
Path("MafiaHelper Out\\" + gameVar.filename + "\\").mkdir(exist_ok=True)
Path("MafiaHelper Out\\" + gameVar.filename + "\\" + "init\\").mkdir(exist_ok=True)
savePath = str(Path.cwd()) + "\\MafiaHelper Out\\" + gameVar.filename + "\\" + "init\\"
#print(savePath)
#initStatusFile = open(savePath + gameVar.filename + " initial status.txt",'w')
initXMLFile = open(savePath + gameVar.filename + " initial status.xml",'w')
initActionsFile = open(savePath + gameVar.filename + " actions template.txt",'w')
numPlayers = len(gameVar.categories)

#
gameElement = ET.Element(gameVar.filename)
gameTree = ET.ElementTree(gameElement)
#gameTree.append(gameElement)

initActionsFile.write("Night X")
for i in range(numPlayers):
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
    
    #if(i < numPlayers-1):
       #initStatusFile.write("\n\n")

    initActionsFile.write("\n" + str(i+1) + ". " + gameVar.players[i].player_name)

ET.indent(gameTree,'    ')
gameTree.write(savePath + gameVar.filename + " initial status.xml", method = 'xml')    
initXMLFile.close()
#initStatusFile.close()
initActionsFile.close()
##gameFile = sys.argv[1,:]

##gameVar = game(gameFile) ## Place setup text file here

