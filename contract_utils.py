# -*- coding: utf-8 -*-
"""
Общие функции для create_contract.py и create_summary.py:
загрузка и проверка JSON, даты, числа прописью, склонение, командная строка.
"""

import argparse
import copy
import json
import os
import re
import sys
from datetime import datetime

MONTHS_GEN = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня', 'июля',
              'августа', 'сентября', 'октября', 'ноября', 'декабря']

NBSP = ' '


# --------------------------------------------------------------------------
# Числа прописью и склонение
# --------------------------------------------------------------------------

_ONES = {
    'nom': ['', 'один', 'два', 'три', 'четыре', 'пять', 'шесть', 'семь', 'восемь', 'девять'],
    'gen': ['', 'одного', 'двух', 'трёх', 'четырёх', 'пяти', 'шести', 'семи', 'восьми', 'девяти'],
}
_TEENS = {
    'nom': ['десять', 'одиннадцать', 'двенадцать', 'тринадцать', 'четырнадцать', 'пятнадцать',
            'шестнадцать', 'семнадцать', 'восемнадцать', 'девятнадцать'],
    'gen': ['десяти', 'одиннадцати', 'двенадцати', 'тринадцати', 'четырнадцати', 'пятнадцати',
            'шестнадцати', 'семнадцати', 'восемнадцати', 'девятнадцати'],
}
_TENS = {
    'nom': ['', '', 'двадцать', 'тридцать', 'сорок', 'пятьдесят', 'шестьдесят', 'семьдесят',
            'восемьдесят', 'девяносто'],
    'gen': ['', '', 'двадцати', 'тридцати', 'сорока', 'пятидесяти', 'шестидесяти', 'семидесяти',
            'восьмидесяти', 'девяноста'],
}
_HUNDREDS = {
    'nom': ['', 'сто', 'двести', 'триста', 'четыреста', 'пятьсот', 'шестьсот', 'семьсот',
            'восемьсот', 'девятьсот'],
    'gen': ['', 'ста', 'двухсот', 'трёхсот', 'четырёхсот', 'пятисот', 'шестисот', 'семисот',
            'восьмисот', 'девятисот'],
}
# (падеж, род) -> форма для 1
_ONE = {('nom', 'm'): 'один', ('nom', 'f'): 'одна', ('nom', 'n'): 'одно',
        ('gen', 'm'): 'одного', ('gen', 'f'): 'одной', ('gen', 'n'): 'одного'}

MAX_NUMBER = 999999


def plural_index(n):
    """0 - форма для 1 (21, 31...), 1 - для 2-4, 2 - для остальных."""
    n = abs(n) % 100
    if 11 <= n <= 19:
        return 2
    last = n % 10
    if last == 1:
        return 0
    if 2 <= last <= 4:
        return 1
    return 2


def _below_1000(n, case, gender):
    words = []
    hundreds, rest = divmod(n, 100)
    if hundreds:
        words.append(_HUNDREDS[case][hundreds])
    if 10 <= rest < 20:
        words.append(_TEENS[case][rest - 10])
    else:
        tens, ones = divmod(rest, 10)
        if tens:
            words.append(_TENS[case][tens])
        if ones == 1:
            words.append(_ONE[(case, gender)])
        elif ones == 2 and gender == 'f' and case == 'nom':
            words.append('две')
        elif ones:
            words.append(_ONES[case][ones])
    return words


def number_to_words(n, case='nom', gender='m'):
    """
    Число прописью от 0 до 999 999.
    case: 'nom' (именительный, он же винительный для неодушевлённых) или 'gen' (родительный).
    gender: 'm', 'f', 'n' (влияет на 1 и 2).
    """
    if not isinstance(n, int) or isinstance(n, bool) or n < 0 or n > MAX_NUMBER:
        raise ValueError('Число прописью поддерживается от 0 до {}: {!r}'.format(MAX_NUMBER, n))
    if n == 0:
        return 'ноль' if case == 'nom' else 'нуля'
    thousands, rest = divmod(n, 1000)
    words = []
    if thousands:
        words += _below_1000(thousands, case, 'f')
        idx = plural_index(thousands)
        if case == 'nom':
            words.append(('тысяча', 'тысячи', 'тысяч')[idx])
        else:
            words.append('тысячи' if idx == 0 else 'тысяч')
    if rest:
        words += _below_1000(rest, case, gender)
    return ' '.join(words)


