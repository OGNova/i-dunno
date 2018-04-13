import json
import humanize

from disco.bot import Plugin
from disco.bot.command import CommandEvent
from disco.util.snowflake import to_datetime

from datetime import datetime

BASE_DIR = 'data/guilds/{}.json'
DEFAULT_CONFIG = 'data/default_config.json'

class EventHandler(Plugin):
  @Plugin.listen('MessageCreate')
  def message_parser(self, event):
    with open(BASE_DIR.format(event.message.guild.id), 'r') as file:
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
    with open(DEFAULT_CONFIG, 'r') as file:
      data = json.load(file)

      with open(BASE_DIR.format(event.guild.id), 'w') as config:
        config.write(json.dumps(data, indent=2))


  @Plugin.listen('GuildMemberAdd')
  def on_member_join(self, event):
    with open(BASE_DIR.format(event.guild.id), 'r') as file:
      config = json.load(file)
    
    created = humanize.naturaltime(datetime.utcnow() - to_datetime(event.user.id))
    self.client.api.channels_messages_create(config['memberLog'], content='`[{}]` :inbox_tray: {}#{} (`{}`) joined ({})'.format(
      humanize.naturaltime(datetime.utcnow()), event.user.username, event.user.discriminator, event.user.id, created
    ))