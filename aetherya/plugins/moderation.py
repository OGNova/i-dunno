from disco.bot import Plugin

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
    else:
      event.msg.reply(':ok_hand: banned {}'.format(member.user if member else user))