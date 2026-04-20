import os
import requests
import pandas as pd
from sqlalchemy import create_engine
from datetime import datetime
import sys
import time
from dotenv import load_dotenv

# Configuration
load_dotenv()
API_KEY = os.getenv('OPENWEATHER_API_KEY')
DB_USER = os.getenv('DB_USER')
DB_PASS = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')
DB_NAME = os.getenv('DB_NAME')

CITIES =['Depok','Jakarta','Bandung']
URL = f'http://api.openweathermap.org/data/2.5/weather?q={{city}}&appid={API_KEY}&units=metric'

# 3. Susun Connection String secara dinamis
DB_URI = f'postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}'

def fetch_weather_data():
    for city in CITIES:
        try:
            print(f"[{datetime.now()}] Fetching data cuaca untuk {city}.." )
            response = requests.get(URL.format(city=city))
            response.raise_for_status() # akan error jika status !=200

            data = response.json()

            # TRANSFORM DATA
            clean_data={
                'city': data.get('name'),
                'country': data.get('sys',{}).get('country'),
                'temp_celsius':data.get('main',{}).get('temp'),
                'humidity': data.get('main',{}).get('humidity'),
                'weather_desc':data.get('weather',{})[0].get('description'),
                'wind_speed':data.get('wind',{}).get('speed'),
                'sunrise_ts':datetime.fromtimestamp(data.get('sys',{}).get('sunrise')),
                'dt':data.get('dt'),
                'ingested_at':datetime.now()
            }
            df = pd.DataFrame([clean_data])

            engine = create_engine(DB_URI)
            df.to_sql('raw_weather',engine,if_exists='append',index=False)

            print(f"SUCCESS: Data cuaca untuk {city} berhasil disimpan ke tabel'raw_weather'.")
            time.sleep(1)
        except Exception as e :
            if "unique_city_time" in str(e):
                print(f"SKIP: Data untuk {city} at this time already exists")
            else:
                print(f"ERROR for {city}  :{e}",file = sys.stderr)
if __name__ == "__main__":
    fetch_weather_data()