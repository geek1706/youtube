from setuptools import setup

setup(
    name='youtube',
    version='0.0.1',
    author='Fallmay',
    url='https://github.com/Fallmay/youtube',
    license='MIT',

    description='Retrieve data from YouTube without using YouTube Data API.',
    long_description='''A simple and fast Python module to retrieve data from YouTube without using 
    YouTube Data API and third-party dependencies.''',

    packages=['youtube'],
    package_data={'youtube': ['data/ciphers.json']},
)
