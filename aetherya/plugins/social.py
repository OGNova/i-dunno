import math
import random
import json

from disco.bot import Plugin

DATA_DIR = 'data/guilds/settings/{}.json'
DEFAULT_CONFIG = 'data/default_config.json'

POINTS_DIR = 'data/guilds/points/{}.json'

# TODO: Make this shit actually work.
class SocialPlugin(Plugin):
  def giveRandomPoints(self, min, max):
    min = math.ceil(min)
    max = math.ceil(max)

    return math.floor(random.random() * (max - min)) + min

  @Plugin.listen('MessageCreate')
  def message_listener(self, event):
    with open(DATA_DIR.format(event.message.guild.id), 'r') as file:
      data = json.load(file)

    if event.message.content.startswith(data['prefix']):
      return
    
    min = int(data['minPoints'])
    max = int(data['maxPoints'])

    points = self.giveRandomPoints(min, max)
    print(points)

    with open(POINTS_DIR.format(event.message.author.id), 'w') as file:
      data = json.load(file)

      data['points'] = int(data['points']) + points

      file.write(json.dumps(data, indent=2))