# coding: utf-8
from __future__ import unicode_literals

import hashlib
import random
import re
import time

from .common import InfoExtractor
from ..compat import compat_str
from ..utils import (
    ExtractorError,
    int_or_none,
    parse_duration,
    try_get,
    urlencode_postdata,
)


class NexxIE(InfoExtractor):
    _VALID_URL = r'''(?x)
                        (?:
                            https?://api\.nexx(?:\.cloud|cdn\.com)/v3/(?P<domain_id>\d+)/videos/byid/|
                            nexx:(?:(?P<domain_id_s>\d+):)?|
                            https?://arc\.nexx\.cloud/api/video/
                        )
                        (?P<id>\d+)
                    '''
    _TESTS = [{
        # movie
        'url': 'https://api.nexx.cloud/v3/748/videos/byid/128907',
        'md5': '828cea195be04e66057b846288295ba1',
        'info_dict': {
            'id': '128907',
            'ext': 'mp4',
            'title': 'Stiftung Warentest',
            'alt_title': 'Wie ein Test abläuft',
            'description': 'md5:d1ddb1ef63de721132abd38639cc2fd2',
            'release_year': 2013,
            'creator': 'SPIEGEL TV',
            'thumbnail': r're:^https?://.*\.jpg$',
            'duration': 2509,
            'timestamp': 1384264416,
            'upload_date': '20131112',
        },
    }, {
        # episode
        'url': 'https://api.nexx.cloud/v3/741/videos/byid/247858',
        'info_dict': {
            'id': '247858',
            'ext': 'mp4',
            'title': 'Return of the Golden Child (OV)',
            'description': 'md5:5d969537509a92b733de21bae249dc63',
            'release_year': 2017,
            'thumbnail': r're:^https?://.*\.jpg$',
            'duration': 1397,
            'timestamp': 1495033267,
            'upload_date': '20170517',
            'episode_number': 2,
            'season_number': 2,
        },
        'params': {
            'skip_download': True,
        },
    }, {
        # does not work via arc
        'url': 'nexx:741:1269984',
        'md5': 'c714b5b238b2958dc8d5642addba6886',
        'info_dict': {
            'id': '1269984',
            'ext': 'mp4',
            'title': '1 TAG ohne KLO... wortwörtlich! 😑',
            'alt_title': '1 TAG ohne KLO... wortwörtlich! 😑',
            'description': 'md5:4604539793c49eda9443ab5c5b1d612f',
            'thumbnail': r're:^https?://.*\.jpg$',
            'duration': 607,
            'timestamp': 1518614955,
            'upload_date': '20180214',
        },
    }, {
        'url': 'https://api.nexxcdn.com/v3/748/videos/byid/128907',
        'only_matching': True,
    }, {
        'url': 'nexx:748:128907',
        'only_matching': True,
    }, {
        'url': 'nexx:128907',
        'only_matching': True,
    }, {
        'url': 'https://arc.nexx.cloud/api/video/128907.json',
        'only_matching': True,
    }]

    @staticmethod
    def _extract_domain_id(webpage):
        mobj = re.search(
            r'<script\b[^>]+\bsrc=["\'](?:https?:)?//require\.nexx(?:\.cloud|cdn\.com)/(?P<id>\d+)',
            webpage)
        return mobj.group('id') if mobj else None

    @staticmethod
    def _extract_urls(webpage):
        # Reference:
        # 1. https://nx-s.akamaized.net/files/201510/44.pdf

        entries = []

        # JavaScript Integration
        domain_id = NexxIE._extract_domain_id(webpage)
        if domain_id:
            for video_id in re.findall(
                    r'(?is)onPLAYReady.+?_play\.init\s*\(.+?\s*,\s*["\']?(\d+)',
                    webpage):
                entries.append(
                    'https://api.nexx.cloud/v3/%s/videos/byid/%s'
                    % (domain_id, video_id))

        # TODO: support more embed formats

        return entries

    @staticmethod
    def _extract_url(webpage):
        return NexxIE._extract_urls(webpage)[0]

    def _handle_error(self, response):
        status = int_or_none(try_get(
            response, lambda x: x['metadata']['status']) or 200)
        if 200 <= status < 300:
            return
        raise ExtractorError(
            '%s said: %s' % (self.IE_NAME, response['metadata']['errorhint']),
            expected=True)

    def _call_api(self, domain_id, path, video_id, data=None, headers={}):
        headers['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8'
        result = self._download_json(
            'https://api.nexx.cloud/v3/%s/%s' % (domain_id, path), video_id,
            'Downloading %s JSON' % path, data=urlencode_postdata(data),
            headers=headers)
        self._handle_error(result)
        return result['result']

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        domain_id = mobj.group('domain_id') or mobj.group('domain_id_s')
        video_id = mobj.group('id')

        video = None

        response = self._download_json(
            'https://arc.nexx.cloud/api/video/%s.json' % video_id,
            video_id, fatal=False)
        if response and isinstance(response, dict):
            result = response.get('result')
            if result and isinstance(result, dict):
                video = result

        # not all videos work via arc, e.g. nexx:741:1269984
        if not video:
            # Reverse engineered from JS code (see getDeviceID function)
            device_id = '%d:%d:%d%d' % (
                random.randint(1, 4), int(time.time()),
                random.randint(1e4, 99999), random.randint(1, 9))

            result = self._call_api(domain_id, 'session/init', video_id, data={
                'nxp_devh': device_id,
                'nxp_userh': '',
                'precid': '0',
                'playlicense': '0',
                'screenx': '1920',
                'screeny': '1080',
                'playerversion': '6.0.00',
                'gateway': 'html5',
                'adGateway': '',
                'explicitlanguage': 'en-US',
                'addTextTemplates': '1',
                'addDomainData': '1',
                'addAdModel': '1',
            }, headers={
                'X-Request-Enable-Auth-Fallback': '1',
            })

            cid = result['general']['cid']

            # As described in [1] X-Request-Token generation algorithm is
            # as follows:
            #   md5( operation + domain_id + domain_secret )
            # where domain_secret is a static value that will be given by nexx.tv
            # as per [1]. Here is how this "secret" is generated (reversed
            # from _play.api.init function, search for clienttoken). So it's
            # actually not static and not that much of a secret.
            # 1. https://nexxtvstorage.blob.core.windows.net/files/201610/27.pdf
            secret = result['device']['clienttoken'][int(device_id[0]):]
            secret = secret[0:len(secret) - int(device_id[-1])]

            op = 'byid'

            # Reversed from JS code for _play.api.call function (search for
            # X-Request-Token)
            request_token = hashlib.md5(
                ''.join((op, domain_id, secret)).encode('utf-8')).hexdigest()

            video = self._call_api(
                domain_id, 'videos/%s/%s' % (op, video_id), video_id, data={
                    'additionalfields': 'language,channel,actors,studio,licenseby,slug,subtitle,teaser,description',
                    'addInteractionOptions': '1',
                    'addStatusDetails': '1',
                    'addStreamDetails': '1',
                    'addCaptions': '1',
                    'addScenes': '1',
                    'addHotSpots': '1',
                    'addBumpers': '1',
                    'captionFormat': 'data',
                }, headers={
                    'X-Request-CID': cid,
                    'X-Request-Token': request_token,
                })

        general = video['general']
        title = general['title']

        stream_data = video['streamdata']
        language = general.get('language_raw') or ''

        # TODO: reverse more cdns

        cdn = stream_data['cdnType']
        assert cdn == 'azure'

        azure_locator = stream_data['azureLocator']

        AZURE_URL = 'http://nx%s%02d.akamaized.net/'

        def get_cdn_shield_base(shield_type='', prefix='-p'):
            for secure in ('', 's'):
                cdn_shield = stream_data.get('cdnShield%sHTTP%s' % (shield_type, secure.upper()))
                if cdn_shield:
                    return 'http%s://%s' % (secure, cdn_shield)
            else:
                return AZURE_URL % (prefix, int(stream_data['azureAccount'].replace('nexxplayplus', '')))

        azure_stream_base = get_cdn_shield_base()
        is_ml = ',' in language
        azure_manifest_url = '%s%s/%s_src%s.ism/Manifest' % (
            azure_stream_base, azure_locator, video_id, ('_manifest' if is_ml else '')) + '%s'

        protection_token = try_get(
            video, lambda x: x['protectiondata']['token'], compat_str)
        if protection_token:
            azure_manifest_url += '?hdnts=%s' % protection_token

        formats = self._extract_m3u8_formats(
            azure_manifest_url % '(format=m3u8-aapl)',
            video_id, 'mp4', 'm3u8_native',
            m3u8_id='%s-hls' % cdn, fatal=False)
        formats.extend(self._extract_mpd_formats(
            azure_manifest_url % '(format=mpd-time-csf)',
            video_id, mpd_id='%s-dash' % cdn, fatal=False))
        formats.extend(self._extract_ism_formats(
            azure_manifest_url % '', video_id, ism_id='%s-mss' % cdn, fatal=False))

        azure_progressive_base = get_cdn_shield_base('Prog', '-d')
        azure_file_distribution = stream_data.get('azureFileDistribution')
        if azure_file_distribution:
            fds = azure_file_distribution.split(',')
            if fds:
                for fd in fds:
                    ss = fd.split(':')
                    if len(ss) == 2:
                        tbr = int_or_none(ss[0])
                        if tbr:
                            f = {
                                'url': '%s%s/%s_src_%s_%d.mp4' % (
                                    azure_progressive_base, azure_locator, video_id, ss[1], tbr),
                                'format_id': '%s-http-%d' % (cdn, tbr),
                                'tbr': tbr,
                            }
                            width_height = ss[1].split('x')
                            if len(width_height) == 2:
                                f.update({
                                    'width': int_or_none(width_height[0]),
                                    'height': int_or_none(width_height[1]),
                                })
                            formats.append(f)

        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'alt_title': general.get('subtitle'),
            'description': general.get('description'),
            'release_year': int_or_none(general.get('year')),
            'creator': general.get('studio') or general.get('studio_adref'),
            'thumbnail': try_get(
                video, lambda x: x['imagedata']['thumb'], compat_str),
            'duration': parse_duration(general.get('runtime')),
            'timestamp': int_or_none(general.get('uploaded')),
            'episode_number': int_or_none(try_get(
                video, lambda x: x['episodedata']['episode'])),
            'season_number': int_or_none(try_get(
                video, lambda x: x['episodedata']['season'])),
            'formats': formats,
        }


