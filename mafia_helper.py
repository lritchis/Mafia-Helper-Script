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
                     "is_visit" : 0,
                     "targeted" : 1
    },
    "seancing" : {"priority" : 0,
                     "is_visit" : 0,
                     "targeted" : 1
    },
    "activating" : {"priority" : 0, # *** I think this is more specific
                     "is_visit" : 0
    }, # this is listed alongside saves in the info doc, but it is treated as a transcendent/0 priority action
    "igniting" : {"priority" : 0,
                     "is_visit" : 0,
                     "targeted" : 0
    },
    "haunting" : {"priority" : 0,
                     "is_visit" : 0,
                     "max_targets" : 1,
                     "targeted" : 0
    },
        "reviving" : {"priority" : 0, # *** reviving can't be blocked, so it should be 0 priority
                     "is_visit" : 0,
                     "max_targets" : 1,
                     "targeted" : 1
    },
    # ***Exe target switching
    "jailing" : {"priority" : 1,
                     "is_visit" : 1,
                     "max_targets" : 1,
                     "targeted" : 1
    },
    "alerting" : {"priority" : 2,
                     "is_visit" : 0,
                     "targeted" : 0
    },
    "transporting" : {"priority" : 3,
                     "is_visit" : 1,
                     "max_targets" : 2,
                     "targeted" : 1
    },
    "resolve_transporting" : {"priority" : 3.5,
                     "is_visit" : 0,
                     "targeted" : 0
    },
    "trapping" : {"priority" : 4,
                     "is_visit" : 1,
                     "max_targets" : 2,
                     "targeted" : 1
    },
    "trapping_atk" : {"priority" : 4,
                         "is_visit" : 0,
                         "targeted" : 0
        },
    "hallowing" : {"priority" : 5,
                     "is_visit" : 1,
                     "max_targets" : 1,
                     "targeted" : 1
    },
    "controlling" : {"priority" : 6,
                     "is_visit" : 1,
                     "max_targets" : 1,
                     "targeted" : 1,
                     "hallow_cancels" : 1
    },
    "blocking" : {"priority" : 7,
                     "is_visit" : 1,
                     "max_targets" : 1,
                     "targeted" : 1
    },
    "remembering" : {"priority" : 8,
                     "is_visit" : 0,
                     "targeted" : 0
    },
    "disguising" : {"priority" : 9,
                     "is_visit" : 1,
                     "max_targets" : 2,
                     "targeted" : 1,
                     "hallow_cancels" : 1
    },
    "resolve_disguising" : {"priority" : 9.5,
                     "is_visit" : 0,
                     "targeted" : 0
    },
    "protecting" : {"priority" : 10,
                     "is_visit" : 1,
                     "max_targets" : 1,
                     "targeted" : 1
    },
    "counterattacking" : {"priority" : 10, # used to create Bodyguard counterattack 
                             "is_visit" : 0,
                             "targeted" : 0
            },
    "sacrificing" : {"priority" : 10, # used to create the attack on Bodyguards 
                         "is_visit" : 0,
                         "targeted" : 0
        },
    "saving" : {"priority" : 11,
                     "is_visit" : 1,
                     "max_targets" : 1,
                     "targeted" : 1
    },
    "self-saving" : {"priority" : 12,
                     "is_visit" : 0,
                     "targeted" : 0 
    },
    "drinking potion" : {"priority" : 12,
                     "is_visit" : 0,
                     "targeted" : 0
    },
    "delivering to" : {"priority" : 13,
                     "is_visit" : 1,
                     "targeted" : 1
    },
    "blessing" : {"priority" : 14,
                     "is_visit" : 0,
                     "targeted" : 0
    },
    "vesting" :{"priority" : 15,
                     "is_visit" : 0,
                     "targeted" : 0 
    },
    "dousing" : {"priority" : 16,
                     "is_visit" : 1,
                     "targeted" : 1
    },
    "blackmailing" : {"priority" : 17,
                     "is_visit" : 1,
                     "max_targets" : 1,
                     "targeted" : 1,
                     "hallow_cancels" : 1
    },
    'resolve_blackmailing' : {"priority" : 17.5,
                     "is_visit" : 0,
                     "targeted" : 0
    },
    "investigating" : {"priority" : 18,
                     "is_visit" : 1,
                     "max_targets" : 1,
                     "targeted" : 1
    },
    "investigating_exact" : {"priority" : 18,
                         "is_visit" : 1,
                         "max_targets" : 1,
                         "targeted" : 1,
                         "hallow_cancels" : 1
    },
    "checking" : {"priority" : 19,
                     "is_visit" : 0,
                     "max_targets" : 1,
                     "targeted" : 0
    },
    "binding" : {"priority" : 20,
                         "is_visit" : 1,
                         "max_targets" : 2,
                         "targeted" : 1,
                         "hallow_cancels" : 1
                },
    "shooting" : {"priority" : 21,
                         "is_visit" : 1,
                         "max_targets" : 1,
                         "targeted" : 1
        },
    "killing" : {"priority" : 22,
                     "is_visit" : 1,
                     "max_targets" : 1,
                     "targeted" : 1
    }, 
    # leaving 22 for Mafioso killing, set in ***
    "cleaning" : {"priority" : 23,
                     "is_visit" : 1,
                     "max_targets" : 1,
                     "targeted" : 1,
                     "hallow_cancels" : 1
    },
    "stabbing" : {"priority" : 24,
                     "is_visit" : 1,
                     "max_targets" : 1,
                     "targeted" : 1
    },
    "mauling" : {"priority" : 25,
                     "is_visit" : 1,
                     "max_targets" : 1,
                     "targeted" : 1
    },
    "mauling_visitor" : {"priority" : 26,
                         "is_visit" : 0,
                         "targeted" : 0
        },
    
    "executing" : {"priority" : 27,
                     "is_visit" : 0,
                     "targeted" : 0
    },
    "hexing" : {"priority" : 28,
                     "is_visit" : 0, # ***
                     "max_targets" : 1,
                     "targeted" : 1
    },
    "tracking" : {"priority" : 29,
                     "is_visit" : 1,
                     "max_targets" : 1,
                     "targeted" : 1
    },
    "watching" : {"priority" : 30,
                     "is_visit" : 1,
                     "max_targets" : 1,
                     "targeted" : 1
    },
    "stalking" : {"priority" : 31,
                     "is_visit" : 1,
                      "max_targets" : 1,
                     "targeted" : 1,
                     "hallow_cancels" : 1
    },
    "resolve_observing" : {"priority" : 31.5,
                         "is_visit" : 0,
                         "targeted" : 0
        },
    "determineVisits" : {"priority" : [],
                     "is_visit" : 0,
                     "targeted" : 0
    },
    "attackEval" : 50
}

death_message_dict = {
    "alerting" : "killed by an alerting Veteran",
    "trapping_atk" : "killed by a Trapper",
    "sacrificing" : "died protecting someone", # for use to set BG's message
    "counterattacking" : "killed by a Bodyguard", # *** verify
    "protecting" : "killed by a Bodyguard", # *** not sure this is right
    "killing" : "killed by a member of the Mafia",
    "shooting" : "shot by a member of the Town",
    "stabbing" : "stabbed by a Serial Killer",
    "mauling" : "mauled by the Werewolf",
    "igniting" : "ignited by an Arsonist",
    "binding" : "life-bound to someone that died",
    "hexing" : "hexed by a Necromancer",
    "executing" : "executed by the Jailor"
}

# some inefficiency but means I don't have to have these listed in the correct order, just in case
# *** do I need mauling_visitor here? I don't actually know
atk_actions = ["killing", "alerting", "trapping_atk", "sacrificing", "counterattacking", "shooting",  "stabbing", "mauling"]
atk_priority = [action_dict[atk]["priority"] for atk in atk_actions]
atk_actions = [atk for _, atk in sorted(zip(atk_priority, atk_actions))]
atk_state_map = {}
for priority_ind, atk in enumerate(atk_actions):
    atk_state_map[priority_ind] = atk
    atk_state_map[atk] = priority_ind # this feels really weird but seems the best way to do it? Both directions are used
num_atk_states = len(atk_actions)

# define attack characteristics flag: 0bABC
# A is 1 if the attack is direct, 0 if indirect
# B is 1 if it is stopped by Night Immunity or vest, 0 if not
# C is 1 if is not stopped by an NE shield, 0 if it is (this one done counter-intuitively because of the negation on the condition)
atk_flags = {
    "killing" : 0b110,
    "alerting" : 0b001,
    "trapping_atk" : 0b001,
    "sacrificing" : 0b001,
    "counterattacking" : 0b001,
    "shooting" : 0b111,
    "stabbing" : 0b110,
    "mauling" : 0b100
}

# *** vesting should not be a defense state, the action should create a night immune attribute
defense_actions = ["protecting", "saving", "self-saving", "blessing"] # *** saving and activating have the same priority. Activating needs to queue object as a save
defense_priority = [action_dict[defense]["priority"] for defense in defense_actions]
defense_actions = [defense for _, defense in sorted(zip(defense_priority, defense_actions))]
defense_state_map = {}
for priority_ind, defense in enumerate(defense_actions):
    defense_state_map[priority_ind] = defense
    defense_state_map[defense] = priority_ind
num_defense_states = len(defense_actions)

