import re
import sys
from global_def import faction_dict
from global_def import role_class_dict
from global_def import action_dict
from global_def import startsWVowel

# define what is imported from file
__all__ = ["player", "bodyguardClass", 
           "medicClass", "veteranClass", 
           "craigClass",
           "necroClass", 
           "doomClass"]

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
                "cleaned" :  int(perpetuated_element.find("cleaned").text),
                "doused_by" : self.readFromXML(perpetuated_element.find("doused_by").text, list),
                "living_status" : int(perpetuated_element.find("living_status").text),
                "potions" : int(perpetuated_element.find("potions").text),
                "gained_temp_immunities" : set()
            }
            self.active_temp_immunities = self.readFromXML(perpetuated_element.find("gained_temp_immunities").text, set)
            
        else:
            self.perpetuated = {
                "appearance" : self.player_num,
                "cleaned" : 0,
                "doused_by" : [],
                "living_status" : 1,
                "potions" : 0,
                "gained_temp_immunities" : set()
            }

        if(self.perpetuated["potions"] > 0):
            self.addAction("drinking potion") #*** need to verify this is correct lol
            self.max_actions = 1

        if("perpetuated" in role_class_dict[self.role_name]):
            self.updatePerpetuated(perpetuated_element)

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
            #case 'Shapeshifter':
                # *** need some manner of tracking the loss of action
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
            # ***Exe
            #case 'Executioner':
                #if(self.perpetuated["target"] is None): # Night 1, assign target
            case 'Jester':
                if night_num == 1:
                    self.addAction("vesting")
                    self.max_actions += 1
                if self.perpetuated["living_status"] == 0: # *** this needs an actual condition
                    self.addAction("haunting")
                    self.max_actions += 1
            case _:
                for static_action in role_class_dict[self.role_name]["actions"]:
                    self.addAction(static_action)
                    self.max_actions += 1

    # *** If I do need variable inputs for the act function, I can define number of input arguments in roles_dict maybe?
    def act(self, action_obj):
        # *** I may do error checking on actions here instead of when creating the action objects, idk
        return 1

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
        dict_key_regex = r"\A([^:]+)\s{0,1}:\s{0,1}"
        dict_value_regex = r"\A.+\s{0,1}:\s(.+),{0,1}"
        set_regex = r"\A\{.+\}(,\s){0,1}"
        int_regex = r"(\A-{0,1}[0-9]+)(,\s){0,1}"
        string_regex = r"\A\'([A-Za-z0-9]+(\s){0,1})+\'(,\s){0,1}" 

        if text_type is int:
            return int (text)
        elif text_type is str:
            return re.match(string_regex, text).group(1) # *** might be better/more robust ways to do this
        elif text_type is list:
            output = [] 
            structure_regex = [r"\A\[", r"\]\Z"]
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

        if(re.match(structure_regex[0] + r".*" + structure_regex[1], text)): # check if text represents the provided type structure
            text = re.sub(structure_regex[0],"",text) # remove starting and ending brackets from text (text is used to check if all entries are read)
            text = re.sub(structure_regex[1],"",text) 

            # iterate while text still has characters
            while(text): 
                if text_type is dict:
                    key = re.search(dict_key_regex, text).group(1)
                    if (re.match(int_regex, key)):
                        key = int (key)
                    elif (re.match(string_regex, key)):
                        key = re.match(string_regex, text).group(1)
                    text = re.sub(dict_key_regex,"",text)

                # check if text matches the pattern for a nested list, an int, or default to string
                if (re.match(int_regex, text)):
                    search_pattern = int_regex
                    entry = int (re.search(search_pattern,text).group(1))

                elif(re.match(string_regex, text)):
                    search_pattern = string_regex
                    entry = re.search(search_pattern,text).group(1)

                elif (re.match(list_regex, text)):
                    search_pattern = list_regex
                    entry = self.readFromXML(re.search(list_regex, text).group(1), list) # recursive f'n call for nested lists

                elif (re.match(dict_regex, text)):
                    search_pattern = dict_value_regex
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

class bodyguardClass (player): 
    def __init__(self, player_name, player_num, role_name, night_num = 0, perpetuated_element = None):
        super().__init__(player_name, player_num, role_name, night_num, perpetuated_element)
        self.addAction("protecting")

        if(self.perpetuated["vest"]):
            self.addAction("vesting")

        self.max_actions += 1

    def act(self, action_obj):
        match action_obj.action:
            case "vesting":
                self.perpetuated["vest"] = 0
            case _:
                pass
        return 1

class medicClass (player): 
    def __init__(self, player_name, player_num, role_name, night_num = 0, perpetuated_element = None):
        super().__init__(player_name, player_num, role_name, night_num, perpetuated_element)

        added_action = 0

        if not ((night_num - 1) % 2):
            self.perpetuated["lim_action"] = 1

        if self.perpetuated["lim_action"]:
            added_action = 1
            self.addAction("saving")

            if self.perpetuated["self-save"]:
                self.addAction("self-saving")

            if self.perpetuated["loaded"]:
                self.addAction("shooting")

        if self.perpetuated["bullets"]:
            self.addAction("loading")
            added_action = 1

        self.max_actions += added_action

    def act(self, action_obj):
        match action_obj.action:
            case "loading":
                self.perpetuated["bullets"] -= 1
                self.perpetuated["loaded"] = 1
            case "saving":
                self.perpetuated["lim_action"] = 0
            case "self-saving": 
                self.perpetuated["lim_action"] = 0
                self.perpetuated["self-save"] = 0 # *** Implement restore self-save on success in kill resolution?
            case "shooting":
                self.perpetuated["lim_action"] = 0
                self.perpetuated["loaded"] = 0
            case _:
                return 0

        return 1
