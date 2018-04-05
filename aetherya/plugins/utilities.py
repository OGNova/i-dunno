import humanize

from datetime import datetime, timedelta

from disco.bot import Plugin
from disco.types.user import GameType, Status
from disco.types.message import MessageEmbed
from disco.util.snowflake import to_datetime

from aetherya.models.message import message

class UtilityPlugin(Plugin):
  def get_status_emoji(presence):
    if presence.game and presence.game.type == GameType.STREAMING:
        return STATUS_EMOJI[GameType.STREAMING], 'Streaming'
    elif presence.status == Status.ONLINE:
        return STATUS_EMOJI[Status.ONLINE], 'Online'
    elif presence.status == Status.IDLE:
        return STATUS_EMOJI[Status.IDLE], 'Idle',
    elif presence.status == Status.DND:
        return STATUS_EMOJI[Status.DND], 'DND'
    elif presence.status in (Status.OFFLINE, Status.INVISIBLE):
        return STATUS_EMOJI[Status.OFFLINE], 'Offline'

  @Plugin.command('info', '<user:user>')
  def info(self, event, user):
    content = []
    content.append(u'**\u276F User Information**')
    content.append(u'ID: {}'.format(user.id))
    content.append(u'Profile: <@{}>'.format(user.id))

    if user.presence:
      emoji, status = get_status_emoji(user.presence)
      content.append('Status: {} <{}>'.format(status, emoji))
      if user.presence.game and user.presence.game.name:
        if user.presence.game.type == GameType.DEFAULT:
          content.append(u'Game: {}'.format(user.presence.game.name))
        else:
          content.append(u'Stream: [{}]({})'.format(user.presence.game.name, user.presence.game.url))

      created_dt = to_datetime(user.id)
      content.append('Created: {} ago ({})'.format(
        humanize.naturaldelta(datetime.utcnow() - created_dt),
        created_dt.isoformat()
      ))

      member = event.guild.get_member(user.id) if event.guild else None
      if member:
        content.append(u'\n**\u276f Member Information**')

        if member.nick:
          content.append(u'Nickname: {}'.format(member.nick))

        content.append('Joined: {} ago ({})'.format(
          humanize.naturaldelta(datetime.utcnow() - member.joined_at),
          member.joined_at.isoformat(),
        ))

        if member.roles:
          content.append(u'Roles: {}'.format(
            ', '.join((member.guild.roles.get(r).name for r in member.roles))
          ))

        newest_msg = Message.select(Message.timestamp).where(
            (Message.author_id == user.id) &
            (Message.guild_id == event.guild.id)
        ).limit(1).order_by(Message.timestamp.desc()).async()

        oldest_msg = Message.select(Message.timestamp).where(
            (Message.author_id == user.id) &
            (Message.guild_id == event.guild.id)
        ).limit(1).order_by(Message.timestamp.asc()).async()

        if newest_msg.value and oldest_msg.value:
            statsd.timing('sql.duration.newest_msg', newest_msg.value._query_time, tags=tags)
            statsd.timing('sql.duration.oldest_msg', oldest_msg.value._query_time, tags=tags)
            newest_msg = newest_msg.value.get()
            oldest_msg = oldest_msg.value.get()

            content.append(u'\n **\u276F Activity**')
            content.append('Last Message: {} ago ({})'.format(
                humanize.naturaldelta(datetime.utcnow() - newest_msg.timestamp),
                newest_msg.timestamp.isoformat(),
            ))
            content.append('First Message: {} ago ({})'.format(
                humanize.naturaldelta(datetime.utcnow() - oldest_msg.timestamp),
                oldest_msg.timestamp.isoformat(),
            ))

        embed = MessageEmbed()

        avatar = u'https://cdn.discordapp.com/avatars/{}/{}.png'.format(
            user.id,
            user.avatar,
        )

        embed.set_author(name=u'{}#{}'.format(
            user.username,
            user.discriminator,
        ), icon_url=avatar)

        embed.set_thumbnail(url=avatar)

        embed.description = '\n'.join(content)
        embed.color = get_dominant_colors_user(user, avatar)
        event.msg.reply('', embed=embed)