# coding: utf-8

from enum import Enum
import argparse
import json
import requests

_API_ORIGIN = 'https://api.trello.com'


class Mode(Enum):
    GET_BOARDS = 'boards'
    GET_ACTIONS = 'actions'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', type=str, default=Mode.GET_ACTIONS.value)
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

    SETTINGS_JSON_FILE_NAME = 'settings.json'
    with open(SETTINGS_JSON_FILE_NAME, 'r', encoding='utf-8') as f:
        settings_dict = json.load(f)

    trello_api_key = settings_dict['trelloApiKey']
    trello_api_secret = settings_dict['trelloApiSecret']
    trello_user_name = settings_dict['trelloUserName']
    trello_board_id = settings_dict['trelloBoardId']

    query = get_query(key=trello_api_key, token=trello_api_secret)

    if mode == Mode.GET_BOARDS:
        get_boards(user_id=trello_user_name, query=query)
    elif mode == Mode.GET_ACTIONS:
        get_actions()


def get_query(key: str, token: str) -> str:
    params = {
        'key': key,
        'token': token,
    }
    query_strings = [f'{key}={value}' for key, value in params.items()]
    query = '&'.join(query_strings)
    return query


def get_boards(user_id: str, query: str):
    get_boards_path = f'/1/members/{user_id}/boards'

    url = f'{_API_ORIGIN}{get_boards_path}?{query}'

    print(f'Get url: {url}')

    result = requests.get(url)
    boards_string = result.text

    print(f'result: {boards_string}')

    boards = json.loads(boards_string)
    with open('debug_boards.json', 'w', encoding='utf-8') as f:
        json.dump(boards, f, ensure_ascii=False, indent=4)


def get_actions():
    pass


if __name__ == '__main__':
    main()
