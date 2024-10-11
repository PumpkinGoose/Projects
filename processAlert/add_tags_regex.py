#!/usr/bin/python3
import sys, json, re

# Se le indica el diccionario y el campo que se quiere obtener, usando dot notation, ejemplo:
# get(doc_data, "alert_data.agent.name")
def get(dictionary, field_dot_notation):
    if "." in field_dot_notation:
        key, rest = field_dot_notation.split(".", 1)
        return get(dictionary.get(key, {}), rest)
    else:
        return dictionary.get(field_dot_notation)


def finder(content, pattern, match_key, current_path=None, found_flag=None):
    if current_path is None:
        current_path = []
    if found_flag is None:
        found_flag = [False]
    match_key_list = match_key.split('.')

    pattern = re.compile(pattern)
    if isinstance(content, dict) and not found_flag[0]:
        #print(match_key_list)
        for key, value in content.items():
            #print(current_path + [key])
            if key in match_key_list:
                if current_path + [key] == match_key_list:
                    if isinstance(value, str):
                        if pattern.search(value):
                            found_flag[0] = True
                            break
                else:
                    finder(value, pattern, match_key, current_path + [key], found_flag)
    elif isinstance(content, list) and not found_flag[0]:
        for index, item in enumerate(content):
            finder(item, pattern, match_key, current_path, found_flag)

    return found_flag[0]


# Input:
# Arg 1 -> doc_data (contiene el json del evento que generó la alerta)
# Arg 2 -> rule_config del módulo akinator, en json
doc_data = json.loads(str(sys.argv[1]).replace("'", '"'))
siem_rule_config = json.loads(str(sys.argv[2]).replace("'", '"'))

# Armo el tag
if "tags" in siem_rule_config:
    tags = siem_rule_config.get("tags")
    # Variable en la que se va a armar la lista de tags
    json_data_tags = ""

    # Recorro cada tag con sus condiciones
    for tag in tags:
        # Si no se agregaron condiciones, agrego el tag de una
        if not "conditions" in tag:
            json_data_tags += "{} ".format(tag["tag_name"])
        else:
            # Valido que se cumplan todas las condiciones
            true_in_all_conditions = True
            # Recorro la lista de condiciones
            for condition in tag["conditions"]:
                field = condition.get("field")
                value = condition.get(r"value")
                # Si hasta ahora todas las condiciones se cumplieron
                if true_in_all_conditions:
                    list_match_flag = False
                    # Traemos el valor del field desde el JSON
                    # alert_value = get(doc_data["alert_data"],field)
                    # Si value es una lista, for con bandera propia
                    if isinstance(value, list):
                        # Por claridad se cambia la variable a value_list
                        value_list = value
                        for element in value_list:
                            found = finder(doc_data, element, field)
                            #print (f"{found = }")
                            if found:
                                list_match_flag = True
                    # Si no es lista, sigue todo igual
                        if not list_match_flag:
                            true_in_all_conditions = False
                    # Si no se cumple la condicion
                    else:
                        true_in_all_conditions = finder(doc_data, value, field)
            # Si se cumplieron todas las condiciones agrego el tag
            if true_in_all_conditions:
                json_data_tags += "{} ".format(tag["tag_name"])
    if json_data_tags != "":
        doc_data["tags"] = json_data_tags[:-1]

print(str(json.dumps(doc_data)))
