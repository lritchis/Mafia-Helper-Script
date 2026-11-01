import re

# define what is imported from file
__all__ = ["category_regex", "roles_regex", "action_dict", "death_message_dict", 
           "atk_state_map", "num_atk_states", "atk_flags", "defense_state_map", "num_defense_states",
           "startsWVowel", "investigator_categories_dict", 
           "role_class_dict", "faction_dict",
           "res_name_map"]

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
NC_regex = r"\AAmnesiac\b|\ADoomsayer\b|\AExecutioner\b|\AJester\b"
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
    "dooming" : {"priority" : 0,
                         "is_visit" : 0,
                         "max_targets" : 3,
                         "targeted" : 0 # *** ?
    },
    "haunting" : {"priority" : 0,
                     "is_visit" : 0,
                     "max_targets" : 1,
                     "targeted" : 0  # *** ?
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
    "loading" : {"priority" : 21,
                         "is_visit" : 0,
                         "targeted" : 0
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
    }
}

# *** Eventually implement for automatic priority indexing
#priority_num = 0
#for action in action_dict:
#    if action_dict[action]["priority"] == 0:
#        priority_num += 1
#   action_dict[action]["priority"] = priority_num

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
    "mauling_visitor" : "mauled by the Werewolf",
    "igniting" : "ignited by an Arsonist",
    "binding" : "life-bound to someone that died",
    "hexing" : "hexed by a Necromancer",
    "executing" : "executed by the Jailor"
}

# some inefficiency but means I don't have to have these listed in the correct order, just in case
# *** do I need mauling_visitor here? I don't actually know
atk_actions = ["killing", "alerting", "trapping_atk", "sacrificing", "counterattacking", "shooting",  "stabbing", "mauling", "mauling_visitor"] # *** This is not an actual fix, mauling_visitor needs fixed
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
    #["Lookout", "Tracker", "Medic", "Stalker", "Werewolf", "Executioner"],
    ["Lookout", "Tracker", "Medic", "Stalker", "Werewolf", "Doomsayer"],
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
                "faction" : "Town",
                "perpetuated" : {"vest" : 1}
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
                "perpetuated" : {"lim_action" : 1, "self-save" : 1, "bullets" : 1, "loaded": 0}
    },

    "Trapper" : {"actions" : ["trapping"],
                "faction" : "Town",
                "perpetuated" : {"num_traps" : 2, "traps_landed" : set()}
    },

    "Veteran" : {"actions" : [],
                "faction" : "Town",
                "perpetuated" : {"alerts" : 3,"vest" : 1}
    },

    "Vigilante" : {"actions" : [],
                "faction" : "Town",
                "perpetuated" : {"bullets" : 3, "loaded" : 0}
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
                "perpetuated" : {"dead_roles" : {}, "shield" : 1}
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
    "Doomsayer" : {"actions" : [],
                    "faction" : "non-Town",
                    "perpetuated" : {"shield" : 1}
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

res_name_map = {
    "tracking" : "observing",
    "watching" : "observing",
    "stalking" : "observing"
}