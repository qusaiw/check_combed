#!/usr/bin/env python
# Written by Qusai Abu-Obaida
# 7-Jan-2017
from collections import defaultdict


class Transistor:
    def __init__(self, transistor_name, drain, gate, source, transistor_type):
        self.name = transistor_name
        self.d = drain
        self.g = gate
        self.s = source
        self.mos = transistor_type


def find_series(branch_head):
    current = branch_head
    big_list = [current]
    while True:
        series = []
        for t in transistors_data.values():
            if t.mos == 'VBN':
                if current.s == t.d and current.s not in branch_points:
                    series.append(t)
            elif t.mos == 'VBP':
                if current.d == t.s and current.d not in branch_points:
                    series.append(t)
        if len(series) == 1:
            big_list.append(series[0])
            current = series[0]
        else:
            if len(big_list) == 0:
                big_list = [branch_head]
            return [big_list, current]
            break

f = open('test_file.txt', 'r')
dgt_dict = defaultdict(list)
sgt_dict = defaultdict(list)
transistors_data = {}
drains_and_sources = []
for line in f:
    line = line.strip()
    if len(line) != 0 and line[0] == 'M':
        line = line.split()
        name = line[0]
        d = line[1]
        g = line[2]
        s = line[3]
        mos = line[4]
        drains_and_sources.append(s)
        drains_and_sources.append(d)
        if d != s:
            dgt = d + " " + g + " " + mos
            sgt = s + " " + g + " " + mos
            transistors_data[name] = Transistor(name, d, g, s, mos)
            dgt_dict[dgt].append(transistors_data[name])
            sgt_dict[sgt].append(transistors_data[name])
branch_points = []
for i in drains_and_sources:
    if drains_and_sources.count(i) > 2 and i not in branch_points:
        branch_points.append(i)
for i in dgt_dict.keys():
    if len(dgt_dict[i]) == 1 or i.split()[2] == 'VBP':
        del dgt_dict[i]
for i in sgt_dict.keys():
    if len(sgt_dict[i]) == 1 or i.split()[2] == 'VBN':
        del sgt_dict[i]

to_delete = []
for key in dgt_dict:
    temporary_dict = defaultdict(list)
    for branch_point in dgt_dict[key]:
        for i in find_series(branch_point)[0]:
            temporary_dict[branch_point.name].append(i.g)
        temporary_dict[branch_point.name].append(find_series(branch_point)[1].s)
    history = []
    for head, tail in temporary_dict.items():
        if tail in history:
            to_delete.append(head)
        else:
            history.append(tail)

for key in sgt_dict:
    temporary_dict = defaultdict(list)
    for branch_point in sgt_dict[key]:
        for i in find_series(branch_point)[0]:
            temporary_dict[branch_point.name].append(i.g)
        temporary_dict[branch_point.name].append(find_series(branch_point)[1].d)
    history = []
    for head, tail in temporary_dict.items():
        if tail in history:
            to_delete.append(head)
        else:
            history.append(tail)
final_list = []
for i in to_delete:
    for u in find_series(transistors_data[i])[0]:
        final_list.append(u.name)
new_file = []

f = open('test_file.txt', 'r')
new_file = open('new_file.txt', 'w')

for line in f:
    if len(line) != 1:
        if line.split()[0] not in final_list:
            new_file.write(line)
print 'Transistors deleted from LVS file: '
print (final_list)
