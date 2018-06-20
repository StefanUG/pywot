#!/usr/bin/env python3
import json
import asyncio
import aiohttp
import async_timeout
from datetime import (
    datetime,
)
from configman import (
    Namespace,
    configuration,
    class_converter
)


async def get_tide_table(config, last_tide=None):
    async with aiohttp.ClientSession() as session:
        async with async_timeout.timeout(config.seconds_for_timeout):
            async with session.get(config.target_url) as response:
                raw_tide_data = json.loads(await response.text())

    raw_future_tides = []
    for item in raw_tide_data["tide"]["tideSummary"]:
        if item["data"]["type"] in ("High Tide", "Low Tide"):
            raw_future_tides.append((
                item["data"]["type"],
                datetime(
                    int(item["date"]["year"]),
                    int(item["date"]["mon"]),
                    int(item["date"]["mday"]),
                    int(item["date"]["hour"]),
                    int(item["date"]["min"]),
                )
            ))

    future_tides = []
    # for i, (x, t) in enumerate(raw_future_tides[:-1]):  #TODO
    for i, (x, t) in enumerate(raw_future_tides[:2]):
        future_tides.append((
            # 0 - tide type
            x,
            # 1 - tide time
            t,
            # 2 - length of tide
            raw_future_tides[i + 1][1] - t,
            # 3 - time between tides
            (raw_future_tides[i + 1][1] - t) / 120
        ))

    if last_tide is None:
        last_tide = (
            "Low Tide" if future_tides[0][0] == "High Tide" else "High Tide",
            future_tides[0][1] - future_tides[0][2],
            future_tides[0][2],
            future_tides[0][3],
        )
    tide_table = [last_tide]

    tide_table.extend(future_tides)
    return tide_table


async def tide_stream(config):
    tide_table = await get_tide_table(config)
    while True:
        for a_tide in tide_table:
            yield a_tide
        tide_table = await get_tide_table(config, tide_table[-1])


low_to_high = [
    '#00ff00', '#04ff00', '#08ff00', '#0cff00', '#10ff00', '#15ff00',
    '#19ff00', '#1dff00', '#21ff00', '#26ff00', '#2aff00', '#2eff00',
    '#32ff00', '#37ff00', '#3bff00', '#3fff00', '#43ff00', '#48ff00',
    '#4cff00', '#50ff00', '#54ff00', '#59ff00', '#5dff00', '#61ff00',
    '#65ff00', '#6aff00', '#6eff00', '#72ff00', '#76ff00', '#7bff00',
    '#7fff00', '#83ff00', '#88ff00', '#8cff00', '#90ff00', '#94ff00',
    '#99ff00', '#9dff00', '#a1ff00', '#a5ff00', '#aaff00', '#aeff00',
    '#b2ff00', '#b6ff00', '#bbff00', '#bfff00', '#c3ff00', '#c7ff00',
    '#ccff00', '#d0ff00', '#d4ff00', '#d8ff00', '#ddff00', '#e1ff00',
    '#e5ff00', '#e9ff00', '#eeff00', '#f2ff00', '#f6ff00', '#faff00',
    '#ffff00', '#fffa00', '#fff600', '#fff200', '#ffee00', '#ffe900',
    '#ffe500', '#ffe100', '#ffdd00', '#ffd800', '#ffd400', '#ffd000',
    '#ffcc00', '#ffc700', '#ffc300', '#ffbf00', '#ffbb00', '#ffb600',
    '#ffb200', '#ffae00', '#ffaa00', '#ffa500', '#ffa100', '#ff9d00',
    '#ff9900', '#ff9400', '#ff9000', '#ff8c00', '#ff8800', '#ff8300',
    '#ff7f00', '#ff7b00', '#ff7700', '#ff7200', '#ff6e00', '#ff6a00',
    '#ff6600', '#ff6100', '#ff5d00', '#ff5900', '#ff5400', '#ff5000',
    '#ff4c00', '#ff4800', '#ff4300', '#ff3f00', '#ff3b00', '#ff3700',
    '#ff3200', '#ff2e00', '#ff2a00', '#ff2600', '#ff2100', '#ff1d00',
    '#ff1900', '#ff1500', '#ff1000', '#ff0c00', '#ff0800', '#ff0400',
]

