#!/usr/bin/env python3

# -About-------------------------------------------------------------------------------

# Version 16
# Gustavo Pico Bosch, April 2024 (Rev. October 2024)
# Option -h, --help          displays a brief help menu
# Option -b, --build         takes in ADI.tsv and builds data file
# Option -s, --search        (set by default) searches the data file
# Option -st, --stats        generate statistics from the data file
# Option -f, --full-strings  disables string cropping, may break output formatting

# -Libraries---------------------------------------------------------------------------

import argparse
import json
import os
import copy
import yaml
from datetime import datetime, timedelta

# -Variables---------------------------------------------------------------------------

# Source and data file names/paths
ADI_TSV_FILE     = 'ADI.tsv'
JSON_DATA_FILE   = 'adi_data_file.json'
ADI_STATS_SCRIPT = '_adiStatsGraph.py'
ADI_CONFIG_FILE  = '_adiConfig.yml'

# Column sizes
CANVAS_PARAMS = [47, 28, 47, 47]

# ADI Table Column Numbers Correspondence
COL_CTRY = 2
COL_NAME = 3
COL__DOB = 4
COL_MAIL = 5
COL_INGR = 6
COL_SENI = 7
COL_SECT = 8
COL_BOSS = 11
COL_DEPT = 30

CONFIG_COMMENTS = """# ANSI escape sequences for color
#               NORMAL   LIGHT    BOLD     BKG      LIGHT_BKG
# GRAYS =       30m      90m
# RED =         31m      91m      1;31m    41m      101m
# GREEN =       32m      92m      1;32m    42m      102m
# YELLOW =      33m      93m      1;33m    43m      103m
# BLUE =        34m      94m      1;34m    44m      104m
# MAGENTA =     35m      95m      1;35m    45m      105m
# CYAN =        36m      96m      1;36m    46m      106m
# WHITE =       37m      97m      1;37m    47m      107m
# BOLD = 1m, ITALIC = 3m, UNDERLINE = 4m, BLINK = 5m, INVERTED = 7m\n
"""

# -Functions---------------------------------------------------------------------------


# [Not yet in use] Checks age of the data file and warns if it's over a month old
# TO DO: Could be modified to trigger an auto-download of ADI file and conversion
def check_file_age(file_path):

    if os.name == 'nt':  # Windows
        creation_time = os.path.getctime(file_path)

    else:  # macOS and Linux
        stat = os.stat(file_path)
        creation_time = stat.st_ctime
    creation_date = datetime.fromtimestamp(creation_time)
    if datetime.now() - creation_date > timedelta(days=30):
        print(f"\nWARNING!: {file_path} is over a month old!\nGet the latest ADI!\n")


# Single search function (non-recurrent)
def search_org(full_strings):
    try:
        # Read and load data file
        with open(JSON_DATA_FILE, 'r') as js:
            tree = json.load(js)
        # Ask user for term to search
        search_input = input(f"\n{COL_FRAME}Enter a{COL_TEXT_2} name, email[@], {COL_FRAME}or {COL_TEXT_2}[#]division {COL_FRAME}to search: {ENDC}{COL_TEXT_1}").strip()
        print(f"{ENDC}")
        # Discern between email, name, and division lookups
        if '@' in search_input:
            all_matches = find_in_tree(tree, search_input, search_by="email")
        elif search_input.startswith("#"):
            search_input = search_input[1:]  # Remove '#' character
            all_matches = find_in_tree(tree, search_input, search_by="division")
        else:
            all_matches = find_in_tree(tree, search_input, search_by="name")
        
        chosen_match = choose_match(all_matches, search_by="email" if '@' in search_input else "division" if search_input.startswith("#") else "name")
        
        # If found, show results through print_frame(), otherwise warn user
        if chosen_match:
            result, peers, subs = chosen_match
            print_frame(result, peers, subs, full_strings)
        else:
            print("No matches found\n")
    # Basic error handling, to be improved
    except KeyboardInterrupt:
        print("\nOperation canceled by user.")
    except Exception as e:
        print(f"Couldn't find data file named {JSON_DATA_FILE}. Error: {e}")


