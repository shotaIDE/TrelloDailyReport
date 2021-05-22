# coding: utf-8

import argparse
import json
from datetime import datetime, timedelta, timezone
from enum import Enum

import requests

_API_ORIGIN = 'https://api.trello.com'
_MOCK_BOARDS_FILE = 'mock_boards.json'
_MOCK_ACTIONS_FILE = 'mock_actions.json'
_UTC = timezone(timedelta(), 'UTC')
_JST = timezone(timedelta(hours=9), name='JST')


class Mode(Enum):
    GET_BOARDS = 'boards'
    GET_ACTIONS = 'actions'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', type=str, default=Mode.GET_ACTIONS.value)
    parser.add_argument('--prod', action='store_true', default=False)
    arguments = parser.parse_args()

    mode_str = arguments.mode
    if mode_str == Mode.GET_BOARDS.value:
        mode = Mode.GET_BOARDS
        print('Run in get boards mode')
    elif mode_str == Mode.GET_ACTIONS.value:
        mode = Mode.GET_ACTIONS
        print('Run in default mode (get actions mode)')
    else:
        raise Exception('Invalid mode')

    mock = not arguments.prod
    if mock:
        print('Run in mock mode')
    else:
        print('Run in production mode')

    SETTINGS_JSON_FILE_NAME = 'settings.json'
    with open(SETTINGS_JSON_FILE_NAME, 'r', encoding='utf-8') as f:
        settings_dict = json.load(f)

    trello_api_key = settings_dict['trelloApiKey']
    trello_api_secret = settings_dict['trelloApiSecret']
    trello_user_name = settings_dict['trelloUserName']
    trello_board_id = settings_dict['trelloBoardId']

    general_params = {
        'key': trello_api_key,
        'token': trello_api_secret,
    }

    if mode == Mode.GET_BOARDS:
        get_boards(user_id=trello_user_name, general_params=general_params)
    elif mode == Mode.GET_ACTIONS:
        if mock:
            with open(_MOCK_ACTIONS_FILE, 'r', encoding='utf-8') as f:
                actions = json.load(f)
        else:
            actions = fetch_actions(
                board_id=trello_board_id,
                general_params=general_params)

            with open(_MOCK_ACTIONS_FILE, 'w', encoding='utf-8') as f:
                json.dump(boards, f, ensure_ascii=False, indent=4)

        if mock:
            start_datetime = datetime(2021, 5, 21, tzinfo=_JST)
        else:
            current = datetime.now(tz=_JST)
            start_datetime = current.replace(
                hour=0, minute=0, second=0, microsecond=0)
        parse_actions(actions=actions, start_datetime=start_datetime)


def get_boards(user_id: str, general_params: dict):
    get_boards_path = f'/1/members/{user_id}/boards'
    query = get_query(params=general_params)
    url = f'{_API_ORIGIN}{get_boards_path}?{query}'

    print(f'Get url: {url}')

    result = requests.get(url)
    boards_string = result.text

    print(f'result: {boards_string}')

    boards = json.loads(boards_string)
    with open(_MOCK_BOARDS_FILE, 'w', encoding='utf-8') as f:
        json.dump(boards, f, ensure_ascii=False, indent=4)


def fetch_actions(board_id: str, general_params: dict) -> dict:
    get_actions_path = f'/1/boards/{board_id}/actions'

    params = general_params.copy()
    params['limit'] = 100
    filter_params = [
        'commentCard',
    ]
    params['filter'] = ','.join(filter_params)

    query = get_query(params=params)

    url = f'{_API_ORIGIN}{get_actions_path}?{query}'

    print(f'Get url: {url}')

    result = requests.get(url)
    actions_string = result.text

    print(f'result: {actions_string}')

    actions = json.loads(actions_string)
    return actions


def get_query(params: dict) -> str:
    query_strings = [f'{key}={value}' for key, value in params.items()]
    query = '&'.join(query_strings)
    return query


def parse_actions(actions: str, start_datetime: datetime):
    print(f'Start period: {start_datetime}')

    in_period_actions = []
    for action in actions:
        action_datetime_str = action['date']
        action_datetime = datetime.strptime(
            action_datetime_str, '%Y-%m-%dT%H:%M:%S.%f%z')
        print(action_datetime)

        if (action_datetime < start_datetime):
            continue

        in_period_actions.append(action)

    print(f'Filtered actions: {in_period_actions}')


if __name__ == '__main__':
    main()
