import gevent
import requests

from disco.bot import Plugin
from gevent.pool import Pool
from PIL import Image
from six import BytesIO

from aetherya.models.message import Message
from aetherya.constants import (
  CDN_URL, EMOJI_RE
)


class TutorialPlugin(Plugin):

  def get_emoji_url(self, emoji):
    return CDN_URL.format('-'.join(
      char.encode('unicode_escape').decode('utf-8')[2:].lstrip('0')
      for char in emoji))

  @Plugin.command('cat', global_=True)
  def cat(self, event):
    for _ in range(3):
      try:
        r = requests.get('http://aws.random.cat/meow')
        r.raise_for_status()
      except:
        continue
    
      url = r.json()['file']
      if not url.endswith('.gif'):
        break
    else:
      return event.msg.reply('404 cat not found :(')

    r = requests.get(url)
    r.raise_for_status()
    event.msg.reply('', attachments=[('cat.jpg', r.content)])

  @Plugin.command('jumbo', '<emojis:str...>')
  def jumbo(self, event, emojis):
    urls = []

    for emoji in emojis.split(' ')[:5]:
      if EMOJI_RE.match(emoji):
        _, eid = EMOJI_RE.findall(emoji)[0]
        urls.append('https://discordapp.com/api/emojis/{}.png'.format(eid))
      else:
        urls.append(self.get_emoji_url(emoji))

    width, height, images = 0, 0, []

    for r in Pool(6).imap(requests.get, urls):
      try:
        r.raise_for_status()
      except requests.HTTPError:
        return

      img = Image.open(BytesIO(r.content))
      height = img.height if img.height > height else height
      width += img.width + 10
      images.append(img)
      
    image = Image.new('RGBA', (width, height))
    width_offset = 0
    for img in images:
      image.paste(img, (width_offset, 0))
      width_offset += img.width + 10

    combined = BytesIO()
    image.save(combined, 'png', quality=55)
    combined.seek(0)
    return event.msg.reply('', attachments=[('emoji.png', combined)])

  @Plugin.command('ping')
  def command_ping(self, event):
      event.msg.reply('Pong!')

  @Plugin.command('echo', '<content:str...>')
  def echo_command(self, event, content):
    event.msg.reply(content)

  tags = {}

  @Plugin.command('tag', '<name:str> [value:str...]')
  def on_tag_command(self, event, name, value=None):
    
    if value:
      self.tags[name] = value
      event.msg.reply(':ok_hand: created tag `{}`'.format(name))
    else:
      if name in self.tags.keys():
        return event.msg.reply(self.tags[name])
      else:
        return event.msg.reply('Unknown tag: `{}`'.format(name))

  @Plugin.command('shutdown')
  def shutdown_command(self, event):
    event.msg.reply('Bye!')
    self.client.gw.ws_event.set()

  @Plugin.command('restart')
  def restart_command(self, event):
    event.msg.reply('<:cog:430175162378223628> Restarting.')
    self.client.gw.ws.close(status=4009)

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
          content.append(u'\n**\u276F Member Information**')
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

        # Execute a bunch of queries async
      newest_msg = Message.select(Message.timestamp).where(
          (Message.author_id == user.id) &
          (Message.guild_id == event.guild.id)
      ).limit(1).order_by(Message.timestamp.desc()).async()

      oldest_msg = Message.select(Message.timestamp).where(
          (Message.author_id == user.id) &
          (Message.guild_id == event.guild.id)
      ).limit(1).order_by(Message.timestamp.asc()).async()


      # Wait for them all to complete (we're still going to be as slow as the
      #  slowest query, so no need to be smart about this.)
      wait_many(newest_msg, oldest_msg, infractions, voice, timeout=10)
      tags = to_tags(guild_id=event.msg.guild.id)

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