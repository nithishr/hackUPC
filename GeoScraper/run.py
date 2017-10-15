from credential import *
from GeoScraper import GeoScraper
import schedule
import time


def main():
    geo_scr = GeoScraper(consumer_key(), consumer_secret(), access_token_key(), access_token_secret())
    geo_scr.prepare_search()
    geo_scr.load_users()
    geo_scr.start_search(max_tweets=200)
    schedule.every(3).minutes.do(geo_scr.start_search)
    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt as e:
        geo_scr.dump()
        print('Okay')

if __name__ == '__main__':
    main()