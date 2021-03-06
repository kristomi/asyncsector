""" Simple asynchronous package for interacting with Sector Alarms web panel """
import async_timeout

from .util import get_json
from .util import find_version


class AsyncSector(object):
    """ Class to interact with sector alarm web panel """

    Base = 'https://mypagesapi.sectoralarm.net/'
    Login = 'User/Login'
    Alarm = 'Panel/GetOverview'
    Temperatures = 'Panel/GetTempratures/'
    Locks = 'Locks/GetLocks/?WithStatus=true&id={}'
    Lock = 'Locks/Lock'
    Unlock = 'Locks/Unlock'
    History = 'Panel/GetPanelHistory/{}'
    Arm = 'Panel/ArmPanel'
    Version = 'v1_1_95'

    @staticmethod
    async def getapiversion(session):
        """ Tries to retrieve current API version """

        with async_timeout.timeout(10):
            response = await session.get(
                AsyncSector.Base, json=None)

            if response.status == 200:
                result = await response.text()
                return find_version(result) if result else None

        return None

    @classmethod
    async def create(cls, session, alarm_id, username, password, version=None):
        """ factory """
        if version == 'auto':
            version = await AsyncSector.getapiversion(session)
        self = AsyncSector(session, alarm_id, username, password, version)
        logged_in = await self.login()

        return self if logged_in else None

    def __init__(self, session, alarm_id, username, password, version=None):
        if version is None:
            version = AsyncSector.Version
        self.alarm_id = alarm_id
        self._session = session
        self._auth = {'userID': username, 'password': password}
        self._version = version

    async def login(self):
        """ Tries to Login to Sector Alarm """

        with async_timeout.timeout(10):
            response = await self._session.post(
                AsyncSector.Base + AsyncSector.Login, json=self._auth)

            if response.status == 200:
                result = await response.text()
                if 'frmLogin' in result:
                    return False
                return True

        return False

    async def get_status(self):
        """
        Fetches the status of the alarm
        """
        request = self._session.post(
            AsyncSector.Base + AsyncSector.Alarm,
            data={
                'PanelId': self.alarm_id,
                'Version': self._version
            }
        )

        return await get_json(request)

    async def get_temperatures(self):
        """
        Fetches a list of all temperature sensors
        """
        data = {
            'id': self.alarm_id,
            'Version': self._version
        }
        request = self._session.post(
            AsyncSector.Base + AsyncSector.Temperatures,
            json=data)
        

        return await get_json(request)

    async def get_locks(self):
        """
        Fetches a list of all locks
        """
        try:
            request = self._session.get(
                AsyncSector.Base + AsyncSector.Locks.format(self.alarm_id))

            return await get_json(request)
        except:
            return None

    async def get_history(self):
        """
        Fetches the alarm event log/history
        """
        request = self._session.get(AsyncSector.Base +
                                    AsyncSector.History.format(self.alarm_id))

        return await get_json(request)

    async def alarm_toggle(self, state, code=None):
        """
        Tries to toggle the state of the alarm
        """
        data = {
            'ArmCmd': state,
            'PanelCode': code,
            'HasLocks': False,
            'id': self.alarm_id
        }

        request = self._session.post(
            AsyncSector.Base + AsyncSector.Arm, json=data)

        result = await get_json(request)
        if 'status' in result and result['status'] == 'success':
            return True

        return False

    async def disarm(self, code=None):
        """ Send disarm command """
        return await self.alarm_toggle('Disarm', code=code)

    async def arm_home(self, code=None):
        """ Send arm home command """
        return await self.alarm_toggle('Partial', code=code)

    async def arm_away(self, code=None):
        """ Send arm away command """
        return await self.alarm_toggle('Total', code=code)

    async def lock_toggle(self, stateUrl, lockSerial=None, code=None):
        """ Tries to toggle the state of the lock """
        data = {
            'LockSerial': lockSerial,
            'DisarmCode': code,
            'id': self.alarm_id
        }

        request = self._session.post(
            AsyncSector.Base + stateUrl, json=data)

        result = await get_json(request)
        if result and 'Status' in result and result['Status'] == 'success':
            return True

        return False

    async def unlock(self, lock=None, code=None):
        """ Send unlock door command """
        return await self.lock_toggle(AsyncSector.Unlock, lockSerial=lock, code=code)

    async def lock(self, lock=None, code=None):
        """ Send lock door command """
        return await self.lock_toggle(AsyncSector.Lock, lockSerial=lock, code=code)
