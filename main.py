# coding: utf-8

import json


def main():
    SETTINGS_JSON_FILE_NAME = 'settings.json'
    with open(SETTINGS_JSON_FILE_NAME, 'r', encoding='utf-8') as f:
        settings_dict = json.load(f)

    trello_api_key = settings_dict['trelloApiKey']
    trello_api_secret = settings_dict['trelloApiSecret']
    trello_user_name = settings_dict['trelloUserName']
    trello_board_id = settings_dict['trelloBoardId']

    params = {
        'key': trello_api_key,
        'token': trello_api_secret,
    }
    query_strings = [f'{key}={value}' for key, value in params.items()]
    query = '&'.join(query_strings)

    url = f'?{query}'

    print(f'API url: {url}')


if __name__ == '__main__':
    main()