# Multiple search option (recurrent, "exit" to exit loop)
def explore_org(full_strings):
    try:
        # Read and load data file
        with open(JSON_DATA_FILE, 'r') as js:
            tree = json.load(js)
        
        # Loops the search until "exit" input
        while True:
            print('\n')
            # Ask user for term to search or "exit" to quit
            search_input = input(f"{COL_FRAME}Enter a{COL_TEXT_2} name, email[@], {COL_FRAME}or {COL_TEXT_2}[#]division {COL_FRAME}to search (or 'exit'):  {ENDC}{COL_TEXT_1}").strip()
            print(f"{ENDC}")
            if search_input.lower() == 'exit':
                break

            # Makes sure to grab a fresh copy each time
            tree_copy = copy.deepcopy(tree)

            # Discern between email, name, or division lookups
            if '@' in search_input:
                # Email search
                all_matches = find_in_tree(tree_copy, search_input, search_by="email")
            elif search_input.startswith("#"):
                search_input = search_input[1:]  # Remove '#' character
                all_matches = find_in_tree(tree_copy, search_input, search_by="division")
            else:
                # Name search (one-word input)
                all_matches = find_in_tree(tree_copy, search_input, search_by="name")
            
            # If found, show results through print_frame(), otherwise warn user
            chosen_match = choose_match(all_matches, search_by="email" if '@' in search_input else "division" if search_input.startswith("#") else "name")
            print('\n')
            if chosen_match:
                result, peers, subs = chosen_match
                print_frame(result, peers, subs, full_strings=full_strings)
            else:
                print("No matches found\n")
    except KeyboardInterrupt:
        print("\nOperation canceled by user.")
    except Exception as e:
        print(f"An error occurred: {e}")



# This is the one that actually paces the tree in search for stuff
def find_in_tree(current_tree, search_value, boss=None, path=[], search_by="name"):
    # Since searches can be ambiguous and matches can be more than one, they're saved in a list
    matches = []
    if search_by == "email":
        search_terms = search_value.lower().split('.')  # Split terms for partial matching
    else:
        search_terms = search_value.lower().split()  # Split terms for partial matching

    for node in current_tree:
        # Stores node info without subs (so, just that person's info)
        clean_node = {k: v for k, v in node.items() if k != "Subordinates"}

        # Perform matching depending on the search criteria (name, email, division)
        if search_by == "name" and compare_strings(search_terms, node["Name"].lower()):
            matches.append((path + [clean_node], boss.get("Subordinates", []) if boss else [], node.get("Subordinates", [])))
        elif search_by == "email" and compare_strings(search_terms, node["Mail"].lower()):
            matches.append((path + [clean_node], boss.get("Subordinates", []) if boss else [], node.get("Subordinates", [])))
        elif search_by == "division" and compare_strings(search_terms, node["Division"].lower()):
            matches.append((path + [clean_node], boss.get("Subordinates", []) if boss else [], node.get("Subordinates", [])))

        # If this node has subs, search recursively
        if "Subordinates" in node:
            result = find_in_tree(node["Subordinates"], search_value, boss=node, path=path + [clean_node], search_by=search_by)
            if result:
                matches.extend(result)
    return matches


# Breaks down search terms into words and compares to current node being looked at
def compare_strings(search_terms, target_string):
    return all(substring in target_string for substring in search_terms)


# Takes matches and responds accordingly
def choose_match(matches, search_by="name"):
    # If no matches, skip
    if not matches:
        return None
    # If just one match, return just that match, no selection
    if len(matches) == 1:
        return matches[0]
    # If matches exist and are more than 1, show selection
    print(f"\n{COL_FRAME}These are the possible matches: {COL_TEXT_1}")
    print(f"{ENDC}")
    # Prints out numbered list of matches
    for i, match in enumerate(matches):
        # Extracts both name and division to display
        name = match[0][-1]["Name"]
        division = match[0][-1].get("Division", "No division")
        print(f"{COL_TEXT_1}\t{i+1}. {name} {COL_TEXT_2}[{division.title()}]{ENDC}")
    # Ask idiot for choice by match number
    choice = int(input(f"\n{COL_FRAME}Select an option by number: {COL_TEXT_1}"))
    # If bad choice, bail out
    if choice < 1 or choice > len(matches):
        return None
    # If happy trail, return match to be displayed
    return matches[choice - 1]


# Prints the output for matches
def print_frame(result, peers, subs, full_strings=False):
    # Hardcoded header info
    ingress_date = result[-1]['Ingress']
    ingress_dt = datetime.strptime(ingress_date, "%d/%m/%Y")  # Adjust format if needed
    current_dt = datetime.now()
    days_in_company = (current_dt - ingress_dt).days
    titles = [{"Country":"CTRY", "Name": f"Started on: {ingress_date} ({days_in_company} days)", "Division": "#DIVISION", "Puesto": "SENIORITY", "Mail": "E-Mail Address @"}]
    # Catches match
    target = [result[-1]]
    # Iterates through peers list to remove the match (otherwise match is shown as peer of itself)
    for peer in peers:
        if peer['Name'] == target[0]['Name']:
            peers.remove(peer)
    # Prints header, match, leads, peers and subs
    print_block("", titles, full_strings=full_strings)
    print_block("YOUR SEARCH MATCH", target, full_strings=full_strings)
    print_block("CHAIN OF LEADS", result[:-1], full_strings=full_strings)
    print_block("PEERS", peers, full_strings=full_strings)
    print_block("SUBORDINATES", subs, full_strings=full_strings)


