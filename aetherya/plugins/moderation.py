import json
import psycopg2

from disco.bot import Plugin
from disco.types.guild import GuildMember

from aetherya.util.input import parse_duration

DATA_DIR = 'data/guilds/{}/settings/settings.json'

def permission_check(self, guild_id, author_id):
  with open(DATA_DIR.format(event.msg.guild.id), 'r') as file:
    config = json.load(file)

  if str(event.msg.author.id) not in config['permission']['admin']['ids']:
    return 

class ModerationPlugin(Plugin):
  @Plugin.command('ban', '<user:user|snowflake> [reason:str...]')
  @Plugin.command('forceban', '<user:user|snowflake> [reason:str...]')
  def ban(self, event, user, reason=None):
    with open(DATA_DIR.format(event.msg.guild.id), 'r') as file:
      config = json.load(file)
    
    if str(event.msg.author.id) not in config['permissions']['admins']['ids']:
      return

    else:

      member = None

      if isinstance(user, GuildMember):
        user.ban(reason=reason)
      else:
        member = event.guild.get_member(user)
        if member:
          member.ban(reason=reason)
        else:
          return event.msg.reply('invalid user')

      if reason:
        event.msg.reply(':ok_hand: banned {} `{}`'.format(member.user if member else user, reason))
        if config['logging'] == True:
          self.client.api.channels_messages_create(config['modLogChannel'], content=':rotating_light: {} (`{}`) was banned by **{}#{}**: `{}`'.format(
            member.user if member else user, member.user.id if member else user.id, event.msg.author.name, event.msg.author.discriminator, reason
          ))
      else:
        event.msg.reply(':ok_hand: banned {}'.format(member.user if member else user))
        if config['logging'] == True:
          self.client.api.channels_messages_create(config['modLogChannel'], content=':rotating_light: {} (`{}`) was banned by **{}#{}**: `{}`'.format(
            member.user if member else user, member.user.id if member else user.id, event.msg.author.name, event.msg.author.discriminator, 'No reason provided.'
          ))

  @Plugin.command('kick', '<user:user|snowflake> [reason:str...]')
  def kick(self, event, user, reason=None):
    with open(DATA_DIR.format(event.msg.guild.id), 'r') as file:
      config = json.load(file)
    
    if str(event.msg.author.id) not in config['permissions']['moderators']['ids']:
      return

    member = None

    if isinstance(user, GuildMember):
      user.kick(reason=reason)
    else:
      member = event.guild.get_member(user)
      if member:
        member.kick(reason=reason)
      else:
        return event.msg.reply('invalid user')

    if reason:
      event.msg.reply(':ok_hand: kicked {} `{}`'.format(member.user if member else user, reason))
      with open(DATA_DIR.format(event.guild.id), 'r') as file:
        config = json.load(file)

      if config['logging'] == 'True':
        self.client.api.channels_messages_create(config['modLogChannel'], content=':boot: {} (`{}`) was kicked by **{}#{}**: `{}`'.format(
          member.user if member else user, member.user.id if member else user.id, event.msg.author.username, event.msg.author.discriminator, reason
        ))
    else:
      event.msg.reply(':ok_hand: kicked {}'.format(member.user if member else user))
      with open(DATA_DIR.format(event.guild.id), 'r') as file:
        config = json.load(file)

      if config['logging'] == 'True':
        self.client.api.channels_messages_create(config['modLogChannel'], content=':boot: {} (`{}`) was kicked by **{}#{}**: `{}`'.format(
          member.user if member else user, member.user.id if member else user.id, event.msg.author.username, event.msg.author.discriminator, 'No reason provided.'
        ))

  @Plugin.command('mute', '<user:user|snowflake> [reason:str...]')
  def mute_command(self, event, user, reason=None):
    with open(DATA_DIR.format(event.msg.guild.id), 'r') as file:
      config = json.load(file)

    if str(event.msg.author.id) not in config['permissions']['moderators']['ids']:
      return event.msg.reply(':no_entry: You don\'t have permission to run this command.')
    
    member = None

    if isinstance(user, GuildMember):
      user.add_role(config['muteRole'], reason=reason)
    else:
      member = event.guild.get_member(user)
      if member:
        member.add_role(config['muteRole'], reason=reason)
      else:
        return event.msg.reply('invalid user')
    if reason:
      event.msg.reply(':ok_hand: muted {} `{}`'.format(member.user if member else user, reason))

      with open(DATA_DIR.format(event.msg.guild.id), 'r') as file:
        config = json.load(file)
      
      if config['logging'] == 'True':
        for i in event.msg.guild.channels.values():
          if config['modLogChannel'] in i.name:
            self.client.api.channels_messages_create(i.id, content=':no_mouth: {} (`{}`) was muted by **{}#{}**: `{}`'.format(member.user if member else user, member.user.id if member else user.id, event.msg.author.username, event.msg.author.discriminator, reason
            ))
    else:
      event.msg.reply(':ok_hand: muted {}'.format(member.user if member else user))

      with open(DATA_DIR.format(event.msg.guild.id), 'r') as file:
        config = json.load(file)
      
      if config['logging'] == 'True':
        self.client.api.channels_messages_create(config['modLogChannel'], content=':no_mouth: {} (`{}`) was muted by **{}#{}**: `{}`'.format(
          member.user if member else user, member.user.id if member else user.id, event.msg.author.username, event.msg.author.discriminator, 'No reason provided.'
        ))