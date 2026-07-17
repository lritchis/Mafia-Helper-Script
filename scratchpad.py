##############################################################################################################################
# Function:
# Class: 
# in:
#   
# out:
#
# Description:
#
#
#
#
##############################################################################################################################

# If in JAL category
            if re.search(r'\AJAL\b',self.slot_name):
                role_regex = jailor_regex
                role_search = re.search(role_regex, text_input)
                # Error if Jailor is not the role assigned to JAL category
                if not role_search:
                    sys.exit("Error, Jailor role not assigned to JAL category: " + text_input)
                self.role = role_search.group()
                print(self.role)

            elif re.search(r'\ATI\d*\b',self.slot_name):
                role_regex = TI_regex
                role_search = re.search(role_regex, text_input)
                # Error if no valid TI role is assigned to a TI category
                if not role_search:
                    sys.exit("Error, no valid TI role assigned to " + self.slot_name + "category: " + text_input)


# create player class using remaining text as name
                match (self.role_name):
                    case 'Jailor':
                        self.player = jailorClass(text_input, self.role_name, living_status = 1, douse_status = 0, disguise = 0,
                                                executions = 3, cannot_execute = 0)
                    # default case (shouldn't ever happen? one hopes)
                    case _: 
                        self.player = playerClass(text_input, self.role_name, living_status = 1, douse_status = 0, disguise = 0)

common_sets = []
if(self.disguise_sets):
    for set_ind, disg_set in enumerate(self.disguise_sets):
        if((self.player_locations[target_inds[0]].player_num | self.player_locations[target_inds[1]].player_num) in disg_set):
                common_sets.append(set_ind)

    match len(common_sets):
        case 2: # both players appear in different sets
            for player_num in self.disguise_sets[common_sets[1]]: # merge sets
                self.disguise_sets[common_sets[0]].append(player_num)
            self.disguise_sets.pop(common_sets[1]) # remove old set
        
        case 1: # one of the players is in a set, add the other to that set
            if self.player_locations[target_inds[0]].player_num not in self.disguise_sets[common_sets[0]]:
                self.disguise_sets[common_sets[0]].append(self.player_locations[target_inds[0]].player_num)
            else:
                self.disguise_sets[common_sets[0]].append(self.player_locations[target_inds[1]].player_num)

        case 0: # new set
            self.disguise_sets.append([self.player_locations[target_inds[0]].player_num, self.player_locations[target_inds[1]].player_num])
else: # first set
    self.disguise_sets.append([self.player_locations[target_inds[0]].player_num, self.player_locations[target_inds[1]].player_num])





## Role Class and Child Classes        
class roleClass: # *** Class definitions as a whole need to be fixed to accept and then parse perpetuatedElement
    def __init__(self, player_num, role_name, perpetuated_element = None):
        
## Town Classes 
class townieClass (roleClass):
    def __init__(self, player_num, role_name, perpetuated_element = None):
        super().__init__(player_num, role_name, perpetuated_element)
        self.faction = faction_dict["Town"]     

## TI Classes
class investigatorClass (townieClass):
    def __init__(self, player_num, role_name, perpetuated_element = None):
        super().__init__(player_num, role_name, perpetuated_element)
        self.action_keywords.append("investigating")
        self.max_targets.append(1)
        self.max_actions = self.max_actions + 1

class lookoutClass (townieClass):
    def __init__(self, player_num, role_name, perpetuated_element = None):
        super().__init__(player_num, role_name, perpetuated_element)
        self.action_keywords.append("watching")
        self.max_targets.append(1)
        self.max_actions = self.max_actions + 1

class scientistClass (townieClass):
    def __init__(self, player_num, role_name, perpetuated_element = None):
        super().__init__(player_num, role_name, perpetuated_element)
        self.action_keywords.append("checking")
        self.max_targets.append(1)
        self.max_actions = self.max_actions + 1

class trackerClass (townieClass):
    def __init__(self, player_num, role_name, perpetuated_element = None):
        super().__init__(player_num, role_name, perpetuated_element)

        self.action_keywords.append("tracking")
        self.max_targets.append(1)
        self.max_actions = self.max_actions + 1

## TS Classes
class escortClass (townieClass):
    def __init__(self, player_num, role_name, perpetuated_element = None):
        super().__init__(player_num, role_name, perpetuated_element)

        self.immunities.extend(["blocking"])
        self.action_keywords.append("blocking")
        self.max_targets.append(1)
        self.max_actions = self.max_actions + 1

# class mediumClass (townieClass):

# class retributionistClass (townieClass):

# class transporterClass (townieClass):

## TP Classes
# class alchemistClass (townieClass):

# class bodyguardClass (townieClass):

# class clericClass (townieClass):

# class doctorClass (townieClass):

## TK Classes
# class medicClass (townieClass):

# class trapperClass (townieClass):

# class veteranClass (townieClass):

# class vigilanteClass (townieClass):

## Mafia Classes
class mafiaClass (roleClass):
    def __init__(self, player_num, role_name, perpetuated_element = None):
        super().__init__(player_num, role_name, perpetuated_element)
        self.faction = faction_dict["Mafia"]

