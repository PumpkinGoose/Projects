#! /usr/bin/python3
# By Gustavo Pico Bosch (Feb 2023)
# Takes an Elastalert OSQL query string as its only parameter and prints it out in a human-readable formatting
import sys


def load(str, lst):
    for char in str:
        lst.append(char)


def find_indices(lst, subs):
    index = []
    start = 0
    while start != -1:
        start += 1
        start = lst.find(subs, start)
        index.append(start)
    return index[:-1]


def formatting(lst, AND, OR):
    indent_level = 0
    and_or = AND + OR
    and_or.sort()
    for i in reversed(range(len(lst))):
        if lst[i] == '(':
            indent_level -= 1
            lst.insert(i, '\n' + '\t'*indent_level)
        if lst[i] == ')':
            lst.insert(i, '\n' + '\t'*indent_level)
            indent_level += 1
        if i in and_or:
            indent_level -= 1
            lst.insert(i, '\n' + '\t' * indent_level)
            indent_level += 1


query = str(sys.argv[1])
listified_query = []

AND_pos = find_indices(query, 'AND')
OR_pos = find_indices(query, 'OR')

load(query, listified_query)
formatting(listified_query, AND_pos, OR_pos)

print("".join(listified_query))