class veteranClass (player): 
    def __init__(self, player_name, player_num, role_name, night_num = 0, perpetuated_element = None):
        super().__init__(player_name, player_num, role_name, night_num, perpetuated_element)
        if self.perpetuated["alerts"] > 0:
            if night_num > 1:
                self.addAction("alerting")
            if self.perpetuated["vest"]:
                self.addAction("vesting")
            self.max_actions += 1

    def act(self, action_obj):
        match action_obj.action:
            case "alerting":
                self.perpetuated["alerts"] -= 1

            case "vesting":
                self.perpetuated["alerts"] -= 1
                self.perpetuated["vest"] = 0

        return 1

class craigClass (player): # I am contractually obligated to specify that Craig means Shapeshifter.
    def __init__(self, player_name, player_num, role_name, night_num = 0, perpetuated_element = None):
        super().__init__(player_name, player_num, role_name, night_num, perpetuated_element)

        if not ((night_num - 1) % 3):
            self.perpetuated["action"] = 1

        if (self.perpetuated["action"]):
            self.addAction("blackmailing")
            self.addAction("blocking")
            self.addAction("cleaning")
            self.addAction("disguising")
            self.addAction("investigating")
            self.addAction("stalking")
            self.addAction("transporting")
            self.max_actions += 1

    def act(self, action_obj):
        # *** The one case where this gets tricky is if transporting and gets cancelled by Witch control
        self.perpetuated["action"] = 0

        # *** Need to add further stipulation about not transporting the target of a Mafia kill
        # because killing is lower on the priority list, I may check that as part of killing/arming? idk
        return 1

necro_actions_dict = {
    "Medium" : ["disguising"],
    "Retributionist" : ["disguising"],
    "Bodyguard" : ["protecting", "vesting"],
    "Medic" : ["alerting"],
    "Trapper" :  ["alerting"],
    "Veteran"  : ["alerting"],
    "Vigilante"  : ["alerting"],
    "Mafioso"  : ["investigating"],
    "Ritualist" : ["investigating"],
    "Shapeshifter" : ["investigating"],
    "Necromancer"  : ["investigating"],
    "Serial Killer ": ["cleaning"],
    "Werewolf" : ["stalking"],
    "Amnesiac" : ["transporting"],
    "Doomsayer" : ["transporting"],
    "Jester" : ["transporting"]
}

class necroClass (player):
    def __init__(self, player_name, player_num, role_name, night_num = 0, perpetuated_element = None):
        super().__init__(player_name, player_num, role_name, night_num, perpetuated_element)
        self.action_to_role_map = {}
        self.max_actions += 2
        super().addAction("hexing")
        if self.perpetuated["dead_roles"]:
            for dead_role in self.perpetuated["dead_roles"]:
                self.addAction(dead_role)
                
        else:
            super().addAction("investigating") # *** find way to make exact

    def addAction(self, dead_role):
        if dead_role in necro_actions_dict:
            options_source = necro_actions_dict[dead_role]

        else:
            options_source = role_class_dict[dead_role]["actions"] # *** needs tested
        
        for opt in options_source:
            super().addAction(opt)
            if opt in self.action_to_role_map:
                self.action_to_role_map[opt].append(dead_role)
            else:
                self.action_to_role_map[opt] = [dead_role]

    def act(self, action_obj): # *** need a way to distinguish between investigates
        if (self.perpetuated["dead_roles"]) and (action_obj.action != "hexing"):
            role_used = self.action_to_role_map[action_obj.action][0]
            self.perpetuated["dead_roles"][role_used] -= 1
            if not self.perpetuated["dead_roles"][role_used]:
                self.perpetuated["dead_roles"].pop(role_used, None)

            match action_obj.action:
                # *** add cleans
                case "disguising":
                    if not self.perpetuated["active_disguise"]:
                        self.perpetuated["active_disguise"] = [-1, -1]
                case "dousing":
                    if not self.perpetuated["douses"]:
                        self.perpetuated["douses"] = []

    def getDeathInfo(self, player, is_vote = 0):
        if startsWVowel(player.role_name):
            result = "an"
        else:
            result = "a"
        result = player.player_name + " was " + result + " " + player.role_name + "! "
        #result += "You may now " # *** I'm lazy rn, might implement later
        self.notifications.append(result)
        self.perpetuated["dead_roles"][player.role_name] = self.perpetuated["dead_roles"].get(player.role_name, 0) + 1
        
        if is_vote:
            self.addAction(player.role_name)

class doomClass (player):
    def __init__(self, player_name, player_num, role_name, night_num = 0, perpetuated_element = None):
        super().__init__(player_name, player_num, role_name, night_num, perpetuated_element)

        self.max_actions += 1
        if night_num == 1:
            self.addAction("checking")

        else:
            self.addAction("dooming")

    # *** is act f'n necessary?