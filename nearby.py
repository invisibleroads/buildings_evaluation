import argparse
import csv
import geopy
import os
import requests
from api_keys import places_key
from invisibleroads_macros.disk import make_folder


RADIUS = 300


def get_nearby_places(address, search_query=None):
    # places search api
    url = 'https://maps.googleapis.com/maps/api/place/nearbysearch/json'
    google_geo = geopy.GoogleV3()
    location = google_geo.geocode(address)
    location = str(location.latitude) + ',' + str(location.longitude)
    params = dict(location=location, radius=RADIUS,
                  key=places_key)
    if search_query:
        params['type'] = search_query
    response = requests.get(url, params=params)
    return response.json()['results']


def get_nearby_transit(address):
    results = []
    # only allowed one type search per query
    # (multiple-type searches is deprecated)
    types = ['bus_station', 'subway_station']
    for query in types:
        results.extend(get_nearby_places(address, query))
    return results


def geomap(address, search_query, target_folder):
    searches = get_nearby_places(address, search_query)
    transit = get_nearby_transit(address)
    google_geo = geopy.GoogleV3()
    # get lat/lng of given address
    coordinates = google_geo.geocode(address)
    building_query_color, building_query_radius = 'red', 20
    searches_color, searches_radius = 'green', 10
    transit_color, transit_radius = 'blue', 10
    columns = ('latitude', 'longitude', 'fillcolor', 'radiusinpixels')
    building = (coordinates.latitude, coordinates.longitude,
                building_query_color, building_query_radius)
    csv_list = [columns, building]
    add_to_csv(searches, searches_color, searches_radius, csv_list)
    add_to_csv(transit, transit_color, transit_radius, csv_list)
    path = os.path.join(target_folder, 'search.csv')
    with open(path, 'w') as csvfile:
        csv.writer(csvfile).writerows(csv_list)
    # required print statement for crosscompute (http://crosscompute.com/docs)
    print('coordinates_geotable_path = ' + path)


def add_to_csv(item_list, color, radius, csv_list=None):
    for query in item_list:
        location = (query['geometry']['location']['lat'],
                    query['geometry']['location']['lng'],
                    color,
                    radius)
        csv_list.append(location)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--target_folder',
                        type=make_folder, default='results')
    parser.add_argument('--address',
                        type=str, required=True)
    parser.add_argument('--search_query',
                        type=str, default=None)
    args = parser.parse_args()
    geomap(args.address, args.search_query, args.target_folder)