high_to_low = [
    '#ff0000', '#ff0008', '#ff0010', '#ff0019', '#ff0022', '#ff002a',
    '#ff0033', '#ff003b', '#ff0043', '#ff004c', '#ff0054', '#ff005d',
    '#ff0066', '#ff006e', '#ff0077', '#ff007f', '#ff0087', '#ff0090',
    '#ff0098', '#ff00a1', '#ff00aa', '#ff00b2', '#ff00bb', '#ff00c3',
    '#ff00cb', '#ff00d4', '#ff00dc', '#ff00e5', '#ff00ee', '#ff00f6',
    '#ff00ff', '#f600ff', '#ee00ff', '#e500ff', '#dc00ff', '#d400ff',
    '#cb00ff', '#c300ff', '#bb00ff', '#b200ff', '#aa00ff', '#a100ff',
    '#9800ff', '#9000ff', '#8700ff', '#7f00ff', '#7700ff', '#6e00ff',
    '#6600ff', '#5d00ff', '#5400ff', '#4c00ff', '#4300ff', '#3b00ff',
    '#3300ff', '#2a00ff', '#2200ff', '#1900ff', '#1000ff', '#0800ff',
    '#0000ff', '#0008ff', '#0011ff', '#0019ff', '#0021ff', '#002aff',
    '#0033ff', '#003bff', '#0043ff', '#004cff', '#0055ff', '#005dff',
    '#0065ff', '#006eff', '#0077ff', '#007fff', '#0087ff', '#0090ff',
    '#0099ff', '#00a1ff', '#00a9ff', '#00b2ff', '#00bbff', '#00c3ff',
    '#00cbff', '#00d4ff', '#00ddff', '#00e5ff', '#00edff', '#00f6ff',
    '#00ffff', '#00fff6', '#00ffed', '#00ffe5', '#00ffdd', '#00ffd4',
    '#00ffcb', '#00ffc3', '#00ffbb', '#00ffb2', '#00ffa9', '#00ffa1',
    '#00ff99', '#00ff90', '#00ff87', '#00ff7f', '#00ff77', '#00ff6e',
    '#00ff65', '#00ff5d', '#00ff55', '#00ff4c', '#00ff43', '#00ff3b',
    '#00ff33', '#00ff2a', '#00ff21', '#00ff19', '#00ff11', '#00ff08',
]


async def control_tide(config):
    async for a_tide in tide_stream(config):
        step_time = a_tide[1]
        print('next ', step_time)
        for step in range(120):
            colors = low_to_high if a_tide[0] == "Low Tide" else high_to_low
            now = datetime.now()
            if now > step_time:
                step_time += a_tide[3]
                print(now, step_time)
                continue
            print("now: {}  step:{}  next:{}".format(now, step_time, a_tide[1]))
            print("set ", colors[step])
            print("wait ", a_tide[3].seconds)
            await put_tide_color(config, colors[step])
            await asyncio.sleep(a_tide[3].seconds)
            step_time += a_tide[3]


async def put_tide_color(config, a_color):
    async with aiohttp.ClientSession() as session:
        async with async_timeout.timeout(config.seconds_for_timeout):
            async with session.put(
                "http://gateway.local/things/{}/properties/color".format(config.thing_id),
                headers={
                    'Accept': 'application/json',
                    'Authorization': 'Bearer {}'.format(config.thing_gateway_auth_key),
                    'Content-Type': 'application/json'
                },
                data='{{"color": "{}"}}'.format(a_color)
            ) as response:
                return await response.text()

def create_url(config, local_namespace, args):
    """generate a URL to fetch local weather data from Weather Underground using
    configuration data"""
    return "http://api.wunderground.com/api/{}/tide/q/{}/{}.json".format(
        local_namespace.weather_underground_api_key,
        local_namespace.state_code,
        local_namespace.city_name
    )

required_config = Namespace()
required_config.add_option(
    'weather_underground_api_key',
    doc='the api key to access Weather Underground data',
    short_form="K",
    default="c5410a6a36d2e304"
)
required_config.add_option(
    'state_code',
    doc='the two letter state code',
    default="OR",
)
required_config.add_option(
    'city_name',
    doc='the name of the city',
    default="Waldport",
)
required_config.add_aggregation(
    'target_url',
    function=create_url
)
required_config.add_option(
    'seconds_for_timeout',
    doc='the number of seconds to allow for fetching weather data',
    default=10
)
required_config.add_option(
    'thing_gateway_auth_key',
    doc='the api key to access the Things Gateway',
    short_form="G",
    default='eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6ImRjYTVkMTQ0LTBkNjAtNDkzYS1iMDU0LWI1NGM0NzBjZDRhYyJ9.eyJjbGllbnRfaWQiOiJsb2NhbC10b2tlbiIsInJvbGUiOiJhY2Nlc3NfdG9rZW4iLCJzY29wZSI6Ii90aGluZ3M6cmVhZHdyaXRlIiwiaWF0IjoxNTI5NDM3MjE1fQ.dUp15a2Qyu6PeaXZYozpySfxkl_gZOsbaDtuzX-6aEY5vVw78H5OKFQIqbnGvmRvPyBHK1xfSMlq4FKxRmfusA',
)
required_config.add_option(
    'thing_id',
    doc='the id of the color bulb to control',
    default="zb-0017880103415d70"
)

if __name__ == '__main__':

    config = configuration(required_config)

    event_loop = asyncio.get_event_loop()
    event_loop.run_until_complete(control_tide(config))