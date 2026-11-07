#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для создания сводки по договору аренды в формате DOCX.

Запуск:
    python3 create_summary.py [--data contract_data.json] [--check] [-o файл.docx]
"""

import sys
from datetime import datetime

from contract_utils import (
    blank, fmt_int, fmt_percent, full_address, inventory_items, load_contract_data, plain, run_cli)
from docx_builder import paragraph, table, write_docx

__all__ = ['load_contract_data', 'create_summary_body', 'create_docx']


def create_summary_body(data):
    """Создает тело сводки (XML). Все значения берутся из data."""
    body = []

    def p(text='', **kw):
        body.append(paragraph(text, **kw))

    def gap():
        body.append(paragraph('', size=24))

    def t(rows):
        body.append(table(rows, font_size=20))

    landlord = data['landlord']
    tenant = data['tenant']
    prop = data['property']
    financial = data['financial']
    bank = data['bank_details']
    contract = data['contract']
    rules = data['rules']

    rent = fmt_int(financial['monthly_rent'])
    deposit = fmt_int(financial['security_deposit'])
    prolong_notice = plain(rules['prolongation_notice_days'], 'day')
    index_notice = plain(rules['indexation_notice_days'], 'day')
    termination_notice = plain(rules['termination_notice_days'], 'day')
    deposit_return = plain(rules['deposit_return_days'], 'day')
    utility_days = plain(rules['utility_payment_days'], 'work_day')
    resident_notice = plain(rules['notification_days_for_residents'], 'day')
    eviction = plain(rules['eviction_days'], 'day')
    residents = plain(rules['max_additional_residents'], 'person')

    p('СВОДКА ПО ДОГОВОРУ АРЕНДЫ КВАРТИРЫ', bold=True, align='center', size=32)
    gap()

    # ОСНОВНАЯ ИНФОРМАЦИЯ
    p('ОСНОВНАЯ ИНФОРМАЦИЯ', bold=True, size=28)
    gap()
    p('СТОРОНЫ:', bold=True, size=26)
    t([
        ['АРЕНДОДАТЕЛЬ:', 'АРЕНДАТОР:'],
        [landlord['full_name'], tenant['full_name']],
        ['Телефон: {}'.format(blank(landlord['phone'], 20)),
         'Дата рождения: {}'.format(blank(tenant['date_of_birth'], 12))],
        ['Email: {}'.format(blank(landlord['email'], 20)),
         'Паспорт: серия {} № {}'.format(blank(tenant['passport_series'], 6),
                                         blank(tenant['passport_number'], 8))],
    ])
    gap()

    p('ОБЪЕКТ АРЕНДЫ:', bold=True, size=26)
    t([
        ['Адрес:', full_address(prop['address'])],
        ['Кадастровый номер:', prop['cadastral_number']],
        ['Площадь:', '{} м2'.format(prop['area'])],
        ['Статус:', 'Принадлежит Арендодателю на праве {}'.format(prop['ownership'])],
    ])
    gap()

    # ФИНАНСОВЫЕ УСЛОВИЯ
    p('ФИНАНСОВЫЕ УСЛОВИЯ', bold=True, size=28)
    gap()
    t([
        ['Арендная плата:', '{} рублей в месяц'.format(rent)],
        ['Срок оплаты:', 'с {} по {} число каждого месяца'.format(
            financial['payment_period_start'], financial['payment_period_end'])],
        ['Первый платеж:', 'не позднее {}'.format(financial['first_payment_deadline'])],
        ['Залог:', '{} рублей (возврат в течение {} после возврата квартиры)'.format(
            deposit, deposit_return)],
        ['Срок внесения залога:', 'не позднее {}'.format(financial['deposit_deadline'])],
        ['Штраф за просрочку:', '{}% от суммы задолженности за каждый день'.format(
            fmt_percent(financial['penalty_rate']))],
    ])
    gap()

    p('СПОСОБЫ ОПЛАТЫ:', bold=True, size=26)
    p('1. СБП по номеру телефона: {}'.format(financial['sbp_phone']), size=22)
    p('2. Банковский перевод на счет {}: {}'.format(bank['bank_name'], bank['account_number']), size=22)
    gap()

    # СРОКИ
    p('СРОКИ И УСЛОВИЯ ДЕЙСТВИЯ ДОГОВОРА', bold=True, size=28)
    gap()
    t([
        ['Дата заключения:', contract['conclusion_date']],
        ['Место заключения:', 'г. {}'.format(contract['conclusion_city'])],
        ['Начало аренды:', contract['start_date']],
        ['Длительность:', plain(contract['duration_months'], 'month')],
        ['Передача ключей:', 'не позднее {} ({})'.format(
            contract['start_date'], plain(contract['keys_count'], 'keys'))],
    ])
    gap()

    p('АВТОМАТИЧЕСКАЯ ПРОЛОНГАЦИЯ:', bold=True, size=26)
    p('Договор автоматически продлевается на новый срок {}, если ни одна из Сторон не уведомит другую за {} до окончания срока.'.format(
        plain(contract['prolongation_months'], 'month'), prolong_notice), size=22)
    gap()

    p('ИНДЕКСАЦИЯ АРЕНДНОЙ ПЛАТЫ:', bold=True, size=26)
    p('При пролонгации размер арендной платы может быть увеличен, но не более чем на уровень официальной инфляции (по данным Росстат). Уведомление за {}.'.format(index_notice), size=22)
    gap()

    # ПРАВИЛА ПРОЖИВАНИЯ
    p('ПРАВИЛА ПРОЖИВАНИЯ', bold=True, size=28)
    gap()
    p('КТО МОЖЕТ ПРОЖИВАТЬ:', bold=True, size=26)
    p('- Основной: Арендатор ({})'.format(tenant['full_name']), size=22)
    p('- Дополнительно: {} (письменное уведомление за {})'.format(residents, resident_notice), size=22)
    p('- Гости: только в присутствии Арендатора', size=22)
    gap()

    p('ДОМАШНИЕ ЖИВОТНЫЕ:', bold=True, size=26)
    if rules['animals_allowed_by_default']:
        p('РАЗРЕШЕНО. Арендатор несет полную ответственность за ущерб, нанесенный животными.', size=22)
    else:
        p('ЗАПРЕЩЕНО. Возможно разрешение по письменному согласованию (отдельное дополнительное соглашение).', size=22)
    gap()

    p('ИСПОЛЬЗОВАНИЕ ПОМЕЩЕНИЯ:', bold=True, size=26)
    p('РАЗРЕШЕНО: Только для проживания', size=22)
    p('ЗАПРЕЩЕНО: Субаренда, коммерческая деятельность, офис, перепланировка без согласия', size=22)
    gap()

    # КОММУНАЛЬНЫЕ ПЛАТЕЖИ
    p('КОММУНАЛЬНЫЕ ПЛАТЕЖИ', bold=True, size=28)
    gap()
    p('ВИДЫ УСЛУГ:', bold=True, size=26)
    p('Электроэнергия, холодная и горячая вода, водоотведение, отопление, эксплуатационные расходы.', size=22)
    gap()

    p('ПЕРЕДАЧА ПОКАЗАНИЙ СЧЕТЧИКОВ:', bold=True, size=26)
    t([
        ['Срок:', '{} числа каждого месяца до {}'.format(
            rules['meters_submission_day'], rules['meters_submission_time'])],
        ['Счетчики:', 'Электроэнергия, холодная вода, горячая вода'],
        ['Способы:', 'Мессенджеры, email, SMS'],
        ['Исключение:', 'При отсутствии - среднее потребление с перерасчетом'],
    ])
    gap()

    p('ПОРЯДОК ОПЛАТЫ КОММУНАЛЬНЫХ:', bold=True, size=26)
    p('1. Арендодатель информирует о сумме (мессенджеры/email/телефон)', size=22)
    p('2. Арендатор оплачивает отдельным платежом на счет Арендодателя', size=22)
    p('3. Срок оплаты: {} с момента получения информации'.format(utility_days), size=22)
    gap()

    # УСЛОВИЯ РАСТОРЖЕНИЯ
    p('УСЛОВИЯ РАСТОРЖЕНИЯ ДОГОВОРА', bold=True, size=28)
    gap()
    t([
        ['По соглашению сторон:', 'В любое время письменным соглашением'],
        ['По инициативе любой стороны:', 'Уведомление за {}'.format(termination_notice)],
        ['Досрочное расторжение (Арендодатель):', '1. Просрочка оплаты 2+ раз подряд'],
        ['', '2. Использование не по назначению'],
        ['', '3. Существенное нарушение условий'],
        ['Срок освобождения:', '{} с момента уведомления'.format(eviction)],
    ])
    gap()

    # ВАЖНЫЕ ДАТЫ
    p('ВАЖНЫЕ ДАТЫ И СРОКИ', bold=True, size=28)
    gap()
    t([
        ['Дата / Период', 'Событие / Действие'],
        [contract['conclusion_date'], 'Дата заключения договора'],
        [contract['start_date'], 'Начало аренды, передача ключей'],
        [financial['first_payment_deadline'], 'Крайний срок оплаты первого месяца'],
        [financial['deposit_deadline'], 'Крайний срок внесения залога'],
        ['{} число до {}'.format(rules['meters_submission_day'], rules['meters_submission_time']),
         'Передача показаний счетчиков'],
        ['{}-{} число'.format(financial['payment_period_start'], financial['payment_period_end']),
         'Период оплаты арендной платы ({} руб)'.format(rent)],
        [utility_days, 'Оплата коммунальных платежей (после уведомления)'],
        ['За {}'.format(termination_notice), 'Уведомление о расторжении'],
        ['За {}'.format(prolong_notice), 'Уведомление о продлении'],
        ['За {}'.format(resident_notice), 'Уведомление о вселении доп. лица'],
        [eviction, 'Освобождение при досрочном расторжении'],
        [deposit_return, 'Возврат залога после возврата квартиры'],
    ])
    gap()

    # ПРИЛОЖЕНИЯ
    p('ПРИЛОЖЕНИЯ К ДОГОВОРУ', bold=True, size=28)
    gap()
    p('ПРИЛОЖЕНИЕ № 1: ОПИСЬ ИМУЩЕСТВА', bold=True, size=26)
    items = inventory_items(data)
    for i, item in enumerate(items, 1):
        parts = [item['name']]
        if item['serial']:
            parts.append('с/н {}'.format(item['serial']))
        if item['quantity'] > 1:
            parts.append('{} шт.'.format(item['quantity']))
        if item['condition']:
            parts.append(item['condition'])
        p('{}. {}'.format(i, ', '.join(parts)), size=22)
    p('{}. (Дополнительные позиции заполняются при приемке)'.format(len(items) + 1), size=22)
    gap()

    p('ПРИЛОЖЕНИЕ № 2: ПОКАЗАНИЯ СЧЕТЧИКОВ', bold=True, size=26)
    p('Показания на дату передачи помещения ({})'.format(contract['start_date']), size=22)
    meters = data['meters']

    def meter_row(title, key):
        m = meters[key]
        return [title, m['reading'].strip() or '(заполнить)', m['date']]

    t([
        ['Счетчик', 'Показания', 'Дата'],
        meter_row('Электроэнергия', 'electricity'),
        meter_row('Холодная вода', 'cold_water'),
        meter_row('Горячая вода', 'hot_water'),
    ])
    gap()

    gap()
    stamp = datetime.now().strftime('%d.%m.%Y %H:%M:%S')
    p('Дата создания сводки: {}'.format(stamp), align='center', size=20)

    return ''.join(body)


def create_docx(filename, data_file='contract_data.json'):
    """Создает DOCX файл со сводкой"""
    data = load_contract_data(data_file)
    _build(data, filename)


def _build(data, filename):
    write_docx(filename, create_summary_body(data), title='Сводка по договору аренды')


if __name__ == '__main__':
    sys.exit(run_cli('Создает сводку по договору аренды в формате DOCX',
                     'doc/summary', 'СВОДКА_ДОГОВОРА_v', _build))
