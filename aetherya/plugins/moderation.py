from disco.bot import Plugin

DATA_DIR = 'data/guilds/{}.json'

class ModerationPlugin(Plugin):
  @Plugin.command('ban', '<user:user|snowflake> [reason:str...]')
  @Plugin.command('forceban', '<user:user|snowflake> [reason:str...]')
  def ban(self, event, user, reason=None):
    member = None

    if isinstance(user, (int)):
      event.guild.ban(self, event, user, reason)
    else:
      member = event.guild.get_member(user)
      if member:
        event.guild.ban(self, event, member, reason)
      else:
        return event.msg.reply('invalid user')

    if reason:
      event.msg.reply(':ok_hand: banned {} (`{}`)'.format(member.user if member else user, reason))
      with open(DATA_DIR.format(event.guild.id), 'r') as file:
        config = json.load(file)

      if config['logging'] == True:
        self.client.api.channels_messages_create(config['modLogChannel'], content=':rotating_light: {} (`{}`) was banned by **{}#{}**: `{}`'.format(
          member.user if member else user, member.user.id if member else user.id, event.msg.author.name, event.msg.author.discriminator, reason
        ))
    else:
      event.msg.reply(':ok_hand: banned {}'.format(member.user if member else user))
      with open(DATA_DIR.format(event.guild.id), 'r') as file:
        config = json.load(file)

      if config['logging'] == True:
        self.client.api.channels_messages_create(config['modLogChannel'], content=':rotating_light: {} (`{}`) was banned by **{}#{}**: `{}`'.format(
          member.user if member else user, member.user.id if member else user.id, event.msg.author.name, event.msg.author.discriminator, 'No reason provided.'
        ))