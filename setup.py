from distutils.core import setup

with open('version.txt') as f:
    version = f.read().strip()

url = 'https://github.com/nejstastnejsistene/gardendb'

classifiers = [
    'Development Status :: 2 - Pre-Alpha',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: BSD License',
    'Natural Language :: English',
    'Operating System :: POSIX',
    'Programming Language :: Python :: 2.7',
    'Programming Language :: Python :: Implementation :: CPython',
    'Topic :: Database',
    ]

setup(
    name = 'gardendb',
    packages = ['gardendb'],
    version = version,
    description = 'Simple python flat-file databases with Cucumbers: '
                  'simple, version-controlled records with streamlined '
                  'pickle representations.',
    author = 'Peter Johnson',
    author_email = 'pajohnson@email.wm.edu',
    url = url,
    download_url = url + '/releases',
    keywords = [],
    classifiers = classifiers,
    long_description = '''\
This is a WIP, see the readme for more info.
'''
    )
