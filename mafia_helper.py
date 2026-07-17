import re
import sys
from pathlib import Path
import xml.etree.ElementTree as ET
import bisect
import random as r

# if you're curious how much I hate myself, the answer is yes
category_regex = r'\A[A-Z]*\d*\b' #r'(\AJAL\b|\ATI\d*\b|\ATK\d*\b|\ATP\d*\b|\ATS\d*\b|\ART\d*\b|\AGF\b|\ARM\d*\b|\ANK\d*\b|\ANC\d*\b|\ANE\d*\b|\ARN\d*\b|\ARNT\d*\b|\bANY\d*\b)'
jailor_regex = r"\AJailor\b"
TI_regex = r"\AInvestigator\b|\ALookout\b|\AScientist\b|\ATracker\b"
TK_regex = r"\AMedic\b|\ATrapper\b|\AVeteran\b|\AVigilante\b"
TP_regex = r"\AAlchemist\b|\ABodyguard\b|\ACleric\b|\ADoctor\b"
TS_regex = r"\AEscort\b|\AMedium\b|\ARetributionist\b|\ATransporter\b"
RT_regex = TI_regex + r"|" + TK_regex + r"|" + TP_regex + r"|" + TS_regex
mafia_regex = r"\ABlackmailer\b|\AConsigliere\b|\AConsort\b|\ACourier\b|\ADisguiser\b|\AGodfather\b|\AJanitor\b|\AMafioso\b|\AShapeshifter\b|\AStalker\b"
NK_regex = r"\AArsonist\b|\ASerial Killer\b|\AWerewolf\b"
NE_regex =  r"\ALifebinder\b|\ANecromancer\b|\AWitch\b"
NC_regex = r"\AAmnesiac\b|\AExecutioner\b|\AJester\b"
roles_regex = jailor_regex + r"|" + RT_regex + r"|" + mafia_regex + r"|" + NK_regex + r"|" + NE_regex + r"|" + NC_regex

# define priorities for various action keywords
# if an action keyword gets changed, it needs to be changed here and in the role(s) that utilizes it
action_dict = {
    "wiretapping" : {"priority" : 0,
                     "is_visit" : 0
    },
    "seancing" : {"priority" : 0,
                     "is_visit" : 0,
    },
    "activating" : {"priority" : 0, # *** I think this is more specific
                     "is_visit" : 0
    }, # this is listed alongside saves in the info doc, but it is treated as a transcendent/0 priority action
    "igniting" : {"priority" : 0,
                     "is_visit" : 0
    },
    "haunting" : {"priority" : 0,
                     "is_visit" : 0,
                     "max_targets" : 1
    },
    # ***Exe target switching
    "jailing" : {"priority" : 1,
                     "is_visit" : 1,
                     "max_targets" : 1
    },
    "alerting" : {"priority" : 2,
                     "is_visit" : 0
    },
    "transporting" : {"priority" : 3,
                     "is_visit" : 1,
                     "max_targets" : 2
    },
    "resolve_transporting" : {"priority" : 3.5,
                     "is_visit" : 0
    },
    "trapping" : {"priority" : 4,
                     "is_visit" : 1
    },
    "hallowing" : {"priority" : 5,
                     "is_visit" : 1,
                     "max_targets" : 1
    },
    "controlling" : {"priority" : 6,
                     "is_visit" : 1,
                     "max_targets" : 1
    },
    "blocking" : {"priority" : 7,
                     "is_visit" : 1,
                     "max_targets" : 1
    },
    "remembering" : {"priority" : 8,
                     "is_visit" : 0
    },
    "disguising" : {"priority" : 9,
                     "is_visit" : 1,
                     "max_targets" : 2
    },
    "determineAppearances" : {"priority" : 9.5,
                     "is_visit" : 0
    },
    "protecting" : {"priority" : 10,
                     "is_visit" : 1,
                     "max_targets" : 1
    },
    "saving" : {"priority" : 11,
                     "is_visit" : 1,
                     "max_targets" : 1
    },
    "self-saving" : {"priority" : 12,
                     "is_visit" : 0 
    },
    "drinking potion" : {"priority" : 12,
                     "is_visit" : 0
    },
    "delivering to" : {"priority" : 13,
                     "is_visit" : 1
    },
    "blessing" : {"priority" : 14,
                     "is_visit" : 0
    },
    "vesting" :{"priority" : 15,
                     "is_visit" : 0 
    },
    "dousing" : {"priority" : 16,
                     "is_visit" : 1
    },
    "blackmailing" : {"priority" : 17,
                     "is_visit" : 1,
                     "max_targets" : 1
    },
    'resolveBlackmails' : {"priority" : 17.5,
                     "is_visit" : 0
    },
    "investigating" : {"priority" : 18,
                     "is_visit" : 1,
                     "max_targets" : 1
    },
    "checking" : {"priority" : 19,
                     "is_visit" : 0,
                     "max_targets" : 1
    },
    "lifebinding" : 20,
    "killing" : {"priority" : 21,
                     "is_visit" : 1,
                     "max_targets" : 1
    }, 
    # leaving 22 for Mafioso killing, set in ***
    "cleaning" : {"priority" : 23,
                     "is_visit" : 1,
                     "max_targets" : 1
    },
    "stabbing" : {"priority" : 24,
                     "is_visit" : 1,
                     "max_targets" : 1
    },
    "mauling" : {"priority" : 25,
                     "is_visit" : 1,
                     "max_targets" : 1
    },
    "shooting" : {"priority" : 26,
                     "is_visit" : 1,
                     "max_targets" : 1
    },
    "executing" : {"priority" : 27,
                     "is_visit" : 0 
    },
    "hexing" : {"priority" : 28,
                     "is_visit" : 0, # ***
                     "max_targets" : 1 
    },
    "tracking" : {"priority" : 29,
                     "is_visit" : 1,
                     "max_targets" : 1
    },
    "watching" : {"priority" : 30,
                     "is_visit" : 1,
                     "max_targets" : 1
    },
    "stalking" : {"priority" : 31,
                     "is_visit" : 1,
                      "max_targets" : 1
    },
    "determineVisits" : {"priority" : 31.5,
                     "is_visit" : 0
    },
    "reviving" : {"priority" : 33,
                     "is_visit" : 0,
                     "max_targets" : 1
    },
    "attackEval" : 50
}

def startsWVowel(text):
    if(re.match(r'\A[AEIOUaeiou]',text)):
        return 1
    else:
        return 0

investigator_categories = [
    ["Jailor", "Scientist", "Bodyguard", "Godfather", "Arsonist", "Jester"],
    ["Medium", "Doctor", "Janitor", "Shapeshifter", "Serial Killer", "Amnesiac"],
    ["Lookout", "Tracker", "Medic", "Stalker", "Werewolf", "Executioner"],
    ["Investigator", "Veteran", "Vigilante", "Consigliere", "Mafioso", "Necromancer"],
    ["Transporter", "Alchemist", "Trapper", "Courier", "Disguiser", "Lifebinder"],
    ["Escort", "Retributionist", "Cleric", "Blackmailer", "Consort", "Witch"]
]

investigator_categories_dict = {}

for category in investigator_categories: # building the categories dictionary like this should mean all that ever needs to be changed is investigator_categories
    if(startsWVowel(category[0])):
        invest_result = "an"
    else:
        invest_result = "a"

    for i in range(len(category)):
        if (i != (len(category) - 1)):
            invest_result = invest_result + " " + category[i]
            invest_result = invest_result + ","
        else:
            invest_result = invest_result + " or " + category[i]
    
    for role in category:
        investigator_categories_dict[role] = invest_result   

