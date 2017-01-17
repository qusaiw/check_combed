#!/usr/bin/env python
from collections import defaultdict
import argparse
import os

cell_fail_list = {}


class Transistor:
    def __init__(self, transistor_name, drain, gate, source, transistor_type):
        self.name = transistor_name
        self.d = drain
        self.g = gate
        self.s = source
        self.mos = transistor_type


def get_transistors(cell_name):
    drains_and_sources = []
    transistors_data = {}
    dgt_dict = defaultdict(list)
    sgt_dict = defaultdict(list)
    try:
        with open("%s/cells/%s/%s.lvs" % (relative_path, cell_name, cell_name)) as lvs_file:
            for t in lvs_file:
                t = t.strip()
                if len(t) != 0 and t[0].isalpha():
                    t = t.split()
                    name = t[0]
                    d = t[1]
                    g = t[2]
                    s = t[3]
                    mos = t[4]
                    drains_and_sources.append(s)
                    drains_and_sources.append(d)
                    if d != s:
                        dgt = '%s %s %s' % (d, g, mos)
                        sgt = '%s %s %s' % (s, g, mos)
                        transistors_data[name] = Transistor(name, d, g, s, mos)
                        dgt_dict[dgt].append(transistors_data[name])
                        sgt_dict[sgt].append(transistors_data[name])

            branch_points = []
            for n in drains_and_sources:
                if drains_and_sources.count(n) > 2 and n not in branch_points:
                    branch_points.append(n)
            for n in dgt_dict.keys():
                if len(dgt_dict[n]) == 1 or n.split()[2] == 'VBP':
                    del dgt_dict[n]
            for n in sgt_dict.keys():
                if len(sgt_dict[n]) == 1 or n.split()[2] == 'VBN':
                    del sgt_dict[n]
        return drains_and_sources, dgt_dict, sgt_dict, branch_points, transistors_data
    except IOError:
        cell_fail_list[cell_name] = "no lvs, or corrupted file"


def find_series(branch_head, cell_name):
    current = branch_head
    big_list = [current]
    while True:
        series = []
        for t in get_transistors(cell_name)[4].values():
            if t.mos == 'VBN':
                if current.s == t.d and current.s not in get_transistors(cell_name)[3]:
                    series.append(t)
            elif t.mos == 'VBP':
                if current.d == t.s and current.d not in get_transistors(cell_name)[3]:
                    series.append(t)
        if len(series) == 1:
            big_list.append(series[0])
            current = series[0]
        else:
            if len(big_list) == 0:
                big_list = [branch_head]
            return [big_list, current]

# //parser//
parser = argparse.ArgumentParser()
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument('-all', help="test all cells", action="store_true")
group.add_argument('-list', help="test for provided list")
parser.add_argument('-path', help="enter the path for the review folder that contains \"cells\" folder",
                    default=os.getcwd())
args = parser.parse_args()
# returns: object

relative_path = args.path
if args.all:
    cell_list_names = {cell: cell.split("_")[1][0] for cell in os.listdir(relative_path + "/cells") if
                       (("_" in cell) and (cell.split("_")[1][0] in ("c", "v")))}
else:
    with open(args.list) as f:
        cell_list_names = {cell: cell.split("_")[1][0] for cell in [line[:-1] for line in f] if
                           (("_" in cell) and (cell.split("_")[1][0] in ("c", "v")))}
for cell in cell_list_names:
    data = get_transistors(cell)
    if not data:
        continue
    # data is [drains_and_sources, dgt_dict, sgt_dict, branch_points, transistors_data]
    to_delete = []
    for key in data[1]:
        temporary_dict = defaultdict(list)
        for branch_point in data[1][key]:
            for i in find_series(branch_point, cell)[0]:
                temporary_dict[branch_point.name].append(i.g)
            temporary_dict[branch_point.name].append(find_series(branch_point, cell)[1].s)
        history = []
        for head, tail in temporary_dict.items():
            if tail in history:
                to_delete.append(head)
            else:
                history.append(tail)

    for key in data[2]:
        temporary_dict = defaultdict(list)
        for branch_point in data[2][key]:
            for i in find_series(branch_point, cell)[0]:
                temporary_dict[branch_point.name].append(i.g)
            temporary_dict[branch_point.name].append(find_series(branch_point, cell)[1].d)
        history = []
        for head, tail in temporary_dict.items():
            if tail in history:
                to_delete.append(head)
            else:
                history.append(tail)
    final_list = []
    for i in to_delete:
        if len(find_series(data[4][i], cell)[0]) > 1:
            for u in find_series(data[4][i], cell)[0]:
                final_list.append(u.name)
    if cell_list_names[cell] == 'c' and len(final_list) == 0:
        cell_fail_list[cell] = "Combed naming, uncombed structure"
    elif cell_list_names[cell] == 'v' and len(final_list) != 0:
        cell_fail_list[cell] = "Combed structure not announced"
if cell_fail_list:
    print cell_fail_list
else:
    print "Pass"
