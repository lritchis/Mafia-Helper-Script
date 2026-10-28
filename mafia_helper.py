import re
import sys
from pathlib import Path
import xml.etree.ElementTree as ET
import bisect
import random as r
from player_classes import *
from global_def import *

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
        self.notify_for_deaths = [] # list to hold Amnesiacs and Necromancers that learn information for every death
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

            match (role_name): # *** We can probably make a more efficient check here to avoid checking against all cases every time
                case "Bodyguard": 
                    player_obj = bodyguardClass(player_name, player_num, role_name, self.night_num, perpetuated_element)
                case "Medic":
                    player_obj = medicClass(player_name, player_num, role_name, self.night_num, perpetuated_element)
                case "Veteran":
                    player_obj = veteranClass(player_name, player_num, role_name, self.night_num, perpetuated_element)
                case "Shapeshifter":
                    player_obj = craigClass(player_name, player_num, role_name, self.night_num, perpetuated_element)
                case "Necromancer":
                    player_obj = necroClass(player_name, player_num, role_name, self.night_num, perpetuated_element)
                    self.notify_for_deaths.append(player_obj)
                case _:
                    player_obj = player(player_name, player_num, role_name, self.night_num, perpetuated_element)

            self.players.append(player_obj)
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

            if not (action_obj.cancelled):
                if action_obj.targeted: 
                    if action_obj.is_visit:
                        action_obj.cancelled = self.processVisit(action_obj)
                    # *** else statement might go here to do targeted non-visits. Right now that would hurt some Arso functionality so I'll decided later

                # *** PLAN: Transports, controls, blocks, hallows, and traps will be set as non-visits and then visits assigned manually in
                # resolution f'n
                # *** need to implement immunities
                if not (action_obj.cancelled): # checking this again feels kinda gross but idk how to do that more cleanly 
                    # resolve any role-specific resource tracking or limitations # *** could word this comment better later
                    if(getattr(action_obj.player, "act", 0)): # *** I should check this sooner and have the resolve actions in their own space? idk
                        action_obj.player.act(action_obj)

                    match (action_obj.action):
                        # *** one line actions resolved here, more complex ones resolved in standalone f'ns
                        #case 'haunting':
                            # *** Temp, can let it randomly determine a Townie to kill (or maybe allow both?)
                            #self.killPlayer(target_inds[0],action_obj.action)
                        case 'reviving':
                            target = self.getTargetPlayerAbs(action_obj.targets[0])
                            if target.perpetuated['living_status'] == 1:
                                sys.exit("Error, Retributionist cannot revive a living player. (" + 
                                            action_obj.player.player_name + " reviving " + target.player_name + ")")
                        case 'jailing': 
                            action_obj.targets[0].jailed = 1
                            # sets cannot_execute from 1 to 0 for the next night. Code has already verified against an illegal execution
                            # by not adding "executing" to Jailor's action keywords when initialized
                            action_obj.player.cannot_execute = 0 
                        case 'alerting':
                            action_obj.player.alerting = 1
                        case 'transporting':
                            # *** Wording needs checked, also untested
                            if action_obj.targets[0].jailed == 1:
                                action_obj.player.notifications.append("Your transport failed!")
                                action_obj.targets[0].notifications.append("Someone tried to transport you, but you were in jail!")
                            elif action_obj.targets[1].jailed == 1:
                                action_obj.player.notifications.append("Your transport failed!")
                                action_obj.targets[1].notifications.append("Someone tried to transport you, but you were in jail!")
                            else:
                                transporting = self.findResolutionObj(action_obj)
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
                            # *** need to check against immunities
                            action_obj.targets[0].notifications.append("You were controlled!")
                            result = action_obj.targets[0].role_name                
                            if startsWVowel(result):
                                result = "an " + result
                            else:
                                result = "a " + result

                            action_obj.player.notifications.append("Your target is " + result + "!")

                        case "trapping":
                            for target in action_obj.targets:
                                target.trappers_targeting.append(action_obj.player)
                            print("***Needs implemented")
                        case "hallowing":
                            # *** this actually needs to be wrapped up in the blocking/controlling resolution, but it's fine for now
                            if action_obj.targets[0] == action_obj.player:
                                if action_obj.player.perpetuated["self-hallow"]:
                                    action_obj.player.perpetuated["self-hallow"] = 0
                                else:
                                    sys.exit("Error, indicated self-hallow when unavailable.")
                            action_obj.targets[0].hallowed = 1
                        case 'delivering to':
                            print("***Still needs implemented, dingus!")
                        case 'protecting':
                            self.updateKillDicts(action_obj, self.defenses_dict)
                        case 'saving':
                            self.updateKillDicts(action_obj, self.defenses_dict)
                        case 'vesting': 
                            action_obj.player.vesting = 1
                            #self.updateKillDicts(action_obj.player.player_num, action_obj, self.defenses_dict)

                            # idk why I had this at all
                            #if action_obj.player.role != "Necromancer":
                            #    action_obj.player.perpetuated["vests"] -= 1
                            if action_obj.player.role_name == "Veteran":
                                action_obj.player.perpetuated["alerts"] -= 1
                        case 'killing': # *** both killing and shooting need work if restructuring attacks
                            self.updateKillDicts(action_obj, self.atks_dict)
                        case 'shooting':
                            self.updateKillDicts(action_obj, self.atks_dict)
                        case 'stabbing':
                            self.updateKillDicts(action_obj, self.atks_dict)
                        case 'mauling':
                            self.updateKillDicts(action_obj, self.atks_dict)
                        case 'blocking':
                            self.resolveBlock(action_obj.targets[0])
                        case 'disguising':
                            # *** need to determine if a new disguise is disrupting non-detereminant old diguises
                            disguising = self.findResolutionObj(action_obj)
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
                            self.resolveBlackmails(action_obj)
                        case 'cleaning':
                            # *** need to evaluate if all uses of getTargetPlayer are correct or if abs is needed
                            #*** I need to lower the number of cleans. But in reality I need to track resources separately from here somehow.
                            action_obj.targets[0].perpetuated["cleaned"] = 1
                        case 'dousing':

                            action_obj.player.perpetuated["first_douse"] = 0 # no need to check if it's 1, just assign it to 0

                            for target in action_obj.targets:
                                target.perpetuated["doused_by"].append(action_obj.player.player_num) # *** still to do activations, plus removing if Arso dies
                                action_obj.player.perpetuated["douses"].append(target.player_num)
                        case 'investigating':
                            if action_obj.player.role_name == "Investigator":
                                if(action_obj.targets[0].perpetuated["doused_by"]):
                                    result = investigator_categories_dict["Arsonist"]
                                else:
                                    result = investigator_categories_dict[self.getPlayerAppearance(action_obj.targets[0],"role")]

                            else: #(action_obj.player.role_name == "Consigliere") | (action_obj.player.role_name == "Necromancer"):
                                if(action_obj.targets[0].perpetuated["doused_by"]):
                                    result = "Arsonist"
                                else:
                                    result = self.getPlayerAppearance(action_obj.targets[0],"role")
                                
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
                                observing = actionObject("determineVisits", [action_obj.player], targets = [action_obj.targets[0]])
                                observing.priority.append(action_obj.priority)
                                self.action_queue.append(observing)
                            else:
                                for remaining_action in self.action_queue: # *** this needs thorough testing
                                    if  remaining_action.action == "determineVisits":
                                        remaining_action.priority.append(action_obj.priority)
                                        remaining_action.player.append(action_obj.player)
                                        remaining_action.targets.append(action_obj.targets[0])
                                        break
                        case 'determineVisits':
                            self.determineVisits(action_obj)
                        case 'wiretapping':
                            for target_num in action_obj.targets:
                                self.players[target_num].notifications.append("You were wiretapped!")
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
                            # pass # uncomment eventually for null actions like loading
                
            self.action_queue.pop(0)

        # *** TO-DO here:
        #       -add indeterminancy info
        #       -add BG/Arso interaction
        #       -add BG/Mafioso interaction
        #       -add vest/shield/jail functionality
        #       -fix WW "you attacked someone!"
        #       -add WW immunity flag?
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

                                    self.updateKillDicts(actionObject("sacrificing", defense_obj.player, [defense_obj.player]), self.atks_dict)
                                    self.updateKillDicts(actionObject("counterattacking", defense_obj.player, [attack_obj.player]), self.atks_dict)

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
                                self.updateKillDicts(actionObject("mauling_visitor", maul.player, [visitor]), self.atks_dict)
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

                        defense_state = self.resolveAtkDefense(attack_obj, atk_state, defense_obj, defense_state, player_num)

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
    def resolveAtkDefense(self, attack_obj, atk_state, defense_obj, defense_state, player_num):
        # *** Update to distinguish between cases
        self.players[player_num].notifications.append("Someone tried to attack you, but you were saved!")
        self.players[defense_obj.player.player_num].notifications.append("Someone tried to attack [TARGET] but you saved them!")
        self.players[attack_obj.player.player_num].notifications.append("Your attack failed!")

        self.defenses_dict[player_num].actions[defense_state].pop(0)

        if (not self.defenses_dict[player_num].actions[defense_state]): # exhausted actions in this atk state, list empty
            del self.defenses_dict[player_num].actions[defense_state]
            defense_state = self.defenses_dict[player_num].determineState(from_start = 1, skip_bg = 1)

        return defense_state


    def processVisit(self, action_obj):
        # *** Trap and hallow still need to be integrated into f'n to process transports and cancels
        for i in range(len(action_obj.targets)):
            action_obj.targets[i] = self.getTargetPlayer(action_obj.targets[i])
            action_obj.targets[i].visitors.append(action_obj.player) 

        for target in action_obj.targets:
            if getattr(target, "alerting", 0): # *** this needs to be tested
                # *** I think this has issues cancelling multi-target actions # I doh't think this should be an issue anymore but not tested
                # an alerting player can never be transported, so using self.players list directly
                self.updateKillDicts(actionObject("alerting", target, [action_obj.player]), self.atks_dict)
                action_obj.cancelled = 1
                return 1
                      
        if (action_obj.player.faction >= faction_dict["non-Town"]):
            for target in action_obj.targets:
                if (target.trappers_targeting):
                    for trapper in target.trappers_targeting:
                        if(action_obj.player.player_num in trapper.perpetuated["traps_landed"]):
                            trapper.perpetuated["traps_landed"].remove(action_obj.player.player_num)
                            trapper.perpetuated["num_traps"] = 1
                            self.updateKillDicts(actionObject("trapping_atk", trapper, [action_obj.player]), self.atks_dict)
                            trapper.notifications.append("Your trap on " + target.player_name + " attacked someone!") # *** need to sort out, probably
                                # *** Need to cancel action (not implemented properly) # idk if this is still true
                            action_obj.cancelled = 1
                            return 1
                        
                        else:
                            trapper.perpetuated["traps_landed"].add(action_obj.player.player_num)
                            action_obj.player.notifications.append("You were trapped!")
                            trapper.notifications.append("Your trap on " + target.player_name + " was activated!") # *** re-write so only one noti
            
        # *** this whole f'n needs work, but everything below here hasn't even been considered
            # *** note hallow not currently cancelling the visit
            if "hallow_cancels" in action_dict[action_obj.action]:
                for target in action_obj.targets:
                    if target.hallowed:
                        action_obj.player.notifications.append("Your " + action_obj.action + " was blocked by the Medium's hallow!")
                        action_obj.cancelled = 1

                if action_obj.cancelled:
                    for target in action_obj.targets:
                        target.visitors.remove(action_obj.player)
                    return 1

        return 0

    def updateKillDicts(self, action_obj, update_dict):
        # there might be more efficient logic here, rn it adds the affected_player_num to the dict if it 
        # isn't there and then checks against the particular action being in the dict
        affected_player_num = action_obj.targets[0].player_num
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

            for notified_player in self.notify_for_deaths: # *** we could integrate kills into action queue and queue this notification for Amnes/Necros, idk. should consider
                notified_player.getDeathInfo(self.players[player_num])
        
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
                # *** needs to be updated to use "the" for unique roles
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
    def queueResolution(self, action_obj): # *** This needs improved, at least to output the resolution object
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
    def findResolutionObj(self, action_obj, resolution_exists = 0): # *** need to go back and use this for BM and such. plus target_inds usage change
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
        target = action_obj.targets[0]
        if "blackmailing" in target.active_temp_immunities:
            target.notifications.append("Someone tried to blackmail you but you were blackmailed the previous night!")

        else:
            noti_string = ("You were blackmailed!\n\n" 
                        "You cannot speak, except for saying 'I am blackmailed' exactly once.\n"
                        "You may vote one time, but you cannot use your vote to communicate information beyond wanting to vote for that person.\n\n")

            # *** this needs to be made optional maybe (leaving for later)
            if(target.faction >= faction_dict["non-Town"]):
                noti_string = noti_string + "Someone tried to blind you, but you are unaffected!"
            else:
                noti_string = noti_string + "You were also blinded! You did not receive any non-essential night notifications." 

            target.notifications.append(noti_string)

            target.perpetuated["gained_temp_immunities"].add("blackmailing")
                            # Old BMer notification
                            #"You were blackmailed!\n\n" \
                            #"You cannot speak, except for saying, 'I am blackmailed,' exactly once.\n" \
                            #"You may not vote, you may only abstain, but you cannot use your abstain to communicate information.")

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
                visitors = action_obj.targets[obs_ind].visitors.copy() # *** Abs because visitors assigned already. Another sign to replace target_inds
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

                tracked_target = self.getPlayerAppearance(action_obj.targets[obs_ind]) # disguises swap who is effectively being tracked
                
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
                                + " tracking " + action_obj.targets[obs_ind].player_name 
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
                                + " tracking " + action_obj.targets[obs_ind].player_name 
                                + ", " + self.players[result].player_name 
                                + " chosen from list of all visits tonight. (" + str(len(all_visits)) + " total)"
                                )
                        self.indeterminant.append(indet_string)

                player.notifications.append("Your target visited " + self.players[result].player_name + "!")
                if(action_obj.targets[obs_ind].faction >= faction_dict["Mafia"]):
                    action_obj.targets[obs_ind].notifications.append("You were tracked! They saw you visit "
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
            # *** can probably put a break here, or just make players a dict tbh
        
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

        for player_actions in eval_obj.actions_list:
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
                node_set = eval_obj.node_set_by_player[action_obj.targets[0].player_num]
                
                now_static_targets = 0
    
                for target in action_obj.targets:
                    if same_night:
                        target.visitors.remove(self.players[acting_player_num])
    
                    node_set["targets"][target.player_num] -= 1
                    if node_set["targets"][target.player_num] < 1:
                        now_static_targets += 1
                        node_set["targets"].pop(target.player_num, None)
                        #eval_obj.affected_locations[target] = 0

                        if(hasattr(eval_obj, "cancel_list")):
                            self.player_locations[target.player_num] = target.player_num
                            if eval_obj.actions_list[target.player_num] and eval_obj.cancel_list[target.player_num]:
                                self.cancelNodeAction(eval_obj, node_list, target.player_num) # recursive cancellations
    
                node_set["actions"].remove(action_obj)
    
                if(now_static_targets == 2): # both targets had only one action affecting them
                    node_list.remove(node_set)
                    if(node_set in eval_obj.nxt_nodes_to_eval):
                        eval_obj.nxt_nodes_to_eval.remove(node_set)
                    for target_num in node_set["targets"]:
                        eval_obj.node_set_by_player[target_num] = None
    
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
    
                        #node_list_len = len(node_list)

                        for new_set in split_node_sets:
                            for target_num in new_set["targets"]:
                                eval_obj.node_set_by_player[target_num] = new_set
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
        t0 = action.targets[0].player_num
        t1 = action.targets[1].player_num
            
        if (node_set_by_player[t0]) or (node_set_by_player[t1]):
            if (node_set_by_player[t0]) and (node_set_by_player[t1] and (node_set_by_player[t0] is not node_set_by_player[t1])):
                node_set = node_set_by_player[t0]
                merging_nodes = node_set_by_player[t1]
                #node_ind = node_list.index(node)
                node_set.update(merging_nodes)

                for merge_player_num in merging_nodes["targets"]:
                    node_set_by_player[merge_player_num] = node_set

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
                t0 = self.getTargetPlayerAbs(active_disguise[0].targets[0]) # *** has been changed to Abs because it should not follow transports; not tested
                t1 = self.getTargetPlayerAbs(active_disguise[0].targets[1])
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
                self.affected_locations[target.player_num] = 1

        if cancel_list is not None:
            self.cancel_list = [None] * num_players
            for cancellation in cancel_list:
                if self.cancel_list[cancellation.targets[0]]: # *** as implemented currently, this should still work. still a player number instead of a player object.
                    self.cancel_list[cancellation.targets[0]].append(cancellation)
                else:
                    self.cancel_list[cancellation.targets[0]] = [cancellation] # target is in a list  

class roleSlot:
    def __init__(self, slot_name, role_name):
        self.slot_name = slot_name
        self.role_name = role_name
        