#investigator_categories_dict = {
#    ("Jailor", "Scientist", "Bodyguard", "Godfather", "Arsonist", "Jester") : "a Jailor, Scientist, Bodyguard, Godfather, Arsonist, or Jester",
#    ("Medium", "Doctor", "Janitor", "Shapeshifter", "Serial Killer", "Amnesiac"): "a Medium, Doctor, Janitor, Shapeshifter, Serial Killer, or Amnesiac",
#    ("Lookout", "Tracker", "Medic", "Stalker", "Werewolf", "Executioner"): "a ",
#    ("", "", "", "", "", ""): "a ",
#    ("", "", "", "", "", ""): "a ",
#    ("", "", "", "", "", ""): "a ",
#}

role_class_dict = {
    "Jailor" : {"actions" : ["jailing"],
                "faction" : "Town",
                "perpetuated" : {"item" : ["cannot_execute", "executions"], 
                                 "default": [1, 3]}
    },

    "Investigator" : {"actions" : ["investigating"],
                "faction" : "Town"
    },

    "Lookout" : {"actions" : ["watching"],
                "faction" : "Town"
    },

    "Scientist" : {"actions" : ["checking"],
                "faction" : "Town"
    },

    "Tracker" : {"actions" : ["tracking"],
                "faction" : "Town"
    },

    "Alchemist" : {"actions" : ["delivering to"],
                "faction" : "Town"
    },

    "Bodyguard" : {"actions" : ["protecting"],
                "faction" : "Town"
    },

    "Cleric" : {"actions" : ["blessing"],
                "faction" : "Town"
    },

    "Doctor" : {"actions" : ["saving"],
                "faction" : "Town"
    },

    "Escort" : {"actions" : ["blocking"],
                "faction" : "Town",
                "immunities" : ["blocking"]
    },

    "Medium" : {"actions" : ["hallowing"],
                "faction" : "Town"
    },

    "Retributionist" : {"actions" : [], # Retri can only revive if there is a dead Townie
                "faction" : "Town"
    },

    "Transporter" : {"actions" : ["transporting"],
                "faction" : "Town"
    },

    "Medic" : {"actions" : ["saving"],
                "faction" : "Town"
    },

    "Trapper" : {"actions" : ["trapping"],
                "faction" : "Town"
    },

    "Veteran" : {"actions" : [],
                "faction" : "Town"
    },

    "Vigilante" : {"actions" : [],
                "faction" : "Town"
    },

    "Godfather" : {"actions" : ["killing"],
                "faction" : "Mafia",
                "immunities" : ["killing", "shooting", "stabbing"]
    },

    "Blackmailer" : {"actions" : ["blackmailing"],
                "faction" : "Mafia"
    },

    "Consigliere" : {"actions" : ["investigating"],
                "faction" : "Mafia"
    },

    "Consort" : {"actions" : ["blocking"],
                "faction" : "Mafia",
                "immunities" : ["blocking"]
    },

    "Courier" : {"actions" : ["transporting"],
                "faction" : "Mafia"
    },

    "Disguiser" : {"actions" : ["disguising"],
                "faction" : "Mafia",
                "perpetuated" : {"item" : ["active_disguise"], 
                                 "default": []}
    },

    "Janitor" : {"actions" : [],
                "faction" : "Mafia"
    },

    "Mafioso" : {"actions" : [],
                "faction" : "Mafia"
    },

    "Shapeshifter" : {"actions" : [],
                "faction" : "Mafia"
    },

    "Stalker" : {"actions" : ["stalking"],
                "faction" : "Mafia"
    },

    "Arsonist" : {"actions" : ["dousing"],
                "faction" : "NK"
    },

    "Serial Killer" : {"actions" : ["stabbing"],
                "faction" : "NK"
    },

    "Werewolf" : {"actions" : [],
                "faction" : "NK"
    },

    "Lifebinder" : {"actions" : ["binding"],
                "faction" : "non-Town"
    },

    "Necromancer" : {"actions" : [],
                "faction" : "non-Town"
    },

    "Witch" : {"actions" : ["controlling"],
                "faction" : "non-Town"
    },

    "Amnesiac" : {"actions" : ["remembering"],
                "faction" : "non-Town"
    },

    "Executioner" : {"actions" : [],
                "faction" : "non-Town"
    },

    "Jester" : {"actions" : [],
                "faction" : "non-Town"
    }
}

faction_dict = { # might add more to this, primarily just Town/non-Town distinguisher is needed in several cases
    "Town" : 1,
    "non-Town" : 2,
    "Mafia" : 3,
    "NK" : 4
}

