import pymongo
import os
import pandas as pd
from datetime import datetime

client = pymongo.MongoClient(os.environ['MONGODB_URI'])
db = client[os.environ['DATABASE']]
days = db["days"]


def insert(cases, timestamp):
    days.update_one({'date': timestamp}, {'$set': {'date': timestamp, 'cases': cases}}, upsert=True)


def insert_from_file(path='../CountyUAs_cases_table-Mar21.csv', timestamp=datetime(2020, 3, 21).timestamp()):
    df = pd.read_csv(path).set_index('GSS_CD')['TotalCases']
    insert(df.to_dict(), timestamp)


def get_available_dates():
    return [datetime.fromtimestamp(document['date']) for document in days.find({}, {'date': 1}).sort('date')]


def get_date(timestamp):
    return pd.DataFrame(
        days.find_one(
            {'date': timestamp}
        )).reset_index().rename(columns={'cases': 'TotalCases', 'index': 'GSS_CD'})
