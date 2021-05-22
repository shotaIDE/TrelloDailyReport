# coding: utf-8

import argparse
import itertools
import json
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum

import requests

_API_ORIGIN = 'https://api.trello.com'
_MOCK_BOARDS_FILE = 'mock_boards.json'
_MOCK_ACTIONS_FILE = 'mock_actions.json'
_MOCK_CARDS_FILE = 'mock_cards.json'
_UTC = timezone(timedelta(), 'UTC')
_JST = timezone(timedelta(hours=9), name='JST')
_PLUS_FOR_TRELLO_COMMENT_FORMAT = r'^plus\! (\d+(\.\d+)?)/(\d+(\.\d+)?) ?(.*)$'
_REPORT_FILE = 'report.md'


class Mode(Enum):
    GET_BOARDS = 'boards'
    GET_ACTIONS = 'actions'
    GET_CARDS = 'cards'
    GET_REPORT = 'report'


@dataclass
class Label:
    id: str
    text: str

    def __eq__(self, other):
        if not isinstance(other, Label):
            return False
        return self.id == other.id

    def __hash__(self):
        return hash(self.id)


@dataclass
class Card:
    id: str
    title: str
    labels: [Label]

    def __eq__(self, other):
        if not isinstance(other, Card):
            return False
        return self.id == other.id

    def __hash__(self):
        return hash(self.id)


@dataclass
class Action:
    card_id: str
    comment: str
    spent: float


@dataclass
class Spent:
    card_id: str
    comments: [str]
    spent: float


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', type=str, default=Mode.GET_REPORT.value)
    parser.add_argument('--prod', action='store_true', default=False)
    arguments = parser.parse_args()

    mode_str = arguments.mode
    if mode_str == Mode.GET_BOARDS.value:
        mode = Mode.GET_BOARDS
        print('Run in get boards mode')
    elif mode_str == Mode.GET_ACTIONS.value:
        mode = Mode.GET_ACTIONS
        print('Run in get actions mode')
    elif mode_str == Mode.GET_CARDS.value:
        mode = Mode.GET_CARDS
        print('Run in get cards mode')
    elif mode_str == Mode.GET_REPORT.value:
        mode = Mode.GET_REPORT
        print('Run in default mode (get report mode)')
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
    projects = settings_dict['projects']
    categories = settings_dict['categories']

    general_params = {
        'key': trello_api_key,
        'token': trello_api_secret,
    }

    if mode == Mode.GET_BOARDS:
        get_boards(user_id=trello_user_name, general_params=general_params)

    elif mode == Mode.GET_ACTIONS:
        get_actions(
            board_id=trello_board_id,
            general_params=general_params,
            mock=mock)

    elif mode == Mode.GET_CARDS:
        get_cards(
            board_id=trello_board_id,
            general_params=general_params,
            mock=mock)

    elif mode == Mode.GET_REPORT:
        spents = get_actions(
            board_id=trello_board_id,
            general_params=general_params,
            mock=mock)
        cards = get_cards(
            board_id=trello_board_id,
            general_params=general_params,
            mock=mock)
        get_report(
            spents=spents,
            cards=cards,
            projects=projects,
            categories=categories)


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


def get_actions(board_id: str, general_params: dict, mock: bool) -> [Spent]:
    if mock:
        with open(_MOCK_ACTIONS_FILE, 'r', encoding='utf-8') as f:
            actions = json.load(f)
    else:
        actions = fetch_actions(
            board_id=trello_board_id,
            general_params=general_params)

        with open(_MOCK_ACTIONS_FILE, 'w', encoding='utf-8') as f:
            json.dump(actions, f, ensure_ascii=False, indent=4)

    if mock:
        start_datetime = datetime(2021, 5, 21, tzinfo=_JST)
    else:
        current = datetime.now(tz=_JST)
        start_datetime = current.replace(
            hour=0, minute=0, second=0, microsecond=0)
    actions = parse_actions(actions=actions, start_datetime=start_datetime)

    return actions


