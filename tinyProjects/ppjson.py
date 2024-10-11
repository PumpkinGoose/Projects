#!/usr/bin/python3
# By Gustavo Pico Bosch (Jan 2023)
# Simple script to pretty-print JSON strings
import sys


def insert(level):
    json_lst.append(character)
    json_lst.append('\n')
    json_lst.append('\t' * level)


json_str = str(sys.argv[1])
json_lst = []

indent_level = 0

for character in json_str:
    if character in "{":
        indent_level = indent_level + 1
        insert(indent_level)
    elif character in "}":
        indent_level = indent_level - 1
        insert(indent_level)
    elif character in ",":
        insert(indent_level)
    else:
        json_lst.append(character)


print(''.join(json_lst))