# единица: род, формы существительного в 'nom' и 'gen' (1 / 2-4 / 5+)
UNITS = {
    'day': ('m', ('день', 'дня', 'дней'), ('дня', 'дней', 'дней')),
    'cal_day': ('m', ('календарный день', 'календарных дня', 'календарных дней'),
                ('календарного дня', 'календарных дней', 'календарных дней')),
    'work_day': ('m', ('рабочий день', 'рабочих дня', 'рабочих дней'),
                 ('рабочего дня', 'рабочих дней', 'рабочих дней')),
    'month': ('m', ('месяц', 'месяца', 'месяцев'), ('месяца', 'месяцев', 'месяцев')),
    'ruble': ('m', ('рубль', 'рубля', 'рублей'), ('рубля', 'рублей', 'рублей')),
    'keys': ('m', ('комплект', 'комплекта', 'комплектов'),
             ('комплекта', 'комплектов', 'комплектов')),
    'person': ('n', ('дополнительное совершеннолетнее лицо',
                     'дополнительных совершеннолетних лица',
                     'дополнительных совершеннолетних лиц'),
               ('дополнительного совершеннолетнего лица',
                'дополнительных совершеннолетних лиц',
                'дополнительных совершеннолетних лиц')),
}


def plain(n, unit, case='nom'):
    """«5 рабочих дней»."""
    forms = UNITS[unit][1 if case == 'nom' else 2]
    return '{} {}'.format(n, forms[plural_index(n)])


def counted(n, unit, case='nom'):
    """«11 (одиннадцать) месяцев» - число, пропись и согласованное слово."""
    gender, nom, gen = UNITS[unit]
    forms = nom if case == 'nom' else gen
    return '{} ({}) {}'.format(n, number_to_words(n, case, gender), forms[plural_index(n)])


def fmt_int(n):
    """60000 -> «60 000» (неразрывный пробел)."""
    return '{:,}'.format(n).replace(',', NBSP)


def money(n):
    """«60 000 (шестьдесят тысяч) рублей»."""
    return '{} ({}) {}'.format(fmt_int(n), number_to_words(n, 'nom', 'm'),
                               UNITS['ruble'][1][plural_index(n)])


def fmt_percent(rate):
    """0.1 -> «0,1»."""
    text = ('%f' % rate).rstrip('0').rstrip('.')
    return text.replace('.', ',')


# --------------------------------------------------------------------------
# Даты и адрес
# --------------------------------------------------------------------------

DATE_FORMAT = '%d.%m.%Y'


def parse_date(value):
    return datetime.strptime(value.strip(), DATE_FORMAT)


def long_date(value):
    """«19.11.2025» -> «19 ноября 2025 г.»"""
    d = parse_date(value)
    return '{} {} {} г.'.format(d.day, MONTHS_GEN[d.month - 1], d.year)


def quoted_date(value):
    """«18.11.2025» -> ««18» ноября 2025 г.»"""
    d = parse_date(value)
    return '«{:02d}» {} {} г.'.format(d.day, MONTHS_GEN[d.month - 1], d.year)


def full_address(addr):
    """Адрес без пустых частей (корпус и этаж необязательны)."""
    parts = ['г. {}'.format(addr['city']), addr['street'], 'д. {}'.format(addr['house'])]
    if addr.get('building', '').strip():
        parts.append('корп. {}'.format(addr['building']))
    parts.append('кв. {}'.format(addr['apartment']))
    if addr.get('floor', '').strip():
        parts.append('этаж {}'.format(addr['floor']))
    return ', '.join(parts)


def inventory_items(data):
    """
    Опись имущества как список словарей {name, serial, quantity, condition}.
    Элемент описи - строка (старый формат) или объект
    {"name": ..., "serial": ..., "quantity": ..., "condition": ...};
    всё, кроме name, необязательно: serial и condition по умолчанию пустые, quantity - 1.
    """
    items = []
    for item in data['inventory']:
        if isinstance(item, str):
            item = {'name': item}
        items.append({
            'name': item['name'].strip(),
            'serial': (item.get('serial') or '').strip(),
            'quantity': item.get('quantity') or 1,
            'condition': (item.get('condition') or '').strip(),
        })
    return items


