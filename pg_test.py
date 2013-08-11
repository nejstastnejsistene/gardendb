import psycopg2

import gardendb
import gardendb.postgres


with open('.dbconfig') as f:
    conn = psycopg2.connect(f.read())
    

ThisIsACucumber= gardendb.cucumber('ThisIsACucumber', 'a b c')

pool = gardendb.postgres.dummy_pool(conn)
my_garden = gardendb.postgres.Garden('my_garden', pool)

import random
test = ThisIsACucumber(*(random.getrandbits(32) for i in range(3)))

with conn.cursor() as cur:
    my_garden['ahoj'] = test
    print my_garden['ahoj']
    my_garden['not_a_cucumber'] = range(10)
    print my_garden['not_a_cucumber']

conn.close()
