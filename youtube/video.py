import json
import re
from html.parser import HTMLParser
from urllib import parse

from youtube import ciphers
from youtube.utils import load, get_video_id


class Video(object):
    """Base class for YouTube video.

    Args:
        url (str): The YouTube video URL.
        identifier (str): The YouTube video ID.
        data (dict): The pre-loaded data.

    Note:
        If the data has not been loaded previously, specify the `url` or `identifier`.
        Otherwise, specify the `identifier` and `data`.

    """

    def __init__(self, url=None, *, identifier=None, data=None):
        self.title = None
        self.duration = None
        self.date = None
        self.description = None
        self.category = None
        self.license = None
        self.keywords = None
        self.statistics = None
        self.channel = None
        self.player = None
        self.streams = None
        self.captions = None
        self.thumbnails = None
        self.id = None
        self.url = None

        self.__init(url, identifier, data)

    def __init(self, url, identifier, data):
        if url is not None:
            self.id = get_video_id(url)
            data = load([self.id], video=True)

        elif identifier is not None and data is None:
            self.id = identifier
            data = load([self.id], video=True)

        elif identifier is not None and data is not None:
            self.id = identifier
            data = {identifier: data}

        data = VideoInfoExtractor(self.id, data)

        self.title = data.title()
        self.duration = data.duration()
        self.date = data.date()
        self.description = data.description()
        self.category = data.category()
        self.license = data.license()
        self.keywords = data.keywords()
        self.statistics = data.statistics()
        self.channel = data.channel()
        self.player = data.player()
        self.streams = data.streams(self.player)
        self.captions = data.captions()
        self.thumbnails = data.thumbnails()
        self.url = 'https://www.youtube.com/watch?v={0}'.format(self.id)

    def best_adaptive(self, fmt='mp4', audio=False, video=False, full=True):
        """Get a best adaptive stream.

        Args:
            fmt (str): The audio/video format. Default to 'mp4'.
            audio (bool): If True, return only audio. Default to False.
            video (bool): If True, return only video. Default to False.
            full (bool): If True, return `dict` audio/video. Default to True.

        """
        fmt = fmt.lower()

        if fmt not in ('mp4', 'webm', '3gp', 'm4a'):
            return None

        if 'adaptive' in self.streams:
            _audio = self.streams['adaptive']['audio']
            _video = self.streams['adaptive']['video']

            def audio_bitrate(itag):
                if _audio[itag]['type'] == 'audio/{0}'.format(fmt):
                    return int(_audio[itag]['bitrate'])
                else:
                    return 0

            def video_bitrate(itag):
                if _video[itag]['type'] == 'video/{0}'.format(fmt):
                    return int(_video[itag]['bitrate'])
                else:
                    return 0

            _audio = _audio[max(_audio, key=audio_bitrate)]
            _video = _video[max(_video, key=video_bitrate)]

            if audio is True:
                return _audio
            elif video is True:
                return _video
            elif full is True:
                return dict(audio=_audio, video=_video)

    def best_multiplexed(self, fmt='mp4'):
        """Get a best multiplexed stream.

        Args:
            fmt (str): The audio/video format. Default to 'mp4'.

        """
        fmt = fmt.lower()

        if fmt not in ('mp4', 'webm', '3gp', 'm4a'):
            return None

        if 'multiplexed' in self.streams:
            itags = ('22', '18', '43', '36', '17')  # Sorted by quality.
            multiplexed = self.streams['multiplexed']

            for itag in itags:
                if multiplexed.get(itag) is not None:
                    if multiplexed[itag]['type'] == 'video/{0}'.format(fmt):
                        return multiplexed[itag]


