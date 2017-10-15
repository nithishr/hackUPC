import schedule, time, tweepy, pickle, os, wget, json, requests
from tqdm import tqdm
import numpy as np
import matplotlib.pyplot as plt


class GeoScraper:
    def __init__(self, consumer_key, consumer_secret, access_token_key, access_token_secret):
        auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        auth.set_access_token(access_token_key, access_token_secret)
        self.api = tweepy.API(auth, wait_on_rate_limit=True)
        print(self.api.me().name)

    def prepare_search(self, city='Barcelona', granularity='city'):
        self.city = city
        self.granularity = granularity
        self.place_id = self.api.geo_search(query=city, granularity=granularity)[0].id
        self.search_q = "place:{}".format(self.place_id)
        self.users = set()
        return self.search_q

    def start_search(self, max_tweets=100):
        self.places = [status._json for status in tqdm(tweepy.Cursor(self.api.search, q=self.search_q).items(max_tweets))]
        for i in self.places:
            if i['coordinates']:
                user = {'lat': i['coordinates']['coordinates'][1],
                        'lon': i['coordinates']['coordinates'][0],
                        'text': ' '.join(i['text'].strip().split()),
                        'hashtags': i['entities'].get('hashtags', []),
                        'media': 'None',

                        }
                media = i['entities'].get('media', [])
                if len(media) > 0:
                    user['media'] = media[0]['media_url']
                self.users.add(json.dumps(user))
        self.dump()
        return self.users

    def load_users(self, path='./out.pickle'):
        with open(path, 'rb') as f:
            self.users = pickle.load(f)
        print('Loaded successfully')

    def generate_locations(self):
        locations = [(json.loads(i)['lat'], json.loads(i)['lon']) for i in self.users]
        lat = np.array([i[0] for i in locations if i[0]])
        long = np.array([i[1] for i in locations if i[0]])
        plt.scatter(lat, long, )
        plt.show()

    def dump(self, pathpickle='./out', pathjson='./out'):
        with open(pathpickle + '.pickle', 'wb') as f:
            pickle.dump(self.users, f)
        with open(pathjson + '.json', 'w+') as f:
            for i in self.users:
                i = json.loads(i)
                f.write("{")
                f.write('"lat":{}, "lon":{}, "text":{}, "media":{}'.format(i['lat'], i['lon'], i['text'], i['media']))
                f.write('}\n')
        with open(pathjson + '.txt', 'w+') as f:
            for user in self.users:
                user = json.loads(user)
                f.write('{} {}\n'.format(user['lat'], user['lon']))