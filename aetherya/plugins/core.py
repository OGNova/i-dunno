import pprint
import json
import gevent

from disco.bot import Plugin
from disco.bot.command import CommandEvent

from disco.types.message import MessageEmbed
import disco.types.permissions as permissions

from datetime import datetime

from aetherya.constants import (
  AETHERYA_CONTROL_CHANNEL, AETHERYA_UID, ENV, OWNER_ID
)

PY_CODE_BLOCK = u'```py\n{}\n```'
CODE_BLOCK = u'```\n{}\n```'
PERMS_BLOCK = u'```\n{}\n```'

BASE_DIR = 'data/guilds/{}.json'
DEFAULT_CONFIG = 'data/default_config.json'

class CorePlugin(Plugin):
  def wait_for_plugin_changes(self):
    import gevent_inotifiyx as inotify
    import socket

    fd = inotify.init()
    inotify.add_watch(fd, 'aetherya/plugins/', inotify.IN_MODIFY)
    while True:
      events = inotify.get_events(fd)
      for event in events:
        if event.name.startswith('core.py'):
          continue
        
        plugin_name = '{}Plugin'.format(event.name.split('.', 1)[0].title())
        plugin = next((v for k, v in self.bot.plugins.items() if k.lower() == plugin_name.lower()), None)
        if plugin:
          self.log.info('Detected change in %s, reloading...', plugin_name)
          try:
            plugin.reload()
          except Exception:
            self.log.exception('Failed to reload: ')

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
          print("[LOG] [CMD] [{}] {} ({}) ran command {}".format(event.message.timestamp, event.message.author.username, event.message.author.id, commands[0][0].name))
          commands[0][0].plugin.execute(CommandEvent(commands[0][0], event.message, commands[0][1]))

  @Plugin.listen('Ready')
  def on_ready(self, event):
    embed = MessageEmbed()
    embed.set_footer(text='Aetherya {}'.format(
      'Production' if ENV == 'prod' else 'Testing'
    ))
    embed.timestamp = datetime.utcnow().isoformat()
    embed.color = 0x779ecb

    reconnects = self.client.gw.reconnects
    self.log.info('Started session %s', event.session_id)
    if reconnects:
      embed.title = 'Reconnected'
      embed.color = 0xffb347
    else:
      embed.title = 'Connected'
      embed.color = 0x77dd77

    embed.add_field(name='Gateway Server', value=event.trace[0], inline=False)
    embed.add_field(name='Session Server', value=event.trace[1], inline=False)

    self.client.api.channels_messages_create(AETHERYA_CONTROL_CHANNEL, embed=embed)

  @Plugin.listen('Resumed')
  def on_resume(self, event):
    embed = MessageEmbed()
    embed.set_footer(text='Aetherya {}'.format(
      'Production' if ENV == 'prod' else 'Testing'
    ))
    embed.timestamp = datetime.utcnow().isoformat()
    embed.color = 0xffb347
    embed.add_field(name='Gateway Server', value=event.trace[0], inline=False)
    embed.add_field(name='Session Server', value=event.trace[1], inline=False)
    embed.add_field(name='Replayed Events', value=str(self.client.gw.replayed_events))

    self.client.api.channels_messages_create(AETHERYA_CONTROL_CHANNEL, embed=embed)

  @Plugin.listen('GuildCreate')
  def on_create(self, event):
    with open(DEFAULT_CONFIG, 'r') as file:
      data = json.load(file)

      with open(BASE_DIR.format(event.guild.id), 'w') as config:
        config.write(json.dumps(data, indent=2))

  @Plugin.command('eval')
  def eval_command(self, event):
    if event.msg.author.id == 166304313004523520:
      ctx = {
        'bot': self.bot,
        'client': self.bot.client,
        'state': self.bot.client.state,
        'event': event,
        'msg': event.msg,
        'guild': event.msg.guild,
        'channel': event.msg.channel,
        'author': event.msg.author
      }

      src = event.codeblock
      if src.count('\n'):
        lines = filter(bool, src.split('\n'))
        if lines[-1] and 'return' not in lines[-1]:
          lines[-1] = 'return ' + lines[-1]
        lines = '\n'.join('    ' + i for i in lines)
        code = 'def f():\n{}\nx = f()'.format(lines)
        local = {}

        try:
          compile(code, '<eval>', 'exec') in ctx, local
        except Exception as e:
          event.msg.reply(PY_CODE_BLOCK.format(type(e).__name__ + ': ' + str(e)))
          return
        
        result = pprint.pformat(local['x'])
      else:
        try:
          result = str(eval(src, ctx))
        except Exception as e:
          event.msg.reply(PY_CODE_BLOCK.format(type(e).__name__ + ': ' + str(e)))
          return

      if len(result) > 1990:
        event.msg.reply('', attachments=[('result.txt', result)])
      else:
        event.msg.reply(PY_CODE_BLOCK.format(result))

    else:
      event.msg.reply('not 4 u')
  
  @Plugin.command('perms')
  def perms_command(self, event):
    perms = event.guild.get_permissions(AETHERYA_UID)
    event.msg.reply(PERMS_BLOCK.format("\n".join([k for k, v in perms.to_dict().items() if v])))