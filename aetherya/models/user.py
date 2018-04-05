from datetime import datetime
from holster.enum import Enum
from peewee import BigIntegerField, IntegerField, SmallIntegerField, TextField, BooleanField, DateTimeField
from playhouse.postgres_ext import BinaryJSONField

from rowboat.sql import BaseModel


@BaseModel.register
class User(BaseModel):
    user_id = BigIntegerField(primary_key=True)
    username = TextField()
    discriminator = SmallIntegerField()
    avatar = TextField(null=True)
    bot = BooleanField()

    created_at = DateTimeField(default=datetime.utcnow)

    admin = BooleanField(default=False)

    SQL = '''
        CREATE INDEX IF NOT EXISTS users_username_trgm ON users USING gin(username gin_trgm_ops);
    '''

    class Meta:
        db_table = 'users'

        indexes = (
            (('user_id', 'username', 'discriminator'), True),
        )

    @property
    def id(self):
        return self.user_id

    @classmethod
    def ensure(cls, user, should_update=True):
        return cls.from_disco_user(user)

    @classmethod
    def with_id(cls, uid):
        try:
            return User.get(user_id=uid)
        except User.DoesNotExist:
            return

    @classmethod
    def from_disco_user(cls, user, should_update=True):
        # DEPRECATED
        obj, _ = cls.get_or_create(
            user_id=user.id,
            defaults={
                'username': user.username,
                'discriminator': user.discriminator,
                'avatar': user.avatar,
                'bot': user.bot
            })

        if should_update:
            updates = {}

            if obj.username != user.username:
                updates['username'] = user.username

            if obj.discriminator != user.discriminator:
                updates['discriminator'] = user.discriminator

            if obj.avatar != user.avatar:
                updates['avatar'] = user.avatar

            if updates:
                cls.update(**updates).where(User.user_id == user.id).execute()

        return obj

    def get_avatar_url(self, fmt='webp', size=1024):
        if not self.avatar:
            return None

        return 'https://cdn.discordapp.com/avatars/{}/{}.{}?size={}'.format(
            self.user_id,
            self.avatar,
            fmt,
            size
        )

    def __unicode__(self):
        return u'{}#{}'.format(self.username, str(self.discriminator).zfill(4))