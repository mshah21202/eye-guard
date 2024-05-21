import argparse
import asyncio
from threading import Thread, Lock
from apiclient import start_api

class EntryExitOptionalAction(argparse.Action):
    def __init__(self,
                 option_strings,
                 dest,
                 default=None,
                 type=None,
                 choices=None,
                 required=False,
                 help=None,
                 metavar=None):

        _option_strings = []
        for option_string in option_strings:
            _option_strings.append(option_string)

            if option_string.startswith('--'):
                option_string = '--exit'
                _option_strings.append(option_string)

        if help is not None and default is not None and default is not argparse.SUPPRESS:
            help += f" (default: {'entry' if default else 'exit'})"

        super().__init__(
            option_strings=_option_strings,
            dest=dest,
            nargs=0,
            default=default,
            type=type,
            choices=choices,
            required=required,
            help=help,
            metavar=metavar)

    def __call__(self, parser, namespace, values, option_string=None):
        if option_string in self.option_strings:
            setattr(namespace, self.dest, not option_string.startswith('--exit'))

    def format_usage(self):
        return ' | '.join(self.option_strings)

parser = argparse.ArgumentParser()
_token = "eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9.eyJuYW1laWQiOiIyMiIsInVuaXF1ZV9uYW1lIjoiR2F0ZSBTdGFmZiIsInJvbGUiOiJHYXRlU3RhZmYiLCJuYmYiOjE3MTQ4NTIxNjksImV4cCI6MTcyMjYyODE2OSwiaWF0IjoxNzE0ODUyMTY5fQ.EL5M9B74yC2eX41_vgDZfdH5jhHVO1qqp7fz9Qt3V9IblL2Oi6u64a8KcrexCHy9agIMLrCyKUXC1klR3nMXcQ"
parser.add_argument('area_id', type=int, help="The area id this camera belongs to. Needs to be an integer")
parser.add_argument('--entry', default=True, type=bool, help="If this camera is an entry camera set this to True, otherwise set to False.", action=EntryExitOptionalAction)
parser.add_argument('--base_url', default="https://localhost:7136", type=str, help="(Default: https://localhost:7136). Endpoints url")
parser.add_argument('--auth', type=str, default=_token, help="Endpoint auth token")
args = parser.parse_args()
area_id = args.area_id
entry = args.entry
base_url = args.base_url
token = args.auth

queue = []
lock = Lock()

from infer import start_infer

# This function runs the event loop
def start_loop(loop: asyncio.AbstractEventLoop, foo):
    asyncio.set_event_loop(loop)
    if foo:
        loop.run_until_complete(foo)
    else:
        loop.run_forever()

def create_thread(loop, foo = None):
    thread = Thread(target=start_loop, args=(loop, foo), daemon=True)
    thread.start()

async def main(area_id: int, entry: bool, base_url: str, token: str):
    vision_loop = asyncio.new_event_loop()
    ecampusguard_loop = asyncio.new_event_loop()
    create_thread(vision_loop)
    create_thread(ecampusguard_loop, start_api(lock, queue, area_id, entry, base_url, token))
    # start_api(lock, queue, area_id, entry, base_url, token)
    start_infer(vision_loop, lock, queue, area_id, entry)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(area_id, entry, base_url, token))