# Prints data blocks
def print_block(header, list, full_strings=False):
    # Extracts widths for each column
    name_width, Division_width, puesto_width, mail_width = CANVAS_PARAMS
    # Prints section header and line
    print(f"{COL_TEXT_3}{header}{ENDC}" + f"{COL_FRAME}={ENDC}" * (sum(CANVAS_PARAMS) - len(header) + 13))
    # When list is empty, indicate there's no results for it
    if len(list) == 0:
        print(f"{COL_TEXT_1}    No results{ENDC}")
    # Otherwise extract values to prepare for print
    else:
        for item in list:
            name = f"[{item['Country']}] {item['Name'].title()}"
            Division = item['Division'].title()
            puesto = item['Puesto'].title()
            mail = item['Mail']
            # This bit crops strings to avoid messing with formatting (overridden with -f, --full_strings)
            if not full_strings:
                name = crop_string(name, name_width)
                Division = crop_string(Division, Division_width)
                puesto = crop_string(puesto, puesto_width)
                mail = crop_string(mail, mail_width)
            # Prints item data
            print(f"    {COL_TEXT_1}{name:<{name_width}}{ENDC} {COL_FRAME}||{ENDC} {COL_TEXT_2}{Division:<{Division_width}}{ENDC} {COL_FRAME}||{ENDC} {COL_TEXT_1}{puesto:<{puesto_width}}{ENDC} {COL_FRAME}||{ENDC} {COL_TEXT_1}[{mail}]{ENDC}")
    # Prints end-of-block line
    print(f"{COL_FRAME}={ENDC}" * (name_width + Division_width + puesto_width + mail_width + 13))


# Crops strings that exceed column width
def crop_string(value, max_width):
    buffer = 3
    if len(value) > max_width - buffer:
        return value[:max_width - buffer] + ".."
    return value


# Builds json data file
def build_org():
    # Notify idiot
    print("Building data file. This may take a few seconds...")
    # Tries to open source file, load contents
    try:
        with open(ADI_TSV_FILE, 'r') as tab:
            # First, toss out the header row
            tab.readline()
            # Then, read useful rows
            entries = tab.readlines()
        # Sends all rows to be processed into a tree structure, catches it
        desp_tree = tree_builder("", entries)
        # Saves tree to file
        with open(JSON_DATA_FILE, 'w') as f:
            json.dump(desp_tree, f, indent=None)
            # Notifies idiot
            print("Data file successfully built.")
    except:
        # Makes excuses
        print("Couldn't find source file", ADI_TSV_FILE)


def replace_spanish_characters(text):
    replacements = {
        'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u', 'ñ': 'n',
        'Á': 'A', 'É': 'E', 'Í': 'I', 'Ó': 'O', 'Ú': 'U', 'Ñ': 'N',
        'ü': 'u', 'Ü': 'U'
    }
    for special_char, normal_char in replacements.items():
        text = text.replace(special_char, normal_char)
    return text

def tree_builder(boss, entries):
    # Initializes highest level
    hierarchy = []
    # Starts reading ADI rows
    for entry in entries:
        # Since it's a .tsv file, splits row by tabs
        seg_entry = entry.split("\t")
        # Matches current node's boss with upper node's name, to form hierarchy
        if seg_entry[COL_BOSS].lower() == boss.lower():
            # Initializes node dictionary
            employee_data = {}
            # Extracts and replaces special characters for all fields
            full_name = replace_spanish_characters(seg_entry[COL_NAME].lower())
            first_name = full_name.split(',')[1].strip().title()
            last_name = full_name.split(',')[0].strip().title()

            employee_data["Name"] = first_name + ' ' + last_name
            employee_data["DateOfBirth"] = replace_spanish_characters(seg_entry[COL__DOB])
            employee_data["Country"] = replace_spanish_characters(seg_entry[COL_CTRY].upper())
            employee_data["Ingress"] = replace_spanish_characters(seg_entry[COL_INGR])
            employee_data["Puesto"] = replace_spanish_characters(seg_entry[COL_SENI].lower())
            employee_data["Division"] = replace_spanish_characters(seg_entry[COL_SECT].lower())
            employee_data["Department"] = replace_spanish_characters(seg_entry[COL_DEPT].lower())
            employee_data["Mail"] = replace_spanish_characters(seg_entry[COL_MAIL].lower())

            # Creates subs list, fills it with recursive nonsense
            employee_data["Subordinates"] = tree_builder(seg_entry[3].lower(), entries)
            # Plugs whole node to hierarchy
            hierarchy.append(employee_data)
    # By returning hierarchy here, each lower recursion will be saved to the "subordinates" attribute
    # Thus is the tree structure achieved
    return hierarchy