# *** all the support code for reading/writing that is done in the other files should be placed as a f'n in this file instead
class game:
    def __init__(self, data_file, action_file = None, vote = None):
        if action_file is None: # init case (no action file)
             self.parseInitFile(data_file)
        
        else: # night evaluation case
            self.parseGameTree(data_file,vote)
            self.parseActionFile(action_file)
            # *** evaluate actions f'n
            self.evaluateActions()

    def parseInitFile(self, init_file):
        file = open(init_file, 'r')
        #self.filename = Path(setup_file).name 
        self.filename = re.sub(r"\.txt","",Path(init_file).name)
        self.filename = re.sub(r"\s","_",self.filename,)
        self.players = []
        self.categories = []

        player_num = 0
        while (True):
            current_line = file.readline() ## read next line in setup file
            if not current_line: ## break loop when file ends
                file.close()
                break

            # search for valid categories in current_line
            slot_search = re.search(category_regex, current_line)

            # verify that a valid slot has been identified
            if slot_search:
                slot_name = slot_search.group()

                # remove category from current_line string
                current_line = re.sub(category_regex+r'\s',"",current_line)

                # search for valid role in current line
                role_search = re.search(roles_regex, current_line)
                if not role_search:
                    sys.exit("Error, invalid role found: " + current_line)
                
                role_name = role_search.group()
                # remove role from current_line string
                current_line = re.sub(roles_regex,"",current_line)
                # the whitespace wouldn't play nice, had to remove it separately
                current_line = re.sub(r'\A\s',"",current_line)
                # remove newline character and assign to player_name
                player_name = re.sub(r'\n',"",current_line)

                self.players.append(player(player_name, player_num, role_name))
                player_num = player_num + 1
                self.categories.append(roleSlot(slot_name, role_name))
            # if text input does not contain a valid role category, exit with error
            else:
                sys.exit("Error, no valid role category detected in: " + current_line) 
    
    def parseGameTree(self, status_file,vote=None):
        gameTree = ET.parse(status_file)
        gameRoot = gameTree.getroot()
        self.filename = gameRoot.tag
        
        self.categories = []
        self.players = []

        num_living = 0
        GF_ind = -99

        for player_num, category in enumerate(gameRoot):
            slot_name = category.tag
            # idk should I validate the category slot? should i even validate the role? idc i'm lazy
                
            role_name = category.find('Role').text
            # Validate role
            role_search = re.search(roles_regex, role_name)
            if not role_search:
                sys.exit("Error, invalid role found: " + role_name)
            player_name = category.find('Player').text
            perpetuated_element = category.find('Perpetuated')

            if(vote == player_name): # vote input will kill whomever was voted that day ***haven't tested btw
                perpetuated_element.find("living_status").text = "0"
                # *** Godfather promotion needs to be able to occur here

            if(perpetuated_element.find("living_status").text == "1"):
                num_living = num_living + 1  
                if((role_name == 'Godfather')):
                    GF_ind = player_num # note which player is a living Godfather
                    # *** there needs to be logic here for dueling Mafias

            self.players.append(player(player_name, player_num, role_name, perpetuated_element))
            self.categories.append(roleSlot(slot_name, role_name))

        if(num_living > int(len(self.players) / 2)):
            if(GF_ind > 0):
                self.determineAvailableWiretaps(GF_ind)
    
    def parseActionFile(self, action_file):
        self.action_queue = []
        file = open(action_file, 'r')
        self.night_num = file.readline() # the first line of the action file should be the night number 
        self.night_num = re.sub(r"\n","",self.night_num)
        # should I verify this? Yes. Will I? No

        while (True):
            current_line = file.readline() # read next line
            if not current_line: # break loop when file ends
                file.close()
                break
            # *** anywhere I use re.match, I think I need to be using re.search
            if re.match(r"\A\d+\.", current_line): # Action lines should start with a number, i.e. "7. "
                # identify the player number from the action line and store as a number
                player_num = int(re.search(r"\A\d+", current_line).group()) - 1

                # remove the "#. " from the action text
                action_text = re.sub(r"\A\d+\.\s+","", current_line)

                if re.match(r"(?i)\A" + self.players[player_num].player_name, action_text):
                    action_text = re.sub(r"(?i)\A" + self.players[player_num].player_name,"", action_text)
                    self.queueActions(self.players[player_num], action_text)
                else:
                    sys.exit("Error parsing action file, line " + current_line + " does not begin with indicated player " + str(player_num+1) + ". " + self.players[player_num].player_name)
            else:
                print("Warning, cannot evaluate action due to incorrect format. Ignoring line: " + current_line)

        #for action in self.action_queue:
            #print(action.action)
            #print(action.priority)
            #print(action.targets)

    def queueActions(self, player, action_text): # this function parses action_text for actions that are possible given the input player,
    # creates an actionObject for each, and then adds that actionObject to game.action_queue
        action_text = re.sub(r"\n","",action_text) # remove any newline characters from action_text
        attempted_actions = 0
        if(len(player.action_keywords) > 0):
            all_actions_regex = player.action_keywords[0]

            if(len(player.action_keywords) > 1):
                for action_option in player.action_keywords[1:]:
                    all_actions_regex = all_actions_regex + r"|" + action_option

            while(action_text != ""):
                found = 0
                for option_num in range(len(player.action_keywords)): 
                    current_action_regex = r"\A\s"+player.action_keywords[option_num]+r"\s"
                    action_found = re.search(current_action_regex,action_text)
                    if(action_found): # \s needed so we are finding standalone keywords 
                        action_text = re.sub(action_found.group(), "", action_text) # remove found action from text
                        current_action = re.sub(r"\A\s|\s\Z","",action_found.group())
                        
                        attempted_actions = attempted_actions + 1
                        found = 1
                        
                        if attempted_actions > player.max_actions:
                            sys.exit("Error, too many actions attempted for " + player.player_name)
                        
                        #print(action_text)
                        if(re.search(r".+\s(" + all_actions_regex + r")\s",action_text)): # there is at least one more action
                            targetting_text = re.sub(r",\s(" + all_actions_regex + r").+", "", action_text) # remove the next action and everything after
                            action_text = re.sub(r"\A" + targetting_text + ",","",action_text)
                        else:
                            targetting_text = action_text
                            action_text = re.sub(r"\A" + targetting_text,"",action_text) # remove targetting_text from action_text
                        
                        # determine targets
                        targets = []
                        # *** taking multiple actions does not work, need to fix
                        #print(targetting_text)
                        num_commas = len(re.findall(",",targetting_text))
                        if (num_commas > 0): # 3 or more targets
                            for target_num in range(num_commas + 1):
                                targets.append(re.search(r"\A[a-zA-Z]+",targetting_text).group())
                                if(target_num <= num_commas):
                                    targetting_text = re.sub(r"\A[a-zA-Z]+,\s","",targetting_text)
                        elif (re.search(r"\sand\s", targetting_text)): # two targets
                            targets.append(re.search(r"\A[a-zA-Z]+",targetting_text).group())
                            targetting_text = re.sub(r"\A[a-zA-Z]+\sand\s","",targetting_text)
                            targets.append(re.search(r"\A[a-zA-Z]+",targetting_text).group())
                        else: # single target
                            targets.append(targetting_text)
                        # *** I think I need a "no targets" case here, also Scientist
                        if(len(targets) > player.max_targets[option_num]):
                            sys.exit("Too many targets selected for " + player.player_name + " (" + current_action + "), maximum of " + str(player.max_targets[option_num]) + " target(s).")
                        
                        player.actions.append(actionObject(current_action, action_dict[current_action]["priority"], player, targets))
                        self.action_queue.append(player.actions[-1]) # queue action
                        # ***I don't know if it's logically possible to find an action that doesn't have a queue IF the action regex and action priority
                        # dicts are up to date, but I should probably add error checking anyways
                        break # break from for loop if action has been found at start of string
                
                if found == 0: # error case for looping through entire set of action options and not finding one in the text
                    sys.exit("No valid option found in: " + action_text)

        #else: # *** idk if I need this or not
            #print("This player apparently has no action options? " +player.role.role + " " + player.player_name) # *** might make this an error idk

    def evaluateActions(self):  
        self.public_announcements = []
        self.indeterminant = []
        self.attacks = []
        self.disguise_nodes = []
        # *** I think targetting is screwed up because of the player_locations list now being a copy. That should just be made a list with player nums
        # action queue pre-processing
        if any(action_obj.action == 'disguising' for action_obj in self.action_queue):
            self.action_queue.append(actionObject('determineAppearances', action_dict['disguising']['priority'] + .1))
        
        # variables use to designate if action objects used for cleaning up action resolution have been queue'd or not
        blackmailing = 0 
        observing = 0
        transporting = 0

        self.action_queue.sort(key = lambda x: x.priority) # sort action queue by priority
        self.player_locations = [player.player_num for player in self.players] # list that holds player_num and is shifted by Transporters
        
        for action_obj in self.action_queue:
            if action_obj.is_visit:
                for i in range(len(action_obj.targets)):
                    action_obj.targets[i] = self.targetText2PlayerNum(action_obj.targets[i])
                    #target_inds.append(self.targetText2PlayerNum(action_obj.targets[i])) 
                    #if (isinstance(action_obj.targets[i],str)): # for blocks I've done some replacing of the targets with their index numbers already. 
                        # *** Instead of this, I should just do all of this ahead of time in the same place, probably. Are there issues with that?
                        #target_inds.append(self.targetText2PlayerNum(action_obj.targets[i])) 
                    #else:
                        #target_inds.append(action_obj.targets[i])

                    if "alerting" in self.players[action_obj.targets[i]].action_keywords: # *** this needs to be tested
                        # *** I think this has issues cancelling multi-target actions
                        # an alerting player can never be transported, so using self.players list directly
                        # *** attackEval needs to be adjusted for the case of a Bodyguard protecting someone killed by Vet 
                        if(self.players[action_obj.targets[i]].alerting == 1):
                            action_obj.player.perpetuated["living_status"] = 0 # *** needs to be made an attack and resolved accordingly
                            action_obj.player.notifications.append("You were killed by an alerting Veteran!\nWill?\n")
                            action_obj.cancelled = 1

        while(self.action_queue): 
            action_obj = self.action_queue[0]
            target_inds = []
            
            if not action_obj.cancelled:
                if action_obj.is_visit:
                    for i in range(len(action_obj.targets)):
                        target_inds.append(action_obj.targets[i])
                        self.getTargetPlayer(target_inds[i]).visitors.append(action_obj.player)
                # *** need to implement immunities               
                match (action_obj.action):
                    # *** one line actions resolved here, more complex ones resolved in standalone f'ns
                    case 'jailing': 
                        self.players[target_inds[0]].jailed = 1
                        # sets cannot_execute from 1 to 0 for the next night. Code has already verified against an illegal execution
                        # by not adding "executing" to jailorClass' action keywords when initialized
                        action_obj.player.cannot_execute = 0 
                        #print(self.players[target_inds[0]].player_name)
                        #print(self.players[target_inds[0]].role.jailed)

                        #print(self.players[target_inds[0]].role.jailed)
                        #print(self.players[target_inds[0]].player_name)
                        #print(self.players[target_inds[0]].role.visitors)
                    case 'transporting':
                        transporting = self.findResolutionObj(action_obj, target_inds, transporting)
                        #self.players[target_inds[0]].transported.append(self.players[target_inds[1]])
                        #self.players[target_inds[1]].transported.append(self.players[target_inds[0]])
                    case 'resolve_transporting':
                        cancel_list = []
                        for remaining_action in self.action_queue:
                            if(type(remaining_action.priority) is int):
                                if (remaining_action.action == "blocking") | (remaining_action.action == "controlling"):
                                    cancel_list.append(remaining_action)
                                elif (remaining_action.priority > action_dict["blocking"]["priority"]):
                                    break     
                        self.resolveTransports(cancel_list, action_obj)
                    case 'killing':
                        self.getTargetPlayer(target_inds[0]).attackers.append(action_obj)
                        if(self.getTargetPlayer(target_inds[0]) not in self.attacks):
                            self.attacks.append(self.getTargetPlayer(target_inds[0]))
                    
                    case 'blocking':
                        self.resolveBlock(self.getTargetPlayer(target_inds[0]))

                    case 'disguising':
                        # *** need to determine if a new disguise is disrupting non-detereminant old diguises
        
                        # (don't want call to determineAppearances to shuffle non-determinant chains that haven't changed)
                        for old_disguise in action_obj.player.perpetuated["active_disguise"]: # should only do anything if there was an active disguise already
                            old_ind = self.targetText2PlayerNum(old_disguise)
                            self.players[old_ind].perpetuated["disguises"].remove(action_obj.player)
                        # *** need to implement functionality of being unable to kill your disguise target night-of. Probably introduct faction attributes
                        action_obj.player.perpetuated["active_disguise"] = [self.getTargetPlayer(target_inds[0]), self.getTargetPlayer(target_inds[1])]
                        
                        self.getTargetPlayer(target_inds[0]).perpetuated["disguises"].append(self.getTargetPlayer(target_inds[1]))
                        self.getTargetPlayer(target_inds[1]).perpetuated["disguises"].append(self.getTargetPlayer(target_inds[0]))

                        #if (len(self.action_queue) > 1):
                        #    self.action_queue.insert(queue_ind + 1, actionObject('determineAppearance', action_dict["disguising"]["priority"] + .5, player = self.players[target_inds[0]]))
                        #elif(self.action_queue[queue_ind + 1].action != "disguising"):
                        #    self.action_queue.insert(queue_ind + 1, actionObject('determineAppearance', action_dict["disguising"]["priority"] + .5, player = self.players[target_inds[0]]))
                            # *** idk I think there are probably a million better ways to do this
                            # this basically needs to run on each set of nodes (not implemented yet)
                    case 'determineAppearances': # *** I need appearance to be perpetuated and only call this if a new disguise happens
                        self.determineAppearances() # *** have determineAppearance include target
                    case 'blackmailing':
                        for remaining_action in self.action_queue: # *** this needs thorough testing
                            if  remaining_action.action[0] == "resolveBlackmails":
                                remaining_action.player.append(action_obj.player)
                                remaining_action.targets.append(target_inds[0])
                                blackmailing = 1
                                break

                        if blackmailing == 0:
                            self.action_queue.append(actionObject("resolveBlackmails", action_obj.priority, [action_obj.player], targets = [target_inds[0]]))
                    case 'resolveBlackmails': 
                        self.resolveBlackmails(action_obj)

                    case 'investigating':
                        if action_obj.player.role_name == "Investigator":
                            if(self.getTargetPlayer(target_inds[0]).perpetuated["doused_by"] == 1):
                                result = investigator_categories_dict["Arsonist"]
                            else:
                                result = investigator_categories_dict[self.getPlayerAppearance(self.getTargetPlayer(target_inds[0]),"role")]

                        elif action_obj.player.role_name == "Consigliere":
                            if(self.getTargetPlayer(target_inds[0]).perpetuated["doused_by"] == 1):
                                result = "Arsonist"
                            else:
                                result = self.getPlayerAppearance(self.getTargetPlayer(target_inds[0]),"role")
                            
                            if startsWVowel(result):
                                result = "an " + result
                            else:
                                result = "a " + result

                        action_obj.player.notifications.append("Your target is " + result + "!")
                    case 'checking':
                        result = ""
                        for category in self.categories:
                            if category.slot_name == action_obj.targets[0]:
                                result = category.role_name
                        if (result):
                            action_obj.player.notifications.append(action_obj.targets[0] + " is " + result + "!")
                        else:
                            sys.exit(action_obj.targets[0] + " not found in role list for player: " + action_obj.player.player_name)
                    case 'watching' | 'tracking' | 'stalking':
                        for remaining_action in self.action_queue: # *** this needs thorough testing
                            if  remaining_action.action == "determineVisits":
                                remaining_action.priority.append(action_obj.priority)
                                remaining_action.player.append(action_obj.player)
                                remaining_action.targets.append(target_inds[0])
                                observing = 1
                                break

                        if observing == 0:
                            self.action_queue.append(actionObject("determineVisits", [action_obj.priority], [action_obj.player], targets = [target_inds[0]]))
                    case 'determineVisits':
                        self.determineVisits(action_obj)
                    case 'wiretapping':
                        for target in target_inds:
                            self.players[target].notifications.append("You were wiretapped!")
                    case _:
                        print("Action defaulted")
                
            self.action_queue.pop(0)
        
        # *** need to write resolution to attacks
        # *** this should probably go to a separate function?
        # *** I might try to put this back into the action queue system idk
        if(self.attacks): # if attacks list is populated with any attacks
            for attacked_player in self.attacks:
                attacked_player.attackers.sort(key = lambda x: x.priority) # sort attackers by priority
                num_attackers = len(attacked_player.attackers)
                num_protectors = len(attacked_player.protectors)

                if(num_protectors):
                    attacked_player.protectors.sort(key = lambda x: x.priority) # sort protectors by priority
                    
                atk_prio_index = -1 # indices are used to determine how many attackers/protectors have the lowest priority value (i.e should be prioritized)
                prot_prio_index = -1
                # I structure this list with a while loop and popping, in contrast to the action_queue. Primarily the popping here 
                # allows me to keep the prio indices easily by assuming the attacks start at index 0... 
                # will have to do something if I merge this back into the action_queue
                while(num_attackers > 0): # go through each attack until there are none remaining. attacks removed from list when resolved
                    if(num_protectors > 0):
                        indet = 0 # should only have indeterminancies if there are protectors (***or shields I guess.......)
                        # I don't think we need to track either index if there are no protectors left so this can go under the num_protectors if statement
                        if atk_prio_index == -1: # when all attacks of the lowest priority are exhausted (or at start), this should be -1
                            atk_prio_index = 0 # set to 0 since there will be at least one (at index [0]) attack of this priority
                            if(num_attackers > 1):
                                for atk in attacked_player.attackers[1:]:
                                    if atk.priority == attacked_player.attackers[0].priority:
                                        atk_prio_index = atk_prio_index + 1 # add 1 to value for every priority matching the attack at [0]
                                    else:
                                        break
                        if (prot_prio_index == -1): # does the same thing for protectors
                            prot_prio_index = 0
                            if(num_protectors > 1):
                                for prot in attacked_player.protectors[1:]:
                                    if prot.priority == attacked_player.protectors[0].priority:
                                        prot_prio_index = prot_prio_index + 1
                                    else:
                                        break

                        # randomize which attack/save is chosen among those of the same priority
                        if(atk_prio_index > 0):
                            chosen_attack = r.randint(0,atk_prio_index)
                            indet = 1
                        else:
                            chosen_attack = 0

                        if(prot_prio_index > 0):
                            chosen_protection = r.randint(0,prot_prio_index)
                            indet = 1
                        else:
                            chosen_protection = 0

                        # let the Narrator know that an indeterminancy took place
                        if indet == 1:
                            atk_options = attacked_player.attackers[0].player.player_name
                            prot_options = attacked_player.protectors[0].player.player_name
                            for i in range(1,atk_prio_index):
                                atk_options = atk_options + ", " + attacked_player.attackers[i].player.player_name
                            for i in range(1,prot_prio_index):
                                prot_options = prot_options + ", " + attacked_player.protectors[i].player.player_name
                            self.indeterminant.append(attacked_player.player.player_name + ": " 
                                                      + attacked_player.attackers[chosen_attack].player.player_name + "(Options: " + atk_options + ") stopped by " 
                                                      + attacked_player.attackers[chosen_protection].player.player_name + "(Options: " + prot_options + ")")
                        
                        # ***TO DO here: 
                        # Do the particular resolving of the TP roles and relevant notifications
                        # pop chosen attacker from attacker list and decrement num_attackers
                        # pop chosen protector from protector list and decrement num_protectors

                    else: # no protectors remaining
                        if(attacked_player.jailed == 1):
                            attacked_player.notifications.append("Someone tried to attack you but you were in jail!")
                            attacked_player.attackers[0].player.notifications.append("You failed to kill your target!") # *** idk that this is given to WWs
                        elif(attacked_player.attackers[0].action in attacked_player.immunities):
                            attacked_player.notifications.append("Someone tried to attack you but you are immune!")
                            attacked_player.attackers[0].player.notifications.append("You failed to kill your target!")
                        else:
                            print(attacked_player.attackers[0].player.player_name + " is attacking " + attacked_player.player_name)
                            match (attacked_player.attackers[0].action):
                                case 'killing':
                                    attacked_player.notifications.append("You were killed by a member of the Mafia!")
                                    death_string = "killed by a member of the Mafia"
                                case _: # default case, shouldn't happen
                                    death_string = ""
                                    print("Warning, no valid killing action identified in: " + attacked_player.attackers[0].action)
                            attacked_player.notifications.append("Will?")
                            attacked_player.perpetuated["living_status"] = 0

                            # *** can modify this text to include "the" for unique roles. If I'm not lazy
                            death_string = attacked_player.player_name + " died last night. He/She was " + death_string + ". He/She was "
                            appearance = self.getPlayerAppearance(attacked_player,"role")
                            
                            if(startsWVowel(appearance)):
                                death_string = death_string + "an "
                            else:
                                death_string = death_string + "a "
                            death_string = death_string + appearance + "."
                        
                            self.public_announcements.append(death_string)

                        attacked_player.attackers.pop(0)
                        num_attackers = num_attackers - 1
    
    def writeNotifications(self, notifications_file):
        notifications_file.write(self.night_num + " Results\n")
        notifications_file.write("Public Notifications:\n")
        for noti in self.public_announcements:
            notifications_file.write(noti + "\n")

        notifications_file.write("__________________\n")

        for player_num, player in enumerate(self.players):
            notifications_file.write(str(player_num + 1) + ". " + player.player_name + "\n")              
            for noti in player.notifications:
                notifications_file.write(noti + "\n")

        notifications_file.write("__________________\n")
        notifications_file.write("Indeterminancies:\n")
        for indet in self.indeterminant:
            notifications_file.write(indet + "\n")

    ## Helper Functions for Game Class
    def findResolutionObj(self, action_obj, target_inds, resolution_exists): # *** need to go back and use this for BM and such. plus target_inds usage change
        action_obj.targets = target_inds # here we do overwrite the actual target text with the target index, but this action is 
        # being discarded elsewhere anyways so it's fine
        
        queue_here = 1
        for queue_ind, remaining_action in enumerate(self.action_queue): # *** this needs thorough testing
            if  remaining_action.action == "resolve_" + action_obj.action:
                
                remaining_action.player.append(action_obj)
                resolution_exists = 1
                break
            elif (type(remaining_action.priority) is int):
                if(remaining_action.priority == action_obj.priority):
                    queue_here = queue_ind + 1

        if resolution_exists == 0:
            self.action_queue.insert(queue_here, actionObject("resolve_" + action_obj.action, action_obj.priority, [action_obj]))
            resolution_exists = 1

        return resolution_exists # should always be 1, but better not to hard code it I suppose

    def resolveBlock(self, target):
        # *** yea I think this doesn't work (because popping and for loops)
        target.notifications.append("You were roleblocked!")

        for queue_ind, remaining_action in enumerate(self.action_queue):
            if remaining_action.player is target:
                self.action_queue.pop(queue_ind)

    def resolveBlackmails(self, action_obj):
        new_blackmails = []
        for bm_target in action_obj.targets:
            if self.getTargetPlayer(bm_target).perpetuated["blackmail_immune"] == 1:
                self.getTargetPlayer(bm_target).notifications.append("Someone tried to blackmail you, but you were blackmailed the previous night!") # *** Check phrasing
                # *** don't know if technically you regain blackmail immunity when someone tries and fails or not
            else:
                self.getTargetPlayer(bm_target).notifications.append(
                "You were blackmailed!\n\n" \
                "You cannot speak, except for saying, 'I am blackmailed,' exactly once.\n" \
                "You may not vote, you may only abstain, but you cannot use your abstain to communicate information.")

                new_blackmails.append(self.getTargetPlayer(bm_target))
        for player in self.players: # *** this needs to be tested once multiple nights are supported
            player.perpetuated["blackmail_immune"] = 0 # remove all the blackmail immunities from previous night
        
        for new_bm in new_blackmails:
            new_bm.perpetuated["blackmail_immune"] = 1 # assign blackmail immunities to targets affected on current night

    def determineAvailableWiretaps(self, GF_ind):
        num_mafia_living = 1
        for player_ind, player in enumerate(self.players):
                if((re.search("RM",self.categories[player_ind].slot_name) != None) & (player.perpetuated["living_status"] == 1)):
                    num_mafia_living = num_mafia_living + 1

        self.players[GF_ind].addAction("wiretapping", num_mafia_living)
        self.players[GF_ind].max_actions += 1
    
    def determineVisits(self, action_obj):
        night_visits = {}
        determined_night_visits = {} # I believe this could be made more memory efficient by not using 
        # determined_night_visits and removing from night_visits once a determination has been made
        # idk about speed efficiency. also idc that much probably

        for obs_ind, player in enumerate(action_obj.player):
            if ((action_obj.priority[obs_ind] == action_dict["watching"]["priority"])  # Lookout stuff
                | (action_obj.priority[obs_ind] == action_dict["stalking"]["priority"])): 
                visitors = self.getTargetPlayer(action_obj.targets[obs_ind]).visitors.copy()
                visitors.remove(player) # remove self from visit list

                num_visitors = len(visitors)
                if num_visitors == 0:
                    result = "wasn't visited by anyone" # *** need to check this phrasing
                elif num_visitors == 1:
                    result = "was visited by " + self.getPlayerAppearance(visitors[0], "name")
                else:
                    result = "was visited by"
                    for visitor_ind in range(num_visitors):
                        if visitor_ind == (num_visitors - 1):
                            result = result + " and " + self.getPlayerAppearance(visitors[visitor_ind], "name")
                        else:
                            result = result + " " + self.getPlayerAppearance(visitors[visitor_ind], "name") 
                            if num_visitors > 2:
                                result = result + ","
                
                result = "Your target " + result + "!"
                player.notifications.append(result)

            if ((action_obj.priority[obs_ind] == action_dict["tracking"]["priority"]) # tracker stuff
                | (action_obj.priority[obs_ind] == action_dict["stalking"]["priority"])): 
                if not (night_visits):
                    # construct dict of all night visits with the visitor's player_num as the key and the 
                    # visited players' player_num in a list as the value
                    for playa in self.players: # I am already using "player" in the overall for loop. Don't judge me
                        for visitor in playa.visitors:
                            night_visits.setdefault(visitor.player_num, []).append(playa.player_num)  
                    all_visits = [visit for visitor in list(night_visits.values()) for visit in visitor]

                tracked_target = self.getPlayerAppearance(self.getTargetPlayer(action_obj.targets[obs_ind])) # disguises swap who is effectively being tracked
                
                # obtain "result" where result is the player_num of the player that the target is tracked to
                if(tracked_target.player_num in determined_night_visits):
                    result = determined_night_visits[tracked_target.player_num]

                else:
                    if (tracked_target.player_num in night_visits): # case where the apparent target did make a visit
                        if (len(night_visits[tracked_target.player_num]) == 1):
                            result = night_visits[tracked_target.player_num][0]
                        
                        else: # (len(night_visits[tracked_target.player_num]) > 1)
                            result = r.choice(night_visits[tracked_target.player_num]) # randomly determine which visit the Tracker sees
                            determined_night_visits[tracked_target.player_num] = result # once a target has been randomly determined, any
                            # tracks should return the same result

                            # *** can implement functionality for evil players choosing their tracked target here
                            indet_string = ("Random Tracker results for " + action_obj.player[obs_ind].player_name
                                + " tracking " + self.getTargetPlayer(action_obj.targets[obs_ind]).player_name 
                                + ", " + self.players[result].player_name 
                                + " chosen. (Options: " + self.players[result].player_name
                            )
                            
                            for visit in night_visits[tracked_target.player_num]:
                                if visit != result:
                                    indet_string += ", " + self.players[visit].player_name
                            indet_string += ")"
                            self.indeterminant.append(indet_string) # tell Narrator that an indeterminancy occured
                    
                    else: # if the apparent target did not visit, pull randomly from all the night's visits
                        result = r.choice(all_visits)
                        determined_night_visits[tracked_target.player_num] = result

                        indet_string = ("Random Tracker results for " + action_obj.player[obs_ind].player_name
                                + " tracking " + self.getTargetPlayer(action_obj.targets[obs_ind]).player_name 
                                + ", " + self.players[result].player_name 
                                + " chosen from list of all visits tonight."
                                )
                        self.indeterminant.append(indet_string)

                player.notifications.append("Your target visited " + self.players[result].player_name + "!")

                if(self.getTargetPlayer(action_obj.targets[obs_ind]).faction >= faction_dict["Mafia"]):
                    self.getTargetPlayer(action_obj.targets[obs_ind]).notifications.append("You were tracked! They saw you visit "
                        + self.players[result].player_name + ".")

    def getPlayerAppearance(self, player, use_case = None):
        if (use_case == "role"):
            return self.players[player.perpetuated["appearance"]].role_name
        elif (use_case == "name"):
            return self.players[player.perpetuated["appearance"]].player_name
        else:
            return self.players[player.perpetuated["appearance"]]
     
    def targetText2PlayerNum(self, target): # finds where a target (passed as string) is in the player list
        target_location = -99
        for location_ind, player in enumerate(self.players):
            if (player.player_name == target):
                target_location = location_ind

        if(target_location == -99): # I don't think this can even happen
            sys.exit("Target not found in player list: " + target)
        return target_location
    
    def getTargetPlayer(self, target_ind): # takes the target_ind (int) and uses it to index player_locations, which indexes players
        return self.players[self.player_locations[target_ind]]
    
    def getTargetPlayerAbs(self, target_ind): # I might never use this, probably just easier to do it directly.
        return self.players[target_ind] 
    
    # Helper Functions for Role Actions
    def resolveTransports(self, cancel_list, resolve_obj): # *** block and control logic needs to be implemented
        num_players = len(self.players)
        eval_obj = transportEvalList(cancel_list, resolve_obj, num_players)
        # transportEvalList class creates lists with blocks_and_controls in the index location of their target and 
        # transport objects in the location index of the transporter  

        for i in range(num_players): 
            # check for transporters that have a cancellation on their location and are not being transported. Cancel their actions first. 
            if (eval_obj.cancel_list[i]) and (eval_obj.transporters_list[i]) and (not eval_obj.affected_locations[i]): #  # eval_obj.transporters_list[eval_obj.locations[i]]
                #if not(eval_obj.affected_locations[i]):
                #transp_player_num = eval_obj.locations[i]
                #transp_player_obj = self.players[transp_player_num]
                transp_action_obj = eval_obj.transporters_list[eval_obj.locations[i]]
                # Notifications
                if(eval_obj.cancel_list[i].action == "blocking"): # *** we need to go and remove all the block/control objects from action_queue. ugh
                    transp_action_obj.player.notifications.append("You were roleblocked!")
                elif(eval_obj.cancel_list[i].action == "controlling"):
                    transp_action_obj.player.notifications.append("You were controlled by a Witch!")

                # remove this cancellation object from cancellations list
                eval_obj.cancel_list[i] = None

                # remove transporter from visits list of the targets
                for visit in eval_obj.transporters_list[eval_obj.locations[i]].targets:
                    self.players[visit].visitors.remove(transp_action_obj.player)
                    
                # remove the other target from the transported list of the target
                #self.players[transp_action_obj.targets[0]].transported.remove(self.players[transp_action_obj.targets[1]])
                #self.players[transp_action_obj.targets[1]].transported.remove(self.players[transp_action_obj.targets[0]])

                # remove this transporter from the transporters list
                eval_obj.transporters_list[eval_obj.locations[i]] = None
                #eval_obj.transporters_list[i] = None
  
        # *** notification logic needs to be implemented
        #node_list = []
        transport_nodes = self.buildTransportNodes(eval_obj.transporters_list) 
        locations_wc = self.player_locations.copy()
        nodes_to_eval = [1] * len(transport_nodes)
        nxt_nodes_to_eval = [0] * len(transport_nodes)
        while any(node_status == 1 for node_status in nodes_to_eval):
            for node_ind, node_status in enumerate(nodes_to_eval):
                if node_status == 1:
                    nxt_nodes_to_eval[node_ind] = 0

                    node_set = transport_nodes[node_ind]["transports"]
                    for location in node_set:
                        locations_wc[location] = self.player_locations[location]
                    
                    swap_node_list = [swap_node for swap_node in node_set if (node_set[swap_node] == 1)]       
                    r.shuffle(swap_node_list)
                    num_swaps = len(swap_node_list)
                    
                    for ind in range(num_swaps - 1):
                        locations_wc[swap_node_list[ind]] = swap_node_list[ind + 1]
                    locations_wc[swap_node_list[num_swaps - 1]] = swap_node_list[0]
   
                    for transported_player_num in node_set:
                        if eval_obj.transporters_list[transported_player_num] and eval_obj.cancel_list[locations_wc.index(transported_player_num)]:
                            for set_eval_ind, eval_node in enumerate(transport_nodes):
                                #print(self.players[transported_player_num])
                                if(self.players[transported_player_num] in eval_node["transporters"]):
                                    #print(self.players[transported_player_num])
                                    #print(node_ind)
                                    #print(set_eval_ind)
                                    nxt_nodes_to_eval[set_eval_ind] = 1
                                    self.players[transported_player_num].blocked = 1 # *** might use if to set block or control idc rn 
                                    eval_node["cancellations"].append(eval_obj.transporters_list[transported_player_num])
                    #print(node_set)
                    #print(nxt_nodes_to_eval[node_ind])
            print("1")
            print(transport_nodes)
            for node_ind, node_status in enumerate(nodes_to_eval):
                # modify node for any changes, see if it needs split
                # isolate transporters in this node, re-build nodes and see if a split occured
                for cancelled_node in transport_nodes[node_ind]["cancellations"]:
                    print(node_ind)
                    t0 = cancelled_node.targets[0]
                    t1 = cancelled_node.targets[1]
                    # A transporter whose targets both are only transported once means the node is removed
                    if transport_nodes[node_ind]["transports"][t0] == 1 & transport_nodes[node_ind]["transports"][t1] == 1: 
                        locations_wc[t0] = self.player_locations[t0]
                        locations_wc[t1] = self.player_locations[t1]
                        nxt_nodes_to_eval[node_ind] = 2 # use 2 to say that the node needs to be removed
                        # *** When a node dissolves, we need to check if any transporters were in that node and mark the respective nodes if they're blocked
                        # *** this is not done, need to actually remove the transport from the node it's in
                        for target in transport_nodes[node_ind]["transports"]:
                            if eval_obj.transporters_list[target] and eval_obj.cancel_list[target]:
                                for node_ind2, node_set in enumerate(transport_nodes): 
                                    if eval_obj.transporters_list[target].player in node_set["transporters"]:
                                        #print(node_ind2)
                                        # *** can I make this all way cleaner by linking player objects to action objects?
                                        nxt_nodes_to_eval[node_ind2] = 1
                                        eval_obj.transporters_list[target].player.blocked = 1
                                        print(eval_obj.transporters_list[target].player.player_name)
                                        transport_nodes[node_ind2]["transports"][eval_obj.transporters_list[target].targets[0]] -= 1
                                        if transport_nodes[node_ind2]["transports"][eval_obj.transporters_list[target].targets[0]] == 0:
                                            transport_nodes[node_ind2]["transports"].pop(eval_obj.transporters_list[target].targets[0], None)
                                            locations_wc[eval_obj.transporters_list[target].targets[0]] = self.player_locations[eval_obj.transporters_list[target].targets[0]]

                                        transport_nodes[node_ind2]["transports"][eval_obj.transporters_list[target].targets[1]] -= 1
                                        if transport_nodes[node_ind2]["transports"][eval_obj.transporters_list[target].targets[1]] == 0:
                                            transport_nodes[node_ind2]["transports"].pop(eval_obj.transporters_list[target].targets[1], None)
                                            locations_wc[eval_obj.transporters_list[target].targets[1]] = self.player_locations[eval_obj.transporters_list[target].targets[1]]
                                        #print(transport_nodes[node_ind2]["transporters"])
                                        #print(eval_obj.transporters_list[target].player)
                                        transport_nodes[node_ind2]["transporters"].remove(eval_obj.transporters_list[target].player)
                    # if only one target is transported exclusively by the cancelled transporter, just remove that target 
                    # and the transporter
                    elif transport_nodes[node_ind]["transports"][t0] == 1:
                        #print("1.5")
                        #print(transport_nodes[node_ind])
                        locations_wc[t0.player_num] = self.player_locations[t0]
                        transport_nodes[node_ind]["transports"].pop(t0, None)
                        transport_nodes[node_ind]["transports"][t1] -= 1
                        transport_nodes[node_ind]["transporters"].remove(cancelled_node)
                    elif transport_nodes[node_ind]["transports"][t1] == 1:
                        
                        locations_wc[t1.player_num] = self.player_locations[t1]
                        transport_nodes[node_ind]["transports"].pop(t1, None)
                        transport_nodes[node_ind]["transports"][t0] -= 1
                        transport_nodes[node_ind]["transporters"].remove(cancelled_node)

                    # if both targets are transported by multiple transporters, a split may need to occur
                    elif transport_nodes[node_ind]["transports"][t0] > 1 & transport_nodes[node_ind]["transports"][t0] > 1: 
                        transport_nodes[node_ind]["transports"][t0] -= 1
                        transport_nodes[node_ind]["transports"][t1] -= 1
                        transport_nodes[node_ind]["transporters"].pop(cancelled_node, None)
                        transp_inds = [transporter for transporter in transport_nodes[node_ind]["transporters"]]
                        new_nodes = self.buildTransportNodes([eval_obj.transporters_list[i] for i in transp_inds])
                        if (new_nodes[0] != transport_nodes[node_ind]):
                            transport_nodes[node_ind] = new_nodes[0]
                            transport_nodes.append(new_nodes[1])
                            nxt_nodes_to_eval.append(1)
                    else: # this case shouldn't happen but is included to catch errors
                        sys.exit("Error in transporter node removal")

            num_nodes = len(nxt_nodes_to_eval)
            transport_nodes = [transport_nodes[i] for i in range(num_nodes) if nxt_nodes_to_eval[i] != 2]
            nodes_to_eval = [nxt_nodes_to_eval[i] for i in range(num_nodes) if nxt_nodes_to_eval[i] != 2]
            nxt_nodes_to_eval[:] = [0] * len(nodes_to_eval)
            print("2")
            print(transport_nodes)
        self.player_locations = locations_wc.copy()
        print(self.player_locations)
        for i in range(num_players):
            if(self.players[self.player_locations[i]].blocked == 1 and not eval_obj.cancel_list[i]):
                self.players[self.player_locations[i]].notifications.append("You were transported into a block!")

    def buildTransportNodes(self, transporters_list):
        transport_nodes = []
        for transport in transporters_list:
            if(transport): # index is None if no transport is occuring
                t0 = transport.targets[0]
                t1 = transport.targets[1]
                transporter = transport.player
                #if (transport_nodes):
                in_node = 0
                for node in transport_nodes:
                    if (t0 in node["transports"]) | (t1 in node["transports"]):
                        node["transports"][t0] = node["transports"].get(t0, 0) + 1
                        node["transports"][t1] = node["transports"].get(t1, 0) + 1
                        node["transporters"].append(transporter)
                        in_node = 1
                        break
                if in_node == 0:
                    transport_nodes.append({"transports" : {t0: 1, t1: 1}, "transporters" : [transporter], "cancellations" : []})
                #else:
                    
        return transport_nodes        

    def determineAppearances(self): # *** I should generalize this function so I can use it for transports and disguises
        # *** this needs to determine if any pre-existing chains have been impacted
        # go through all players 
        # a player's chain needs evaluated if:
        # they are disguised with one other person, but appear as themselves
        # they are disguised with multiple people, but do not appear as themselves
        # they are not disguised, but do not appear as themselves
        # if a player does not need to be evaluated, remove from list
        # if a player does need to be evaluated, evaluate all connected players in chain.
        # for each connected player, remove them from the list to be evaluated later
        players_to_check = self.players.copy()
        while(players_to_check):
            self.node_dict = {} 
            needs_evaluated = 0
            # build nodes
            self.buildNodes(players_to_check[0],"disguise") # recursively fill out all connected nodes
            # loop will remove all connected players before iterating again, eventually hitting all players
            for player_num in self.node_dict:
                players_to_check.remove(self.players[player_num])
                if(needs_evaluated == 0):
                    if (
                    (((self.node_dict[player_num] == 0) | (self.node_dict[player_num] >= 2)) & (self.players[player_num].perpetuated["appearance"] != player_num)) |
                    ((self.node_dict[player_num] == 1) & (self.players[player_num].perpetuated["appearance"] == player_num)) 
                    ):                                 
                        needs_evaluated = 1
            if (needs_evaluated):
                swap_node_list = [swap_node for swap_node in self.node_dict if (self.node_dict[swap_node] == 1)]    

                r.shuffle(swap_node_list)
                num_swaps = len(swap_node_list)
                for ind in range(num_swaps - 1):
                    self.players[swap_node_list[ind]].perpetuated["appearance"] = swap_node_list[ind + 1]
                self.players[swap_node_list[(num_swaps - 1)]].perpetuated["appearance"] = swap_node_list[0]

                for swap_node in swap_node_list:
                    print(self.players[swap_node].player_name + " is appearing as " + self.players[self.players[swap_node].perpetuated["appearance"]].player_name)

        
        #self.buildAppearanceNodes(action_obj.player) # recursively fill out all connected nodes

        #swap_node_list = [swap_node for swap_node in self.node_dict if (self.node_dict[swap_node] == 1)]    

        #r.shuffle(swap_node_list)
        #num_swaps = len(swap_node_list)
        #for ind in range(num_swaps - 1):
        #    self.players[swap_node_list[ind]].role.appearance = swap_node_list[ind + 1]
        #self.players[swap_node_list[(num_swaps - 1)]].role.appearance = swap_node_list[0]

        #for swap_node in swap_node_list:
            #print(self.players[swap_node].role.appearance)
        #    print(self.players[swap_node].player_name + " is appearing as " + self.players[self.players[swap_node].role.appearance].player_name)

    def buildNodes(self, node, node_type):
    ##############################################################################################################################
    # Function: buildNodes
    # Class: game
    # in: 
    #   game self
    #   player node: player object to be evaluated
    #   str node_type: either "disguise" or "transport" to determine where to look for connected nodes. This function handles
    #   both because the algorithm is the same. 
    # out: 
    #   None
    # Description:
    #   Adds the node's player_num attribute to self.node_dict as a key and a value equal to the number of disguises/transports
    #   active on the target. If a connected node is not yet in node_dict, it calls this function for that node, so the result
    #   of calling this function on any node is to add all connected nodes to self.node_dict. 
    ##############################################################################################################################
        if node_type == "disguise":
            connected_nodes = node.perpetuated["disguises"]
        elif node_type == "transport": # *** Unused
            connected_nodes = node.transported
        else:
            sys.exit("Improper node_type for function buildNodes")

        self.node_dict[node.player_num] = len(connected_nodes)
            
        for c_node in connected_nodes:
            if(c_node.player_num not in self.node_dict):
                self.buildNodes(c_node, node_type)

