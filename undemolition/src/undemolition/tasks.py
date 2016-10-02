import json
import copy 
import re
import math
import random
import time

# from urllib import quote_plus
import requests

from celery.contrib import rdb as pdb
from flask.ext.celery import Celery

from undemolition import app, redis_store


celery = Celery(app)


def get_redis_map_with_default(map_name):
    store_val = redis_store.hmget(map_name)
    return store_val if store_val is not None else {}


@celery.task()
def query_demolition_permits():
    """
    task called by celerybeat will query Socrata API endpoint
    for Seattle demolition permits and will save any new permits
    to Redis store queue of permits to process, if they have not
    already been processed.
    No return value.  Side-effect only
    """
    
    demo_permits_processed = get_redis_map_with_default('demo_permits_processed')
    demo_permits_process_queue = get_redis_map_with_default('demo_permits_queue')
    print "getting demolition permits from Socrata (data.seattle.gov)"
    
    json_res = requests.get('https://data.seattle.gov/resource/i5jq-ms7b.json?permit_type=Demolition')
    permit_res = json.dumps(json_res)
    new_permits = dict([(key, val) for (key, val) in permit_res.iter_items() if key not in demo_permits_processed])

    demo_permits_queue.update(new_permits)
    redis_store.hmset('demo_permits_queue', demo_permits_queue)