def blank(value, length=30):
    """Пустое значение -> линия для заполнения от руки."""
    value = (value or '').strip()
    return value if value else '_' * length


# --------------------------------------------------------------------------
# Проверка данных
# --------------------------------------------------------------------------

class ValidationError(Exception):
    def __init__(self, errors):
        super().__init__('\n'.join(errors))
        self.errors = errors


_PLACEHOLDER_EXACT = {
    'СЕРИЯ', 'НОМЕР', 'КЕМ ВЫДАН', 'АДРЕС РЕГИСТРАЦИИ', 'ГОРОД', 'УЛИЦА', 'ДОМ', 'КОРПУС',
    'КВАРТИРА', 'ЭТАЖ', 'ПЛОЩАДЬ', 'БИК', 'НАЗВАНИЕ БАНКА', 'КОРР. СЧЕТ', 'ИНН', 'КПП',
    'НОМЕР СЧЕТА', 'НОМЕР СЧЕТЧИКА', 'ПОКАЗАНИЯ',
}
_PLACEHOLDER_PARTS = ('DD.MM.YYYY', 'DD МЕСЯЦ', 'XXX', 'НАИМЕНОВАНИЕ ИМУЩЕСТВА',
                      'НОМЕР_ДОГОВОРА', 'ФАМИЛИЯ ИМЯ ОТЧЕСТВО', 'email@example.com')

_MISSING = object()


def is_placeholder(value):
    value = value.strip()
    return value in _PLACEHOLDER_EXACT or any(p in value for p in _PLACEHOLDER_PARTS)


def _get(data, path):
    cur = data
    for key in path.split('.'):
        if not isinstance(cur, dict) or key not in cur:
            return _MISSING
        cur = cur[key]
    return cur


def _is_int(v):
    return isinstance(v, int) and not isinstance(v, bool)


def _walk_strings(node, path=''):
    if isinstance(node, dict):
        for k, v in node.items():
            yield from _walk_strings(v, '{}.{}'.format(path, k) if path else k)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from _walk_strings(v, '{}[{}]'.format(path, i))
    elif isinstance(node, str):
        yield path, node


# обязательные непустые строки
_REQ_STR = [
    'landlord.full_name', 'tenant.full_name', 'property.type', 'property.address.city',
    'property.address.street', 'property.address.house', 'property.address.apartment',
    'property.cadastral_number', 'property.area', 'property.ownership',
    'bank_details.recipient', 'bank_details.bank_name', 'financial.sbp_phone',
    'rules.meters_submission_time',
    'meters.electricity.date', 'meters.cold_water.date', 'meters.hot_water.date',
]
# необязательные строки: пустое значение превращается в линию для заполнения от руки
_OPT_STR = [
    'landlord.passport_series', 'landlord.passport_number', 'landlord.passport_issued_by',
    'landlord.passport_issued_date', 'landlord.registration_address', 'landlord.phone',
    'landlord.email', 'tenant.date_of_birth', 'tenant.passport_series',
    'tenant.passport_number', 'tenant.passport_issued_by', 'tenant.passport_issued_date',
    'tenant.registration_address', 'tenant.phone', 'tenant.email',
    'property.address.building', 'property.address.floor', 'bank_details.payment_purpose',
    'meters.electricity.number', 'meters.electricity.reading',
    'meters.cold_water.number', 'meters.cold_water.reading',
    'meters.hot_water.number', 'meters.hot_water.reading',
]
_REQ_DATES = ['contract.conclusion_date', 'contract.start_date',
              'financial.first_payment_deadline', 'financial.deposit_deadline']
_REQ_POSINT = ['contract.duration_months', 'contract.keys_count', 'rules.max_additional_residents',
               'rules.notification_days_for_residents', 'rules.utility_payment_days',
               'rules.termination_notice_days', 'rules.eviction_days', 'rules.deposit_return_days']
_REQ_DAY_OF_MONTH = ['financial.payment_period_start', 'financial.payment_period_end',
                     'rules.meters_submission_day']
