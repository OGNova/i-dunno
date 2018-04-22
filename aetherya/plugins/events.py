import json
import humanize

from disco.bot import Plugin
from disco.bot.command import CommandEvent
from disco.util.snowflake import to_datetime

from datetime import datetime
from os import listdir

DATA_DIR = 'data/guilds/settings/{}.json'
DEFAULT_CONFIG = 'data/default_config.json'

TAGS_DIR = 'data/guilds/tags/{}.json'
DEFAULT_TAGS = 'data/default_tags.json'

POINTS_DIR = 'data/guilds/points/{}.json'
DEFAULT_POINTS = 'data/default_points.json'

class EventHandler(Plugin):
  @Plugin.listen('MessageCreate')
  def message_parser(self, event):
    with open(DATA_DIR.format(event.message.guild.id), 'r') as file:
      data = json.load(file)
    if event.message.author.bot:
      return

    if event.message.content.startswith(data['prefix']):
      commands = self.bot.get_commands_for_message(
          False,
          {},
          data['prefix'],
          event.message
      )

      if len(commands):
          print("[LOG] [CMD] [{}] {}#{} ({}) ran command {}".format(event.message.timestamp, event.message.author.username, event.message.author.discriminator, event.message.author.id, commands[0][0].name))
          commands[0][0].plugin.execute(CommandEvent(commands[0][0], event.message, commands[0][1]))

  @Plugin.listen('GuildCreate')
  def on_create(self, event):
    file = str(event.guild.id) + '.json'

    if not file in listdir(DATA_DIR[:-7]):

      with open(DEFAULT_CONFIG, 'r') as settings_file:
        settings_data = json.load(settings_file)

        with open(DATA_DIR.format(event.guild.id), 'w') as settings_config:
          settings_config.write(json.dumps(settings_data, indent=2))

    if not file in listdir(TAGS_DIR[:-7]):
      with open(DEFAULT_TAGS, 'r') as tags_file:
        tags_data = json.load(tags_file)

        with open(TAGS_DIR.format(event.guild.id), 'w') as tags_config:
          tags_config.write(json.dumps(tags_data, indent=2))


  @Plugin.listen('GuildMemberAdd')
  def on_member_join(self, event):
    now = datetime.now().strftime("%H:%M:%S")
    
    with open(DATA_DIR.format(event.guild.id), 'r') as file:
      config = json.load(file)
    
    created = humanize.naturaltime(datetime.utcnow() - to_datetime(event.user.id))
    self.client.api.channels_messages_create(config['memberLog'], content='`[{}]` :inbox_tray: {}#{} (`{}`) joined ({})'.format(
      now, event.user.username, event.user.discriminator, event.user.id, created
    ))

    file = str(event.user.id) + '.json'

    if not file in listdir(POINTS_DIR[:-7]):
      with open(DEFAULT_POINTS, 'r') as points_file:
        points_data = json.load(points_file)

        with open(POINTS_DIR, 'w') as points_config:
          points_config.write(json.dumps(points_data))