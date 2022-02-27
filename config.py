# -*- coding: utf-8 -*-
from pywidevine.cdm import deviceconfig

CDM_DEVICE = deviceconfig.some_l3_device

UA = 'okhttp/2.5.0'

KEY_FILE = 'client_key.json'
SUBS_FILE = 'subs'

# use this for device registration which will generate a client key that lasts
# for 6 months
INIT_AES_SECRET = b'A3s68aORSgHs$71P'
CLIENT_SECRET = 'apalyaSonyTV'

REGISTER_DEVICE_URL = 'https://api.sunnxt.com/user/v7/registerDevice'
CODE_URL = 'https://api.sunnxt.com/user/v4/device/code'
LINK_URL = 'https://api.sunnxt.com/user/v4/device/validate'
MEDIA_URL = 'https://api.sunnxt.com/content/v3/media/{}/'
LICENSE_URL = 'https://api.sunnxt.com/licenseproxy/v3/modularLicense/'

PRESETS = [1080, 720]
