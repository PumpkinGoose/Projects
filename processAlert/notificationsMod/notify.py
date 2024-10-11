#!/usr/bin/python3
import sys
import json
import yaml
sys.path.insert(1, '/opt/soc-scripts/include')
sys.path.insert(1,"/opt/soc-scripts/exec/elastalert/process_alert/notifications_scripts")
import vault_manager
import send_telegram
import send_email


def get_json_values(dictionary, field_dot_notation):
    if "." in field_dot_notation:
        key, rest = field_dot_notation.split(".", 1)
        return get_json_values(dictionary.get(key, {}), rest)
    else:
        return dictionary.get(field_dot_notation)

def build_body(body, dot_notation_list):
    values = []
    for dot_notation in dot_notation_list:
        values.append(get_json_values(doc_data, dot_notation))
    return body.format(*values)


telegram_bot_name = "soc_updates_bot"
notifications_file = "/home/despegar/notifications.yaml"
doc_data = json.loads(str(sys.argv[1]).replace("'", '"'))
rule_config = json.loads(str(sys.argv[3]).replace("'", '"'))
alert_name = get_json_values(doc_data, "alert.rule_name")
telegram_module_flagged = bool(get_json_values(rule_config, "telegram_enabled"))
email_module_flagged = bool(get_json_values(rule_config, "email_enabled"))

with open(notifications_file, "r") as file:
    template_yaml = yaml.safe_load(file)

if telegram_module_flagged:
    bot_token = vault_manager.get_credentials(telegram_bot_name)['value']
    dot_notation_list = get_json_values(template_yaml, "telegram."+alert_name+".vars")
    body = get_json_values(template_yaml, "telegram."+alert_name+".body")
    body = build_body(body, dot_notation_list)
    chat_id = get_json_values(template_yaml, "telegram."+alert_name+".dest")
    parse_mode = "html"
    send_telegram.send_message(bot_token, chat_id, body, parse_mode)

if email_module_flagged:
    #sender_email = vault_manager.get_credentials(soc_email_address)['value']
    #sender_passw = vault_manager.get_credentials(soc_email_token)['value']
    dot_notation_list = get_json_values(template_yaml, "email."+alert_name+".vars")
    body = get_json_values(template_yaml, "email."+alert_name+".body")
    body = build_body(body, dot_notation_list)
    dest_email = get_json_values(template_yaml, "email."+alert_name+".dest")
    #send_email.send_email(sender_email, sender_passw, dest_email, alert_name, body)
    send_email.send_email(dest_email, alert_name, body)
