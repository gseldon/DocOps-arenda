#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для создания сводки по договору аренды в формате DOCX
"""

import zipfile
import os
import json
from datetime import datetime
import shutil
import tempfile

def load_contract_data(filename='contract_data.json'):
    """Загружает данные договора из JSON файла"""
    with open(filename, 'r', encoding='utf-8') as f:
        return json.load(f)

def create_paragraph(text, bold=False, align='both', size=24):
    """Создает параграф с текстом"""
    bold_tag = '<w:b/>' if bold else ''
    align_map = {'left': 'left', 'center': 'center', 'right': 'right', 'both': 'both'}
    jc = align_map.get(align, 'both')
    
    return f'''<w:p>
<w:pPr>
<w:jc w:val="{jc}"/>
<w:rPr>
{bold_tag}
<w:sz w:val="{size}"/>
<w:szCs w:val="{size}"/>
</w:rPr>
</w:pPr>
<w:r>
<w:rPr>
{bold_tag}
<w:sz w:val="{size}"/>
<w:szCs w:val="{size}"/>
</w:rPr>
<w:t xml:space="preserve">{text}</w:t>
</w:r>
</w:p>'''

def create_table_row(cells, font_size=20):
    """Создает строку таблицы"""
    cells_xml = ''
    for cell in cells:
        cells_xml += f'''<w:tc>
<w:tcPr>
<w:tcBorders>
<w:top w:val="single" w:sz="4" w:space="0" w:color="000000"/>
<w:left w:val="single" w:sz="4" w:space="0" w:color="000000"/>
<w:bottom w:val="single" w:sz="4" w:space="0" w:color="000000"/>
<w:right w:val="single" w:sz="4" w:space="0" w:color="000000"/>
</w:tcBorders>
</w:tcPr>
<w:p>
<w:r>
<w:rPr>
<w:sz w:val="{font_size}"/>
<w:szCs w:val="{font_size}"/>
</w:rPr>
<w:t xml:space="preserve">{cell}</w:t>
</w:r>
</w:p>
</w:tc>'''
    
    return f'<w:tr>{cells_xml}</w:tr>'

def create_table(rows, font_size=20):
    """Создает таблицу"""
    rows_xml = ''.join([create_table_row(row, font_size) for row in rows])
    return f'''<w:tbl>
<w:tblPr>
<w:tblW w:w="5000" w:type="pct"/>
<w:tblBorders>
<w:top w:val="single" w:sz="4" w:space="0" w:color="000000"/>
<w:left w:val="single" w:sz="4" w:space="0" w:color="000000"/>
<w:bottom w:val="single" w:sz="4" w:space="0" w:color="000000"/>
<w:right w:val="single" w:sz="4" w:space="0" w:color="000000"/>
<w:insideH w:val="single" w:sz="4" w:space="0" w:color="000000"/>
<w:insideV w:val="single" w:sz="4" w:space="0" w:color="000000"/>
</w:tblBorders>
</w:tblPr>
{rows_xml}
</w:tbl>'''

def create_docx_structure():
    """Создает базовую XML структуру для DOCX"""
    document_xml = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
<w:body>
{body}
<w:sectPr>
<w:pgSz w:w="11906" w:h="16838"/>
<w:pgMar w:top="1134" w:right="850" w:bottom="1134" w:left="1701" w:header="708" w:footer="708" w:gutter="0"/>
<w:cols w:space="708"/>
<w:docGrid w:linePitch="360"/>
<w:footerReference w:type="default" r:id="rId1"/>
</w:sectPr>
</w:body>
</w:document>'''
    return document_xml

def create_summary_body(data):
    """Создает тело сводки"""
    body = []
    
    # Извлекаем данные
    landlord = data['landlord']
    tenant = data['tenant']
    prop = data['property']
    addr = prop['address']
    financial = data['financial']
    contract = data['contract']
    rules = data['rules']
    
    full_address = f'г. {addr["city"]}, {addr["street"]}, д. {addr["house"]}, корп. {addr["building"]}, кв. {addr["apartment"]}, этаж {addr["floor"]}'
    
    # Заголовок
    body.append(create_paragraph('СВОДКА ПО ДОГОВОРУ АРЕНДЫ КВАРТИРЫ', bold=True, align='center', size=32))
    body.append(create_paragraph('', size=24))
    
    # ОСНОВНАЯ ИНФОРМАЦИЯ
    body.append(create_paragraph('ОСНОВНАЯ ИНФОРМАЦИЯ', bold=True, size=28))
    body.append(create_paragraph('', size=24))
    
    body.append(create_paragraph('СТОРОНЫ:', bold=True, size=26))
    
    parties_info = [
        ['АРЕНДОДАТЕЛЬ:', 'АРЕНДАТОР:'],
        [landlord['full_name'], tenant['full_name']],
        [f'Телефон: {landlord["phone"]}', f'Дата рождения: {tenant["date_of_birth"]}'],
        [f'Email: {landlord["email"]}', f'Паспорт: серия {tenant["passport_series"]} № {tenant["passport_number"]}'],
    ]
    body.append(create_table(parties_info, font_size=20))
    body.append(create_paragraph('', size=24))
    
    body.append(create_paragraph('ОБЪЕКТ АРЕНДЫ:', bold=True, size=26))
    
    property_info = [
        ['Адрес:', full_address],
        ['Кадастровый номер:', prop['cadastral_number']],
        ['Площадь:', f'{prop["area"]} м2'],
        ['Статус:', f'{prop["ownership"].capitalize()} Арендодателя'],
    ]
    body.append(create_table(property_info, font_size=20))
    body.append(create_paragraph('', size=24))
    
    # ФИНАНСОВЫЕ УСЛОВИЯ
    body.append(create_paragraph('ФИНАНСОВЫЕ УСЛОВИЯ', bold=True, size=28))
    body.append(create_paragraph('', size=24))
    
    financial_info = [
        ['Арендная плата:', f'{financial["monthly_rent"]:,} рублей в месяц'.replace(',', ' ')],
        ['Срок оплаты:', f'с {financial["payment_period_start"]} по {financial["payment_period_end"]} число каждого месяца'],
        ['Первый платеж:', f'не позднее {financial["first_payment_deadline"]}'],
        ['Залог:', f'{financial["security_deposit"]:,} рублей (возврат в течение {rules["deposit_return_days"]} дней после возврата квартиры)'.replace(',', ' ')],
        ['Штраф за просрочку:', f'{financial["penalty_rate"]}% от суммы задолженности за каждый день'],
    ]
    body.append(create_table(financial_info, font_size=20))
    body.append(create_paragraph('', size=24))
    
    body.append(create_paragraph('СПОСОБЫ ОПЛАТЫ:', bold=True, size=26))
    body.append(create_paragraph(f'1. СБП по номеру телефона: {financial["sbp_phone"]}', size=22))
    body.append(create_paragraph(f'2. Банковский перевод на счет Т-Банк: {data["bank_details"]["account_number"]}', size=22))
    body.append(create_paragraph('', size=24))
    
    # СРОКИ
    body.append(create_paragraph('СРОКИ И УСЛОВИЯ ДЕЙСТВИЯ ДОГОВОРА', bold=True, size=28))
    body.append(create_paragraph('', size=24))
    
    dates_info = [
        ['Дата заключения:', contract['conclusion_date']],
        ['Начало аренды:', contract['start_date']],
        ['Длительность:', f'{contract["duration_months"]} месяцев'],
        ['Передача ключей:', f'не позднее {contract["start_date"]} ({contract["keys_count"]} комплект)'],
    ]
    body.append(create_table(dates_info, font_size=20))
    body.append(create_paragraph('', size=24))
    
    body.append(create_paragraph('АВТОМАТИЧЕСКАЯ ПРОЛОНГАЦИЯ:', bold=True, size=26))
    body.append(create_paragraph(f'Договор автоматически продлевается на новый срок {contract["duration_months"]} месяцев, если ни одна из Сторон не уведомит другую за {rules["termination_notice_days"]} дней до окончания срока.', size=22))
    body.append(create_paragraph('', size=24))
    
    body.append(create_paragraph('ИНДЕКСАЦИЯ АРЕНДНОЙ ПЛАТЫ:', bold=True, size=26))
    body.append(create_paragraph(f'При пролонгации размер арендной платы может быть увеличен, но не более чем на уровень официальной инфляции (по данным Росстат). Уведомление за {rules["termination_notice_days"]} дней.', size=22))
    body.append(create_paragraph('', size=24))
    
    # ПРАВИЛА ПРОЖИВАНИЯ
    body.append(create_paragraph('ПРАВИЛА ПРОЖИВАНИЯ', bold=True, size=28))
    body.append(create_paragraph('', size=24))
    
    body.append(create_paragraph('КТО МОЖЕТ ПРОЖИВАТЬ:', bold=True, size=26))
    body.append(create_paragraph(f'- Основной: Арендатор ({tenant["full_name"]})', size=22))
    body.append(create_paragraph(f'- Дополнительно: {rules["max_additional_residents"]} совершеннолетнее лицо (письменное уведомление за {rules["notification_days_for_residents"]} дня)', size=22))
    body.append(create_paragraph('- Гости: только в присутствии Арендатора', size=22))
    body.append(create_paragraph('', size=24))
    
    body.append(create_paragraph('ДОМАШНИЕ ЖИВОТНЫЕ:', bold=True, size=26))
    body.append(create_paragraph('ЗАПРЕЩЕНО. Возможно разрешение по письменному согласованию (отдельное дополнительное соглашение).', size=22))
    body.append(create_paragraph('', size=24))
    
    body.append(create_paragraph('ИСПОЛЬЗОВАНИЕ ПОМЕЩЕНИЯ:', bold=True, size=26))
    body.append(create_paragraph('РАЗРЕШЕНО: Только для проживания', size=22))
    body.append(create_paragraph('ЗАПРЕЩЕНО: Субаренда, коммерческая деятельность, офис, перепланировка без согласия', size=22))
    body.append(create_paragraph('', size=24))
    
    # КОММУНАЛЬНЫЕ ПЛАТЕЖИ
    body.append(create_paragraph('КОММУНАЛЬНЫЕ ПЛАТЕЖИ', bold=True, size=28))
    body.append(create_paragraph('', size=24))
    
    body.append(create_paragraph('ВИДЫ УСЛУГ:', bold=True, size=26))
    body.append(create_paragraph('Электроэнергия, холодная и горячая вода, водоотведение, отопление, эксплуатационные расходы.', size=22))
    body.append(create_paragraph('', size=24))
    
    body.append(create_paragraph('ПЕРЕДАЧА ПОКАЗАНИЙ СЧЕТЧИКОВ:', bold=True, size=26))
    
    meters_info = [
        ['Срок:', f'{rules["meters_submission_day"]} числа каждого месяца до {rules["meters_submission_time"]}'],
        ['Счетчики:', 'Электроэнергия, холодная вода, горячая вода (газа нет)'],
        ['Способы:', 'Мессенджеры, email, SMS'],
        ['Исключение:', 'При отсутствии - среднее потребление с перерасчетом'],
    ]
    body.append(create_table(meters_info, font_size=20))
    body.append(create_paragraph('', size=24))
    
    body.append(create_paragraph('ПОРЯДОК ОПЛАТЫ КОММУНАЛЬНЫХ:', bold=True, size=26))
    body.append(create_paragraph('1. Арендодатель информирует о сумме (мессенджеры/email/телефон)', size=22))
    body.append(create_paragraph('2. Арендатор оплачивает отдельным платежом на счет Арендодателя', size=22))
    body.append(create_paragraph(f'3. Срок оплаты: {rules["utility_payment_days"]} рабочих дней с момента получения информации', size=22))
    body.append(create_paragraph('', size=24))
    
    # УСЛОВИЯ РАСТОРЖЕНИЯ
    body.append(create_paragraph('УСЛОВИЯ РАСТОРЖЕНИЯ ДОГОВОРА', bold=True, size=28))
    body.append(create_paragraph('', size=24))
    
    termination_info = [
        ['По соглашению сторон:', 'В любое время письменным соглашением'],
        ['По инициативе любой стороны:', f'Уведомление за {rules["termination_notice_days"]} дней'],
        ['Досрочное расторжение (Арендодатель):', '1. Просрочка оплаты 2+ раз подряд'],
        ['', '2. Использование не по назначению'],
        ['', '3. Существенное нарушение условий'],
        ['Срок освобождения:', f'{rules["eviction_days"]} дней с момента уведомления'],
    ]
    body.append(create_table(termination_info, font_size=20))
    body.append(create_paragraph('', size=24))
    
    # ВАЖНЫЕ ДАТЫ
    body.append(create_paragraph('ВАЖНЫЕ ДАТЫ И СРОКИ', bold=True, size=28))
    body.append(create_paragraph('', size=24))
    
    important_dates = [
        ['Дата / Период', 'Событие / Действие'],
        [contract['conclusion_date'], 'Дата заключения договора'],
        [contract['start_date'], 'Начало аренды, передача ключей'],
        [financial['first_payment_deadline'], 'Крайний срок оплаты первого месяца + залога'],
        [f'{rules["meters_submission_day"]} число до {rules["meters_submission_time"]}', 'Передача показаний счетчиков'],
        [f'{financial["payment_period_start"]}-{financial["payment_period_end"]} число', f'Период оплаты арендной платы ({financial["monthly_rent"]:,} руб)'.replace(',', ' ')],
        [f'{rules["utility_payment_days"]} рабочих дней', 'Оплата коммунальных платежей (после уведомления)'],
        [f'За {rules["termination_notice_days"]} дней', 'Уведомление о расторжении/продлении'],
        [f'За {rules["notification_days_for_residents"]} дня', 'Уведомление о вселении доп. лица'],
        [f'{rules["eviction_days"]} дней', 'Освобождение при досрочном расторжении'],
        [f'{rules["deposit_return_days"]} дней', 'Возврат залога после возврата квартиры'],
    ]
    body.append(create_table(important_dates, font_size=20))
    body.append(create_paragraph('', size=24))
    
    # ПРИЛОЖЕНИЯ
    body.append(create_paragraph('ПРИЛОЖЕНИЯ К ДОГОВОРУ', bold=True, size=28))
    body.append(create_paragraph('', size=24))
    
    body.append(create_paragraph('ПРИЛОЖЕНИЕ № 1: ОПИСЬ ИМУЩЕСТВА', bold=True, size=26))
    for i, item in enumerate(data['inventory'], 1):
        body.append(create_paragraph(f'{i}. {item}', size=22))
    body.append(create_paragraph(f'{len(data["inventory"]) + 1}. (Дополнительные позиции заполняются при приемке)', size=22))
    body.append(create_paragraph('', size=24))
    
    body.append(create_paragraph('ПРИЛОЖЕНИЕ № 2: ПОКАЗАНИЯ СЧЕТЧИКОВ', bold=True, size=26))
    body.append(create_paragraph(f'Показания на дату передачи помещения ({contract["start_date"]})', size=22))
    
    meters = data['meters']
    meters_table = [
        ['Счетчик', 'Показания', 'Дата'],
        ['Электроэнергия', meters['electricity']['reading'] or '(заполнить)', meters['electricity']['date']],
        ['Холодная вода', meters['cold_water']['reading'] or '(заполнить)', meters['cold_water']['date']],
        ['Горячая вода', meters['hot_water']['reading'] or '(заполнить)', meters['hot_water']['date']],
    ]
    body.append(create_table(meters_table, font_size=20))
    body.append(create_paragraph('', size=24))
    
    # Футер
    body.append(create_paragraph('', size=24))
    timestamp = datetime.now().strftime('%d.%m.%Y %H:%M:%S')
    body.append(create_paragraph(f'Дата создания сводки: {timestamp}', align='center', size=20))
    
    return '\n'.join(body)

def create_docx(filename, data_file='contract_data.json'):
    """Создает DOCX файл со сводкой"""
    
    # Загружаем данные из JSON
    data = load_contract_data(data_file)
    
    # Создаем временную директорию для файлов
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Создаем структуру папок DOCX
        os.makedirs(os.path.join(temp_dir, 'word'))
        os.makedirs(os.path.join(temp_dir, 'word', '_rels'))
        os.makedirs(os.path.join(temp_dir, '_rels'))
        
        # Создаем document.xml
        document_xml = create_docx_structure()
        body_content = create_summary_body(data)
        document_xml = document_xml.replace('{body}', body_content)
        
        with open(os.path.join(temp_dir, 'word', 'document.xml'), 'w', encoding='utf-8') as f:
            f.write(document_xml)
        
        # Создаем [Content_Types].xml
        content_types = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
<Override PartName="/word/footer1.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml"/>
</Types>'''
        
        with open(os.path.join(temp_dir, '[Content_Types].xml'), 'w', encoding='utf-8') as f:
            f.write(content_types)
        
        # Создаем _rels/.rels
        rels = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>'''
        
        with open(os.path.join(temp_dir, '_rels', '.rels'), 'w', encoding='utf-8') as f:
            f.write(rels)
        
        # Создаем word/_rels/document.xml.rels
        document_rels = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/footer" Target="footer1.xml"/>
</Relationships>'''
        
        with open(os.path.join(temp_dir, 'word', '_rels', 'document.xml.rels'), 'w', encoding='utf-8') as f:
            f.write(document_rels)
        
        # Создаем footer1.xml для номеров страниц
        footer_xml = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:ftr xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
<w:p>
<w:pPr>
<w:jc w:val="center"/>
</w:pPr>
<w:r>
<w:fldChar w:fldCharType="begin"/>
</w:r>
<w:r>
<w:instrText>PAGE</w:instrText>
</w:r>
<w:r>
<w:fldChar w:fldCharType="end"/>
</w:r>
</w:p>
</w:ftr>'''
        
        with open(os.path.join(temp_dir, 'word', 'footer1.xml'), 'w', encoding='utf-8') as f:
            f.write(footer_xml)
        
        # Создаем ZIP-архив (DOCX файл)
        with zipfile.ZipFile(filename, 'w', zipfile.ZIP_DEFLATED) as docx:
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arc_name = os.path.relpath(file_path, temp_dir)
                    docx.write(file_path, arc_name)
        
        print(f'Сводка успешно создана: {filename}')
        
    finally:
        # Удаляем временную директорию
        shutil.rmtree(temp_dir)

if __name__ == '__main__':
    # Создаем папку для документов если её нет
    os.makedirs('doc/summary', exist_ok=True)
    
    # Добавляем дату и время к имени файла
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    output_file = f'doc/summary/СВОДКА_ДОГОВОРА_v{timestamp}.docx'
    create_docx(output_file)
