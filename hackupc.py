from flask import Flask, jsonify, request, render_template, redirect
import googlemaps
from datetime import datetime, timedelta
import json
import requests
import pymongo
import uuid
from raven.contrib.flask import Sentry
import random
from operator import itemgetter

gmaps = googlemaps.Client(key='AIzaSyDPqWY4_srj9nrZwlRke9Sz7APe76DdSwk')
gmaps_dist = googlemaps.Client(key='AIzaSyAjG2UNQiTRwSKYr3j85TXQYueADPNcGSo')
MONGO_URI = r'mongodb://admin:tel#261290@ds033976.mlab.com:33976/ariadne-db'
client = pymongo.MongoClient(MONGO_URI)
db = client.get_default_database()
queries = db['queries']
db_errors = db['errors']

app = Flask(__name__)


@app.route('/')
def hello_world():
    return render_template('landing.html')


@app.route('/transit', methods=['POST'])
def get_google_transit():
    source = request.form.get('source')
    destination = request.form.get('destination')
    ip = request.remote_addr
    uid = str(uuid.uuid4())
    now = datetime.now()
    next = now + timedelta(minutes=10)
    future = next + timedelta(minutes=10)
    doc = {'source': source, 'destination': destination, 'id': uid, 'time': now, 'ip': ip}
    try:
        directions_result = gmaps.directions(source, destination,
                                             mode="transit",
                                             departure_time=now)
        directions_result_next = gmaps.directions(source, destination,
                                             mode="transit",
                                             departure_time=next)
        directions_result_future = gmaps.directions(source, destination,
                                             mode="transit",
                                             departure_time=future)
        # print(directions_result)
        direction_current = parse_google_result(directions_result)
        direction_next = parse_google_result(directions_result_next)
        direction_future = parse_google_result(directions_result_future)
        directions = []
        directions.append(direction_current)
        directions.append(direction_next)
        directions.append(direction_future)
        if len(directions)>0:
            print(directions)
            directions_sorted = sorted(directions, key=itemgetter('forecast'), reverse=True)
            print(directions_sorted)
            print("-1", directions_sorted[-1])
            # return jsonify(directions_sorted)
            return render_template("results.html", recommendation=directions_sorted[-1], directions=directions)
        else:
            print("Error")
            return redirect('/error', code=302)
    except Exception as e:
        print(repr(e))
        # db_errors.insert_one(doc)
        return redirect('/error', code=302)
        # render_template('error.html')


@app.route('/density-map')
def get_info():
    latlons = []
    with open("/home/nithishr/hackupc/out.txt", 'r') as f:
        latlons = [i for i in f.readlines()]
    lats = [i.split()[0] for i in latlons]
    longs = [i.split()[1] for i in latlons]
    # print(lats)
    # print(longs)
    return render_template("density.html", lats=lats, lons=longs)


@app.route('/error')
def load_error():
    return render_template('error.html')


def parse_google_result(directions_result):
    if len(directions_result) > 0:
        # print json.dumps(directions_result)
        directions = json.dumps(directions_result[0])
        legs = directions_result[0]['legs'][0]
        steps = legs['steps']
        result_steps = {}
        result_steps['legs'] = []
        exit_step = 0
        count = 0
        count_transit = 0
        for step in steps:
            res_step = {}
            if step['travel_mode'] == 'WALKING':
                res_step['timeDep'] = ''
                res_step['type'] = 'walk'
                res_step['summary'] = step['html_instructions']
                res_step['direction'] = ''
                res_step['line'] = ''
                res_step['start'] = ''
                res_step['stop'] = ''
                # res_step['exit'] = ''
                # res_step['compartment'] = ''
                #         print res_step
                result_steps['legs'].append(res_step)
            elif step['travel_mode'] == 'TRANSIT':
                res_step['timeDep'] = step['transit_details']['departure_time']['text']
                res_step['type'] = step['transit_details']['line']['vehicle']['name']
                res_step['summary'] = step['html_instructions']
                res_step['direction'] = step['transit_details']['headsign']
                try:
                    res_step['line'] = step['transit_details']['line']['short_name']
                except KeyError:
                    res_step['line'] = step['transit_details']['line']['name']
                try:
                    res_step['line_logo'] = step['transit_details']['line']['vehicle']['local_icon']
                except:
                    pass
                res_step['start'] = step['transit_details']['departure_stop']['name']
                res_step['stop'] = step['transit_details']['arrival_stop']['name']
                result_steps['legs'].append(res_step)
                count_transit += 1
            count += 1
        # print result_steps
        result_steps['forecast'] = random.randint(1,3)
        result_steps['duration'] = legs['duration']['text']
        if result_steps['forecast'] != 1:
            result_steps['delay'] = random.randint(2,6)
        else:
            result_steps['delay'] = random.randint(0,1)
        print(result_steps)
        return result_steps
        # return jsonify(directions_result[0])
    else:
        return None


if __name__ == '__main__':
    app.run(host='0.0.0.0')