class godfatherClass(mafiaClass): 
    def __init__(self, player_num, role_name, perpetuated_element = None):
        super().__init__(player_num, role_name, perpetuated_element)

        self.immunities.extend(["killing", "stabbing","shooting"])
        self.action_keywords.append("killing")
        self.max_targets.append(1)
        self.max_actions = self.max_actions + 1
    
    def determineAvailableWiretaps(self,categories_list, players_list):
        num_mafia_living = 1
        for player_ind, player in enumerate(players_list):
                if((re.search("RM",categories_list[player_ind].slot_name) != None) & (player.role.perpetuated["living_status"] == 1)):
                    num_mafia_living = num_mafia_living + 1

        self.action_keywords.append("wiretapping")
        self.max_targets.append(num_mafia_living) 
        self.max_actions = self.max_actions + 1

class blackmailerClass (mafiaClass):
    def __init__(self, player_num, role_name, perpetuated_element = None):
        super().__init__(player_num, role_name, perpetuated_element)
        
        self.action_keywords.append("blackmailing")
        self.max_targets.append(1)
        self.max_actions = self.max_actions + 1

class consigliereClass (mafiaClass):
    def __init__(self, player_num, role_name, perpetuated_element = None):
        super().__init__(player_num, role_name, perpetuated_element)
        
        self.action_keywords.append("investigating")
        self.max_targets.append(1)
        self.max_actions = self.max_actions + 1

class consortClass (mafiaClass):
    def __init__(self, player_num, role_name, perpetuated_element = None):
        super().__init__(player_num, role_name, perpetuated_element)
        
        self.immunities.extend(["blocking"])
        self.action_keywords.append("blocking")
        self.max_targets.append(1)
        self.max_actions = self.max_actions + 1

# class courierClass (mafiaClass):

class disguiserClass (mafiaClass):
    def __init__(self, player_num, role_name, perpetuated_element = None):
        super().__init__(player_num, role_name, perpetuated_element)
   
        self.action_keywords.append("disguising")
        self.max_targets.append(2)
        self.max_actions = self.max_actions + 1

        if(perpetuated_element):
            self.perpetuated.update ({
                "active_disguise" : self.readListFromXML(perpetuated_element.find("active_disguise").text)
            })
        else:
            self.perpetuated.update ({
                "active_disguise" : []
            })
# *** I think the best way to do disguises might be to evaluate them all as an Action that is queue'd after Disguiser actions
# Should make the functionality generic, I think Transporter logic will be the same?
    #def getApparentRole(self, origin = None): 
        # assess disguises and returns apparent role
        # *** I should spend some time thinking about this, there might be a recursive way to make this all nice
        #if (len(self.perpetuated["disguised"]) == 1): # disguises only work if there is one; two or more and you show up normally
        #    return self.perpetuated["disguised"][0].role.role_name # *** need to account for multiple disguises here
        #else:
        #    if((len(self.perpetuated["disguised"])) > 1 & (origin)):
                
        #    return self.role.role_name
# class janitorClass (mafiaClass):

# class mafiosoClass (mafiaClass):

# class craigClass (mafiaClass):
# I am contractually obligated to specify that Craig means Shapeshifter 

class stalkerClass (mafiaClass):
    def __init__(self, player_num, role_name, perpetuated_element = None):
        super().__init__(player_num, role_name, perpetuated_element)
        
        self.action_keywords.append("stalking")
        self.max_targets.append(1)
        self.max_actions = self.max_actions + 1

## NK Classes
# class arsonistClass (roleClass):

# class serialKillerClass (roleClass):

# class werewolfClass (roleClass):

## NE Classes
# class lifebinderClass (roleClass):

# class necromancerClass (roleClass):

# class witchClass (roleClass):

## NC Classes
# class amnesiacClass (roleClass):

# class executionerClass (roleClass):

# class jesterClass (roleClass):

# this is so incredibly disgusting and I abhor it holy frick
        # remove straightforward cancellations where the Transporter is uninvolved in any transports
        blocks_and_controls_wc = []
        for can_ind, obj in enumerate(cancel_obj):
            remove_obj = 0
            target_num = self.targetText2PlayerNum(obj.targets[0])
            if ('transporting' in self.players[target_num].action_keywords):
                in_transports = 0
                for obj in resolve_obj.player:
                    if target_num in obj.targets:
                        in_transports = 1
                        break
                if(in_transports == 0):
                    remove_obj = 1
                    resolve_obj.player = [obj for obj in resolve_obj.player if obj.player is not self.players[target_num]]

                    if(blocks_and_controls[can_ind].action == "blocking"): # *** we need to go and remove all the block/control objects from action_queue. ugh
                        self.players[target_num].notifications.append("You were roleblocked!")
                    elif(blocks_and_controls[can_ind].action == "controlling"):
                        self.players[target_num].notifications.append("You were controlled by a Witch!")

                    for visit in obj.targets:
                        self.players[visit].visitors.remove(self.players[target_num])
                    self.players[obj.targets[0]].transported.remove(self.players[obj.targets[1]])
                    self.players[obj.targets[1]].transported.remove(self.players[obj.targets[0]])
            
            if(remove_obj == 0):
                blocks_and_controls_wc.append(obj)