import re
import sys
from global_def import faction_dict
from global_def import role_class_dict
from global_def import action_dict
from global_def import startsWVowel

# define what is imported from file
__all__ = ["player", 
           "alchClass", "bodyguardClass", "docClass",
           "vigiClass", "medicClass", "veteranClass", 
           "janitorClass", "mafiosoClass", "craigClass",
           "werewolfClass",
           "necroClass", 
           "doomClass"]

class player:  
    def __init__(self, player_name, player_num, role_name, night_num = 0, perpetuated_element = None): 
# region Function: player.__init__ 
##############################################################################################################################
# Class: player
# in:
# str player_name: player's name
# int player_num: player's ordered number in the game.players list
# str role_name: player's role
# int night_num: night number for the evaluation. default 0 for game initialization
# ***Elem perpetuated_element: XML tree element for perpetuated player information. default to None for game initialization
#
# out: None
#
# Description:
# Initializes player class object. 
# When initializing the game (perpetuated_element defaulted to None), sets common perpetuated values appropriately
# and pulls role-specific perpetuated variables from role_class_dict by calling self.updatedPerpetuated() method. 
# When evaluating a night, reads all perpetuated information in perpetuated_element by calling self.readFromXML on all 
# common fields and self.updatePerpetuated() for all class-dependent fields.
##############################################################################################################################
# endregion 
        self.player_name = player_name

        # non-perpetuated class variables for evaluating night actions
        self.actions = []
        #self.attackers = []
        self.blackmailed = 0
        self.blocked = 0 
        self.controlled = 0
        self.hallowed = 0 # *** name is weird, idc about that so much, but this may not need to be set unless it actually
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

    ## Player Class Helper Functions
    def updatePerpetuated (self, perpetuated_element):
    # region Function: player.updatePerpetuated()
    ##############################################################################################################################
    
    # Class: player
    # in:
    #   ET.Element perpetuated_element: XML Tree Element corresponding to a player's "perpetuated" tag in XML status doc. Used to 
    #   track role information across nights. If perpetuated_element is None, the player is being initialized. 
    # out:
    #   None
    # Description: 
    #   Use role_class_dict for the given role name to iterate through all expected items on the perpetuated list. 
    #   Pull data from the perpetuated_element if it exists, otherwise set to default from role_class_dict. 
    ##############################################################################################################################
    # endregion
        if(perpetuated_element):
            for expected_elem, default_value in role_class_dict[self.role_name]["perpetuated"].items():
                expected_type = type(default_value)
                self.perpetuated[expected_elem] = self.readFromXML(perpetuated_element.find(expected_elem).text, expected_type)
            
        else:
            for expected_elem, default_value in role_class_dict[self.role_name]["perpetuated"].items():
                self.perpetuated[expected_elem] = default_value 

    def readFromXML(self, text, text_type):
    # region Function: player.readFromXML
    ##############################################################################################################################
    # Class: player
    # in:
    # str text: Text string to be parsed. 
    # text_type: Expected type of the output. Determined using regex to classify the text input.
    # out:
    # Will output the text parsed and cast as the appropriate type.
    # Description:
    # Takes text input as it appears in the XML status file and parses it for use. 
    # Can handle str, int, set, dict, and lists.
    # Will recursively call itself to handle nested lists, sets, dicts. 
    ##############################################################################################################################
    # endregion
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

    def addAction(self, action_keyword, max_targets = 0):
    # region Function: player.addAction
    ##############################################################################################################################
    # Class: player
    # in:
    # str action_keyword: Action keyword to be added to list of potential actions for the player.
    # int max_targets: Maximum number of targets available to be selected for this action.
    #
    # out:
    # None
    # Description:
    # Adds the provided action keyword to action_keywords list attribute. 
    # Either pulls the appropriate number of maximum targets from action_dict, if available, or 
    # uses the provided max_targets value if not and appends to max_targets list attribute.
    ##############################################################################################################################
    # endregion
        self.action_keywords.append(action_keyword)
        if("max_targets" in action_dict[action_keyword]):
            self.max_targets.append(action_dict[action_keyword]["max_targets"])
        else:
            self.max_targets.append(max_targets) # variable max_targets can be input to addAction

