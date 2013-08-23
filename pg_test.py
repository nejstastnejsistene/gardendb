import psycopg2

import gardendb
import gardendb.postgres


with open('.dbconfig') as f:
    conn = psycopg2.connect(f.read())
    

ThisIsACucumber= gardendb.cucumber('ThisIsACucumber', 'a b c')

pool = gardendb.postgres.dummy_pool(conn)
my_garden = gardendb.postgres.PgGarden('my_garden', pool)

import random
test = ThisIsACucumber(*(random.getrandbits(32) for i in range(3)))

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

typed_garden = gardendb.postgres.PgGarden('typed_garden', pool, cls=ThisIsACucumber)

typed_garden['foo'] = test
print typed_garden['foo']
try:
    typed_garden['bar'] = (1, 2, 3)
except TypeError:
    pass
else:
    assert False, 'type error should have been raised'

import collections
NamedTuple = collections.namedtuple('NamedTuple', 'x y z')
named_tuple_garden = gardendb.postgres.PgGarden('named_tuple_garden', pool, NamedTuple)

named_tuple_garden['foo'] = NamedTuple(1, 2, 3)
print named_tuple_garden['foo']
try:
    named_tuple_garden['bar'] = test
except TypeError:
    pass
else:
    assert False, 'type error should have been raised'

print named_tuple_garden.get('not here', 'not here')
try: named_tuple_garden['not here']
except KeyError: pass
else: assert False
del named_tuple_garden['not here']

asdf = gardendb.postgres.PgGarden('asdf', pool)
with asdf.lock('dictionary', {}) as ctx:
    ctx.value['x'] = 1
print asdf['dictionary']['x']

conn.close()
