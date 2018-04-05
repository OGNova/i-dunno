import re
import six
import json
import uuid
import traceback

from peewee import (
    BigIntegerField, ForeignKeyField, TextField, DateTimeField,
    BooleanField, UUIDField
)
from datetime import datetime, timedelta
from playhouse.postgres_ext import BinaryJSONField, ArrayField
from disco.types.base import UNSET


from aetherya.util import default_json
from aetherya.models.user import User
from aetherya.sql import BaseModel

EMOJI_RE = re.compile(r'<:.+:([0-9]+)>')


@BaseModel.register
class Message(BaseModel):
    id = BigIntegerField(primary_key=True)
    channel_id = BigIntegerField()
    guild_id = BigIntegerField(null=True)
    author = ForeignKeyField(User)
    content = TextField()
    timestamp = DateTimeField()
    edited_timestamp = DateTimeField(null=True, default=None)
    deleted = BooleanField(default=False)
    num_edits = BigIntegerField(default=0)
    command = TextField(null=True)

    mentions = ArrayField(BigIntegerField, default=[], null=True)
    emojis = ArrayField(BigIntegerField, default=[], null=True)
    attachments = ArrayField(TextField, default=[], null=True)
    embeds = BinaryJSONField(default=[], null=True)

    SQL = '''
        CREATE INDEX\
                IF NOT EXISTS messages_content_fts ON messages USING gin(to_tsvector('english', content));
        CREATE INDEX\
                IF NOT EXISTS messages_mentions ON messages USING gin (mentions);
    '''

    class Meta:
        db_table = 'messages'

        indexes = (
            # These indexes are mostly just general use
            (('channel_id', ), False),
            (('guild_id', ), False),
            (('deleted', ), False),

            # Timestamp is regularly sorted on
            (('timestamp', ), False),

            # Some queries want to get history in a guild or channel
            (('author', 'guild_id', 'channel_id'), False),
        )

    @classmethod
    def from_disco_message_update(cls, obj):
        if not obj.edited_timestamp:
            return

        to_update = {
            'edited_timestamp': obj.edited_timestamp,
            'num_edits': cls.num_edits + 1,
            'mentions': list(obj.mentions.keys()),
        }

        if obj.content is not UNSET:
            to_update['content'] = obj.with_proper_mentions
            to_update['emojis'] = list(map(int, EMOJI_RE.findall(obj.content)))

        if obj.attachments is not UNSET:
            to_update['attachments'] = [i.url for i in obj.attachments.values()]

        if obj.embeds is not UNSET:
            to_update['embeds'] = [json.dumps(i.to_dict(), default=default_json) for i in obj.embeds]

        cls.update(**to_update).where(cls.id == obj.id).execute()

    @classmethod
    def from_disco_message(cls, obj):
        _, created = cls.get_or_create(
            id=obj.id,
            defaults=dict(
                channel_id=obj.channel_id,
                guild_id=(obj.guild and obj.guild.id),
                author=User.from_disco_user(obj.author),
                content=obj.with_proper_mentions,
                timestamp=obj.timestamp,
                edited_timestamp=obj.edited_timestamp,
                num_edits=(0 if not obj.edited_timestamp else 1),
                mentions=list(obj.mentions.keys()),
                emojis=list(map(int, EMOJI_RE.findall(obj.content))),
                attachments=[i.url for i in obj.attachments.values()],
                embeds=[json.dumps(i.to_dict(), default=default_json) for i in obj.embeds]))

        for user in obj.mentions.values():
            User.from_disco_user(user)

        return created

    @classmethod
    def from_disco_message_many(cls, messages, safe=False):
        q = cls.insert_many(map(cls.convert_message, messages))

        if safe:
            q = q.on_conflict('DO NOTHING')

        return q.execute()

    @staticmethod
    def convert_message(obj):
        return {
            'id': obj.id,
            'channel_id': obj.channel_id,
            'guild_id': (obj.guild and obj.guild.id),
            'author': User.from_disco_user(obj.author),
            'content': obj.with_proper_mentions,
            'timestamp': obj.timestamp,
            'edited_timestamp': obj.edited_timestamp,
            'num_edits': (0 if not obj.edited_timestamp else 1),
            'mentions': list(obj.mentions.keys()),
            'emojis': list(map(int, EMOJI_RE.findall(obj.content))),
            'attachments': [i.url for i in obj.attachments.values()],
            'embeds': [json.dumps(i.to_dict(), default=default_json) for i in obj.embeds],
        }

    @classmethod
    def for_channel(cls, channel):
        return cls.select().where(cls.channel_id == channel.id)

@BaseModel.register
class MessageArchive(BaseModel):
    FORMATS = ['txt', 'csv', 'json']

    archive_id = UUIDField(primary_key=True, default=uuid.uuid4)

    message_ids = BinaryJSONField()

    created_at = DateTimeField(default=datetime.utcnow)
    expires_at = DateTimeField(default=lambda: datetime.utcnow() + timedelta(days=7))

    class Meta:
        db_table = 'message_archives'

        indexes = (
            (('created_at', ), False),
            (('expires_at', ), False)
        )

    @classmethod
    def create_from_message_ids(cls, message_ids):
        return cls.create(message_ids=message_ids)

    @property
    def url(self):
        # TODO: use web endpoint here
        return 'http:/cdn.aetherya.stream/api/archive/{}.txt'.format(self.archive_id)

    def encode(self, fmt='txt'):
        from rowboat.models.user import User

        if fmt not in self.FORMATS:
            raise Exception('Invalid format {}'.format(fmt))

        q = Message.select(
            Message.id,
            Message.channel_id,
            Message.timestamp,
            Message.content,
            Message.deleted,
            Message.attachments,
            User
        ).join(
            User
        ).where(
            (Message.id << self.message_ids)
        )

        if fmt == 'txt':
            return u'\n'.join(map(self.encode_message_text, q))
        elif fmt == 'csv':
            return u'\n'.join([
                'id,channel_id,timestamp,author_id,author,content,deleted,attachments'
            ] + map(self.encode_message_csv, q))
        elif fmt == 'json':
            return json.dumps({
                'messages': map(self.encode_message_json, q)
            })

    @staticmethod
    def encode_message_text(msg):
        return u'{m.timestamp} ({m.id} / {m.channel_id} / {m.author.id}) {m.author}: {m.content} ({attach})'.format(
            m=msg, attach=', '.join(map(unicode, msg.attachments or [])))

    @staticmethod
    def encode_message_csv(msg):
        def wrap(i):
            return u'"{}"'.format(six.text_type(i).replace('"', '""'))

        return ','.join(map(wrap, [
            msg.id,
            msg.timestamp,
            msg.author.id,
            msg.author,
            msg.content,
            str(msg.deleted).lower(),
            ' '.join(msg.attachments or [])
        ]))

    @staticmethod
    def encode_message_json(msg):
        return dict(
            id=str(msg.id),
            timestamp=str(msg.timestamp),
            author_id=str(msg.author.id),
            username=msg.author.username,
            discriminator=msg.author.discriminator,
            content=msg.content,
            deleted=msg.deleted,
            attachments=msg.attachments)