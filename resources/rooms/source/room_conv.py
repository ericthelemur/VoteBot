#!/usr/bin/env python3

"""
Manually run. Combines Tabula's mapping and Timetable reports to form single room mapping
These data sources need manually fetching, so combining them is a one time thing.
"""
import json


def read_mapping(filename):
    with open(str(filename)) as f:
        l = [l.split(" | ") for l in f.readlines()]
        return {x[0].strip(): x[1].strip() for x in l if len(x) > 1}


tabtonames = read_mapping("tabula-sciencianame.txt")
nametourl = read_mapping("scientianame-url.txt")

custom_names = read_mapping("custom-maptotab.txt")
custom_tabtoname = read_mapping("custom-tabtosname.txt")


def main():
    print("Missing Conversions")
    mapping = {}
    for tab, n in (tabtonames | custom_names).items():
        if tab in custom_tabtoname:
            name = custom_tabtoname[tab]
        else:
            name = n
        url = nametourl.get(name)
        if url is None:
            url = nametourl.get(tab)
        if url is None:
            print(tab, "|", name, "|", url)
        else:
            mapping[tab] = url

    for name in nametourl:
        if name not in mapping.keys() and name not in mapping.values():
            v = nametourl[name]
            mapping[name] = mapping[name] = v

    with open("../room_to_surl.json", "w") as room_to_surl:
        json.dump(mapping, room_to_surl, indent=4)


if __name__ == "__main__":
    main()