# поле -> допустимая длина цифровой строки
_DIGITS = {'bank_details.account_number': (20,), 'bank_details.bik': (9,),
           'bank_details.correspondent_account': (20,), 'bank_details.inn': (10, 12)}
_OPT_POSINT = ['contract.prolongation_months', 'rules.prolongation_notice_days',
               'rules.indexation_notice_days']


def validate(data):
    """Возвращает список ошибок (пустой, если данные корректны)."""
    errors = []

    if not isinstance(data, dict):
        return ['Корень JSON должен быть объектом']

    def err(path, msg):
        errors.append('{}: {}'.format(path, msg))

    for path in _REQ_STR + _OPT_STR + list(_DIGITS) + ['bank_details.kpp']:
        v = _get(data, path)
        required = path in _REQ_STR or path in _DIGITS
        if v is _MISSING:
            if required or path in _OPT_STR:
                err(path, 'поле отсутствует')
        elif not isinstance(v, str):
            err(path, 'ожидается строка')
        elif required and not v.strip():
            err(path, 'поле не заполнено')

    for path in _REQ_DATES:
        v = _get(data, path)
        if v is _MISSING:
            err(path, 'поле отсутствует')
        elif not isinstance(v, str):
            err(path, 'ожидается дата в формате ДД.ММ.ГГГГ')
        elif not is_placeholder(v):
            try:
                parse_date(v)
            except ValueError:
                err(path, 'ожидается дата в формате ДД.ММ.ГГГГ, получено {!r}'.format(v))

    for path in _REQ_POSINT + _OPT_POSINT:
        v = _get(data, path)
        if v is _MISSING:
            if path in _REQ_POSINT:
                err(path, 'поле отсутствует')
        elif not _is_int(v) or v < 1 or v > 999:
            err(path, 'ожидается целое число от 1 до 999, получено {!r}'.format(v))

    for path in _REQ_DAY_OF_MONTH:
        v = _get(data, path)
        if v is _MISSING:
            err(path, 'поле отсутствует')
        elif not _is_int(v) or not 1 <= v <= 31:
            err(path, 'ожидается число месяца от 1 до 31, получено {!r}'.format(v))

    start, end = _get(data, 'financial.payment_period_start'), _get(data, 'financial.payment_period_end')
    if _is_int(start) and _is_int(end) and start > end:
        err('financial.payment_period_start', 'не может быть больше payment_period_end')

    for path in ('financial.monthly_rent', 'financial.security_deposit'):
        v = _get(data, path)
        if v is _MISSING:
            err(path, 'поле отсутствует')
        elif not _is_int(v) or not 1 <= v <= MAX_NUMBER:
            err(path, 'ожидается целое число рублей от 1 до {}, получено {!r}'.format(MAX_NUMBER, v))

    v = _get(data, 'financial.penalty_rate')
    if v is _MISSING:
        err('financial.penalty_rate', 'поле отсутствует')
    elif isinstance(v, bool) or not isinstance(v, (int, float)) or not 0 < v <= 100:
        err('financial.penalty_rate', 'ожидается число процентов в день больше 0, получено {!r}'.format(v))

    for path, lengths in _DIGITS.items():
        v = _get(data, path)
        if isinstance(v, str) and v.strip() and not is_placeholder(v):
            if not (v.isdigit() and len(v) in lengths):
                err(path, 'ожидается {} цифр, получено {!r}'.format(
                    ' или '.join(str(n) for n in lengths), v))
    kpp = _get(data, 'bank_details.kpp')
    if isinstance(kpp, str) and kpp.strip() and not is_placeholder(kpp):
        if not (kpp.isdigit() and len(kpp) == 9):
            err('bank_details.kpp', 'ожидается 9 цифр или пустое значение, получено {!r}'.format(kpp))

    phone = _get(data, 'financial.sbp_phone')
    if isinstance(phone, str) and not is_placeholder(phone):
        if len(re.sub(r'\D', '', phone)) < 10:
            err('financial.sbp_phone', 'ожидается номер телефона, получено {!r}'.format(phone))

    flag = _get(data, 'rules.animals_allowed_by_default')
    if flag is not _MISSING and not isinstance(flag, bool):
        err('rules.animals_allowed_by_default', 'ожидается true или false')

    inv = _get(data, 'inventory')
    if inv is _MISSING:
        err('inventory', 'поле отсутствует')
    elif not isinstance(inv, list):
        err('inventory', 'ожидается список предметов (может быть пустым)')
    else:
        for i, item in enumerate(inv):
            path = 'inventory[{}]'.format(i)
            if isinstance(item, str):
                if not item.strip():
                    err(path, 'пустое наименование')
            elif isinstance(item, dict):
                name = item.get('name')
                if not isinstance(name, str) or not name.strip():
                    err(path + '.name', 'ожидается непустая строка')
                for key in ('serial', 'condition'):
                    v = item.get(key)
                    if v is not None and not isinstance(v, str):
                        err('{}.{}'.format(path, key), 'ожидается строка или пустое значение')
                qty = item.get('quantity')
                if qty is not None and not (_is_int(qty) and qty >= 1):
                    err(path + '.quantity', 'ожидается целое число не меньше 1')
                extra = set(item) - {'name', 'serial', 'quantity', 'condition'}
                if extra:
                    err(path, 'неизвестные поля: {}'.format(', '.join(sorted(extra))))
            else:
                err(path, 'ожидается строка или объект {"name": ..., "serial": ...}')

    city = _get(data, 'contract.conclusion_city')
    if city is not _MISSING and city is not None and not isinstance(city, str):
        err('contract.conclusion_city', 'ожидается строка или пустое значение')

    for path, value in _walk_strings(data):
        if is_placeholder(value):
            err(path, 'не заменена заглушка шаблона ({!r})'.format(value))

    return errors


