import pymongo
import os
import pandas as pd
from datetime import datetime

client = pymongo.MongoClient(os.environ['MONGODB_URI'])
db = client[os.environ['DATABASE']]
days = db["days"]


def insert(cases: dict, timestamp):
    days.update_one(
        {'date': timestamp},
        {'$set': {'date': timestamp,
                  **{'cases.{}'.format(key): value for key, value in cases.items()}}},
        upsert=True)


def insert_from_file(path='../CountyUAs_cases_table-Mar21.csv', timestamp=datetime(2020, 3, 21).timestamp()):
    df = pd.read_csv(path).set_index('GSS_CD')['TotalCases']
    insert(df.to_dict(), timestamp)


def get_available_dates():
    return [datetime.fromtimestamp(document['date']) for document in days.find({}, {'date': 1}).sort('date')]


def get_date(timestamp):
    return document_to_dataframe(days.find_one({'date': timestamp}))


def get_location(location):
    return [(datetime.fromtimestamp(loc['date']).isoformat(), loc['cases'][location])
            for loc in days.find({}, {'date': 1, 'cases.{}'.format(location): 1, '_id': -1}).sort('date')
            if location in loc['cases']]


def document_to_dataframe(document):
    return pd.DataFrame(document).reset_index().rename(columns={'index': 'code'})


def get_all_documents():
    docs = list(days.find({}, {'_id': 0}).sort('date'))
    for doc in docs:
        if 'S08000015' in doc['cases'].keys():
            del doc['cases']['S92000003']
    docs = pd.concat([document_to_dataframe(doc) for doc in docs])
    docs['date'] = docs.date.apply(lambda x: datetime.fromtimestamp(x).strftime('%d/%m'))
    return docs