## Object Definitions for Use in Game Class
class actionObject:
    def __init__(self, action, priority, player = None,  targets = None):
        self.action = action
        self.player = player
        self.priority = priority
        self.targets = targets
        self.is_visit = action_dict[self.action]["is_visit"]
        self.cancelled = 0

class transportEvalList:
    def __init__(self, cancel_list, resolution_obj, num_players):
        self.cancel_list = [None] * num_players
        self.transporters_list = [None] * num_players
        self.cancellation_notice_list = [None] * num_players
        for cancellation in cancel_list:
           self.cancel_list[cancellation.targets[0]] = cancellation # target is in a list     

        self.affected_locations = [0] * num_players
        for transport in resolution_obj.player:
            self.transporters_list[transport.player.player_num] = transport # *** Currently this does not support Necro using multiple transports on the same night
            for target in transport.targets: 
                self.affected_locations[target] = 1
            
        self.locations = [i for i in range(num_players)]

    #def swapLocations(self, )
        

class roleSlot:
    def __init__(self, slot_name, role_name):
        self.slot_name = slot_name
        self.role_name = role_name
             
class player:  
    def __init__(self, player_name, player_num, role_name,  perpetuated_element = None):   
        self.player_name = player_name

        # non-perpetuated class variables for evaluating night actions
        self.actions = []
        self.attackers = []
        self.blocked = 0
        self.controlled = 0
        self.immunities = []
        self.jailed = 0
        self.player_num = player_num # *** I might want to use player_num instead of passing players/names in a lot of places
        self.protectors = []
        self.role_name = role_name
        #self.transported = []
        self.visitors = []
        self.wiretapped = 0
        self.notifications = []

        # role-dependent variables
        self.faction = 0 
        self.action_keywords = [] 
        self.max_actions = 0
        self.max_targets = []

        #self.appearance = self # used to assess disguises

        # perpetuated class variables for evaluating night actions
        if(perpetuated_element):
            self.perpetuated = {
                "appearance" : int(perpetuated_element.find("appearance").text),
                "blackmail_immune" : int(perpetuated_element.find("blackmail_immune").text),
                "disguises" : self.readListFromXML(perpetuated_element.find("disguises").text), 
                "doused_by" : self.readListFromXML(perpetuated_element.find("doused_by").text),
                "living_status" : int(perpetuated_element.find("living_status").text),
                "potions" : int(perpetuated_element.find("potions").text)
            }
        else:
            self.perpetuated = {
                "appearance" : self.player_num,
                "blackmail_immune" : 0,
                "disguises" : [], 
                "doused_by" : [],
                "living_status" : 1,
                "potions" : 0
            }

        if(self.perpetuated["potions"] > 0):
            self.addAction("drinking potion") #*** need to verify this is correct lol
            self.max_actions = 1

        if("perpetuated" in role_class_dict[self.role_name]):
            self.updatePerpetuated(perpetuated_element)

        if("immunities" in role_class_dict[self.role_name]):
            for immunity in role_class_dict[self.role_name]["immunities"]:
                self.immunities.append(immunity) 

        match (role_name):
            case 'Jailor':
                if(self.perpetuated["cannot_execute"] | (self.perpetuated["executions"] < 1)):
                    self.addAction("jailing")
                    self.max_actions = 1
                else:
                    self.addAction("jailing")
                    self.addAction("executing")
                    self.max_actions = 2

            case _:
                for static_action in role_class_dict[self.role_name]["actions"]:
                    self.addAction(static_action)
                    self.max_actions += 1

    ## Role Class Helper Functions
    def updatePerpetuated (self, perpetuated_element):
    ##############################################################################################################################
    # Function: updatePerpetuated
    # Class: player
    # in:
    #   player self
    #   ET.Element perpetuated_element: XML Tree Element corresponding to a player's "perpetuated" tag in XML status doc. Used to 
    #   track role information across nights. If perpetuated_element is None, the player is being initialized. 
    # out:
    #   None
    # Description: 
    #   Use role_class_dict for the given role name to iterate through all expected items on the perpetuated list. 
    #   Pull data from the perpetuated_element if it exists, otherwise set to default from role_class_dict. 
    ##############################################################################################################################
        for elem_ind, expected_elem in enumerate(role_class_dict[self.role_name]["perpetuated"]["item"]):
            if(perpetuated_element):
                if(type(role_class_dict[self.role_name]["perpetuated"]["default"][elem_ind]) is int):
                    self.perpetuated[expected_elem] = int(perpetuated_element.find(expected_elem).text)
                else:
                    self.perpetuated[expected_elem] = self.readListFromXML(perpetuated_element.find(expected_elem).text)
            
            else:
                self.perpetuated[expected_elem] = role_class_dict[self.role_name]["perpetuated"]["default"][elem_ind]

    def readListFromXML(self, text):
        # takes XML data for a list stored as a string (i.e. "[1, 2, 3]") and re-constructs the list
        out_list = []
        iter = 0
        if(not re.match(r"\[\]",text)):
            text = re.sub(r"\[","",text)
            text = re.sub(r"\]","",text)
            while(re.match(r",\s",text)):
                entry = re.search(r"(\A[A-Za-z0-9]+),\s",text).group(1)
                out_list.append(entry)
                text = re.sub(r"\A[A-Za-z]+,\s","",text)

                iter = iter + 1
                if(iter >= 100):
                    sys.exit("Error in readListFromXML, can't exit while loop")
            out_list.append(text)
        return out_list

    def addAction(self, action_keyword, max_targets = 0):
        self.action_keywords.append(action_keyword)
        if("max_targets" in action_dict[action_keyword]):
            self.max_targets.append(action_dict[action_keyword]["max_targets"])
        else:
            self.max_targets.append(max_targets) # variable max_targets can be input to addAction
        
        
