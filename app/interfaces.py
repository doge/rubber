from .utils import database
from .config import Config


class Interfaces:
    images = database.Database(Config.database, 'images')
    users = database.Database(Config.database, 'users')
    invites = database.Database(Config.database, 'invites')
