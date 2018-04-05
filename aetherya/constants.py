import re

# Aetherya Control Settings
AETHERYA_UID = 379402095914123264
ENV = 'production'
OWNER_ID = '166304313004523520'

# Channels
AETHEYRA_CONTROL_GUILD = 335951728560046080
AETHERYA_CONTROL_CHANNEL = 352108856542887936

# Emojis
STATUS_EMOJI = {
    Status.ONLINE: ':status_online:351889710056210432',
    Status.IDLE: ':status_away:351889707681972234',
    Status.DND: ':status_dnd:351889706285400075',
    Status.OFFLINE: ':status_offline:351889709078937601',
    GameType.STREAMING: ':status_streaming:351889710253080587',
}

# Misc.
EMOJI_RE = re.compile(r'<:(.+):([0-9]+)>')
CDN_URL = 'https://twemoji.maxcdn.com/2/72x72/{}.png'