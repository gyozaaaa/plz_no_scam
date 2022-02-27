#!/usr/bin/env python
# -*- coding: utf-8 -*-
import base64
import json
import os
import sys
import time
import urllib.parse

import httpx
import typer
from Cryptodome.Cipher import AES
from Cryptodome.Util import Padding
from loguru import logger

import config
from dashole.dashole import utils


class SunNXT(object):
    def __init__(self, media_id):
        self.media_id = media_id

        if not os.path.exists(config.KEY_FILE):
            logger.error(
                f'{config.KEY_FILE} does not exist, run device_registration.py'
            )
            sys.exit()

        with open(config.KEY_FILE, 'r') as f:
            data = json.load(f)

        self.client_key = data['client_key']
        self.aes_secret = config.INIT_AES_SECRET[-4:] + \
                          data["device_id"][-8:].encode() + \
                          config.INIT_AES_SECRET[:4]

        self.session = httpx.Client()
        self.session.headers.update(
            {
                'user-agent': config.UA,
                'clientKey': self.client_key,
                'X-myplex-platform': 'AndroidTV',
                'ContentLanguage': 'telugu',
                'Accept-Language': 'en'
            }
        )

    @staticmethod
    def encrypt(data: dict) -> str:
        cipher = AES.new(config.INIT_AES_SECRET, AES.MODE_CBC, iv=bytes([0] * 16))
        encrypted = cipher.encrypt(
            Padding.pad(json.dumps(data, separators=(',', ':')).encode(), 16)
        )
        return base64.b64encode(encrypted).decode()

    @staticmethod
    def decrypt(data: str, secret_key: bytes):
        cipher = AES.new(
            secret_key,
            AES.MODE_CBC,
            iv=bytes([0] * 16)
        )
        return json.loads(
            Padding.unpad(cipher.decrypt(base64.b64decode(data)), 16).decode()
        )

    def get_mpd_urls(self) -> tuple:
        resp = self.session.get(config.MEDIA_URL.format(self.media_id))
        data = self.decrypt(resp.json()['response'], self.aes_secret)

        subs = []
        for sub in data['results'][0]['subtitles']['values']:
            subs.append(
                {
                    'name': sub['language'],
                    'url': f"{sub['link_sub']}.vtt",
                    'lang': ''
                }
            )

        with open(config.SUBS_FILE, 'w') as f:
            f.write(json.dumps(subs))

        audio_mpd, video_mpd = None, None
        for video in data['results'][0]['videos']['values']:
            # download will give a flat file url for audio with ec3, but no 1080p
            # video
            if not audio_mpd and video['type'] == 'download' and video[
                    'profile'] == 'High':
                audio_mpd = video['link']

            if not video_mpd and video['profile'] == 'High' and video[
                    'type'] == 'streaming':
                video_mpd = video['link']

        return audio_mpd, video_mpd

    def parse_mpd(self, audio_mpd, video_mpd) -> tuple:
        audio_mpd_data = self.session.get(audio_mpd).content
        audio, _, subs, _ = utils.parse(audio_mpd, None, audio_mpd_data, presets=[])

        video_mpd_data = self.session.get(video_mpd).content
        _, video, _, pssh = utils.parse(video_mpd, None, video_mpd_data, config.PRESETS)

        return audio, video, pssh

    def run(self):
        audio_mpd, video_mpd = self.get_mpd_urls()

        audio, video, pssh = self.parse_mpd(audio_mpd, video_mpd)

        query = {
            'content_id': self.media_id,
            'licenseType': 'streaming',
            'timestamp': int(time.time()),
            'clientKey': self.client_key
        }
        wv_keys = utils.get_wv_keys(
            f'{config.LICENSE_URL}?{urllib.parse.urlencode(query)}',
            pssh,
            config.CDM_DEVICE
        )
        logger.info(wv_keys)


# ex. 117166
def main(media_id: str):
    s = SunNXT(media_id)
    s.run()


if __name__ == '__main__':
    typer.run(main)
