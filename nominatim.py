#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import re
import requests


NOMINATIM_URL = "https://nominatim.openstreetmap.org"
SEARCH_URL = f"{NOMINATIM_URL}/search"
REVERSE_URL = f"{NOMINATIM_URL}/reverse"

BBOX_DELTA = 5e-3

OSM_URL_TPL = "https://www.openstreetmap.org/?mlat={}&mlon={}&zoom=17/{}/{}"
JOSM_URL_TPL = "http://localhost:8111/load_and_zoom?top={}&bottom={}&left={}&right={}"

USER_AGENT = "Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:109.0) Gecko/20100101 Firefox/112.0"





def search(query):
    params = {
        "format": "jsonv2",
        "q": query
    }

    result = request(SEARCH_URL, params)

    return result

def reverse(point):
    params = {
        "format": "jsonv2",
        "lat": point[0],
        "lon": point[1]
    }

    result = request(REVERSE_URL, params)
    if not result:
        return None

    if "error" in result:
        print(result["error"], file=sys.stderr)
        return None

    return result

def request(url, params):
    headers = {
        "User-Agent": USER_AGENT
    }

    response = requests.get(url=url, params=params, headers=headers)
    if response.status_code < 200 or response.status_code >= 300:
        print(f"GET {url} error: {response.status_code}", file=sys.stderr)
        return None

    return response.json()


def get_bbox(point):
    return (
        point[0] + BBOX_DELTA,
        point[0] - BBOX_DELTA,
        point[1] - BBOX_DELTA,
        point[1] + BBOX_DELTA
    )

def get_num(s):
    n = re.findall(r'[+-]?(\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?', s)[0][0]
    return float(n)

def open_josm(url):
    try:
        response = requests.get(url=url)
    except Exception as error:
        print(error)
        return False

    if response.status_code < 200 or response.status_code >= 300:
        print(f"GET {url} error: {response.status_code}", file=sys.stderr)
        return False

    if response.text != "ok":
        print("JOSM error", file=sys.stderr)
        return False

    return True



def direct_geocode(args):
    query = args[0].strip()

    result = search(query)
    if not result:
        return False

    places = {}

    for item in result:
        latitude = float(item["lat"])
        longitude = float(item["lon"])
        bbox = get_bbox((latitude, longitude))
        view_url = OSM_URL_TPL.format(latitude, longitude, latitude, longitude)
        edit_url = JOSM_URL_TPL.format(*bbox)
        category = item["category"];
        type = item["type"];
        name = item["display_name"];
        place = {
            "name": name,
            "view": view_url,
            "edit": edit_url
        }

        if category not in places:
            places[category] = {}
        if type not in places[category]:
            places[category][type] = []

        places[category][type].append(place)

    for category in places:
        print(category)

        for type in places[category]:
            print(f"  {type}")

            for place in places[category][type]:
                print("    {}, view on OSM: <{}>, edit in JOSM: <{}>".format(place["name"], place["view"], place["edit"]))

    return True


def reverse_geocode(args):
    if len(args) < 2:
        print(f"latitude longitude required", file=sys.stderr)
        return False

    point = list(map(get_num, args))
    
    result = reverse(point)
    if not result:
        return False

    latitude = point[0] #result["lat"]
    longitude = point[1] #result["lon"]
    category = result["category"]
    type = result["type"]
    name = result["display_name"]
    bbox = get_bbox(point)
    view_url = OSM_URL_TPL.format(latitude, longitude, latitude, longitude)
    edit_url = JOSM_URL_TPL.format(*bbox)

    print(f"{category}/{type} {name}, view on OSM: <{view_url}>, edit in JOSM: <{edit_url}>")

    if len(args) > 2:
        return open_josm(edit_url)

    return True




handlers = {
    "s": direct_geocode,
    "r": reverse_geocode
}




def main():
    if len(sys.argv) < 2:
        print(f"usage: {os.path.basename(sys.argv[0])} <s|r> <query|lat lon>", file=sys.stderr)
        sys.exit(1)

    mode = sys.argv[1].strip().lower()
    if mode not in handlers.keys():
        print(f"unknown mode: {mode}", file=sys.stderr)
        sys.exit(1)

    result = handlers[mode](sys.argv[2:])
    if not result:
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()

