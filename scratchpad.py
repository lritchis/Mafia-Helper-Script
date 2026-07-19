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
                            if eval_obj.transports_list[target] and eval_obj.cancel_list[target]:
                                for node_ind2, node_set in enumerate(transport_nodes): 
                                    if eval_obj.transports_list[target].player in node_set["transporters"]:
                                        #print(node_ind2)
                                        # *** can I make this all way cleaner by linking player objects to action objects?
                                        nxt_nodes_to_eval[node_ind2] = 1
                                        eval_obj.transports_list[target].player.blocked = 1
                                        print(eval_obj.transports_list[target].player.player_name)
                                        transport_nodes[node_ind2]["transports"][eval_obj.transports_list[target].targets[0]] -= 1
                                        if transport_nodes[node_ind2]["transports"][eval_obj.transports_list[target].targets[0]] == 0:
                                            transport_nodes[node_ind2]["transports"].pop(eval_obj.transports_list[target].targets[0], None)
                                            locations_wc[eval_obj.transports_list[target].targets[0]] = self.player_locations[eval_obj.transports_list[target].targets[0]]

                                        transport_nodes[node_ind2]["transports"][eval_obj.transports_list[target].targets[1]] -= 1
                                        if transport_nodes[node_ind2]["transports"][eval_obj.transporters_list[target].targets[1]] == 0:
                                            transport_nodes[node_ind2]["transports"].pop(eval_obj.transports_list[target].targets[1], None)
                                            locations_wc[eval_obj.transports_list[target].targets[1]] = self.player_locations[eval_obj.transports_list[target].targets[1]]
                                        #print(transport_nodes[node_ind2]["transporters"])
                                        #print(eval_obj.transporters_list[target].player)
                                        transport_nodes[node_ind2]["transporters"].remove(eval_obj.transports_list[target].player)
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