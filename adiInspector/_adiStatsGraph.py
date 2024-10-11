#!/usr/bin/env python3

# -About-------------------------------------------------------------------------------

# Version 19
# Gustavo Pico Bosch, April 2024 (Rev. October 2024)

# -Libraries---------------------------------------------------------------------------

import json, yaml
from datetime import datetime, timedelta
from collections import defaultdict, OrderedDict

# -Variables---------------------------------------------------------------------------

JSON_DATA_FILE = 'adi_data_file.json'
ADI_CONFIG_FILE  = '_adiConfig.yml'

# -Functions---------------------------------------------------------------------------

def traverse_tree(nodes, helper_func, accumulator, category):
    if isinstance(nodes, list):
        for node in nodes:
            if isinstance(node, dict):
                traverse_tree(node, helper_func, accumulator, category)
    elif isinstance(nodes, dict):
        helper_func(nodes, accumulator, category)
        for subordinate in nodes.get("Subordinates", []):
            traverse_tree(subordinate, helper_func, accumulator, category)


def count_employees(tree, category):
    country_count = defaultdict(int)

    def people_per_country(node, accumulator, category):
        country = node.get(category.title())
        if country:
            accumulator[country] += 1
        else:
            accumulator[f"{category} missing"] += 1

    traverse_tree(tree, people_per_country, country_count, category)

    sorted_country_count = OrderedDict(sorted(country_count.items(), key=lambda item: item[1], reverse=True))
    return sorted_country_count


def cat_by_age_brackets(tree):
    age_bracket_count = defaultdict(int)
    age_brackets = {
        "18-25": (18, 25),
        "26-35": (26, 35),
        "36-45": (36, 45),
        "46-55": (46, 55),
        "56-65": (56, 65),
        "66+": (66, 120)
    }

    for bracket in age_brackets:
        age_bracket_count[bracket] = 0

    def people_per_age_bracket(node, accumulator, unused):
        dob_str = node.get("DateOfBirth")
        if dob_str:
            dob = datetime.strptime(dob_str, "%d/%m/%Y")
            age = (datetime.now() - dob).days // 365
            for bracket, (min_age, max_age) in age_brackets.items():
                if min_age <= age <= max_age:
                    accumulator[bracket] += 1
                    break

    traverse_tree(tree, people_per_age_bracket, age_bracket_count, "")

    sorted_age_bracket_count = OrderedDict(sorted(age_bracket_count.items()))
    return sorted_age_bracket_count


def average_retention_by_category(tree, category):
    retention_data = defaultdict(list)

    def calculate_retention(node, accumulator, category):
        ingress_date = datetime.strptime(node["Ingress"], "%d/%m/%Y")
        current_date = datetime.now()
        retention_years = (current_date - ingress_date).days / 365.25
        cat = node.get(category.title(), "No Category")
        accumulator[cat].append(retention_years)

    traverse_tree(tree, calculate_retention, retention_data, category)

    average_retention = {}
    for cat, retention_list in retention_data.items():
        #average_retention[cat] = f"{sum(retention_list) / len(retention_list):.2f}"
        average_retention[cat] = round(sum(retention_list) / len(retention_list), 1)

    sorted_average_retention = OrderedDict(sorted(average_retention.items(), key=lambda item: item[1], reverse=True))

    return sorted_average_retention


def new_hires_last_months_by_category(tree, months, category):
    start_date = datetime.now() - timedelta(days=months * 30.5)
    new_hires_count = defaultdict(int)

    def count_new_hires(node, _, category):
        ingress_date = datetime.strptime(node["Ingress"], "%d/%m/%Y")
        department = node.get(category.title(), "No Category")
        
        if ingress_date >= start_date:
            new_hires_count[department] += 1

    traverse_tree(tree, count_new_hires, None, category)

    sorted_new_hires_count = OrderedDict(sorted(new_hires_count.items(), key=lambda item: item[1], reverse=True))
    return sorted_new_hires_count


