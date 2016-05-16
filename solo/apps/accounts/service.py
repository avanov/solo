import logging
from aiohttp.web import Application
from sqlalchemy.sql import select

from solo.services import SQLService
from solo.apps.accounts.models import User


log = logging.getLogger(__name__)


class UserService(SQLService):
    def __init__(self, app: Application):
        super(UserService, self).__init__(app, User)
