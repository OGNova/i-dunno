import math
import random
import json

from disco.bot import Plugin

from os import listdir

DATA_DIR = 'data/guilds/{}/settings/settings.json'
DEFAULT_CONFIG = 'data/default_config.json'

POINTS_DIR = 'data/guilds/{}/points/{}.json'
DEFAULT_POINTS = 'data/default_points.json'

class SocialPlugin(Plugin):
  def giveRandomPoints(self, min, max):
    min = math.ceil(min)
    max = math.ceil(max)

    return math.floor(random.random() * (max - min)) + min

  @Plugin.listen('MessageCreate')
  def message_listener(self, event):
    if event.message.author.bot:
      return

    with open(DATA_DIR.format(event.message.guild.id), 'r') as file:
      data = json.load(file)

      min = int(data['minPoints'])
      max = int(data['maxPoints'])

      if event.message.content.startswith(data['prefix']):
        return

      with open(POINTS_DIR.format(event.message.guild.id, event.message.author.id), 'r') as file:
        data = json.load(file)

      points = self.giveRandomPoints(min, max)

      data['points'] = int(data['points']) + points
      with open(POINTS_DIR.format(event.message.guild.id, event.message.author.id), 'w') as file:
        file.write(json.dumps(data, indent=2))

  @Plugin.command('points', '[user:user|snowflake]')
  def points_command(self, event, user=None):
    if user:
      with open(POINTS_DIR.format(user.id), 'r') as file:
        data = json.load(file)

      event.msg.reply('User {} has {} points, and is level {}.'.format(event.msg.guild.get_member(user).user.username, data['points'], data['level']))

    else:
      with open(POINTS_DIR.format(event.msg.author.id), 'r') as file:
        data = json.load(file)

      # event.msg.reply('You currently have {} points, and are level {}.'.format(data['points'], data['level']))

      realPoints = data['points'] / 100

      multiple = 100

      print(math.floor(realPoints))

      remaining_points = 10 - math.floor(realPoints)

      prog_bar = '▰' * math.floor(realPoints)
      remaining = '▱' * remaining_points

      event.msg.reply(prog_bar + remaining)