import json
from urllib import request, error

from django.conf import settings


class MondayAPIError(Exception):
    pass


def run_query(query, variables=None):
    if not settings.MONDAY_API_KEY:
        raise MondayAPIError('MONDAY_API_KEY nao configurado.')
    if not settings.MONDAY_API_URL:
        raise MondayAPIError('MONDAY_API_URL nao configurado.')

    payload = {'query': query}
    if variables:
        payload['variables'] = variables

    http_request = request.Request(
        settings.MONDAY_API_URL,
        data=json.dumps(payload).encode('utf-8'),
        headers={
            'Authorization': settings.MONDAY_API_KEY,
            'Content-Type': 'application/json',
        },
        method='POST',
    )

    try:
        with request.urlopen(http_request, timeout=30) as response:
            body = json.loads(response.read().decode('utf-8'))
    except error.HTTPError as exc:
        raise MondayAPIError(f'Monday API retornou erro HTTP {exc.code}.') from exc
    except error.URLError as exc:
        raise MondayAPIError(f'Falha ao conectar na Monday API: {exc.reason}') from exc

    if body.get('errors'):
        raise MondayAPIError('; '.join(err.get('message', 'erro desconhecido') for err in body['errors']))

    return body.get('data', {})


def _label_colors_from_settings(settings_str):
    """Extrai {label_texto: cor_hex} do settings_str de uma coluna status."""
    if not settings_str:
        return {}
    try:
        settings_data = json.loads(settings_str)
    except (TypeError, ValueError):
        return {}

    labels = settings_data.get('labels')
    labels_colors = settings_data.get('labels_colors')
    if not isinstance(labels, dict) or not isinstance(labels_colors, dict):
        return {}

    result = {}
    for index, label_text in labels.items():
        color_info = labels_colors.get(index)
        if label_text and color_info and color_info.get('color'):
            result[label_text] = color_info['color']
    return result


def _fetch_board_columns(board_id):
    data = run_query(
        '''
        query GetBoardColumns($boardId: ID!) {
          boards(ids: [$boardId]) {
            name
            columns {
              id
              title
              type
              settings_str
            }
          }
        }
        ''',
        variables={'boardId': str(board_id)},
    )
    boards = data.get('boards') or []
    if not boards:
        raise MondayAPIError(f'Board {board_id} nao encontrado (ou sem acesso).')

    board = boards[0]
    columns = {}
    for column in board.get('columns', []):
        columns[column['id']] = {
            'title': column['title'],
            'type': column['type'],
            'colors': _label_colors_from_settings(column.get('settings_str')),
        }
    return board.get('name', ''), columns


def _format_date_text(text):
    """Converte a data/hora ISO do Monday (YYYY-MM-DD[ HH:MM:SS]) para o formato brasileiro."""
    if not text:
        return text
    date_part, _, time_part = text.partition(' ')
    pieces = date_part.split('-')
    if len(pieces) != 3:
        return text
    year, month, day = pieces
    formatted = f'{day}/{month}/{year}'
    if time_part:
        formatted += f' {time_part[:5]}'
    return formatted


def _parse_item(raw_item, columns):
    values = {}
    for cv in raw_item.get('column_values', []):
        column_id = cv['id']
        column_meta = columns.get(column_id, {})
        column_type = column_meta.get('type', cv.get('type', ''))
        text = cv.get('text') or ''
        if column_type == 'date':
            text = _format_date_text(text)
        values[column_id] = {
            'text': text,
            'type': column_type,
            'color': column_meta.get('colors', {}).get(cv.get('text') or ''),
        }

    subitems = [
        {
            'id': sub['id'],
            'name': sub['name'],
            'values': {
                cv['id']: {
                    'text': _format_date_text(cv.get('text')) if cv.get('type') == 'date' else (cv.get('text') or ''),
                    'type': cv.get('type', ''),
                }
                for cv in sub.get('column_values', [])
            },
        }
        for sub in raw_item.get('subitems', [])
    ]

    return {
        'id': raw_item['id'],
        'name': raw_item['name'],
        'values': values,
        'subitems': subitems,
    }


def get_board_action_plans(board_id, limit=100):
    """Busca todos os itens de um board do Monday, paginando via cursor."""
    board_name, columns = _fetch_board_columns(board_id)

    items = []
    cursor = None
    items_query = '''
    query GetBoardItems($boardId: ID!, $limit: Int!) {
      boards(ids: [$boardId]) {
        items_page(limit: $limit) {
          cursor
          items {
            id
            name
            column_values { id text type }
            subitems { id name column_values { id text type } }
          }
        }
      }
    }
    '''
    next_page_query = '''
    query GetNextItems($cursor: String!, $limit: Int!) {
      next_items_page(cursor: $cursor, limit: $limit) {
        cursor
        items {
          id
          name
          column_values { id text type }
          subitems { id name column_values { id text type } }
        }
      }
    }
    '''

    data = run_query(items_query, variables={'boardId': str(board_id), 'limit': limit})
    boards = data.get('boards') or []
    if not boards:
        raise MondayAPIError(f'Board {board_id} nao encontrado (ou sem acesso).')

    page = boards[0]['items_page']
    items.extend(_parse_item(raw, columns) for raw in page['items'])
    cursor = page.get('cursor')

    while cursor:
        data = run_query(next_page_query, variables={'cursor': cursor, 'limit': limit})
        page = data.get('next_items_page') or {}
        page_items = page.get('items') or []
        if not page_items:
            break
        items.extend(_parse_item(raw, columns) for raw in page_items)
        cursor = page.get('cursor')

    return {
        'board_name': board_name,
        'columns': columns,
        'items': items,
    }
