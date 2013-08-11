import psycopg2

import gardendb
import gardendb.postgres


with open('.dbconfig') as f:
    conn = psycopg2.connect(f.read())
    

ThisIsACucumber= gardendb.cucumber('ThisIsACucumber', 'a b c')

pool = gardendb.postgres.dummy_pool(conn)
db = gardendb.postgres.Cucumber(ThisIsACucumber, pool)

import random
test = ThisIsACucumber(*(random.random() for i in range(3)))

with conn.cursor() as cur:
    cur.execute('SET bytea_output=hex')
    db['ahoj'] = test
    print db['ahoj']

conn.close()