class NexxEmbedIE(InfoExtractor):
    _VALID_URL = r'https?://embed\.nexx(?:\.cloud|cdn\.com)/\d+/(?P<id>[^/?#&]+)'
    _TEST = {
        'url': 'http://embed.nexx.cloud/748/KC1614647Z27Y7T?autoplay=1',
        'md5': '16746bfc28c42049492385c989b26c4a',
        'info_dict': {
            'id': '161464',
            'ext': 'mp4',
            'title': 'Nervenkitzel Achterbahn',
            'alt_title': 'Karussellbauer in Deutschland',
            'description': 'md5:ffe7b1cc59a01f585e0569949aef73cc',
            'release_year': 2005,
            'creator': 'SPIEGEL TV',
            'thumbnail': r're:^https?://.*\.jpg$',
            'duration': 2761,
            'timestamp': 1394021479,
            'upload_date': '20140305',
        },
        'params': {
            'format': 'bestvideo',
            'skip_download': True,
        },
    }

    @staticmethod
    def _extract_urls(webpage):
        # Reference:
        # 1. https://nx-s.akamaized.net/files/201510/44.pdf

        # iFrame Embed Integration
        return [mobj.group('url') for mobj in re.finditer(
            r'<iframe[^>]+\bsrc=(["\'])(?P<url>(?:https?:)?//embed\.nexx(?:\.cloud|cdn\.com)/\d+/(?:(?!\1).)+)\1',
            webpage)]

    def _real_extract(self, url):
        embed_id = self._match_id(url)

        webpage = self._download_webpage(url, embed_id)

        return self.url_result(NexxIE._extract_url(webpage), ie=NexxIE.ie_key())
