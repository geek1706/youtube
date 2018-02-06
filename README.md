# youtube

<img title="The YouTube Logo" align="right" width="20%" src="logo.png">

[![Python](https://img.shields.io/badge/Python-3.6-blue.svg)](https://docs.python.org/3/whatsnew/3.6.html)

A simple and fast Python module to retrieve data from YouTube.

  - Does not use third-party dependencies and YouTube Data API.
  - Uses a pool of threads to execute asynchronously requests. 
  - Can receive data from multiple videos at once.

## Installation

Install from source:

```
$ git clone https://github.com/Fallmay/youtube.git
$ cd youtube
$ python setup.py install
```

## Usage

Get information about a video:

```python
import youtube

video = youtube.Video('https://www.youtube.com/watch?v=nKIu9yen5nc')
print(video.title, video.duration, video.date, sep='\n')
# What Most Schools Don't Teach
# 05:44
# 2013-02-26

print(video.description)
# Learn about a new "superpower" that isn't being taught in 90% of US schools ...

print(video.statistics)
# {'likes': '115618', 'dislikes': '3549', 'rating': '4.88', 'views': '14134818'}

print(video.channel)
# {'title': 'Code.org', 'subscribers': '203K', ...

print(video.streams['adaptive']['audio'])
# {'140': {'bitrate': '128056', 'type': 'audio/mp4', ...
print(video.streams['adaptive']['video'])
# {'137': {'quality': '1080p', 'bitrate': '4276030', 'fps': '24', ...
print(video.streams['multiplexed'])
# {'22': {'quality': 'hd720', 'type': 'video/mp4', ...

if 'English' in video.captions:
    print(video.captions['English'])
# {'languageCode': 'en', 'url': ...
```

Serialize information about your favorite videos to a JSON formatted string:

```python
import json
import youtube

favorite = ['nKIu9yen5nc', 'n_KghQP86Sw', 'kccUxGDsMAQ', 'QQmFyybzon0',
            'U6hkOAnFJxM', 'qDbsiVWA2Ag', '6mbFO0ZLMW8']

data = youtube.load(favorite, video=True)
for identifier, value in data.items():
    video = youtube.Video(identifier=identifier, data=value)
    print(json.dumps(video.__dict__))
    
# {"title": "What Most Schools Don't Teach", ...
# {"title": "Internet - Understanding Technology - by CS50 at Harvard", ...
# {"title": "Multimedia - Understanding Technology - by CS50 at Harvard", ...
# {"title": "Security - Understanding Technology - by CS50 at Harvard", ...
# {"title": "Web Development - Understanding Technology - by CS50 at Harvard", ...
# {"title": "Programming - Understanding Technology - by CS50 at Harvard", ...
# {"title": "Hardware - Understanding Technology - by CS50 at Harvard", ...
```

Please see [JSON output example](docs/video.json).
