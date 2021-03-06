import gevent
import requests
import json

from disco.bot import Plugin
from gevent.pool import Pool
from PIL import Image
from six import BytesIO
from pprint import pprint
from os import listdir

from aetherya.constants import (
  CDN_URL, EMOJI_RE, CODE_BLOCK, COG_EMOTE
)

DATA_DIR = 'data/guilds/{}/settings/settings.json'

TAGS_DIR = 'data/guilds/{}/tags/tags.json'

class TutorialPlugin(Plugin):
  def filter_roles(self, roles):
    index = 0
    highest = 0

    response = ''

    for role in roles:
      if roles[role].position > highest:
        highest = roles[role].position

    while index != highest:
      for role in roles:
        if roles[role].position == index:
          response = str(roles[role].id + ' - ' + roles[role].name + '\n' + response)
          index += 1

    return response

  def get_emoji_url(self, emoji):
    return CDN_URL.format('-'.join(
      char.encode('unicode_escape').decode('utf-8')[2:].lstrip('0')
      for char in emoji))

  @Plugin.command('cat', global_=True)
  def cat(self, event):
    for _ in range(3):
      try:
        r = requests.get('https://aws.random.cat/meow')
        r.raise_for_status()
      except:
        continue
    
      url = r.json()['file']
      if not url.endswith('.gif'):
        break
    else:
      return event.msg.reply('404 cat not found :(')

    r = requests.get(url)
    r.raise_for_status()
    event.msg.reply('', attachments=[('cat.jpg', r.content)])

  @Plugin.command('jumbo', '<emojis:str...>')
  def jumbo(self, event, emojis):
    urls = []

    for emoji in emojis.split(' ')[:5]:
      if EMOJI_RE.match(emoji):
        _, eid = EMOJI_RE.findall(emoji)[0]
        urls.append('https://discordapp.com/api/emojis/{}.png'.format(eid))
      else:
        urls.append(self.get_emoji_url(emoji))

    width, height, images = 0, 0, []

    for r in Pool(6).imap(requests.get, urls):
      try:
        r.raise_for_status()
      except requests.HTTPError:
        return

      img = Image.open(BytesIO(r.content))
      height = img.height if img.height > height else height
      width += img.width + 10
      images.append(img)
      
    image = Image.new('RGBA', (width, height))
    width_offset = 0
    for img in images:
      image.paste(img, (width_offset, 0))
      width_offset += img.width + 10

    combined = BytesIO()
    image.save(combined, 'png', quality=55)
    combined.seek(0)
    return event.msg.reply('', attachments=[('emoji.png', combined)])

  @Plugin.command('ping')
  def command_ping(self, event):
      event.msg.reply('Pong!')

  @Plugin.command('set', '[action:str] [key:str] [value:str...]')
  @Plugin.command('settings', '[action:str] [key:str] [value:str...]')
  def settings_command(self, event, action=None, key=None, value=None):
    with open(DATA_DIR.format(event.msg.guild.id), 'r') as file:
      data = json.load(file)

    if action:
      if action == 'edit':
        data['{}'.format(
          key
        )] = '{}'.format(
          value
        )
        with open(DATA_DIR.format(event.msg.guild.id), 'w') as file:
          file.write(json.dumps(data, indent=2))
        event.msg.reply('The key `{}` has been successfully edited to `{}`.'.format(key, value))
      else:
        event.msg.reply('\n'.join('{}'.format(data)))
    else:
      event.msg.reply('\n'.join('{}'.format(data)))


  @Plugin.command('echo', '<content:str...>')
  def echo_command(self, event, content):
    event.msg.reply(content)

  @Plugin.command('tag', '<name:str> [value:str...]')
  def on_tag_command(self, event, name, value=None):
    with open(TAGS_DIR.format(event.msg.guild.id), 'r') as file:
      data = json.load(file)

    if value:
      data['{}'.format(
        name
      )] = '{}'.format(
        value
      )

      with open(tags_dir.format(event.msg.guild.id), 'w') as file:
        file.write(json.dumps(data, indent=2))

      event.msg.reply(':notepad_spiral: Created tag `{}`'.format(name))

    else:
      event.msg.reply(data['{}'.format(name)])

  @Plugin.command('roles')
  def roles_command(self, event):
    buff = ''
    for role in event.guild.roles.values():
      role = ('{} - {}\n'.format(role.id, role.name))
      if len(role) + len(buff) > 1990:
        event.msg.reply(CODE_BLOCK.format(buff))
        buff = ''
      buff += role
    return event.msg.reply(CODE_BLOCK.format(buff))

    # TODO: Make this work.
    # roles = event.guild.roles.values()
    # self.filter_roles(roles)

  @Plugin.command('perms', '[user:user|snowflake]')
  def perm_command(self, event, user=None):
    data_dir = 'data/guilds/settings/{}.json'
    if user:
      if user.id == 166304313004523520:
        event.msg.reply('▰▰▰▰')
      else:
        with open(data_dir.format(event.msg.guild.id), 'r') as file:
          data = json.load(file)

        if user.id in data['permissions']['admins']['ids']:
          event.msg.reply('▰▰▰▱')
        elif user.id in data['permissions']['moderators']['ids']:
          event.msg.reply('▰▰▱▱')
        else:
          event.msg.reply('▰▱▱▱')

    else:
      if event.msg.author.id == 166304313004523520:
        event.msg.reply('▰▰▰▰')
      else:
        with open(data_dir.format(event.msg.guild.id), 'r') as file:
          data = json.load(file)

        if event.msg.author.id in data['permissions']['admins']['ids']:
          event.msg.reply('▰▰▰▱')
        elif event.msg.author.id in data['permissions']['moderators']['ids']:
          event.msg.reply('▰▰▱▱')
        else:
          event.msg.reply('▰▱▱▱')

  @Plugin.command('emojis')
  def emojis_command(self, event):
    # event.msg.reply(CODE_BLOCK.format(event.msg.guild.emojis))

    for emoji in event.msg.guild.emojis:
      print(emoji)

    # print(event.msg.guild.emojis)

  @Plugin.command('shutdown')
  def shutdown_command(self, event):
    event.msg.reply('{} Shutting down.'.format(COG_EMOTE))
    self.client.gw.ws_event.set()

  @Plugin.command('restart')
  def restart_command(self, event):
    event.msg.reply('{} Restarting.'.format(COG_EMOTE))
    self.client.gw.ws.close(status=4009)