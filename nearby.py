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


def geomap(address, search_query, target_folder=None):
    if not address.strip():
        error_address = '1234 sesame street'
        error_points = '1234 poop road'
        return {'address': {'address': error_address},
                'points': {'address': error_points}}
    search_query = search_query.strip()
    searches = get_nearby_places(address, search_query)
    transit = get_nearby_transit(address)
    google_geo = geopy.GoogleV3()
    # get lat/lng of given address
    coordinates = google_geo.geocode(address)
    building_descr = "Queried Building"
    building_query_color, building_query_radius = 'red', 20
    searches_descr = "Nearby " + search_query
    searches_color, searches_radius = 'green', 10
    transit_descr = "Nearby bus or subway"
    transit_color, transit_radius = 'blue', 10
    columns = ('description', 'latitude',
               'longitude', 'FillColor', 'radius_in_pixels')
    building = dict(description=building_descr,
                    latitude=coordinates.latitude,
                    longitude=coordinates.longitude,
                    color=building_query_color,
                    radius=building_query_radius)
    points_list = [columns, building]
    add_to_csv(searches, searches_descr,
               searches_color, searches_radius, points_list)
    add_to_csv(transit, transit_descr,
               transit_color, transit_radius, points_list)
    if target_folder:
        path = os.path.join(target_folder, 'search.csv')
        with open(path, 'w') as csvfile:
            csv.writer(csvfile).writerows(points_list)
        # required print statement for crosscompute
        #   (http://crosscompute.com/docs)
        print('coordinates_geotable_path = ' + path)
    building = dict(latitude=building['latitude'],
                    longitude=[building['longitude']])
    return dict(address=building, points=points_list[1:])


def add_to_csv(item_list, description, color, radius, csv_list=None):
    for query in item_list:
        location = dict(description=description,
                        latitude=query['geometry']['location']['lat'],
                        longitude=query['geometry']['location']['lng'],
                        color=color,
                        radius=radius)
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
