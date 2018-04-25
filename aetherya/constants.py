import re

# Aetherya Control Settings
AETHEYRA_CONTROL_GUILD = 335951728560046080
AETHERYA_CONTROL_CHANNEL = 436720557678002176
AETHERYA_UID = 379402095914123264
ENV = 'production'
OWNER_ID = '166304313004523520'

# Emojis
COG_EMOTE_ID = 430175162378223628
COG_EMOTE = '<:cog:{}>'.format(COG_EMOTE_ID)

# Misc.
EMOJI_RE = re.compile(r'<:(.+):([0-9]+)>')
CDN_URL = 'https://twemoji.maxcdn.com/2/72x72/{}.png'
PY_CODE_BLOCK = u'```py\n{}\n```'
CODE_BLOCK = u'```\n{}\n```'