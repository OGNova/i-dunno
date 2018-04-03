import pprint

from disco.bot import Plugin

from disco.types.message import MessageEmbed
from disco.types.guild import Guild

from datetime import datetime

from aetherya.constants import (
  AETHERYA_CONTROL_CHANNEL, AETHERYA_UID, ENV, OWNER_ID
)

PY_CODE_BLOCK = u'```py\n{}\n```'
CODE_BLOCK = u'```\n{}\n```'

class CorePlugin(Plugin):
  @Plugin.listen('MessageCreate')
  def on_message_create(self, event):
    if event.message.author.bot:
      return
    commands = self.bot.get_commands_for_message(
        False,
        {},
        "!",
        event.message
    )

    if len(commands):
        print("[LOG] [CMD] [{}] {} ({}) ran command {}".format(event.message.timestamp, event.message.author.username, event.message.author.id, commands[0][0].name))

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
    event.msg.reply(CODE_BLOCK.format(perms))