''' Start asyncsector '''

import sys
import asyncio
import argparse

import aiohttp

from asyncsector import AsyncSector
from asyncsector.util import get_time
from asyncsector.util import find

async def async_main(loop):
    '''
    Async main function

    Logs in to Sector Alarm and prints alarm history + temperatures repeatedly with delay.
    '''

    parser = argparse.ArgumentParser(description='Check Sector Alarm status')

    parser.add_argument('alarm_id', type=str, help='ID of your alarm system')
    parser.add_argument('username', type=str,
                        help='Your Sector Alarm username')
    parser.add_argument('password', type=str,
                        help='Your Sector Alarm password')
    parser.add_argument('--repeat', type=int, default=1)
    parser.add_argument('--delay', type=int, default=10)
    parser.add_argument('--history', type=int, default=1)
    parser.add_argument('--version', type=str, default='auto', help='Version string or "auto"')
    parser.add_argument('--getversion',dest='getversion',action='store_true')
    parser.add_argument('--status', type=int, default=1)
    parser.add_argument('--lock', type=str)
    parser.add_argument('--unlock', type=str)
    parser.add_argument('--code', type=str)
    parser.set_defaults(getversion=False)

    args = parser.parse_args()

    async with aiohttp.ClientSession(loop=loop) as session:

        if args.getversion:
            version = await AsyncSector.getapiversion(session)
            print(version)
            return

        alarm = await AsyncSector.create(session,
                                         args.alarm_id, args.username, args.password, args.version)

        if not alarm:
            print("Failed to connecto to alarm, bad credentials")
            return

        if args.lock:
            result = await alarm.lock(args.lock, args.code)
            print("lock: {}".format(result))
            return result

        if args.unlock:
            result = await alarm.unlock(args.unlock, args.code)
            print("unlock: {}".format(result))
            return result

        for i in range(0, args.repeat):

            if i != 0:
                await asyncio.sleep(args.delay)

            status, history, temperatures, locks = await asyncio.gather(
                                                            alarm.get_status(),
                                                            alarm.get_history(),
                                                            alarm.get_temperatures(),
                                                            alarm.get_locks())

            print()

            if history:
                log = history.get('LogDetails', None)
                if log is not None:
                    for entry in log[:args.history]:
                        print(
                            '{:12}{:12}{:12}{}'.format(
                                entry['EventType'],
                                entry['LockName'],
                                entry['User'],
                                get_time(entry['Time'])))
                    print()

            if temperatures:
                print("Temps:")
                for temperature in temperatures:
                    print('{:12}{}'.format(temperature['Label'], temperature['Temprature']))
                print()
            
            if locks:
                print("Locks:")
                for lock in locks:
                    info = find(lambda data: data['Serial'] == lock['Serial'], status['Locks'])
                    print('{:12}{:12}{}'.format(lock['Serial'], info['Label'], lock['Status']))

            if args.status:
                print()
                print("IsOnline: {}".format(status['Panel']['IsOnline']))

def main():
    '''
    Synchronous main, bootstraps async main
    '''
    loop = asyncio.get_event_loop()
    loop.run_until_complete(async_main(loop))


if __name__ == "__main__":
    sys.exit(main())