def with_defaults(data):
    """Копия данных с необязательными параметрами по умолчанию."""
    data = copy.deepcopy(data)
    data['contract'].setdefault('prolongation_months', data['contract']['duration_months'])
    # место заключения: если не указано, город квартиры
    if not (data['contract'].get('conclusion_city') or '').strip():
        data['contract']['conclusion_city'] = data['property']['address']['city']
    rules = data['rules']
    rules.setdefault('prolongation_notice_days', rules['termination_notice_days'])
    rules.setdefault('indexation_notice_days', rules['termination_notice_days'])
    rules.setdefault('animals_allowed_by_default', False)
    return data


def load_contract_data(filename='contract_data.json'):
    """Читает JSON, проверяет его и возвращает данные с параметрами по умолчанию."""
    with open(filename, 'r', encoding='utf-8') as f:
        data = json.load(f)
    errors = validate(data)
    if errors:
        raise ValidationError(errors)
    return with_defaults(data)


# --------------------------------------------------------------------------
# Командная строка
# --------------------------------------------------------------------------

def run_cli(description, out_dir, file_prefix, build, argv=None):
    """Общая точка входа: --data, --check, --output. Возвращает код выхода."""
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('--data', default='contract_data.json',
                        help='файл с данными (по умолчанию contract_data.json)')
    parser.add_argument('--check', action='store_true',
                        help='только проверить данные, ничего не создавать')
    parser.add_argument('-o', '--output', help='путь к создаваемому файлу')
    args = parser.parse_args(argv)

    try:
        data = load_contract_data(args.data)
    except FileNotFoundError:
        print('Файл данных не найден: {}. Создайте его из contract_data.template.json'.format(args.data),
              file=sys.stderr)
        return 1
    except json.JSONDecodeError as e:
        print('Некорректный JSON в {}: {}'.format(args.data, e), file=sys.stderr)
        return 1
    except ValidationError as e:
        print('Ошибки в {}:'.format(args.data), file=sys.stderr)
        for line in e.errors:
            print('  - ' + line, file=sys.stderr)
        return 1

    if args.check:
        print('Данные корректны: {}'.format(args.data))
        return 0

    if args.output:
        output = args.output
    else:
        stamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        output = os.path.join(out_dir, '{}{}.docx'.format(file_prefix, stamp))
    folder = os.path.dirname(output)
    if folder:
        os.makedirs(folder, exist_ok=True)
    build(data, output)
    print('Создан файл: {}'.format(output))
    return 0
