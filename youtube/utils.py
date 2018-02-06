import concurrent.futures
import json
import re
from urllib import request, parse


def load(identifiers, video=False, playlist=False, max_workers=None):
    """Load data from YouTube.

    Args:
        identifiers (list): Unique identifiers for each YouTube video/playlist.
        video (bool): True if the video.
        playlist (bool): True if the playlist.
        max_workers (int): The maximum number of threads that can be used to execute the given
            calls.

    Note:
        If `max_workers` is None, it will default to the number of processors on the machine,
        multiplied by 5.

    """
    if video and playlist or not video and not playlist:
        raise ValueError('Set video or playlist to True, depending on the type of data.')

    host = 'https://www.youtube.com'
    data = {}
    urls = []

    if video:
        for identifier in identifiers:
            html = '{0}/watch?v={1}&hl=en'.format(host, identifier)
            info = '{0}/get_video_info?video_id={1}&hl=en&eurl={0}'.format(host, identifier)
            data.update({identifier: dict(html=html, info=info)})
            urls.extend([info, html])

    if playlist:
        for identifier in identifiers:
            info = '{0}/list_ajax?style=json&action_get_list=1&list={1}'.format(host, identifier)
            data.update({identifier: info})
            urls.append(info)

    def urlopen(url):
        with request.urlopen(url) as response:
            return response.read()

    # See details at:
    # https://docs.python.org/3/library/concurrent.futures.html#concurrent.futures.ThreadPoolExecutor
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(urlopen, url): url for url in urls}
        for future in concurrent.futures.as_completed(futures):
            url = futures[future]
            try:
                result = future.result().decode('utf-8')
                for identifier, urls in data.items():
                    if video:
                        if url == urls['info']:
                            data[identifier]['info'] = dict(parse.parse_qsl(result))
                            break
                        elif url == urls['html']:
                            data[identifier]['html'] = result
                            break
                    if playlist:
                        data[identifier] = json.loads(result)
            except Exception as exception:
                print('{0!r} generated an exception: {1!s}'.format(url, exception))
    return data


def get_video_id(url):
    return re.search(r'(?<=[?&]v=)[\w-]+|(?<=be/)[\w-]+|(?<=embed/)[\w-]+', url).group()