# Stats are pretty
def generate_stats():
    # Checks whether the stats script exists so as to avoid import errors
    if not os.path.exists(ADI_STATS_SCRIPT):
        print(f"The script {ADI_STATS_SCRIPT} could not be found.")
    # Since it does, it imports it and runs the main function
    # TO DO: Break down the stats main function so the user can select through a menu?
    else:
        stats_module = __import__(ADI_STATS_SCRIPT.replace('.py', ''))
        stats_module.module_selector()


def theme_manager():
    # Load the YAML file
    with open(ADI_CONFIG_FILE, 'r') as f:
        config = yaml.safe_load(f)
    
    themes = config['themes']

    # Print the themes with color formatting
    print("Available themes:\n")
    for theme_name, colors in themes.items():
        frame_color = "\033[" + colors['frame']
        text1_color = "\033[" + colors['text1']
        text2_color = "\033[" + colors['text2']
        text3_color = "\033[" + colors['text3']
        reset = "\033[0m"  # Reset code for colors
        print(f"{theme_name.title():<8} {frame_color}▇▇▇{reset} | {text1_color}▇▇▇ {text2_color}▇▇▇ {text3_color}▇▇▇{reset}")

    # Prompt user for input
    selected_theme = input("\nEnter the name of the theme you want to set: ")

    # Validate the user's input
    if selected_theme.lower() in themes:
        # Update the current theme in the YAML config 
        config['current_theme'] = selected_theme
        with open(ADI_CONFIG_FILE, 'w') as f:
            f.write(CONFIG_COMMENTS)
            yaml.safe_dump(config, f)
        print(f"Theme changed to '{selected_theme}'.")
    else:
        print("Invalid theme name. No changes made.")


# Load the saved theme and theme definitions
def load_config():
    with open(ADI_CONFIG_FILE, 'r') as file:
        return yaml.safe_load(file)


# Get the currently active theme
def get_theme():
    config = load_config()
    theme_name = config.get("current_theme", "default")
    return config["themes"].get(theme_name, config["themes"]["default"])


# These are declared here because they need to be global, but also have to be after get_theme()
SELECTED_THEME = get_theme()
COL_FRAME = "\033[" + SELECTED_THEME["frame"]
COL_TEXT_1 = "\033[" + SELECTED_THEME["text1"]
COL_TEXT_2 = "\033[" + SELECTED_THEME["text2"]
COL_TEXT_3 = "\033[" + SELECTED_THEME["text3"]
ENDC = "\033[0m"  # Reset color


# -Main and argument parser------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(description="""\
    ADI Inspector (by Gustavo Pico Bosch, 2024)

    This tool allows you to search for users in the Active Directory Information (ADI)
    by name, email, or division. Use it to quickly find specific information and explore
    the organizational structure with ease. Simply input the search term, and the tool will 
    guide you through potential matches and details.
""",formatter_class=argparse.RawTextHelpFormatter)

    group = parser.add_mutually_exclusive_group()
    group.add_argument("-s", "--search", action="store_true", help="one-time search (default)", default=True)
    group.add_argument("-b", "--build", action="store_true", help="build json data file (from " + ADI_TSV_FILE + " in same directory)")
    group.add_argument("-e", "--explore", action="store_true", help="looping search until user exits")
    group.add_argument("-t", "--theme", action="store_true", help="check and set the color theme")
    parser.add_argument("-st", "--stats", action="store_true", help="generate statistics from data")
    parser.add_argument("-f", "--full_strings", action="store_true", help="show full strings without cropping (default crops overflow)")

    args = parser.parse_args()

    if args.build:
        build_org()
    elif args.theme:
        theme_manager()
    elif args.stats:
        generate_stats()
    elif args.explore:
        explore_org(full_strings=args.full_strings)
    elif args.search:
        search_org(full_strings=args.full_strings)


# Python main guard
if __name__ == "__main__":
    main()