class alchClass (player): # *** class not tested
    def __init__(self, player_name, player_num, role_name, night_num = 0, perpetuated_element = None):
        super().__init__(player_name, player_num, role_name, night_num, perpetuated_element)
        if night_num == 0:
            self.perpetuated["delivered_potions"].add(player_num) # start with self potion

        if night_num <= 2:
            self.addAction("delivering to", 2)
        else:
            self.addAction("delivering to", 1)
        self.max_actions += 1

        if self.perpetuated["delivered_potions"]:
            self.addAction("activating") # *** need to allow activation targets
            self.max_actions += 1

        def act(self, action_obj):
            match action_obj.action:
                case "activating":
                    for target in action_obj.targets:
                        if target.player_num in self.perpetuated["delivered_potions"]:
                            self.perpetuated["delivered_potions"].remove(target.player_num)
                        else:
                            sys.exit("Error in alchClass.act: Potion activation on " + target.player_name + " when they don't have a potion from " + self.player_name + ".")
                case "delivering to":
                    for target in action_obj.targets:
                        if target is not self:
                            if target.player_num not in self.perpetuated["delivered_potions"]:
                                self.perpetuated["delivered_potions"].add(target.player_num)
                            else:
                                sys.exit("Error in alchClass.act: " + target.player_name + " already has a potion from " + self.player_name + ".")
                        else:
                            sys.exit("Error in alchClass.act: " + self.player_name + " attempting to give potion to self.")

# Medium stuff
# *** this actually needs to be wrapped up in the blocking/controlling resolution, but it's fine for now
    #if action_obj.targets[0] == action_obj.player:
    #    if action_obj.player.perpetuated["self-hallow"]:
    #        action_obj.player.perpetuated["self-hallow"] = 0
    #    else:
    #        sys.exit("Error, indicated self-hallow when unavailable.")

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

class docClass (player):
    def __init__(self, player_name, player_num, role_name, night_num = 0, perpetuated_element = None):
        super().__init__(player_name, player_num, role_name, night_num, perpetuated_element)

        if self.perpetuated["self-save"]:
            self.addAction("self-saving")

    def act(self, action_obj):
        match action_obj.action:
            case "saving":
                if action_obj.targets_player_num != self.player_num:
                    return 1
                else:
                    sys.exit("Error in docClass.act: " + self.player_name + " self-saving without using self-save action.") # *** needs tested
            case "self-saving":
                self.perpetuated["self-save"] = 0 # *** need to restore on success

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

class vigiClass (player): 
    def __init__(self, player_name, player_num, role_name, night_num = 0, perpetuated_element = None):
        super().__init__(player_name, player_num, role_name, night_num, perpetuated_element)

        if self.perpetuated["bullets"] > 0 and not self.perpetuated["loaded"]:
            self.addAction("loading")
            self.max_actions += 1
        elif self.perpetuated["loaded"]:
            self.addAction("shooting")
            self.max_actions += 1

    def act(self, action_obj):
            match action_obj.action:
                case "loading":
                    self.perpetuated["bullets"] -= 1
                    self.perpetuated["loaded"] = 1
                case "shooting":
                    self.perpetuated["loaded"] = 0
                case _:
                    return 0
    
            return 1 
    
class janitorClass (player):
    def __init__(self, player_name, player_num, role_name, night_num = 0, perpetuated_element = None):
        super().__init__(player_name, player_num, role_name, night_num, perpetuated_element)
        if (self.perpetuated["cleans"] > 0):
            self.addAction("cleaning")
            self.max_actions += 1

    def act(self, action_obj):
        self.perpetuated["cleans"] -= 1
        self.perpetuated["cleans_on"].add(action_obj.targets[0].player_num)

class mafiosoClass (player):
    def __init__(self, player_name, player_num, role_name, night_num = 0, perpetuated_element = None):
        super().__init__(player_name, player_num, role_name, night_num, perpetuated_element)
        if(self.perpetuated["shot"]):
            self.addAction("killing")
            self.max_actions += 1

    def act(self, action_obj):
        self.perpetuated["shot"] = 0 # *** needs to restore on failure

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
    
class werewolfClass (player): 
    def __init__(self, player_name, player_num, role_name, night_num = 0, perpetuated_element = None):
        super().__init__(player_name, player_num, role_name, night_num, perpetuated_element)
        if night_num == 1 or night_num == 3:
            self.addAction("stalking",1)
        else:
            self.addAction("mauling",1)
        self.max_actions += 1

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
    "Jester" : ["transporting"],
    "Janitor" : ["cleaning"] # ***
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