def filter_tree_by_category(tree, filtr, value):
    if not filtr:
        return tree if isinstance(tree, list) else [tree]

    matches = []

    def recursive_filter(node, filtr, value):
        if filtr.title() in node and str(node[filtr.title()]).lower() == str(value).lower():
            match_node = {key: node[key] for key in node if key != "Subordinates"}
            matches.append(match_node)
        if "Subordinates" in node:
            for sub in node["Subordinates"]:
                recursive_filter(sub, filtr, value)

    recursive_filter(tree, filtr, value)
    return matches


def print_stats(statistics, title, category, filtr, value):
    width = 50
    print("\n ")
    print(f"  {COL_TEXT_3}{title} by {category.title()}{ENDC}{COL_FRAME}" + "_" * (width - (len(title) + len(category)) - 8))
    if filtr:
        print(f"  {COL_TEXT_3}{filtr.title()}: {value.title()}{ENDC}{COL_FRAME}" + "_" * (width - (len(filtr) + len(value)) - 6))
    for key, count in statistics.items():
        dots = '_' * (width - 4 - len(key) - len(str(count)))
        print(f"  {COL_TEXT_1}{key.title()}{ENDC}{COL_FRAME}{dots}{ENDC}{COL_TEXT_2}{count}{ENDC}")
    print(" ")


def print_stats_with_bars(statistics, title, category, filtr, value):
    width = 70
    max_count = max(statistics.values()) if statistics else 1
    total_count = sum(statistics.values()) if statistics else 1
    max_key_length = max(len(key) for key in statistics.keys())

    print("\n ")
    print(f"  {COL_TEXT_3}{title} by {category.title()}{ENDC}{COL_FRAME}" + "_" * (width - (len(title) + len(category)) - 8))
    if filtr:
        print(f"  {COL_TEXT_3}{filtr.title()}: {value.title()}{ENDC}{COL_FRAME}" + "_" * (width - (len(filtr) + len(value)) - 6))
    
    for key, count in statistics.items():
        bar_length = max(1, int((count / max_count) * (width - max_key_length - 19))) if count > 0 else 0
        bar_char = f'{COL_FRAME}▐{ENDC}'
        bar = bar_char * bar_length
        percentage = (count / total_count) * 100
        print(f"  {COL_TEXT_1}{key.title():<{max_key_length + 2}}{ENDC}{COL_FRAME}{bar} {COL_TEXT_2}{count:<4}{ENDC} {COL_TEXT_3}{percentage:.1f}%{ENDC}")
    
    print(" ")