class VideoInfoExtractor(object):
    """Provides methods to extract information about a YouTube video.

    Args:
        identifier (str): The YouTube video ID.
        data (dict): The pre-loaded data.

    """

    def __init__(self, identifier, data):
        self.id = identifier

        # Information received from https://www.youtube.com/get_video_info?...
        self.info = data[self.id]['info']

        # HTML page https://www.youtube.com/watch?v=...
        self.html = data[self.id]['html']

    def title(self):
        return self.info.get('title')

    def duration(self):
        seconds = int(self.info.get('length_seconds'))
        if 3600 < seconds:
            return '{:02}:{:02}:{:02}'.format(seconds // 3600, seconds % 3600 // 60, seconds % 60)
        elif 3600 > seconds:
            return '{:02}:{:02}'.format(seconds % 3600 // 60, seconds % 60)

    def date(self):
        return re.search(r'itemprop="datePublished" content="(.*)">', self.html).group(1)

    def description(self):
        description = re.search('<p id="eow-description" class="" >(.*)</p>', self.html).group(1)
        if description == '':
            return None

        class DescriptionParser(HTMLParser):
            """Extract a video description from the HTML. See examples at:
            https://docs.python.org/3/library/html.parser.html

            """

            data = []
            urls = []

            def error(self, message):
                pass

            def handle_starttag(self, tag, attrs):
                attrs = dict(attrs)
                if 'href' in attrs:
                    href = dict(parse.parse_qsl(attrs['href']))

                    if 'q' in href:
                        self.urls.append(href['q'])

                    elif '/watch?v' in href:
                        url = 'https://www.youtube.com/watch?v={0}'.format(href['/watch?v'])
                        self.urls.append(url)

                    elif 'https://www.youtube.com/playlist?list' in href:
                        identifier = href['https://www.youtube.com/playlist?list']
                        url = 'https://www.youtube.com/playlist?list={0}'.format(identifier)
                        self.urls.append(url)

            def handle_endtag(self, tag):
                if tag == 'br':
                    self.data.append('\n')

            def handle_data(self, data):
                try:
                    if re.match('(?:http|https).*\.\.\.', data):
                        self.data.append(self.urls[-1])
                    else:
                        self.data.append(data)
                except IndexError:
                    pass

        parser = DescriptionParser()
        parser.feed(description)
        return ''.join(parser.data)

    def category(self):
        return re.search(r'"genre" content="(.*)"', self.html).group(1)

    def license(self):
        return re.search(r'Standard YouTube License|Creative Commons - Attribution',
                         self.html).group()

    def keywords(self):
        keywords = self.info.get('keywords')
        if keywords is not None:
            return keywords.replace(',', ', ')

    def statistics(self):
        likes = re.search(r'like this video along with (.*) other', self.html)
        dislikes = re.search(r'dislike this video along with (.*) other', self.html)
        rating = '{:.4}'.format(self.info.get('avg_rating'))
        views = self.info.get('view_count')

        if likes and dislikes:
            likes = likes.group(1).replace(',', '')
            dislikes = dislikes.group(1).replace(',', '')

        if 'allow_ratings' not in self.info:
            likes, dislikes = None, None

        return dict(likes=likes, dislikes=dislikes, rating=rating, views=views)

    def channel(self):
        author = self.info.get('author')
        identifier = self.info.get('ucid')
        subscribers = re.search(r'yt-subscriber-count" title="(.*)" aria-label', self.html)
        url = 'https://www.youtube.com/channel/{0}'.format(identifier)

        if subscribers:
            subscribers = subscribers.group(1)

        return dict(title=author, subscribers=subscribers, id=identifier, url=url)

    def player(self):
        sts = re.search(r'"sts":(\d+)', self.html).group(1)
        url = re.search(r'"js":"\\/(.*base\.js)"', self.html).group(1).replace('\\', '')
        url = 'https://www.youtube.com/{0}'.format(url)

        return dict(sts=sts, url=url)

    def streams(self, player):
        streams = dict(adaptive=None, multiplexed=None)
        cipher = ciphers.get(player)

        if 'adaptive_fmts' in self.info:
            adaptive = self.info['adaptive_fmts'].split(',')
            adaptive = [dict(parse.parse_qsl(stream)) for stream in adaptive]
            adaptive = {stream.pop('itag'): stream for stream in adaptive}

            audio = {}
            video = {}

            for itag, stream in adaptive.items():
                # Change 'type=...; codecs=...' to {'type': ..., 'codecs': ...}
                fmt = stream.pop('type').split('; codecs=')
                stream['type'], stream['codecs'] = fmt[0], fmt[1].replace('\"', '')

                # Disable the rate limit.
                if 'ratebypass=yes' not in stream['url']:
                    stream['url'] += '&ratebypass=yes'

                # Decipher the signature.
                if 's' in stream:
                    signature = ciphers.decipher(stream.pop('s'), cipher)
                    stream['url'] += '&signature={0}'.format(signature)

                if 'quality_label' in stream:
                    video.update({itag: dict(
                        quality=stream.pop('quality_label'),
                        bitrate=stream.pop('bitrate'),
                        fps=stream.pop('fps'),
                        type=stream.pop('type'),
                        codecs=stream.pop('codecs'),
                        size=stream.pop('clen'),
                        url=stream.pop('url'))
                    })

                else:
                    audio.update({itag: dict(
                        bitrate=stream.pop('bitrate'),
                        type=stream.pop('type'),
                        codecs=stream.pop('codecs'),
                        size=stream.pop('clen'),
                        url=stream.pop('url'))
                    })

            streams['adaptive'] = dict(audio=audio, video=video)

        if 'url_encoded_fmt_stream_map' in self.info:
            multiplexed = self.info['url_encoded_fmt_stream_map'].split(',')
            multiplexed = [dict(parse.parse_qsl(stream)) for stream in multiplexed]
            multiplexed = {stream.pop('itag'): stream for stream in multiplexed}

            streams['multiplexed'] = {}

            for itag, stream in multiplexed.items():
                # Change 'type=...; codecs=...' to {'type': ..., 'codecs': ...}
                fmt = stream.pop('type').split('; codecs=')
                stream['type'], stream['codecs'] = fmt[0], fmt[1].replace('\"', '')

                # Disable the rate limit.
                if 'ratebypass=yes' not in stream['url']:
                    stream['url'] += '&ratebypass=yes'

                # Decipher the signature.
                if 's' in stream:
                    signature = ciphers.decipher(stream.pop('s'), cipher)
                    stream['url'] += '&signature={0}'.format(signature)

                streams['multiplexed'].update({itag: dict(
                    quality=stream.pop('quality'),
                    type=stream.pop('type'),
                    codecs=stream.pop('codecs'),
                    url=stream.pop('url'))
                })

        return streams

    def captions(self):
        player_response = json.loads(self.info['player_response'])
        if 'captions' in player_response:
            tracks = player_response['captions'].get('playerCaptionsTracklistRenderer', {})

            if 'captionTracks' in tracks:
                tracks = tracks['captionTracks']
                captions = {}

                for track in tracks:
                    captions.update({track['name']['simpleText']: dict(
                        languageCode=track['languageCode'], url=track['baseUrl'])
                    })

                return captions

    def thumbnails(self):
        return {
            'default': 'https://i.ytimg.com/vi/{0}/default.jpg'.format(self.id),
            'medium': 'https://i.ytimg.com/vi/{0}/mqdefault.jpg'.format(self.id),
            'high': 'https://i.ytimg.com/vi/{0}/hqdefault.jpg'.format(self.id),
            'standard': 'https://i.ytimg.com/vi/{0}/sddefault.jpg'.format(self.id),
            'maxres': 'https://i.ytimg.com/vi/{0}/maxresdefault.jpg'.format(self.id),
        }