def startsWVowel(text):
    if(re.match(r'\A[AEIOUaeiou]',text)):
        return 1
    else:
        return 0

investigator_categories = [
    #["Jailor", "Scientist", "Bodyguard", "Godfather", "Arsonist", "Jester"],
    #["Medium", "Doctor", "Janitor", "Shapeshifter", "Serial Killer", "Amnesiac"],
    ["Scientist", "Bodyguard", "Shapeshifter", "Arsonist", "Jester"],
    ["Medium", "Doctor", "Janitor", "Serial Killer", "Amnesiac"],
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

role_class_dict = {
    "Jailor" : {"actions" : ["jailing"],
                "faction" : "Town",
                "perpetuated" : {"cannot_execute" : 1, "executions" : 3}
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
                "faction" : "Town",
                "perpetuated" : {"self-hallow" : 1}
    },

    "Retributionist" : {"actions" : ["reviving"], # *** May eventually want to place conditionals on this, idk
                "faction" : "Town"
    },

    "Transporter" : {"actions" : ["transporting"],
                "faction" : "Town"
    },

    "Medic" : {"actions" : ["saving"],
                "faction" : "Town",
                "perpetuated" : {"save" : 1, "self-save" : 1, "shots" : 1}
    },

    "Trapper" : {"actions" : ["trapping"],
                "faction" : "Town",
                "perpetuated" : {"num_traps" : 2, "traps_landed" : set()}
    },

    "Veteran" : {"actions" : [],
                "faction" : "Town",
                "perpetuated" : {"alerts" : 3,"vests" : 1}
    },

    "Vigilante" : {"actions" : [],
                "faction" : "Town",
                "perpetuated" : {"shots" : 3}
    },

    "Godfather" : {"actions" : ["killing"],
                "faction" : "Mafia",
                "night_immune" : 1
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
                "perpetuated" : {"active_disguise" : [-1, -1]}
    },

    "Janitor" : {"actions" : [],
                "faction" : "Mafia",
                "perpetuated" : {"cleans" : 3}
    },

    "Mafioso" : {"actions" : [],
                "faction" : "Mafia",
                "perpetuated" : {"shot" : 1}
    },

    "Shapeshifter" : {"actions" : [],
                "faction" : "Mafia",
                "perpetuated" : {"action" : 1}
    },

    "Stalker" : {"actions" : ["stalking"],
                "faction" : "Mafia"
    },

    "Arsonist" : {"actions" : ["dousing"],
                "faction" : "NK",
                "night_immune" : 1,
                "perpetuated" : {"douses" : [], "first_douse" : 1} # *** douses can be a set
    },

    "Serial Killer" : {"actions" : ["stabbing"],
                "faction" : "NK",
                "night_immune" : 1,
    },

    "Werewolf" : {"actions" : [],
                "faction" : "NK",
                "night_immune" : 1
    },

    "Lifebinder" : {"actions" : ["binding"],
                "faction" : "NE",
                "perpetuated" : {"shield" : 1}
    },

    "Necromancer" : {"actions" : [],
                "faction" : "NE",
                "perpetuated" : {"shield" : 1}
    },

    "Witch" : {"actions" : ["controlling"],
                "faction" : "NE",
                "perpetuated" : {"shield" : 1}
    },

    "Amnesiac" : {"actions" : ["remembering"],
                "faction" : "non-Town",
                "perpetuated" : {"shield" : 1}
    },

    "Executioner" : {"actions" : [],
                "faction" : "non-Town",
                "perpetuated" : {"switch" : 1, "target" : None}
    },

    "Jester" : {"actions" : [],
                "faction" : "non-Town"
    }
}

faction_dict = { # might add more to this, primarily just Town/non-Town distinguisher is needed in several cases
    "Town" : 1,
    "non-Town" : 2,
    "NE" : 3,
    "Mafia" : 4,
    "NK" : 5
}

# *** all the support code for reading/writing that is done in the other files should be placed as a f'n in this file instead
class game:
    def __init__(self, data_file, action_file = None, vote_target = None):
        if action_file is None: # init case (no action file)
             self.parseInitFile(data_file)
        
        else: # night evaluation case
            self.parseGameTree(data_file,vote_target)
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

                # ***
                #if role_name == "Executioner":
                #    target_name = re.match(r'\(target\s([A-Za-z]+)\)',player_name).group()[0] # ***
                #    player_name = re.sub(r'\(target\s([A-Za-z]+)\)',"",player_name)

                self.players.append(player(player_name, player_num, role_name))
                player_num = player_num + 1
                self.categories.append(roleSlot(slot_name, role_name))
            # if text input does not contain a valid role category, exit with error
            else:
                sys.exit("Error, no valid role category detected in: " + current_line) 
    
    def parseGameTree(self, status_file,vote_target = None):
        gameTree = ET.parse(status_file)
        gameRoot = gameTree.getroot()
        self.filename = gameRoot.tag
        
        self.categories = []
        self.players = []
        # will add 1 for every Townie found. Compared to a logical condition for finding the last Townie this is easier and should be just as efficient
        self.num_town = 0 
        self.living_medium = 0

        num_living = 0
        GF_ind = -99

        self.night_num = int(gameRoot.find('Night').text) + 1

        for player_num, category in enumerate(gameRoot[1:]):
            slot_name = category.tag
            # idk should I validate the category slot? should i even validate the role? idc i'm lazy
                
            role_name = category.find('Role').text
            # Validate role
            role_search = re.search(roles_regex, role_name)
            if not role_search:
                sys.exit("Error, invalid role found: " + role_name)
            player_name = category.find('Player').text
            perpetuated_element = category.find('Perpetuated')

            if(vote_target == player_name): # vote input will kill whomever was voted that day ***haven't tested btw
                perpetuated_element.find("living_status").text = "0"
                # *** Godfather promotion needs to be able to occur here

            if(perpetuated_element.find("living_status").text == "1"):
                num_living = num_living + 1  
                if((role_name == 'Godfather')):
                    GF_ind = player_num # note which player is a living Godfather
                    # *** there needs to be logic here for dueling Mafias
                
                elif((role_name == 'Medium')):
                    self.living_medium = 1

            if (role_class_dict[role_name]["faction"] == "Town"):
                self.num_town += 1

            self.players.append(player(player_name, player_num, role_name, self.night_num, perpetuated_element))
            self.categories.append(roleSlot(slot_name, role_name))

        if(num_living > int(len(self.players) / 2)):
            if(GF_ind > 0):
                self.determineAvailableWiretaps(GF_ind)
    
    def parseActionFile(self, action_file):
        self.action_queue = []
        file = open(action_file, 'r')
        #self.night_num =  
        #self.night_num = re.sub(r"\n","",self.night_num)
        # *** Might remove
        file.readline() # the first line of the action file should be the night number
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
                    current_action_regex = r"\A\s"+player.action_keywords[option_num]+r"(\s|$)"
                    action_found = re.search(current_action_regex,action_text)
                    if(action_found): # \s needed so we are finding standalone keywords 
                        action_text = re.sub(action_found.group(), "", action_text) # remove found action from text
                        current_action = re.sub(r"\A\s|\s\Z","",action_found.group())
                        attempted_actions = attempted_actions + 1
                        found = 1 # *** can probably remove a variable here. too lazy rn
                        
                        if attempted_actions > player.max_actions:
                            sys.exit("Error, too many actions attempted for " + player.player_name)
                        
                        if(re.search(r".+\s(" + all_actions_regex + r")\s",action_text)): # there is at least one more action
                            targetting_text = re.sub(r",\s(" + all_actions_regex + r").+", "", action_text) # remove the next action and everything after
                            action_text = re.sub(r"\A" + targetting_text + ",","",action_text)
                        else:
                            targetting_text = action_text
                            action_text = re.sub(r"\A" + targetting_text,"",action_text) # remove targetting_text from action_text
                        
                        # determine targets
                        targets = []
                        # *** taking multiple actions does not work, need to fix
                        num_commas = len(re.findall(",",targetting_text))
                        if(targetting_text):
                            if (num_commas > 0): # 3 or more targets
                                for target_num in range(num_commas + 1): # *** This needs to be improved, names are very limited rn
                                    targets.append(re.search(r"\A[a-zA-Z0-9]+(\s[A-Z])?",targetting_text).group())
                                    if(target_num <= num_commas):
                                        targetting_text = re.sub(r"\A[a-zA-Z0-9]+(\s[A-Z])?,\s","",targetting_text)
                            elif (re.search(r"\sand\s", targetting_text)): # two targets
                                targets.append(re.search(r"\A[a-zA-Z0-9]+(\s[A-Z])?",targetting_text).group())
                                targetting_text = re.sub(r"\A[a-zA-Z0-9]+(\s[A-Z])?\sand\s","",targetting_text)
                                targets.append(re.search(r"\A[a-zA-Z0-9]+(\s[A-Z])?",targetting_text).group())
                            else: # single target
                                targets.append(targetting_text)
                            if(len(targets) > player.max_targets[option_num]):
                                sys.exit("Too many targets selected for " + player.player_name + " (" + current_action + "), maximum of " + str(player.max_targets[option_num]) + " target(s).")
                        player.actions.append(actionObject(current_action, player, targets))
                        self.action_queue.append(player.actions[-1]) # queue action
                        # ***I don't know if it's logically possible to find an action that doesn't have a queue IF the action regex and action priority
                        # dicts are up to date, but I should probably add error checking anyways
                        break # break from for loop if action has been found at start of string
                
                if found == 0: # error case for looping through entire set of action options and not finding one in the text
                    sys.exit("No valid option found in: " + action_text)

        #else: # *** idk if I need this or not
            #print("This player apparently has no action options? " +player.role.role + " " + player.player_name) # *** might make this an error idk

    def evaluateActions(self):  
        #self.public_announcements = []
        self.death_announcements = {}
        self.narrator_announcements = []
        self.indeterminant = []
        self.kill_res_dict = {}
        self.atks_dict = {}
        self.defenses_dict = {}

        # *** I think targetting is screwed up because of the player_locations list now being a copy. That should just be made a list with player nums
        # action queue pre-processing
        #if any(action_obj.action == 'disguising' for action_obj in self.action_queue):
        #    self.action_queue.append(actionObject('determineAppearances', action_dict['disguising']['priority'] + .1, 0))
        
        # *** This is a temp fix and resolution stuff needs to be cleaned up
        self.resolution_dict = {}
        observing = None
        blackmailing = 0 # *** fix to match?

        self.action_queue.sort(key = lambda x: x.priority) # sort action queue by priority
        self.player_locations = [player.player_num for player in self.players] # list that holds player_num and is shifted by Transporters

        # *** entire section with how Vet and Trapper are resolved does not properly account for transports, blocks, controls, etc.
        for action_obj in self.action_queue:
            if action_obj.targeted:
                for i in range(len(action_obj.targets)):
                    action_obj.targets[i] = self.targetText2PlayerNum(action_obj.targets[i])
                    #target_inds.append(self.targetText2PlayerNum(action_obj.targets[i])) 
                    #if (isinstance(action_obj.targets[i],str)): # for blocks I've done some replacing of the targets with their index numbers already. 
                        # *** Instead of this, I should just do all of this ahead of time in the same place, probably. Are there issues with that?

        while(self.action_queue): 
            action_obj = self.action_queue[0]
            target_inds = []

            if action_obj.targeted:
                for i in range(len(action_obj.targets)): # *** I think I can just get rid of target_inds...
                    target_inds.append(self.getTargetPlayer(action_obj.targets[i]).player_num)
                if action_obj.is_visit:
                    self.processVisit(target_inds, action_obj)
                
            # *** need to implement immunities               
            match (action_obj.action):
                # *** one line actions resolved here, more complex ones resolved in standalone f'ns
                case 'reviving':
                    if self.players[target_inds[0]].perpetuated['living_status'] == 1:
                        sys.exit("Error, Retributionist cannot revive a living player. (" + 
                                    action_obj.player.player_name + " reviving " + self.players[target_inds[0]].player_name + ")")
                case 'jailing': 
                    self.players[target_inds[0]].jailed = 1
                    # sets cannot_execute from 1 to 0 for the next night. Code has already verified against an illegal execution
                    # by not adding "executing" to jailorClass' action keywords when initialized
                    action_obj.player.cannot_execute = 0 
                case 'alerting':
                    action_obj.player.alerting = 1
                    if action_obj.player.role != "Necromancer":
                        action_obj.player.perpetuated["alerts"] -= 1
                case 'transporting':
                    # *** Wording needs checked, also untested
                    if self.players[target_inds[0]].jailed == 1:
                        action_obj.player.notifications.append("Your transport failed!")
                        self.players[target_inds[0]].notifications.append("Someone tried to transport you, but you were in jail!")
                    elif self.players[target_inds[1]].jailed == 1:
                        action_obj.player.notifications.append("Your transport failed!")
                        self.players[target_inds[1]].notifications.append("Someone tried to transport you, but you were in jail!")
                    else:
                        transporting = self.findResolutionObj(action_obj, target_inds)
                    #self.players[target_inds[0]].transported.append(self.players[target_inds[1]])
                    #self.players[target_inds[1]].transported.append(self.players[target_inds[0]])
                case 'resolve_transporting':
                    cancel_list = []
                    for remaining_action in self.action_queue:
                        if(remaining_action.cancelled == 0):
                            if (remaining_action.action == "blocking") | (remaining_action.action == "controlling"):
                                cancel_list.append(remaining_action)
                            elif (remaining_action.priority > action_dict["blocking"]["priority"]):
                                break     
                    self.resolveTransports(cancel_list, action_obj)
                case "controlling":
                    # *** does not actually implement a control
                    target_player = self.getTargetPlayer(target_inds[0])
                    target_player.notifications.append("You were controlled!")
                    result = target_player.role_name                
                    if startsWVowel(result):
                        result = "an " + result
                    else:
                        result = "a " + result

                    action_obj.player.notifications.append("Your target is " + result + "!")

                case "trapping":
                    for target_num in target_inds:
                        target = self.getTargetPlayer(target_num)
                        target.trappers_targeting.append(action_obj.player.player_num)
                    print("***Needs implemented")
                case "hallowing":
                    # *** this actually needs to be wrapped up in the blocking/controlling resolution, but it's fine for now
                    if target_inds[0] == action_obj.player.player_num:
                        if action_obj.player.perpetuated["self-hallow"]:
                            action_obj.player.perpetuated["self-hallow"] = 0
                        else:
                            sys.exit("Error, indicated self-hallow when unavailable.")
                    self.getTargetPlayer(target_inds[0]).hallowed = 1
                case 'delivering to':
                    print("***Still needs implemented, dingus!")
                case 'protecting':
                    self.updateKillDicts(target_inds[0], action_obj, self.defenses_dict)
                case 'saving':
                    self.updateKillDicts(target_inds[0], action_obj, self.defenses_dict)
                case 'vesting': 
                    action_obj.player.vesting = 1
                    #self.updateKillDicts(action_obj.player.player_num, action_obj, self.defenses_dict)

                    # idk why I had this at all
                    #if action_obj.player.role != "Necromancer":
                    #    action_obj.player.perpetuated["vests"] -= 1
                    if action_obj.player.role_name == "Veteran":
                        action_obj.player.perpetuated["alerts"] -= 1
                case 'killing': # *** both killing and shooting need work if restructuring attacks
                    self.updateKillDicts(target_inds[0], action_obj, self.atks_dict)
                case 'shooting':
                    self.updateKillDicts(target_inds[0], action_obj, self.atks_dict)
                    action_obj.player.perpetuated['shots'] -= 1
                case 'stabbing':
                    self.updateKillDicts(target_inds[0], action_obj, self.atks_dict)
                case 'mauling':
                    self.updateKillDicts(target_inds[0], action_obj, self.atks_dict)
                case 'blocking':
                    self.resolveBlock(self.getTargetPlayer(target_inds[0]))

                case 'disguising':
                    # *** need to determine if a new disguise is disrupting non-detereminant old diguises
                    disguising = self.findResolutionObj(action_obj, target_inds)
                    # (don't want call to determineAppearances to shuffle non-determinant chains that haven't changed)
                    #print(action_obj.player.perpetuated["active_disguise"])
                    #if action_obj.player.perpetuated["active_disguise"][0] != -1: # *** why the frick is this turning into a string
                    #    print(action_obj.player.perpetuated["active_disguise"][0])
                    #    disg0 = action_obj.player.perpetuated["active_disguise"][0]
                    #    disg1 = action_obj.player.perpetuated["active_disguise"][1]

                    #    self.players[disg0].perpetuated["disguises"].remove(disg1)
                    #    self.players[disg1].perpetuated["disguises"].remove(disg0)
                        #for disguise_ind, old_disguise in enumerate(action_obj.player.perpetuated["active_disguise"]): # should only do anything if there was an active disguise already
                        #    if disguise_ind == 0: # probably a better way to do this, this is kinda gross
                        #        old_ind = 1
                        #    else:
                        #        old_ind = 0
                        #    self.players[old_disguise].perpetuated["disguises"].remove(old_ind)
                    # *** need to implement functionality of being unable to kill your disguise target night-of. Probably introduct faction attributes
                    #action_obj.player.perpetuated["active_disguise"] = [self.getTargetPlayer(target_inds[0]).player_num, self.getTargetPlayer(target_inds[1]).player_num]
                    
                    #self.getTargetPlayer(target_inds[0]).perpetuated["disguises"].append(self.getTargetPlayer(target_inds[1]).player_num)
                    #self.getTargetPlayer(target_inds[1]).perpetuated["disguises"].append(self.getTargetPlayer(target_inds[0]).player_num)

                    #if (len(self.action_queue) > 1):
                    #    self.action_queue.insert(queue_ind + 1, actionObject('determineAppearance', action_dict["disguising"]["priority"] + .5, player = self.players[target_inds[0]]))
                    #elif(self.action_queue[queue_ind + 1].action != "disguising"):
                    #    self.action_queue.insert(queue_ind + 1, actionObject('determineAppearance', action_dict["disguising"]["priority"] + .5, player = self.players[target_inds[0]]))
                        # *** idk I think there are probably a million better ways to do this
                        # this basically needs to run on each set of nodes (not implemented yet)
                case 'resolve_disguising':
                    self.resolveDisguises(action_obj)
                case 'blackmailing':
                    self.queueResolution(action_obj)
                    #self.resolveBlackmails(action_obj)
                    #for remaining_action in self.action_queue: # *** this needs thorough testing
                    #    if  remaining_action.action[0] == "resolveBlackmails":
                    #        remaining_action.player.append(action_obj.player)
                    #        remaining_action.targets.append(target_inds[0])
                    #        blackmailing = 1
                    #        break

                    #if blackmailing == 0:
                    #    self.action_queue.append(actionObject("resolveBlackmails", [action_obj.player], targets = [target_inds[0]]))
                case 'resolve_blackmailing': 
                    self.resolveBlackmails(action_obj)
                case 'cleaning':
                    # *** need to evaluate if all uses of getTargetPlayer are correct or if abs is needed
                    #*** I need to lower the number of cleans. But in reality I need to track resources separately from here somehow.
                    self.getTargetPlayer(target_inds[0]).perpetuated["cleaned"] = 1
                case 'dousing':

                    action_obj.player.perpetuated["first_douse"] = 0 # no need to check if it's 1, just assign it to 0

                    for target in target_inds:
                        target_player = self.getTargetPlayer(target)
                        target_player.perpetuated["doused_by"].append(action_obj.player.player_num) # *** still to do activations, plus removing if Arso dies
                        action_obj.player.perpetuated["douses"].append(target_player.player_num)
                case 'investigating':
                    if action_obj.player.role_name == "Investigator":
                        if(self.getTargetPlayer(target_inds[0]).perpetuated["doused_by"]):
                            result = investigator_categories_dict["Arsonist"]
                        else:
                            result = investigator_categories_dict[self.getPlayerAppearance(self.getTargetPlayer(target_inds[0]),"role")]

                    else: #(action_obj.player.role_name == "Consigliere") | (action_obj.player.role_name == "Necromancer"):
                        if(self.getTargetPlayer(target_inds[0]).perpetuated["doused_by"]):
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
                    # *** I can fix this to be way better
                    if observing is None:
                        observing = actionObject("determineVisits", [action_obj.player], targets = [target_inds[0]])
                        observing.priority.append(action_obj.priority)
                        self.action_queue.append(observing)
                    else:
                        for remaining_action in self.action_queue: # *** this needs thorough testing
                            if  remaining_action.action == "determineVisits":
                                remaining_action.priority.append(action_obj.priority)
                                remaining_action.player.append(action_obj.player)
                                remaining_action.targets.append(target_inds[0])
                                break
                case 'determineVisits':
                    self.determineVisits(action_obj)
                case 'wiretapping':
                    for target in target_inds:
                        self.players[target].notifications.append("You were wiretapped!")
                case 'igniting': # *** the way this targeting works will need to go in the README
                    if(action_obj.targets):
                        for douse_ind in action_obj.targets:
                            douse_ind = int (douse_ind) - 1
                            target_inds.append(action_obj.player.perpetuated["douses"][douse_ind])
                    else:
                        target_inds = action_obj.player.perpetuated["douses"].copy()

                    for target in target_inds:
                        action_obj.player.perpetuated["douses"].remove(target)
                        self.players[target].perpetuated["doused_by"].remove(action_obj.player.player_num)

                        if self.players[target].jailed: # *** could make a dict for phrasing from actions (i.e. igniting to ignite) if desired
                            self.players[target].notifications.append("Someone tried to ignite you, but you were in jail!")
                        elif (self.players[target].role_name == "Arsonist"):
                            self.players[target].notifications.append("Someone tried to ignite you, but you are immune!")
                            action_obj.player.notifications.append("You tried to ignite another Arsonist!") # *** idk if that's correct
                        else:
                            self.killPlayer(target, action_obj)
                case _:
                    print("Action defaulted: " + action_obj.action)
                
            self.action_queue.pop(0)

        # *** TO-DO here:
        #       -add indeterminancy info
        #       -add BG/Arso interaction
        #       -add BG/Mafioso interaction
        #       -add vest/shield/jail functionality
        if (self.atks_dict): # *** need to 
            # *** debug code
            #for player_num in self.atks_dict:
                #print(player_num)
                #for atk_type in self.atks_dict[player_num].actions:
                    #print(atk_type)

            attacked_players_list = [player_num for player_num in self.atks_dict]
            for player_num in attacked_players_list:
                if player_num in self.defenses_dict:
                    if "protecting" in self.defenses_dict[player_num].actions:
                        if player_num in self.atks_dict:
                            if "dousing" not in self.atks_dict[player_num].actions: # *** make this the else statement later. Need to add Arso 
                                # *** might do this further up idk
                                atk_state = self.atks_dict[player_num].determineState(from_start = 1, direct_only = 1)
                                self.defenses_dict[player_num].determineState(from_start = 1, skip_bg = 0)

                                # I might re-write this as conditional on atk_state but idk that it matters either way
                                while (self.atks_dict[player_num].state < num_atk_states) and (self.defenses_dict[player_num].actions["protecting"]):
                                    defense_obj = self.defenses_dict[player_num].getAction()
                                    attack_obj = self.atks_dict[player_num].getAction()

                                    self.updateKillDicts(defense_obj.player.player_num, actionObject("sacrificing", player = defense_obj.player), self.atks_dict)
                                    self.updateKillDicts(attack_obj.player.player_num, actionObject("counterattacking", player = defense_obj.player), self.atks_dict)

                                    self.getTargetPlayer(defense_obj.targets[0]).notifications.append("You were protected by a Bodyguard!")

                                    self.atks_dict[player_num].actions[atk_state].pop(0)
                                    self.defenses_dict[player_num].actions["protecting"].pop(0)

                                    if (not self.atks_dict[player_num].actions[atk_state]): # exhausted actions in this atk state, list empty
                                        del self.atks_dict[player_num].actions[atk_state]
                                        atk_state = self.atks_dict[player_num].determineState(from_start = 1, direct_only = 1)
                                
                                if not self.atks_dict[player_num]: # *** remove empty entry. Needs testing
                                    del self.atks_dict[player_num]

                            if "mauling" in self.atks_dict[player_num].actions: # this means Bodyguard did not line up on a maul, since it'd be removed
                                for visitor in self.players[player_num].visitors:
                                    for maul in self.atks_dict[player_num].actions["mauling"]:
                                        if visitor != maul.player:
                                            self.updateKillDicts(visitor.player_num, actionObject("mauling_visitor", maul.player, [visitor]), self.atks_dict)
                                            # *** "You attacked someone!"" should go here?
            # *** I think the inner loops can be written as a function for both bg and the general case, and will add stuff for bg?
            attacked_players_list = [player_num for player_num in self.atks_dict] 
            for player_num in attacked_players_list:
                atk_state = self.atks_dict[player_num].determineState(from_start = 1)
                
                if player_num in self.defenses_dict:
                    defense_state = self.defenses_dict[player_num].determineState(from_start = 1, skip_bg = 1)
                else:
                    defense_state = None

                while (self.atks_dict[player_num].state < num_atk_states):
                    if defense_state: # using the state condition prevents issues like inapplicable BGs from being an issue
                        defense_obj = self.defenses_dict[player_num].getAction()
                        attack_obj = self.atks_dict[player_num].getAction()

                        self.resolveAtkDefense(attack_obj, defense_obj, player_num)

                    else:
                        attack_obj = self.atks_dict[player_num].getAction()
                        attacked_player = self.players[player_num]
                        # cases:
                        # Night Immunity, vesting, shields
                        if getattr(attacked_player, "vesting", 0) and (atk_flags[attack_obj.action] & 0b010):
                            attacked_player.notifications.append("Someone tried to attack you but you were protected by your vest!")
                            self.players[attack_obj.player.player_num].notifications.append("Your attack failed!")
                        elif attacked_player.night_immune and (atk_flags[attack_obj.action] & 0b010):
                            attacked_player.notifications.append("Someone tried to attack you but you were protected by you are immune!")
                            self.players[attack_obj.player.player_num].notifications.append("Your attack failed!")
                        elif (attacked_player.perpetuated.get("shield", 0) and not 
                            (role_class_dict[attacked_player.role_name]["faction"] == faction_dict["NE"] and (atk_flags[attack_obj.action] & 0b1))):
                            attacked_player.notifications.append("Someone tried to attack you but they broke your shield instead!")
                            attacked_player.perpetuated["shield"] = 0
                            if attack_obj.action != "mauling": # mauling should be the only attack that gets to here and doesn't get "Your attack failed!" but needs testing
                                self.players[attack_obj.player.player_num].notifications.append("Your attack failed!") 
                        
                        else:
                            # *** TO-DO: Technically need to make this optional
                            if attack_obj.action == "stabbing":
                                self.players[player_num].cleaned = 1
                            self.killPlayer(player_num, attack_obj)

                            # *** needs all the logic surrounding disguises and cleans. Also need to figure out announcement order.
                            if(self.players[player_num].role_name == "Retributionist"):
                                if self.players[player_num].actions:
                                    rev_player_num = self.players[player_num].actions[0].targets[0]
                                    self.players[rev_player_num].perpetuated["living_status"] = 1
                                    self.narrator_announcements.append(self.players[rev_player_num].player_name + " WAS REVIVED BY THE RETRIBUTIONIST!")
                        
                        if (attack_obj.action == "mauling") | (attack_obj.action == "mauling_visitor") | (attack_obj.action == "alerting"):
                            # *** can be made better I think
                            self.players[attack_obj.player.player_num].notifications.append("You attacked someone!")

                    self.atks_dict[player_num].actions[atk_state].pop(0)
                    if (not self.atks_dict[player_num].actions[atk_state]): # exhausted actions in this atk state, list empty
                        del self.atks_dict[player_num].actions[atk_state]
                        atk_state = self.atks_dict[player_num].determineState(from_start = 1)

                # We could remove entry from attacked list here if there were a reason to do that

            # *** debug code
            #print("After")
            #for player_num in self.atks_dict:
            #    print(player_num)
            #    for atk_type in self.atks_dict[player_num].actions:
            #        print(atk_type)  
    def resolveAtkDefense(self, attack_obj, defense_obj, player_num):
        # *** Update to distinguish between cases
        self.players[player_num].notifications.append("Someone tried to attack you, but you were saved!")
        self.players[defense_obj.player.player_num].notifications.append("Someone tried to attack [TARGET] but you saved them!")
        self.players[attack_obj.player.player_num].notifications.append("Your attack failed!")

        self.defenses_dict[player_num].actions[defense_state].pop(0)

        if (not self.defenses_dict[player_num].actions[defense_state]): # exhausted actions in this atk state, list empty
            del self.defenses_dict[player_num].actions[defense_state]
            defense_state = self.defenses_dict[player_num].determineState(from_start = 1, skip_bg = 1)


    def processVisit(self, target_inds, action_obj):
        # *** Trap and hallow still need to be integrated into f'n to process transports and cancels
        for i in range(len(target_inds)):
            self.getTargetPlayerAbs(target_inds[i]).visitors.append(action_obj.player)
        
        for target in action_obj.targets:
            if getattr(self.players[target], "alerting", 0): # *** this needs to be tested
                # *** I think this has issues cancelling multi-target actions # I doh't think this should be an issue anymore but not tested
                # an alerting player can never be transported, so using self.players list directly
                self.updateKillDicts(action_obj.player, self.players[target], self.atks_dict)
                action_obj.cancelled = 1
        
        if not action_obj.cancelled:                 
            if (action_obj.player.faction >= faction_dict["non-Town"]):
                for target_num in action_obj.targets:
                    target = self.getTargetPlayer(target_num)
                    if (target.trappers_targeting):
                        for trapper_num in self.players[target_num].trappers_targeting:
                            trapper = self.getTargetPlayerAbs(trapper_num)
                            if(action_obj.player.player_num in trapper.perpetuated["traps_landed"]):
                                trapper.perpetuated["traps_landed"].remove(action_obj.player.player_num)
                                trapper.perpetuated["num_traps"] = 1
                                self.updateKillDicts(action_obj.player.player_num, actionObject("trapping_atk", trapper, action_obj.player.player_num), self.atks_dict)
                                trapper.notifications.append("Your trap on " + target.player_name + " attacked someone!") # *** need to sort out, probably
                                    # *** Need to cancel action (not implemented properly) # idk if this is still true
                                action_obj.cancelled = 1
                            else:
                                trapper.perpetuated["traps_landed"].add(action_obj.player.player_num)
                                action_obj.player.notifications.append("You were trapped!")
                                trapper.notifications.append("Your trap on " + target.player_name + " was activated!") # *** re-write so only one noti
            
            if not action_obj.cancelled:
            # *** this whole f'n needs work, but everything below here hasn't even been considered
                # *** note hallow not currently cancelling the visit
                if "hallow_cancels" in action_dict[action_obj.action]:
                    for target_num in action_obj.targets:
                        target = self.getTargetPlayer(target_num)
                        if target.hallowed:
                            action_obj.player.notifications.append("Your " + action_obj.action + " was blocked by the Medium's hallow!")
                            action_obj.cancelled = 1
                    if action_obj.cancelled:
                        for target_num in action_obj.targets:
                            self.getTargetPlayer(target_num).visitors.remove(action_obj.player.player_num)

    def updateKillDicts(self, affected_player_num, action_obj, update_dict):
        # there might be more efficient logic here, rn it adds the affected_player_num to the dict if it 
        # isn't there and then checks against the particular action being in the dict
        if affected_player_num not in update_dict:
            if update_dict is self.atks_dict:
                update_dict[affected_player_num] = atkResObject(affected_player_num)
            elif update_dict is self.defenses_dict:
                update_dict[affected_player_num] = defenseResObject(affected_player_num)
            else:
                sys.exit("Invalid update dict provided for f'n updateKillDicts")

        if action_obj.action in update_dict[affected_player_num].actions:
            update_dict[affected_player_num].actions[action_obj.action].append(action_obj)
        else:
            update_dict[affected_player_num].actions[action_obj.action] = [action_obj]

    def killPlayer(self, player_num, death_source):
        if death_source.action in death_message_dict:
            self.players[player_num].perpetuated["living_status"] = 0
            if death_source.action == "sacrificing":
                self.players[player_num].notifications.append("You " + death_message_dict[death_source.action] + "!")
            else:
                self.players[player_num].notifications.append("You were " + death_message_dict[death_source.action] + "!")

            if(player_num not in self.death_announcements):
                self.death_announcements[player_num] = [death_source.action]
            else:
                self.death_announcements[player_num].append(death_source.action)
        else:
            sys.exit("Death source not recognized: " + death_source.action)

    # *** should consider the order I want announcements to be made in
    def writeNotifications(self, notifications_file):
        notifications_file.write(str(self.night_num) + " Results\n")
        notifications_file.write("Public Notifications:\n")
        for dead_player_num in self.death_announcements:
            dead_player = self.getTargetPlayerAbs(dead_player_num)
            noti = dead_player.player_name + " died last night. "
            for death_source in self.death_announcements[dead_player_num]:
                if death_source == "sacrificing":
                    noti += "He/She " + death_message_dict[death_source] + ". "
                else:
                    noti += "He/She was " + death_message_dict[death_source] + ". "
                
            
            # *** can modify this text to include "the" for unique roles. If I'm not lazy
            noti += "He/She was "
            if(dead_player.perpetuated["cleaned"]):
                noti += "cleaned."
            else:
                appearance = self.getPlayerAppearance(dead_player,"role")
                
                if(startsWVowel(appearance)):
                    noti += "an "
                else:
                    noti += "a "
                noti += appearance + "."

            notifications_file.write(noti + "\n")

            self.players[dead_player_num].notifications.append("Will?") # this is not writing out to the file, but prevents having repeat "Will?" messages

        for announcement in self.narrator_announcements:
            notifications_file.write(announcement + "\n")
        
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
    def queueResolution(self, action_obj):
        if action_obj.action in self.resolution_dict:
            self.resolution_dict[action_obj.action].player.append(action_obj.player)
            self.resolution_dict[action_obj.action].targets.append(action_obj.targets)

        else:
            queue_len = len(self.action_queue)
            if queue_len > 1:
                for queue_ind, remaining_action in enumerate(self.action_queue[1:]):
                    if remaining_action.priority > action_dict["resolve_" + action_obj.action]["priority"]:
                        break
            
            if (re.match(r"tracking|watching|stalking", action_obj.action)): # separate thing for these is kinda gross but idc
                self.action_queue.insert(queue_ind + 1, actionObject("resolve_observing" + action_obj.action, [action_obj.player], [action_obj.targets]))
            else:
                self.action_queue.insert(queue_ind + 1, actionObject("resolve_" + action_obj.action, [action_obj.player], [action_obj.targets]))

    # *** the resolution_exists thing is weird
    def findResolutionObj(self, action_obj, target_inds, resolution_exists = 0): # *** need to go back and use this for BM and such. plus target_inds usage change
        action_obj.targets = target_inds # here we do overwrite the actual target text with the target index, but this action is 
        # being discarded elsewhere anyways so it's fine
        # *** I think this is fiexed so it's unnecessary. Test
        
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
            self.action_queue.insert(queue_here, actionObject("resolve_" + action_obj.action, [action_obj]))
            resolution_exists = 1

        return resolution_exists # should always be 1, but better not to hard code it I suppose

    def resolveBlock(self, target):
        target.notifications.append("You were roleblocked!")

        for queue_ind, remaining_action in enumerate(self.action_queue):
            if remaining_action.player is target:
                remaining_action.cancelled = 1

    def resolveBlackmails(self, action_obj):
        new_blackmails = []
        #if self.getTargetPlayer(bm_target).perpetuated["blackmail_immune"] == 1 or self.getTargetPlayer(bm_target).perpetuated["blackmail_immune"] == -1:
        for bm_target in action_obj.targets:
            if self.getTargetPlayer(bm_target[0]).perpetuated["blackmail_immune"] == 1:
                self.getTargetPlayer(bm_target[0]).notifications.append("Someone tried to blackmail you, but you were blackmailed the previous night!") # *** Check phrasing
                # *** don't know if technically you regain blackmail immunity when someone tries and fails or not
            else:
                self.getTargetPlayer(bm_target[0]).notifications.append(
                "You were blackmailed!\n\n" \
                "You cannot speak, except for saying, 'I am blackmailed,' exactly once.\n" \
                "You may not vote, you may only abstain, but you cannot use your abstain to communicate information.")

                new_blackmails.append(self.getTargetPlayer(bm_target[0]))
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

                    # this section can be un-commented to debug the list of all visits for the night
                    #all_visitors = []
                    #for visitor in night_visits.keys():
                    #    for num_visits in range(len(night_visits[visitor])):
                    #        all_visitors.append(visitor)
                    #print(all_visitors)
                    #for visit_ind, visitor in enumerate(all_visitors):
                        #print(self.players[visitor].player_name + " to " + self.players[all_visits[visit_ind]].player_name)

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
                                + " chosen from list of all visits tonight. (" + str(len(all_visits)) + " total)"
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
    def resolveTransports(self, cancel_list, resolve_obj):
        num_players = len(self.players)

        # eval_obj has attributes:
        # -transports_list: list of len num_players. At the index corresponding to their player_num, this list will be None if 
        #       the players is not transporting and will be a sub-list of the player's transport action objects if they are. 
        # -cancel_list: list of len num_players. At the index corresponding to player_num, this list will be None if no cancellation
        #       objects are targetted at the player and will be a sub-list of the corresponding cancellation action objects if they are.
        # -affected_locations: list of len num_players. At the index corresponding to their player_num, will be -2 if they are not being
        #       transported, and -1 if they are. Passed into buildNodeList and used to track the index of the node set that contains 
        #       a transport of that player. 
        # -nodes_to_eval: initialized to empty list. Used to hold eval status (0: eval not needed, 1: eval needed, 2: remove node) of
        #       the transport node sets constructed by buildNodeList.
        # -nxt_nodes_to_eval: initialized to empty list. Used to hold eval status (0: eval not needed, 1: eval needed, 2: remove node) of
        #       the transport node sets constructed by buildNodeList. Kept separately so that for loop can iterate through 
        #       nodes_to_eval without affecting the status the nodes should have as of the last pass. 
        eval_obj = evalObject(resolve_obj.player, num_players, cancel_list)
  
        node_list = self.buildNodeList(eval_obj, update_eval=True) 

        # check for transporters that have a cancellation on their location and are not being transported. Cancel their actions first. 
        for i in range(num_players): 
            if (eval_obj.cancel_list[i]) and (eval_obj.actions_list[i]) and (eval_obj.affected_locations[i] == 0):
                self.cancelNodeAction(eval_obj, node_list, i)

        while eval_obj.nxt_nodes_to_eval:
            eval_obj.nodes_to_eval = eval_obj.nxt_nodes_to_eval.copy()
            eval_obj.nxt_nodes_to_eval = []

            for node_set in eval_obj.nodes_to_eval:
                for location in node_set["targets"]:
                    self.player_locations[location] = self.players[location].player_num
                
                swap_node_list = [swap_node for swap_node in node_set["targets"] if (node_set["targets"][swap_node] == 1)]       
                r.shuffle(swap_node_list)
                num_swaps = len(swap_node_list)
                
                for ind in range(num_swaps - 1):
                    self.player_locations[swap_node_list[ind]] = swap_node_list[ind + 1]
                self.player_locations[swap_node_list[num_swaps - 1]] = swap_node_list[0]

                #transported_player_nums = list(node_set.keys())
                #for player_num in transported_player_nums:
                players_to_cancel = []
                for player_num in node_set["targets"]:
                    if eval_obj.actions_list[player_num] and eval_obj.cancel_list[self.player_locations.index(player_num)]:
                        players_to_cancel.append(player_num)

                for player_num in players_to_cancel:
                    self.cancelNodeAction(eval_obj, node_list, player_num)

            num_nodes = len(eval_obj.nxt_nodes_to_eval)

        # set notifications for transported targets
        for node_set in node_list:
            for target in node_set['targets']:
                for noti in range(node_set['targets'][target]):
                    self.players[target].notifications.append("You were transported!")

        # determine notifications for transporters that are transported into a block or control
        for i in range(num_players):
            if self.players[self.player_locations[i]].blocked > 0 or self.players[self.player_locations[i]].controlled > 0:  
                blocks_on_location = 0
                controls_on_location = 0
                if eval_obj.cancel_list[i]:
                    for cancellation in eval_obj.cancel_list[i]:
                        if cancellation.action == "blocking":
                            blocks_on_location += 1
                        elif cancellation.action == "controlling":
                            controls_on_location += 1
                
                num_diff = self.players[self.player_locations[i]].blocked - blocks_on_location
                for noti_num in range(num_diff):
                    self.players[self.player_locations[i]].notifications.append("You were transported into a block!") # *** get exact noti
                
                num_diff = self.players[self.player_locations[i]].controlled - controls_on_location
                for noti_num in range(num_diff):
                    self.players[self.player_locations[i]].notifications.append("You were transported into a control!")

    def buildNodeList(self, eval_obj, update_eval = False):
        node_list = []
        num_nodes = 0

        for player_actions in  eval_obj.actions_list:
            if(player_actions): # index is None if no action is occuring
                for action in player_actions:
                    if(action): 
                        num_nodes = self.addNode(node_list, action, eval_obj, num_nodes, update_eval)
                                         
        return node_list      

    def cancelNodeAction(self, eval_obj, node_list, acting_player_num, same_night = True):
    # same_night used to indicate visitors need to be removed (i.e. from Transports)
            if(hasattr(eval_obj, "cancel_list")):
                for action_obj in eval_obj.actions_list[acting_player_num]:
                    action_obj.cancelled = 1

                for cancellation in eval_obj.cancel_list[self.player_locations.index(acting_player_num)]:
                    if cancellation.action == "blocking":
                        self.players[acting_player_num].blocked += 1 
                    elif cancellation.action == "controlling":
                        self.players[acting_player_num].controlled += 1 
    
            for action_obj in eval_obj.actions_list[acting_player_num]:
                node_set = eval_obj.node_set_by_player[action_obj.targets[0]]
                
                now_static_targets = 0
    
                for target_ind, target in enumerate(action_obj.targets):
                    if same_night:
                        self.players[target].visitors.remove(self.players[acting_player_num])
    
                    node_set["targets"][target] -= 1
                    if node_set["targets"][target] < 1:
                        now_static_targets += 1
                        node_set["targets"].pop(target, None)
                        #eval_obj.affected_locations[target] = 0

                        if(hasattr(eval_obj, "cancel_list")):
                            self.player_locations[target] = self.players[target].player_num
                            if eval_obj.actions_list[target] and eval_obj.cancel_list[target]:
                                self.cancelNodeAction(eval_obj, node_list, target) # recursive cancellations
    
                node_set["actions"].remove(action_obj)
    
                if(now_static_targets == 2): # both targets had only one action affecting them
                    node_list.remove(node_set)
                    if(node_set in eval_obj.nxt_nodes_to_eval):
                        eval_obj.nxt_nodes_to_eval.remove(node_set)
                    for target in node_set["targets"]:
                        eval_obj.node_set_by_player[target] = None
    
                elif(now_static_targets == 0): # need to check for node split
                    #action_inds = [action.player.player_num for action in node_set["actions"]]
                    # *** game object should just store number of players at this point
                    temp_eval_obj = evalObject(node_set["actions"], len(self.players))
                    split_node_sets = self.buildNodeList(temp_eval_obj)
                    if (split_node_sets[0] != node_set):
                        node_list.remove(node_set)
                        if(node_set in eval_obj.nxt_nodes_to_eval):
                            eval_obj.nxt_nodes_to_eval.remove(node_set)

                        node_list.append(split_node_sets[0])
                        node_list.append(split_node_sets[1])

                        eval_obj.nxt_nodes_to_eval.append(split_node_sets[0])
                        eval_obj.nxt_nodes_to_eval.append(split_node_sets[1])
    
                        node_list_len = len(node_list)

                        for new_set in split_node_sets:
                            for target in new_set["targets"]:
                                eval_obj.node_set_by_player[target] = new_set
                        #for target in node_list[node_list_len - 1]["targets"]:
                            #eval_obj.affected_locations[target] = node_list_len - 1
                            #transport.node = node_list[node_list_len - 1]

                else:
                    # *** do I want to set something to update if cancelling when there are still 2 or more targeting the node blah blah
                    if(node_set not in eval_obj.nxt_nodes_to_eval):
                        eval_obj.nxt_nodes_to_eval.append(node_set)
            eval_obj.actions_list[acting_player_num] = None

    def addNode(self, node_list, action, eval_obj, num_nodes, update_eval):
        node_set_by_player = eval_obj.node_set_by_player
        t0 = action.targets[0]
        t1 = action.targets[1]
            
        if (node_set_by_player[t0]) or (node_set_by_player[t1]):
            if (node_set_by_player[t0]) and (node_set_by_player[t1] and (node_set_by_player[t0] is not node_set_by_player[t1])):
                node_set = node_set_by_player[t0]
                merging_nodes = node_set_by_player[t1]
                #node_ind = node_list.index(node)
                node_set.update(merging_nodes)

                for merge_player in merging_nodes["targets"]:
                    node_set_by_player[merge_player] = node_set

                node_list.remove(merging_nodes)
                num_nodes -= 1

            elif not node_set_by_player[t0]:
                node_set_by_player[t0] = node_set_by_player[t1]

            elif not node_set_by_player[t1]: # I don't think there are logically any other cases but it's fine
                node_set_by_player[t1] = node_set_by_player[t0]
                
            node_set = node_set_by_player[t0]
            node_set["targets"][t0] = node_set["targets"].get(t0, 0) + 1
            node_set["targets"][t1] = node_set["targets"].get(t1, 0) + 1
            node_set["actions"].append(action)

            # not tracking nxt_nodes_to_eval for split node calls
            # only want to mark node for re-eval if something changes, so increasing both targets to 3 and beyond does not mark
            if (update_eval) and (node_set["targets"][t0] <= 2) and (node_set["targets"][t0] <= 2):
                if(node_set not in eval_obj.nxt_nodes_to_eval):
                    eval_obj.nxt_nodes_to_eval.add(node_set) # *** fix

        else:
            node_list.append({"targets" : {t0: 1, t1: 1}, "actions" : [action]})
            node_set_by_player[t0] = node_list[-1]
            node_set_by_player[t1] = node_list[-1] 
            num_nodes = num_nodes + 1 # *** don't think I need to track this anymore

            if (update_eval): # *** fix
                eval_obj.nxt_nodes_to_eval.append(node_list[-1])

        return num_nodes

    # *** Complete testing and test cases still need to be developed
    def resolveDisguises(self, resolution_obj): 
        old_disguises = []
        for player in self.players:
            if "active_disguise" in player.perpetuated:
                if(player.perpetuated["active_disguise"][0] >= 0):
                    old_disguises.append(actionObject("disguising", player, player.perpetuated["active_disguise"]))
        eval_obj = evalObject(old_disguises, len(self.players))

        node_list = self.buildNodeList(eval_obj)
        num_nodes = len(node_list)

        for new_disguise in resolution_obj.player:
            active_disguise = eval_obj.actions_list[new_disguise.player.player_num]
            if active_disguise: 
                # *** Right now there can only ever be one active disguise per player, would need to re-write if that changes
                self.cancelNodeAction(eval_obj, node_list, new_disguise.player.player_num, same_night=False)
                t0 = self.getTargetPlayer(active_disguise[0].targets[0])
                t1 = self.getTargetPlayer(active_disguise[0].targets[1])
                t0.perpetuated["appearance"] = t0.player_num
                t1.perpetuated["appearance"] = t1.player_num

            num_nodes = self.addNode(node_list, new_disguise, eval_obj, num_nodes, update_eval=True)
        
        # don't need to update nxt_nodes_to_eval because this one doesn't loop, as opposed to the transport resolution
        for node_set in eval_obj.nxt_nodes_to_eval:
            swap_node_list = [swap_node for swap_node in node_set["targets"] if (node_set["targets"][swap_node] == 1)]    

            r.shuffle(swap_node_list)
            num_swaps = len(swap_node_list)
            for ind in range(num_swaps - 1):
                self.players[swap_node_list[ind]].perpetuated["appearance"] = swap_node_list[ind + 1]
            self.players[swap_node_list[(num_swaps - 1)]].perpetuated["appearance"] = swap_node_list[0]

            # This section can be un-commented to debug disguises
            #for swap_node in swap_node_list:
                #print(self.players[swap_node].player_name + " is appearing as " + self.players[self.players[swap_node].perpetuated["appearance"]].player_name)

## Object Definitions for Use in Game Class
class killResObject: 
    def __init__(self, player_num):
        self.player_num = player_num
        self.state = -1 # set uninitialized state to -1
        self.actions = {}

    def add_action(self, action_to_add):
        action_type = action_to_add.action
        if action_type in self.actions:
            self.actions[action_type].append(action_to_add)
        else:
            self.actions[action_type] = [action_to_add]

class atkResObject(killResObject):
    def __init__(self, player_num):
        super().__init__(player_num)
    
    def determineState(self, from_start = 0, direct_only = False):
        if (from_start) | (self.state == -1):
            self.state = 0

        while self.state < num_atk_states: 
            if (atk_state_map[self.state] in self.actions) and ((not direct_only) | action_dict[atk_state_map[self.state]]["targeted"]):
                atk_state = atk_state_map[self.state]
                r.shuffle(self.actions[atk_state])
                return atk_state
            else:
                self.state += 1

        return None

    def getAction(self):
        atk_state = atk_state_map[self.state]
        return self.actions[atk_state][0]
    
class defenseResObject(killResObject):
    def __init__(self, player_num):
        super().__init__(player_num)

    def determineState(self, from_start = 0, skip_bg = 1):
        if (from_start) | (self.state == -1):
            if skip_bg:
                self.state = 1
            else:
                self.state = 0

        while self.state < num_defense_states:
            if (defense_state_map[self.state] in self.actions):
                defense_state = defense_state_map[self.state]
                r.shuffle(self.actions[defense_state])
                return defense_state
            else:
                self.state += 1

        return None

    def getAction(self):
        defense_state = defense_state_map[self.state]
        return self.actions[defense_state][0]

class actionObject:
    def __init__(self, action, player = None,  targets = None):
        self.action = action
        self.player = player
        # *** I may want to allow custom priorities, tbd
        self.priority = action_dict[action]["priority"]
        self.targeted = action_dict[action]["targeted"]
        self.targets = targets
        self.is_visit = action_dict[self.action]["is_visit"]
        self.cancelled = 0

class evalObject:
    def __init__(self, action_list, num_players, cancel_list = None):
        self.actions_list = [None] * num_players
        self.node_set_by_player = [None] * num_players
        self.nodes_to_eval = []
        self.nxt_nodes_to_eval = []

        # 0 indicates the player is not being affected by any node action,
        # 1 indicates player is affected by at least one 
        self.affected_locations = [0] * num_players

        for action in action_list:
            if self.actions_list[action.player.player_num]:
                self.actions_list[action.player.player_num].append(action)
            else:
                self.actions_list[action.player.player_num] = [action]
            
            for target in action.targets: 
                self.affected_locations[target] = 1

        if cancel_list is not None:
            self.cancel_list = [None] * num_players
            for cancellation in cancel_list:
                if self.cancel_list[cancellation.targets[0]]:
                    self.cancel_list[cancellation.targets[0]].append(cancellation)
                else:
                    self.cancel_list[cancellation.targets[0]] = [cancellation] # target is in a list  

class roleSlot:
    def __init__(self, slot_name, role_name):
        self.slot_name = slot_name
        self.role_name = role_name
             
class player:  
    def __init__(self, player_name, player_num, role_name, night_num = 0, perpetuated_element = None):   
        self.player_name = player_name

        # non-perpetuated class variables for evaluating night actions
        self.actions = []
        #self.attackers = []
        self.blackmailed = 0
        self.blocked = 0 
        self.controlled = 0
        self.hallowed = 0
        self.immunities = []
        self.jailed = 0
        self.night_immunity = 0
        self.player_num = player_num # *** I might want to use player_num instead of passing players/names in a lot of places
        #self.protectors = []
        self.role_name = role_name
        #self.transported = []
        self.trappers_targeting = []
        self.visitors = []
        self.wiretapped = 0
        self.notifications = []

        # role-dependent variables
        self.faction = faction_dict[role_class_dict[role_name]["faction"]]
        self.night_immune = role_class_dict[role_name].get("night_immune", 0)
        self.action_keywords = [] 
        self.max_actions = 0
        self.max_targets = []

        #self.appearance = self # used to assess disguises

        # perpetuated class variables for evaluating night actions
        if(perpetuated_element):
            self.perpetuated = {
                "appearance" : int(perpetuated_element.find("appearance").text),
                "blackmail_immune" : int(perpetuated_element.find("blackmail_immune").text),
                "cleaned" :  int(perpetuated_element.find("cleaned").text),
                "doused_by" : self.readFromXML(perpetuated_element.find("doused_by").text, list),
                "living_status" : int(perpetuated_element.find("living_status").text),
                "potions" : int(perpetuated_element.find("potions").text)
                #temp_immunities : 
            }
        else:
            self.perpetuated = {
                "appearance" : self.player_num,
                "blackmail_immune" : 0,
                "cleaned" : 0,
                "doused_by" : [],
                "living_status" : 1,
                "potions" : 0,
                "temp_immunities" : {}
            }

        if(self.perpetuated["potions"] > 0):
            self.addAction("drinking potion") #*** need to verify this is correct lol
            self.max_actions = 1

        if("perpetuated" in role_class_dict[self.role_name]):
            self.updatePerpetuated(perpetuated_element)
        #print(self.role_name)
        #print(self.perpetuated)

        # *** this is ugly, might want to fix
        #if self.faction >= faction_dict["non-Town"]:
        #    if perpetuated_element:
        #        self.perpetuated["trapped_by"] = self.readListFromXML(perpetuated_element.find("trapped_by").text)
        #    else:
        #        self.perpetuated["trapped_by"] = []

        if("immunities" in role_class_dict[self.role_name]):
            for immunity in role_class_dict[self.role_name]["immunities"]:
                self.immunities.append(immunity) 

        match (role_name):
            # *** I think add check for [] in role_class_dict["actions"] before case statement, so the default
            # doesn't need to check against all these cases every time
            case 'Jailor':
                if(self.perpetuated["cannot_execute"] | (self.perpetuated["executions"] < 1)):
                    self.addAction("jailing")
                    self.max_actions = 1
                else:
                    self.addAction("jailing")
                    self.addAction("executing")
                    self.max_actions = 2
            case 'Alchemist':
                self.addAction("delivering to", 2)
                self.max_actions += 1
                self.addAction("activating") # *** need to give self potion, and allow activation targets
                self.max_actions += 1
            case 'Bodyguard':
                # *** vest needs to be added. I could also update to have roles add all static actions and then parse this list for conditionals
                self.addAction("protecting")
                self.max_actions += 1
            case 'Medic':
                self.addAction("saving") # *** this is not implemented at all
                self.max_actions += 1
                if(self.perpetuated["shots"]) and (night_num > 1):
                    self.addAction("shooting")
            case 'Veteran':
                if self.perpetuated["alerts"] > 0:
                    if night_num > 1:
                        self.addAction("alerting")
                    if self.perpetuated["vests"] > 0:
                        self.addAction("vesting")
            case 'Vigilante':
                if(self.perpetuated["shots"]) and (night_num > 1):
                    self.addAction("shooting")
                    self.max_actions += 1
            case 'Mafioso':
                if(self.perpetuated["shot"]):
                    self.addAction("killing")
                    self.max_actions += 1
            case 'Janitor':
                if (self.perpetuated["cleans"] > 0):
                    self.addAction("cleaning")
                    self.max_actions += 1
            case 'Shapeshifter':
                # *** need some manner of tracking the loss of action
                if (self.perpetuated["action"]):
                    self.addAction("blackmailing")
                    self.addAction("blocking")
                    self.addAction("cleaning")
                    self.addAction("disguising")
                    self.addAction("investigating")
                    self.addAction("stalking")
                    self.addAction("transporting")
                    self.max_actions += 1
            case 'Arsonist':
                if(self.perpetuated["first_douse"]):
                    self.addAction("dousing",2)
                else:
                    self.addAction("dousing",1)
                self.max_actions += 1

                if(self.perpetuated["douses"]):
                    self.addAction("igniting",len(self.perpetuated["douses"]))
                    #if(night_num == 3): # temporary or permanent removal for re-work
                    self.max_actions += 1
            case 'Werewolf':
                # *** needs to be variable by night
                self.addAction("mauling",1)
                self.addAction("stalking",1)
                self.max_actions += 1
            case 'Necromancer':
                self.addAction("investigating") # *** also not implemented at all lol
                self.addAction("transporting")
                self.max_actions += 1
            # ***Exe
            #case 'Executioner':
                #if(self.perpetuated["target"] is None): # Night 1, assign target
            case 'Jester':
                if night_num == 1:
                    self.addAction("vesting")
                    self.max_actions += 1
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
        if(perpetuated_element):
            for expected_elem, default_value in role_class_dict[self.role_name]["perpetuated"].items():
                expected_type = type(default_value)
                self.perpetuated[expected_elem] = self.readFromXML(perpetuated_element.find(expected_elem).text, expected_type)
                #if(type(role_class_dict[self.role_name]["perpetuated"]["default"][elem_ind]) is int):
                #    self.perpetuated[expected_elem] = int(perpetuated_element.find(expected_elem).text)
                #elif(type(role_class_dict[self.role_name]["perpetuated"]["default"][elem_ind]) is list):
                #    self.perpetuated[expected_elem] = self.readListFromXML(perpetuated_element.find(expected_elem).text)
                #elif(type(role_class_dict[self.role_name]["perpetuated"]["default"][elem_ind]) is set):
                #    self.perpetuated[expected_elem] = self.readSetFromXML(perpetuated_element.find(expected_elem).text)
                #else:
                #    self.perpetuated[expected_elem] = perpetuated_element.find(expected_elem).text
            
        else:
            for expected_elem, default_value in role_class_dict[self.role_name]["perpetuated"].items():
                self.perpetuated[expected_elem] = default_value 

    def readFromXML(self, text, text_type):
        # takes XML data for a list stored as one string (i.e. "[entry1, entry2, entry3]") and re-constructs the list as string entries. 
        # Converts whole number entries to int type instead of string. 

        iter = 0
        list_regex = r"\A\[.+\](,\s){0,1}"
        dict_regex = r"\A\{(.+:.+(,){0,1}(\s){0,1})+\}(,\s){0,1}"
        dict_key_regex = r"\A(.+)\s{0,1}:\s{0,1}"
        set_regex = r"\A\{.+\}(,\s){0,1}"
        int_regex = r"(\A-{0,1}[0-9]+)(,\s){0,1}"
        #string_regex = r"\A([A-Za-z0-9]+(\s){0,1})+(,\s){0,1}" # *** I think I'd need to account for quotation marks? Anyways I'm not using this currently

        if text_type is int:
            return int (text)
        elif text_type is list:
            output = [] 
            structure_regex = [r"\A\[", r"\]\Z"]
            #type_match_regex = r"\A\[.*\]\Z"
        elif text_type is set or text_type is dict:
            if text_type is dict:
                output = {}
            else:
                output = set()
                if re.match(r"\Aset\(\)\Z",text): # empty sets looks like this ig
                    return output
            structure_regex = [r"\A\{", r"\}\Z"]
        else:
            sys.exit("Error in readFromXML, text_type provided is not valid: " + str(text_type))
            #type_match_regex = r"\A\{.*\}\Z"
        #else:
        #    return text

        if(re.match(structure_regex[0] + r".*" + structure_regex[1], text)): # check if text represents the provided type structure
            text = re.sub(structure_regex[0],"",text) # remove starting and ending brackets from text (text is used to check if all entries are read)
            text = re.sub(structure_regex[1],"",text) 

            # iterate while text still has characters
            while(text): 
                if text_type is dict:
                    key = re.search(dict_key_regex, text).group(1)
                    text = re.sub(dict_key_regex,"",text)
                # check if text matches the pattern for a nested list, an int, or default to string
                if (re.match(int_regex, text)):
                    search_pattern = int_regex
                    entry = int (re.search(search_pattern,text).group(1))

                #elif(re.match(string_regex, text)):
                #    search_pattern = string_regex
                #    entry = re.search(search_pattern,text).group(1)

                elif (re.match(list_regex, text)):
                    search_pattern = list_regex
                    entry = self.readFromXML(re.search(list_regex, text).group(1), list) # recursive f'n call for nested lists

                elif (re.match(dict_regex, text)):
                    search_pattern = list_regex
                    entry = self.readFromXML(re.search(dict_regex, text).group(1), dict) # recursive f'n call for nested dicts

                elif (re.match(set_regex, text)):
                    search_pattern = set_regex
                    entry = self.readFromXML(re.search(set_regex, text).group(1), set) # recursive f'n call for nested sets

                else:
                    sys.exit("Error in readFromXML, data does not match any expected type: " + str(text))

                if(text_type is list):
                    output.append(entry)
                elif text_type is dict:
                    output[key] = entry
                elif text_type is set:
                    output.add(entry)

                text = re.sub(search_pattern,"",text) # removal of pattern from text to meet while loop condition

                # track iterations and break on 100 as a safety measure against getting stuck in this loop
                iter = iter + 1
                if(iter >= 100):
                    sys.exit("Error in readFromXML, can't exit while loop")

        else:
            sys.exit("Text does not match type structure passed to readFromXML: " + text +  ", " + str(text_type)) # *** idk if this works lol
        
        return output

    def readSetFromXML(self, text):
            # takes XML data for a list stored as one string (i.e. "[entry1, entry2, entry3]") and re-constructs the list as string entries. 
            # Converts whole number entries to int type instead of string. 
            out_set = set()
            iter = 0
            list_regex_pattern = r"(\A\[.+\])(,\s){0,1}"
            int_regex_pattern = r"(\A-{0,1}[0-9]+)(,\s){0,1}"
            string_regex_pattern = r"(\A[A-Za-z0-9]+)(,\s){0,1}"

            if(re.match(r"\A\{.*\}\Z",text)): # check if text represents a set
                
                text = re.sub(r"\A\{","",text) # remove starting and ending brackets from text (text is used to check if all entries are read)
                text = re.sub(r"\}\Z","",text) 
    
                # iterate while text still has characters
                while(text): 
                    # check if text matches the pattern for a nested list, an int, or default to string
                    if(re.match(list_regex_pattern, text)):
                        search_pattern = list_regex_pattern
                        entry = self.readListFromXML(re.search(list_regex_pattern, text).group(1)) # recursive f'n call for nested lists
                    elif(re.match(int_regex_pattern, text)):
                        search_pattern = int_regex_pattern
                        entry = int (re.search(search_pattern,text).group(1))
                        
                    else:
                        search_pattern = string_regex_pattern
                        entry = re.search(search_pattern,text).group(1)
    
                    out_set.add(entry)
                    text = re.sub(search_pattern,"",text) # removal of pattern from text to meet while loop condition
    
                    # track iterations and break on 100 as a safety measure against getting stuck in this loop
                    iter = iter + 1
                    if(iter >= 100):
                        sys.exit("Error in readDictFromXML, can't exit while loop")
            
            elif not(re.match(r"\Aset\(.*\)\Z",text)): # if it's an empty set, it looks like this for some reason idk
                sys.exit("Non-set passed to readSetFromXML: " + text)
            
            return out_set

    def addAction(self, action_keyword, max_targets = 0):
        self.action_keywords.append(action_keyword)
        if("max_targets" in action_dict[action_keyword]):
            self.max_targets.append(action_dict[action_keyword]["max_targets"])
        else:
            self.max_targets.append(max_targets) # variable max_targets can be input to addAction