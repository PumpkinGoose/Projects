import streamlit as st
import json
import pandas as pd

JSON_DATA_FILE = 'adi_data_file.json'

st.set_page_config(layout="wide")


def load_data_file(file_name):
    try:
        with open(file_name, 'r') as js:
            return json.load(js)
    except Exception as e:
        st.error(f"Error loading data file {file_name}: {e}")
        return None


def search_and_display(tree, query, search_type):
    if search_type == "Email":
        all_matches = find_in_tree(tree, query.replace('@', ''), search_by="email")
    elif search_type == "Division":
        all_matches = find_in_tree(tree, query.replace('#', ''), search_by="division")
    elif search_type == "Name":
        all_matches = find_in_tree(tree, query, search_by="name")

    if not all_matches:
        st.warning("No matches found.")
        return []
    return all_matches


def search_org(query, search_type):
    tree = load_data_file(JSON_DATA_FILE)
    if tree is None:
        return []

    return search_and_display(tree, query, search_type)

def find_in_tree(current_tree, search_value, boss=None, path=[], search_by="name"):
    matches = []
    
    search_terms = search_value.lower().split('.') if search_by == "email" else search_value.lower().split()

    for node in current_tree:
        clean_node = {k: v for k, v in node.items() if k != "Subordinates"}

        if search_by == "name" and compare_strings(search_terms, node["Name"].lower()):
            peers = [{k: v for k, v in peer.items() if k != "Subordinates"} for peer in boss["Subordinates"] if peer["Name"] != node["Name"]] if boss else []  
            subordinates = node.get("Subordinates", [])
            matches.append((path + [clean_node], peers, subordinates))

        elif search_by == "email" and compare_strings(search_terms, node["Mail"].lower()):
            peers = [{k: v for k, v in peer.items() if k != "Subordinates"} for peer in boss["Subordinates"] if peer["Name"] != node["Name"]] if boss else []
            subordinates = node.get("Subordinates", [])
            matches.append((path + [clean_node], peers, subordinates))

        elif search_by == "division" and compare_strings(search_terms, node["Division"].lower()):
            peers = [{k: v for k, v in peer.items() if k != "Subordinates"} for peer in boss["Subordinates"] if peer["Name"] != node["Name"]] if boss else []
            subordinates = node.get("Subordinates", [])
            matches.append((path + [clean_node], peers, subordinates))

        if "Subordinates" in node:
            result = find_in_tree(node["Subordinates"], search_value, boss=node, path=path + [clean_node], search_by=search_by)
            matches.extend(result)

    return matches


def compare_strings(search_terms, target_string):
    return all(substring in target_string for substring in search_terms)

def display_results(result, col):
    with col:
        st.write("Chain of Leads")
        leaders_chain = result[0][:-1]
        if leaders_chain:
            leaders_df = pd.DataFrame(leaders_chain)
            st.dataframe(leaders_df, use_container_width=True, hide_index=True)
        else:
            st.write("No leaders found.")

        st.write("Selected Match")
        match_data = result[0][-1]
        match_df = pd.DataFrame([match_data])
        st.dataframe(match_df, use_container_width=True, hide_index=True)

        st.write("Peers")
        if result[1]:
            peers_df = pd.DataFrame(result[1])
            st.dataframe(peers_df, use_container_width=True, hide_index=True)
        else:
            st.write("No peers found.")

        st.write("Subordinates")
        if result[2]:
            subordinates_cleaned = [{k: v for k, v in sub.items() if k != "Subordinates"} for sub in result[2]]
            subordinates_df = pd.DataFrame(subordinates_cleaned)
            st.dataframe(subordinates_df, use_container_width=True, hide_index=True)
        else:
            st.write("No subordinates found.")


col1, col2 = st.columns([1, 2])

with col1: # Logo and search boxes
    st.image('logo.png', use_column_width=True)
    search_type = st.radio("Search by", ["Name", "Email", "Division"])
    query = st.text_input("Enter your query")

with col2: # Multiple choice and results
    if query:
        results = search_org(query, search_type)

        if len(results) == 1:
            display_results(results[0], col2)

        elif len(results) > 1:
            match_labels = [match[0][-1]['Name'] for match in results]

            selected_index = st.selectbox("Multiple matches found. Select one:", range(len(match_labels)), format_func=lambda x: match_labels[x])

            selected_match = results[selected_index]
            display_results(selected_match, col2)

        else:
            st.write("No matches found.")
