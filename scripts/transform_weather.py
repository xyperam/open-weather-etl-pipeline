import os
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
DB_USER = os.getenv('DB_USER')
DB_PASS = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')
DB_NAME = os.getenv('DB_NAME')
#Database Connection

DB_URI = f'postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}'

def transform_bronze_to_silver():
    engine = create_engine(DB_URI)
    
    
    print ("Reading data from bronze layer")
    #watermark data terakhir di silver
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT MAX(observation_time) FROM silver_weather"))
            last_watermark = result.scalar()
    except Exception:
        last_watermark =None    
    print(f"last watermark : {last_watermark}")
    
    # tarik data dari bronze yang baru
    if last_watermark:
    #Extract 
        query_extract ="""
            SELECT city,temp_celsius,humidity,weather_desc,dt FROM raw_weather
            WHERE TO_TIMESTAMP(dt) AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Jakarta' > :wm
            """
        df_raw = pd.read_sql(text(query_extract), engine,params={'wm': last_watermark})
    else : 
        df_raw = pd.read_sql("SELECT city,temp_celsius,humidity,weather_desc,dt FROM raw_weather",engine)
        df_raw = pd.read_sql_query(query_extract,engine)
    
    if df_raw.empty:
        print("No data found in bronze")
        return
    
    print("Transforming {len(df_raw)} data")
    
    #Konversi unix timestamp ke Date Time (WIB)
    
    df_raw['observation_time']= pd.to_datetime(df_raw['dt'],unit='s').dt.tz_localize('UTC').dt.tz_convert('Asia/Jakarta').dt.tz_localize(None)
    
    #mapping kolom ke format silver
    df_silver = df_raw[[
        'city',
        'temp_celsius',
        'humidity',
        'weather_desc',
        'observation_time'
    ]].rename(columns={'weather_desc':'weather_condition'})
    
    #delete duplikat dataframe sebelum dikirim
    df_silver = df_silver.drop_duplicates(subset=['city','observation_time'])
    print(f"Cleaning duplicates: {len(df_silver)} unique rows remaining.")
    
    #load : Masukan ke silver
    
    print(f"loading{len(df_silver)}rows into silver layer..")
    print(df_silver.head())
    try:
        df_silver.to_sql('silver_weather',engine, if_exists='append', index=False, method='multi')
        print("Transformation success!")
        
    except Exception as e:
        print(f"Detail error: {e}")
        
    # except Exception as e:
    #     if "unique_city_obs" in str(e):
    #         print ("Skip: data already exist in silver")
    #     else:
    #         print(f"error: {e}")
if __name__ == "__main__":
    transform_bronze_to_silver()