def module_selector():
    try:
        with open(JSON_DATA_FILE, 'r') as js:
            tree = json.load(js)
    except FileNotFoundError:
        print(f"Error: The file '{JSON_DATA_FILE}' was not found.")
        return
    except json.JSONDecodeError:
        print("Error: The file could not be decoded. Please check the JSON format.")
        return

    # Menu options
    options = {
        '1': 'Count Employees',
        '2': 'Count Employees Chart',
        '3': 'Age Brackets',
        '4': 'Age Brackets Chart',
        '5': 'Average Retention',
        '6': 'Average Retention Chart',
        '7': 'New Hires',
        '8': 'New Hires Chart',
        '0': 'Exit'
    }

    while True:
        # Display the menu
        print(f"\n{COL_TEXT_3}Menu:{ENDC}")
        for key, value in options.items():
            print(f"  {COL_TEXT_2}{key}{ENDC}. {COL_TEXT_1}{value}{ENDC}")

        choice = input(f"\n{COL_TEXT_1}Select an option{ENDC} {COL_TEXT_2}(0 to exit){ENDC}: ").strip()

        if choice == '0':
            print("Exiting...")
            break

        elif choice in ('1', '2'):
            print(f"{COL_TEXT_3}\n===Count Employees==={ENDC}")
            category = input(f"\n{COL_TEXT_1}Categorize by (cannot be blank){ENDC}: ").strip()
            while not category:
                print("Category cannot be blank. Please enter a valid term.")
                category = input(f"\n{COL_TEXT_1}Categorize by (cannot be blank){ENDC}: ").strip()
            filtr = input(f"\n{COL_TEXT_1}[Optional] Filter by (leave blank for all){ENDC}: ").strip()
            value = ""
            if filtr:
                value = input(f"\n{COL_TEXT_1}Enter value for '{filtr}'{ENDC}: ").strip()
            subtree = filter_tree_by_category(tree[0], filtr, value)
            country_stats = count_employees(subtree, category)
            if choice == '1':
                print_stats(country_stats, "Employee Count", category, filtr, value)
            else:
                print_stats_with_bars(country_stats, "Employee Count", category, filtr, value)

        elif choice in ('3', '4'):
            print(f"{COL_TEXT_3}\n===Age Brackets==={ENDC}")
            filtr = input(f"\n{COL_TEXT_1}[Optional] Filter by (leave blank for all){ENDC}: ").strip()
            value = ""
            if filtr:
                value = input(f"\n{COL_TEXT_1}Enter value for '{filtr}'{ENDC}: ").strip()
            subtree = filter_tree_by_category(tree[0], filtr, value)
            age_bracket_stats = cat_by_age_brackets(subtree)
            if choice == '3':
                print_stats(age_bracket_stats, "Age Brackets", "", filtr, value)
            else:
                print_stats_with_bars(age_bracket_stats, "Age Brackets", "", filtr, value)

        elif choice in ('5', '6'):
            print(f"{COL_TEXT_3}\n===Average Retention==={ENDC}")
            category = input(f"\n{COL_TEXT_1}Categorize by (cannot be blank){ENDC}: ").strip()
            while not category:
                print("Category cannot be blank. Please enter a valid term.")
                category = input(f"\n{COL_TEXT_1}Categorize by (cannot be blank){ENDC}: ").strip()
            filtr = input(f"\n{COL_TEXT_1}[Optional] Filter by (leave blank for all){ENDC}: ").strip()
            value = ""
            if filtr:
                value = input(f"\n{COL_TEXT_1}Enter value for '{filtr}'{ENDC}: ").strip()
            subtree = filter_tree_by_category(tree[0], filtr, value)
            country_stats = average_retention_by_category(subtree, category)
            if choice == '5':
                print_stats(country_stats, "Average Retention (Yrs)", category, filtr, value)
            else:
                print_stats_with_bars(country_stats, "Average Retention (Yrs)", category, filtr, value)

        elif choice in ('7', '8'):
            print(f"{COL_TEXT_3}\n===Recent Hires==={ENDC}")
            try:
                months = int(input(f"{COL_TEXT_1}Enter the number of months{ENDC}: ").strip())
            except ValueError:
                print("Invalid input. Please enter a number.")
                continue
            category = input(f"\n{COL_TEXT_1}Categorize by (cannot be blank){ENDC}: ").strip()
            while not category:
                print("Category cannot be blank. Please enter a valid term.")
                category = input(f"\n{COL_TEXT_1}Categorize by (cannot be blank){ENDC}: ").strip()
            filtr = input(f"\n{COL_TEXT_1}[Optional] Filter by (leave blank for all){ENDC}: ").strip()
            value = ""
            if filtr:
                value = input(f"\n{COL_TEXT_1}Enter value for '{filtr}'{ENDC}: ").strip()
            subtree = filter_tree_by_category(tree[0], filtr, value)
            country_stats = new_hires_last_months_by_category(subtree, months, category)
            if choice == '7':
                print_stats(country_stats, f"New Hires (last {months} months)", category, filtr, value)
            else:
                print_stats_with_bars(country_stats, f"New Hires (last {months} months)", category, filtr, value)

        else:
            print("Invalid choice. Please try again.")


def load_config():
    with open(ADI_CONFIG_FILE, 'r') as file:
        return yaml.safe_load(file)


def get_theme():
    config = load_config()
    theme_name = config.get("current_theme", "default")
    return config["themes"].get(theme_name, config["themes"]["default"])


# -Main and argument parser------------------------------------------------------------


SELECTED_THEME = get_theme()
COL_FRAME = "\033[" + SELECTED_THEME["frame"]
COL_TEXT_1 = "\033[" + SELECTED_THEME["text1"]
COL_TEXT_2 = "\033[" + SELECTED_THEME["text2"]
COL_TEXT_3 = "\033[" + SELECTED_THEME["text3"]
ENDC = "\033[0m"  # Reset color


if __name__ == "__main__":
    module_selector()