def get_cards(board_id: str, general_params: dict, mock: bool) -> [Card]:
    if mock:
        with open(_MOCK_CARDS_FILE, 'r', encoding='utf-8') as f:
            cards = json.load(f)
    else:
        cards = fetch_cards(
            board_id=board_id,
            general_params=general_params)

        with open(_MOCK_CARDS_FILE, 'w', encoding='utf-8') as f:
            json.dump(cards, f, ensure_ascii=False, indent=4)

    cards = parse_cards(cards=cards)
    return cards


def get_report(
        spents: [Spent], cards: {str: Card}, projects=[str], categories=[str]):
    spent_card_ids = [spent.card_id for spent in spents]
    spent_cards = [cards[card_id] for card_id in spent_card_ids]
    print(f'Spent cards: {spent_cards}')

    target_labels = set(
        list(itertools.chain.from_iterable(
            [card.labels for card in spent_cards])))
    target_label_texts = [label.text for label in target_labels]
    print(f'Target labels: {target_labels}')

    target_projects = [
        label for label in target_labels if label.text in projects]
    print(f'Target projects: {target_projects}')

    target_categories = [
        label for label in target_labels if label.text in categories]
    print(f'Target categories: {target_categories}')

    report = ''
    for project in target_projects:
        report += f'## {project.text}\n'

        target_card_id_set = [
            card.id for card in cards.values() if project in card.labels]
        target_spents = [
            spent for spent in spents if spent.card_id in target_card_id_set]

        for spent in target_spents:
            card = cards[spent.card_id]
            report += f'- [{spent.spent:.2f}h] {card.title}\n'
            for comment in spent.comments:
                report += f'  - {comment}\n'

        report += '\n'

    print('====================')
    print(report)

    with open(_REPORT_FILE, 'w', encoding='utf=8')as f:
        f.write(report)


def fetch_actions(board_id: str, general_params: dict) -> [dict]:
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


def parse_actions(actions: [dict], start_datetime: datetime) -> [Spent]:
    print(f'Start period: {start_datetime}')

    pattern = re.compile(_PLUS_FOR_TRELLO_COMMENT_FORMAT)

    in_period_actions = []
    for action in actions:
        action_datetime_str = action['date']
        action_datetime = datetime.strptime(
            action_datetime_str, '%Y-%m-%dT%H:%M:%S.%f%z')
        print(action_datetime)

        if (action_datetime < start_datetime):
            continue

        text = action['data']['text']
        matched = pattern.match(text)
        if not matched:
            continue

        matched_groups = matched.groups()
        spent = float(matched_groups[0])
        comment = matched_groups[4]

        card_id = action['data']['card']['id']

        action = Action(card_id=card_id, comment=comment, spent=spent)

        print(action)

        in_period_actions.append(action)

    print(f'Filtered actions: #{len(in_period_actions)}')

    duplicated_card_id_list = [action.card_id for action in in_period_actions]
    card_id_set = set(duplicated_card_id_list)

    spents = []
    for card_id in card_id_set:
        card_actions = [action for action in in_period_actions]
        card_spent_raw = sum([action.spent for action in card_actions])
        card_spent = round(card_spent_raw, 2)
        card_comments = [
            action.comment for action in card_actions if action.comment != '']
        spent = Spent(
            card_id=card_id,
            comments=card_comments,
            spent=card_spent)
        spents.append(spent)

    print(spents)

    return spents


def fetch_cards(board_id: str, general_params: dict) -> [dict]:
    target_status = 'visible'
    get_actions_path = f'/1/boards/{board_id}/cards/{target_status}'

    query = get_query(params=general_params)

    url = f'{_API_ORIGIN}{get_actions_path}?{query}'

    print(f'Get url: {url}')

    result = requests.get(url)
    cards_string = result.text

    print(f'result: {cards_string}')

    cards = json.loads(cards_string)
    return cards


def parse_cards(cards: [{}]) -> {str: Card}:
    parsed_cards = {}
    for card in cards:
        labels = [
            Label(id=label['id'], text=label['name'])
            for label in card['labels']
        ]
        card_id = card['id']
        parsed_cards[card_id] = Card(
            id=card_id, title=card['name'], labels=labels)

    print(parsed_cards)

    return parsed_cards


if __name__ == '__main__':
    main()
