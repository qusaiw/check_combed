#!/usr/bin/env python
# Written by Qusai Abu-Obaida
# 17-Jan-2017
#test_GE8
import argparse
import os
import re
import pprint

from collections import defaultdict

cell_fail_list = {}


class Transistor:
    def __init__(self, transistor_name, drain, gate, source, transistor_type):
        self.name = transistor_name
        self.d = drain
        self.g = gate
        self.s = source
        self.mos = transistor_type


def get_transistors(cell_name):
    """ Return drains and sources in a cell (list), ((drain/source) gate type) combinations with
        transistors that share them(dict: {dgt/sgt: [trans1, trans2 ...}), branch point (list),
        and transistors data (dict: {transistor: transistor(object)})
    """
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
        cell_fail_list[cell_name] = "no lvs"


def find_series(branch_head, cell_name):
    """ Returns a list of transistors connected in series with a given branch point
        and the name of the last transistor before encountering another branch point
    """
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

# Parser
parser = argparse.ArgumentParser()
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument('-all', help="test all cells", action="store_true")
group.add_argument('-list', help="test for provided list")
parser.add_argument('-path', help="Review folder path", default=os.getcwd())
args = parser.parse_args()
# args is an object, ex: args.path = PATH
relative_path = args.path


def main():
    """ Performs a structure test on all cells excluding flops, latches, CK cells, and fillers in their name and
        determines whether they have a combed structure, then checks if that structure is announced in the name.
        prints a dictionary: {cell: error)
    """
    combed = re.compile(r'_(cv)(\d+)')
    exclude = re.compile(r'(^(f|l)[dsi])|(^ck)')
    # regex that matches any occurrence of either _cv*_ or _v*_ in a cell's name

    def combed_cell(cell): return combed.search(cell)
    if args.all:
        try:
            cell_list_names = {cell: combed_cell(cell) for cell in os.listdir(relative_path + "/cells") if
                               not exclude.search(cell)}
        except OSError:
            print 'Did not find "cells" folder'
            quit()
    else:
        try:
            with open(args.list) as f:
                cell_list_names = {cell.strip(): combed_cell(cell) for cell in [line[:-1] for line in f] if
                                   len(cell) != 0 and not exclude.search(cell)}
        except IOError:
            print "%s doesn't exist" % args.list
            quit()
    print "Testing %d cells..." % len(cell_list_names)
    for cell in cell_list_names:
        data = get_transistors(cell)
        if not data:
            continue
        # data is [drains_and_sources, dgt_dict, sgt_dict, branch_points, transistors_data]
        to_delete = []
        for key in data[1]:
            temporary_dict = defaultdict(list)
            for branch_point in data[1][key]:
                series = find_series(branch_point, cell)
                for i in series[0]:
                    temporary_dict[branch_point.name].append(i.g)
                temporary_dict[branch_point.name].append(series[1].s)
                # temporary_dict now contains the name of a branch point as key and it's value
                # is the gates of the transistors connected with in series and finally the last
                #  point before encountering another branch point
            history = []
            for head, tail in temporary_dict.items():
                if tail in history:
                    to_delete.append(head)
                else:
                    history.append(tail)
            # This part appends to the "to_delete" list all the non unique items in temporary_dict
        for key in data[2]:
            temporary_dict = defaultdict(list)
            for branch_point in data[2][key]:
                series = find_series(branch_point, cell)
                for i in series[0]:
                    temporary_dict[branch_point.name].append(i.g)
                temporary_dict[branch_point.name].append(series[1].d)
            history = []
            for head, tail in temporary_dict.items():
                if tail in history:
                    to_delete.append(head)
                else:
                    history.append(tail)
        final_list = []
        for i in to_delete:
            # exclude "fingers" of the same transistor ex: MP1 A B C VBN, MP1_2 A B C VBN
            if len(find_series(data[4][i], cell)[0]) > 1:
                for u in find_series(data[4][i], cell)[0]:
                    final_list.append(u.name)
        if cell_list_names[cell] and len(final_list) == 0:
            cell_fail_list[cell] = "Combed naming, uncombed structure"
        elif not cell_list_names[cell] and len(final_list) != 0:
            cell_fail_list[cell] = "Combed structure not announced" + str(final_list)
    if cell_fail_list:
        pprint.pprint(cell_fail_list)
    else:
        print("Pass")


if __name__ == '__main__':
    main()
