#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import uuid

import click
import httpx
from loguru import logger
from rich import print

import config
from sun_nxt import SunNXT


@click.command()
def run():
    client = httpx.Client()
    client.headers.update(
        {
            'user-agent': config.UA,
            'X-myplex-platform': 'AndroidTV',
            'ContentLanguage': 'telugu',
            'Accept-Language': 'en'
        }
    )

    reg_data = {
        'serialNo': str(uuid.uuid4()),
        'os': 'AndroidSony',
        'osVersion': '9',
        'make': 'NVIDIA',
        'model': 'SHIELD Android TV',
        'resolution': '3840x2160',
        'profile': 'work',
        'deviceType': 'Android',
        'clientSecret': config.CLIENT_SECRET
    }
    form_data = {
        'payload': SunNXT.encrypt(reg_data),
        'version': 1
    }
    resp = client.post(config.REGISTER_DEVICE_URL, data=form_data)

    data = SunNXT.decrypt(resp.json()['response'], secret_key=config.INIT_AES_SECRET)

    client_key = data['clientKey']
    with open(config.KEY_FILE, 'w') as f:
        f.write(
            json.dumps(
                {
                    'client_key': client_key,
                    # this device_id is important as it is used to build the aes
                    # secret key used to decrypt the manifest request
                    'device_id': data['deviceId']
                }
            )
        )

    logger.info(f'Successfully saved client key to: {config.KEY_FILE}')
    logger.info('Now doing code pair...')

    client.headers['clientKey'] = client_key

    resp = client.get(config.CODE_URL)

    data = resp.json()['results']

    input(
        f'Go to https://www.{data["confirmation_url"]} and enter: {data["auth_code"]}'
    )

    resp = client.post(config.LINK_URL, data={'device_code': data['device_code']})
    print(resp.json())


if __name__ == '__main__':
    run()

