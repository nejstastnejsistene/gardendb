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
    my_garden[1, 2, 3] = "key isn't a string".split()
    print my_garden[1, 2, 3]

    import pprint
    pprint.pprint(my_garden.getall())
    del my_garden['ahoj']
    pprint.pprint(my_garden.getall())

    dct = { x: x**2 for x in range(20) }
    my_garden.putmany(dct)

    pprint.pprint(my_garden.getall())
conn.close()
