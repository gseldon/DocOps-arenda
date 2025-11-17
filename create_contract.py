#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для создания договора аренды квартиры в формате DOCX
"""

import zipfile
import os
import json
from datetime import datetime

def load_contract_data(filename='contract_data.json'):
    """Загружает данные договора из JSON файла"""
    with open(filename, 'r', encoding='utf-8') as f:
        return json.load(f)

def create_docx_structure():
    """Создает базовую структуру DOCX файла"""
    
    # Создаем XML для основного документа
    document_xml = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" 
            xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
            xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing">
<w:body>
{body}
<w:sectPr>
<w:pgSz w:w="11906" w:h="16838"/>
<w:pgMar w:top="1134" w:right="850" w:bottom="1134" w:left="1701" w:header="708" w:footer="708" w:gutter="0"/>
</w:sectPr>
</w:body>
</w:document>'''

    return document_xml

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

def create_table_row(cells, font_size=24):
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

def create_table(rows, font_size=24):
    """Создает таблицу"""
    rows_xml = ''.join([create_table_row(row, font_size) for row in rows])
    return f'''<w:tbl>
<w:tblPr>
<w:tblStyle w:val="TableGrid"/>
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
<w:tblGrid>
<w:gridCol w:w="2500"/>
<w:gridCol w:w="2500"/>
<w:gridCol w:w="2500"/>
</w:tblGrid>
{rows_xml}
</w:tbl>'''

def create_contract_body(data):
    """Создает тело договора"""
    body = []
    
    # Извлекаем данные для удобства
    landlord = data['landlord']
    tenant = data['tenant']
    prop = data['property']
    addr = prop['address']
    financial = data['financial']
    bank = data['bank_details']
    contract = data['contract']
    rules = data['rules']

    # Заголовок
    body.append(create_paragraph('Договор аренды помещения для проживания', bold=True, align='center', size=28))
    body.append(create_paragraph('(далее – Договор)', bold=True, align='center', size=28))
    body.append(create_paragraph('', size=24))
    # Место и дата
    body.append(create_paragraph(f'г. {addr["city"]}                                                                                           «___» _________ 2025 г.', size=24))
    body.append(create_paragraph('', size=24))
    # Таблица реквизитов сторон
    landlord_passport = f'Паспорт серии {landlord["passport_series"] or "_______"} № {landlord["passport_number"] or "___________"},'
    tenant_passport = f'Паспорт серии {tenant["passport_series"]} № {tenant["passport_number"]},'
    
    parties_rows = [
        ['Арендодатель:', 'Арендатор:'],
        ['', ''],
        [f'Гр. РФ {landlord["full_name"]} (ФИО)', f'Гр. РФ {tenant["full_name"]} (ФИО)'],
        [landlord_passport, tenant_passport],
        [f'выдан {landlord["passport_issued_by"] or "___________________________________"}', f'выдан {tenant["passport_issued_by"] or "___________________________________"}'],
        ['_________________________________________', '_________________________________________'],
        [f'Адрес регистрации:{landlord["registration_address"] or "________________________"}', f'Адрес регистрации:{tenant["registration_address"] or "________________________"}'],
        ['_________________________________________', '_________________________________________'],
        [f'Тел.: {landlord["phone"]}', f'Тел.: {tenant["phone"] or "____________________________________"}'],
        [f'Email: {landlord["email"]}', f'Email: {tenant["email"] or "___________________________________"}'],
    ]
    body.append(create_table(parties_rows, font_size=20))
    body.append(create_paragraph('', size=24))
    # Информация о помещении
    full_address = f'г. {addr["city"]}, {addr["street"]}, д. {addr["house"]}, корп. {addr["building"]}, кв. {addr["apartment"]}, этаж {addr["floor"]}'
    property_rows = [
        [f'Помещение: {prop["type"]} / Комната', ''],
        [f'Адрес: {full_address};', ''],
        [f'Кадастровый номер: {prop["cadastral_number"]}; Общая площадь {prop["area"]} м2.', ''],
        ['• Принадлежит Арендодателю на праве собственности, что подтверждается Свидетельством о государственной регистрации права (при наличии) и (или) Выпиской из Единого государственного реестра недвижимости.', ''],
        ['• Не является предметом спора, не находится под арестом, не сдано в аренду/наем иным лицам.', ''],
        ['• Пригодно для проживания. Состояние Помещения указывается Сторонами в акте приема-передачи Помещения.', ''],
    ]
    body.append(create_table(property_rows, font_size=20))
    body.append(create_paragraph('', size=24))
    # 1. Предмет Договора
    body.append(create_paragraph('1. Предмет Договора.', bold=True, size=26))
    body.append(create_paragraph('1.1. По Договору Арендодатель обязуется за плату предоставить Арендатору во владение и пользование Помещение для проживания в нем.', size=24))
    body.append(create_paragraph('1.2. Договор вступает в силу с даты его подписания Сторонами и действует до истечения срока аренды.', size=24))
    body.append(create_paragraph(f'1.3. Срок аренды: {contract["duration_months"]} (одиннадцать) месяцев, начиная с «{contract["start_date"]}».', size=24))
    body.append(create_paragraph('1.4. Помещение принадлежит Арендодателю на праве единоличной собственности. Согласия третьих лиц на заключение настоящего Договора не требуется.', size=24))
    body.append(create_paragraph('1.5. АВТОМАТИЧЕСКАЯ ПРОЛОНГАЦИЯ: Если ни одна из Сторон не уведомит другую Сторону о намерении расторгнуть Договор не менее чем за 30 (тридцать) календарных дней до окончания срока его действия, Договор считается автоматически продленным на тех же условиях на новый срок 11 (одиннадцать) месяцев.', size=24))
    body.append(create_paragraph('1.5.1. ИНДЕКСАЦИЯ АРЕНДНОЙ ПЛАТЫ: При автоматической пролонгации Договора размер арендной платы может быть увеличен Арендодателем, но не более чем на уровень официальной инфляции (индекса потребительских цен) в Российской Федерации за предыдущий календарный год, по данным Федеральной службы государственной статистики (Росстат). Арендодатель обязан уведомить Арендатора о новом размере арендной платы не менее чем за 30 (тридцать) календарных дней до начала нового срока аренды.', size=24))
    body.append(create_paragraph('1.6. ПРОЖИВАЮЩИЕ ЛИЦА И ЖИВОТНЫЕ:', bold=True, size=24))
    body.append(create_paragraph(f'1.6.1. В соответствии с настоящим Договором в Помещении проживает Арендатор. Арендатор имеет право вселить для постоянного проживания {rules["max_additional_residents"]} (одно) дополнительное совершеннолетнее лицо с обязательным письменным уведомлением Арендодателя не менее чем за {rules["notification_days_for_residents"]} (три) дня до вселения с указанием ФИО и степени родства. Вселение третьих лиц без уведомления или свыше установленного лимита является основанием для расторжения Договора.', size=24))
    body.append(create_paragraph('1.6.2. Нахождение в Помещении домашних животных ЗАПРЕЩЕНО. По письменному согласованию Сторон (оформляется отдельным дополнительным соглашением к настоящему Договору) может быть разрешено содержание домашних животных с указанием их вида и породы. При разрешении содержания животных Арендатор несет полную ответственность за любой ущерб, нанесенный животными Помещению и имуществу.', size=24))
    body.append(create_paragraph('1.6.3. Арендатор обязуется использовать Помещение исключительно для проживания. Запрещается использование Помещения для субаренды, коммерческой деятельности, в качестве офиса или для иных целей, не связанных с проживанием.', size=24))
    body.append(create_paragraph('', size=24))
    # 2. Приемка - передача Помещения
    body.append(create_paragraph('2. Приемка – передача Помещения.', bold=True, size=26))
    body.append(create_paragraph(f'2.1. Не позднее {contract["start_date"]} (дата) Арендодатель обязуется передать, а Арендатор принять {contract["keys_count"]} (один) комплект(а/ов) ключей для доступа в Помещение.', size=24))
    body.append(create_paragraph('2.2. Передача Помещения Арендатору осуществляется не позднее 19 ноября 2025 г. (дата) на основании акта приема передачи. Обратная передача Помещения от Арендатора к Арендодателю в любом случае осуществляется по акту возврата Помещения.', size=24))
    body.append(create_paragraph('2.3. В случае, если одна из Сторон не исполнила в срок или ненадлежащим образом исполнила обязанность, предусмотренную настоящим разделом, действие Договора прекращается в день истечения срока, представленного для исполнения обязанности и указанного в п. 2.1 или п 2.2. Договора соответственно.', size=24))
    body.append(create_paragraph('', size=24))
    # 3. Расчеты
    body.append(create_paragraph('3. Расчеты.', bold=True, size=26))
    body.append(create_paragraph(f'3.1. Плата за аренду в месяц составляет {financial["monthly_rent"]:,} ({financial["monthly_rent_text"]}) рублей.'.replace(',', ' '), size=24))
    body.append(create_paragraph(f'3.2. Оплата осуществляется не позднее {financial["payment_period_end"]} числа (включительно) каждого календарного месяца, независимо от фактического срока проживания Арендатора в Помещении.', size=24))
    body.append(create_paragraph('3.2.1. Плата за первый месяц пользования Помещением вносится Арендатором не позднее 20 ноября 2025 г. (дата).', size=24))
    body.append(create_paragraph('3.2.2. В случае неоплаты за первый месяц пользования Помещением действие Договора прекращается в день истечения срока, предусмотренного настоящим пунктом.', size=24))
    body.append(create_paragraph('3.3. Оплата арендной платы производится одним из следующих способов:', size=24))
    body.append(create_paragraph(f'     - перевод по Системе быстрых платежей (СБП) по номеру телефона: {financial["sbp_phone"]};', size=24))
    body.append(create_paragraph('     - перевод на банковские реквизиты Арендодателя:', size=24))
    # Таблица реквизитов для оплаты
    payment_details_rows = [
        ['Получатель:', bank['recipient']],
        ['Номер счета:', bank['account_number']],
        ['Назначение платежа:', bank['payment_purpose']],
        ['БИК:', bank['bik']],
        ['Банк-получатель:', bank['bank_name']],
        ['Корр. счет:', bank['correspondent_account']],
        ['ИНН при необходимости:', bank['inn']],
        ['КПП при необходимости:', bank['kpp']],
    ]
    body.append(create_table(payment_details_rows, font_size=20))
    body.append(create_paragraph('3.4. Обеспечительный платеж (залог) в размере 30 000 (тридцать тысяч) рублей вносится Арендатором не позднее 20 ноября 2025 г. тем же способом, что и арендная плата.', size=24))
    body.append(create_paragraph(f'3.5. Обеспечительный платеж возвращается Арендатору в течение {rules["deposit_return_days"]} (десяти) календарных дней с момента возврата Помещения по Акту приема-передачи при условии отсутствия задолженности по арендной плате и коммунальным платежам, а также при отсутствии повреждений имущества и Помещения.', size=24))
    body.append(create_paragraph('3.6. В случае причинения Арендатором ущерба Помещению или имуществу, указанному в Описи, либо при наличии задолженности по арендной плате или коммунальным платежам, Арендодатель имеет право удержать из обеспечительного платежа сумму ущерба и/или задолженности, возвратив Арендатору оставшуюся часть.', size=24))
    body.append(create_paragraph('', size=24))
    # 4. Права и обязанности Арендодателя
    body.append(create_paragraph('4. Права и обязанности Арендодателя.', bold=True, size=26))
    body.append(create_paragraph('4.1. Арендодатель обязуется:', size=24))
    body.append(create_paragraph('4.1.1. Передать Помещение Арендатору в состоянии, пригодном для проживания, со всеми коммуникациями и инженерными системами в исправном состоянии.', size=24))
    body.append(create_paragraph('4.1.2. Обеспечить Арендатору беспрепятственное пользование Помещением в течение всего срока действия Договора.', size=24))
    body.append(create_paragraph('4.1.3. Производить за свой счет капитальный ремонт Помещения при необходимости, если такая необходимость возникла не по вине Арендатора.', size=24))
    body.append(create_paragraph('4.1.4. В случае возникновения экстренных ситуаций (аварии, пожар, затопление, несанкционированный доступ третьих лиц, иные случаи, угрожающие ущербом Помещению, имуществу или жизни и здоровью людей) незамедлительно принять меры для их устранения, содействовать Арендатору в минимизации ущерба.', size=24))
    body.append(create_paragraph('4.2. Арендодатель имеет право:', size=24))
    body.append(create_paragraph('4.2.1. Требовать своевременного внесения арендной платы.', size=24))
    body.append(create_paragraph('4.2.2. Требовать от Арендатора соблюдения условий настоящего Договора.', size=24))
    body.append(create_paragraph('4.2.3. Не чаще одного раза в месяц в присутствии Арендатора проверять состояние Помещения и находящегося в нем имущества в предварительно согласованное с Арендатором время (не менее чем за 24 часа до посещения).', size=24))
    body.append(create_paragraph('4.2.4. Получать доступ в Помещение в любое время в случае экстренных ситуаций (аварии, пожар, затопление и т.д.) или при угрозе их возникновения без предварительного согласования с Арендатором.', size=24))
    body.append(create_paragraph('4.2.5. В случае существенного нарушения Арендатором условий настоящего Договора потребовать его досрочного расторжения.', size=24))
    body.append(create_paragraph('', size=24))
    # 5. Права и обязанности Арендатора
    body.append(create_paragraph('5. Права и обязанности Арендатора.', bold=True, size=26))
    body.append(create_paragraph('5.1. Арендатор обязуется:', size=24))
    body.append(create_paragraph('5.1.1. Использовать Помещение только для проживания в соответствии с его назначением.', size=24))
    body.append(create_paragraph('5.1.2. Своевременно и в полном объеме вносить арендную плату в порядке и размере, определенных настоящим Договором.', size=24))
    body.append(create_paragraph('5.1.3. Поддерживать Помещение в надлежащем состоянии, не хуже того, в котором он его получил при заключении Договора, с учетом нормального износа.', size=24))
    body.append(create_paragraph('5.1.4. Производить за свой счет текущий ремонт Помещения.', size=24))
    body.append(create_paragraph('5.1.5. Бережно относиться к Помещению и находящемуся в нем имуществу.', size=24))
    body.append(create_paragraph('5.1.6. Соблюдать правила пользования жилыми помещениями, правила пожарной безопасности, санитарно-гигиенические и экологические требования.', size=24))
    body.append(create_paragraph('5.1.7. Не производить перепланировку, переустройство и реконструкцию Помещения без письменного согласия Арендодателя.', size=24))
    body.append(create_paragraph('5.1.8. Не сдавать Помещение в субаренду и не передавать свои права и обязанности по настоящему Договору третьим лицам без письменного согласия Арендодателя.', size=24))
    body.append(create_paragraph('5.1.9. Не менее чем за 30 (тридцать) календарных дней до окончания срока действия Договора известить Арендодателя о намерении продлить или расторгнуть настоящий Договор.', size=24))
    body.append(create_paragraph('5.1.10. По окончании срока действия Договора или при его досрочном расторжении вернуть Помещение Арендодателю в том состоянии, в котором он его получил, с учетом нормального износа, со всем имуществом согласно Описи.', size=24))
    body.append(create_paragraph('5.1.11. Соблюдать тишину и уважать покой соседей, особенно в ночные часы (с 23:00 до 07:00). Не допускать действий, создающих повышенный шум и нарушающих права других жильцов дома.', size=24))
    body.append(create_paragraph('5.1.12. Нести полную ответственность за действия своих гостей. Оставлять гостей в Помещении без присутствия Арендатора только с письменного разрешения Арендодателя. Арендатор несет ответственность за любой ущерб, причиненный гостями Помещению или имуществу.', size=24))
    body.append(create_paragraph('5.1.13. Проводить серьезные ремонтные работы или осуществлять какие-либо значительные изменения в Помещении (перепланировка, переустройство, реконструкция) только с письменного разрешения Арендодателя.', size=24))
    body.append(create_paragraph('5.1.14. Допускать Арендодателя в Помещение для проверки его состояния в соответствии с п. 4.2.3 настоящего Договора.', size=24))
    body.append(create_paragraph('5.2. Арендатор имеет право:', size=24))
    body.append(create_paragraph('5.2.1. Пользоваться Помещением и находящимся в нем имуществом в соответствии с их назначением.', size=24))
    body.append(create_paragraph('5.2.2. С письменного согласия Арендодателя производить за свой счет улучшения Помещения.', size=24))
    body.append(create_paragraph('5.2.3. Требовать от Арендодателя своевременного проведения капитального ремонта Помещения.', size=24))
    body.append(create_paragraph('5.2.4. В случае невыполнения Арендодателем обязательств по осуществлению капитального ремонта, что создает риск возникновения экстренных ситуаций, Арендатор вправе за свой счет произвести необходимый ремонт и вычесть суммы понесенных расходов из ближайшей подлежащей выплате суммы арендной платы, направив Арендодателю соответствующее письменное уведомление.', size=24))
    body.append(create_paragraph('5.3. Арендатор НЕ несет ответственность за естественную амортизацию (износ) Помещения, мебели и оборудования при их надлежащем использовании.', size=24))
    body.append(create_paragraph('', size=24))
    # 6. Ответственность Сторон
    body.append(create_paragraph('6. Ответственность Сторон.', bold=True, size=26))
    body.append(create_paragraph('6.1. За неисполнение или ненадлежащее исполнение обязательств по настоящему Договору Стороны несут ответственность в соответствии с действующим законодательством Российской Федерации.', size=24))
    body.append(create_paragraph('6.2. За нарушение сроков внесения арендной платы Арендатор уплачивает Арендодателю неустойку в размере 0,1% от суммы задолженности за каждый день просрочки.', size=24))
    body.append(create_paragraph('6.3. В случае порчи или утраты имущества, указанного в Описи имущества (Приложение № 1), Арендатор обязуется возместить Арендодателю причиненный ущерб в полном объеме.', size=24))
    body.append(create_paragraph('6.4. Сторона, не исполнившая или ненадлежащим образом исполнившая обязательства по настоящему Договору, обязана возместить другой Стороне причиненные таким неисполнением убытки.', size=24))
    body.append(create_paragraph('', size=24))
    # 7. Коммунальные и эксплуатационные платежи
    body.append(create_paragraph('7. Коммунальные и эксплуатационные платежи.', bold=True, size=26))
    body.append(create_paragraph('7.1. Арендатор обязуется своевременно и в полном объеме оплачивать коммунальные услуги (электроэнергию, холодное и горячее водоснабжение, водоотведение, отопление) и эксплуатационные расходы (содержание и текущий ремонт общего имущества многоквартирного дома) по действующим тарифам.', size=24))
    body.append(create_paragraph('7.2. Оплата коммунальных и эксплуатационных платежей производится Арендатором отдельным платежом на счет Арендодателя (реквизиты указаны в п. 3.3 настоящего Договора) после получения информации о сумме платежа от Арендодателя.', size=24))
    body.append(create_paragraph('7.3. Арендодатель обязуется ежемесячно информировать Арендатора о суммах подлежащих оплате коммунальных и эксплуатационных платежей через мессенджеры, электронную почту или по номеру телефона, предоставив копии квитанций или счетов.', size=24))
    body.append(create_paragraph(f'7.4. Арендатор обязуется оплатить коммунальные и эксплуатационные платежи в течение {rules["utility_payment_days"]} (пяти) рабочих дней с момента получения информации от Арендодателя о сумме платежа.', size=24))
    body.append(create_paragraph('7.5. Показания счетчиков на момент передачи Помещения Арендатору указаны в Приложении № 2 к настоящему Договору.', size=24))
    body.append(create_paragraph(f'7.6. ПЕРЕДАЧА ПОКАЗАНИЙ СЧЕТЧИКОВ: Арендатор обязуется передавать Арендодателю показания приборов учета (счетчиков) электроэнергии, холодной и горячей воды строго {rules["meters_submission_day"]} числа каждого месяца до {rules["meters_submission_time"]} любым удобным способом (мессенджеры, электронная почта, SMS). В случае нахождения Арендатора вне региона (по причине отпуска, командировки) допускается указание среднего потребления с обязательным перерасчетом в следующие периоды после предоставления фактических показаний.', size=24))
    body.append(create_paragraph('', size=24))
    # 8. Изменение и расторжение Договора
    body.append(create_paragraph('8. Изменение и расторжение Договора.', bold=True, size=26))
    body.append(create_paragraph('8.1. Настоящий Договор может быть изменен или расторгнут по соглашению Сторон. Все изменения и дополнения к настоящему Договору оформляются в письменной форме в виде дополнительных соглашений, подписываемых обеими Сторонами.', size=24))
    body.append(create_paragraph(f'8.2. Каждая из Сторон вправе в любое время отказаться от исполнения настоящего Договора, письменно уведомив об этом другую Сторону не менее чем за {rules["termination_notice_days"]} (тридцать) календарных дней до предполагаемой даты расторжения.', size=24))
    body.append(create_paragraph('8.3. Арендодатель имеет право досрочно расторгнуть настоящий Договор в одностороннем порядке в следующих случаях:', size=24))
    body.append(create_paragraph('8.3.1. Невнесение Арендатором арендной платы более двух раз подряд по истечении установленного срока платежа.', size=24))
    body.append(create_paragraph('8.3.2. Использование Помещения не по назначению или с нарушением условий настоящего Договора.', size=24))
    body.append(create_paragraph('8.3.3. Существенное нарушение Арендатором условий настоящего Договора или невыполнение обязанностей по содержанию Помещения.', size=24))
    body.append(create_paragraph(f'8.4. При досрочном расторжении Договора по инициативе Арендодателя Арендатор обязан освободить Помещение и передать его Арендодателю по акту приема-передачи в течение {rules["eviction_days"]} (семи) календарных дней с даты получения письменного уведомления о расторжении.', size=24))
    body.append(create_paragraph('', size=24))
    # 9. Заключительные положения
    body.append(create_paragraph('9. Заключительные положения.', bold=True, size=26))
    body.append(create_paragraph('9.1. Все споры и разногласия, которые могут возникнуть из настоящего Договора или в связи с ним, Стороны будут стремиться разрешить путем переговоров.', size=24))
    body.append(create_paragraph('9.2. При невозможности разрешения споров путем переговоров споры подлежат разрешению в судебном порядке по месту нахождения Помещения в соответствии с действующим законодательством Российской Федерации.', size=24))
    body.append(create_paragraph('9.3. Стороны освобождаются от ответственности за частичное или полное неисполнение обязательств по настоящему Договору, если это неисполнение явилось следствием обстоятельств непреодолимой силы (форс-мажор), возникших после заключения настоящего Договора, которые Стороны не могли предвидеть или предотвратить.', size=24))
    body.append(create_paragraph('9.4. Настоящий Договор составлен в двух экземплярах, имеющих одинаковую юридическую силу, по одному экземпляру для каждой из Сторон.', size=24))
    body.append(create_paragraph('9.5. Неотъемлемой частью настоящего Договора являются:', size=24))
    body.append(create_paragraph('     - Приложение № 1 – Опись имущества, находящегося в Помещении;', size=24))
    body.append(create_paragraph('     - Приложение № 2 – Показания счетчиков на дату передачи Помещения.', size=24))
    body.append(create_paragraph('9.6. Во всем остальном, что не предусмотрено настоящим Договором, Стороны руководствуются действующим законодательством Российской Федерации.', size=24))
    body.append(create_paragraph('9.7. При подписании настоящего Договора Стороны подтверждают, что:', size=24))
    body.append(create_paragraph('     - они полностью понимают юридические последствия заключения настоящего Договора;', size=24))
    body.append(create_paragraph('     - они не лишены и не ограничены в дееспособности и правоспособности;', size=24))
    body.append(create_paragraph('     - отсутствуют обстоятельства, вынуждающие их совершить сделку на крайне невыгодных для себя условиях (сделка не является кабальной);', size=24))
    body.append(create_paragraph('     - они действуют добровольно, по своей воле и в своем интересе.', size=24))
    body.append(create_paragraph('', size=24))
    body.append(create_paragraph('', size=24))
    # Таблица подписей
    signature_table_rows = [
        ['АРЕНДОДАТЕЛЬ:', 'АРЕНДАТОР:'],
        [landlord['full_name'], tenant['full_name']],
        ['', ''],
        ['_______________________ / ______________', '_______________________ / ______________'],
        ['(подпись)                          (дата)', '(подпись)                          (дата)'],
    ]
    body.append(create_table(signature_table_rows, font_size=20))
    body.append(create_paragraph('', size=24))
    body.append(create_paragraph('', size=24))
    # Новая страница - Приложение 1
    body.append(create_paragraph('Приложение № 1', bold=True, align='center', size=26))
    body.append(create_paragraph('к Договору аренды помещения для проживания', align='center', size=24))
    body.append(create_paragraph('от «___» __________ 2025 г.', align='center', size=24))
    body.append(create_paragraph('', size=24))
    body.append(create_paragraph('ОПИСЬ ИМУЩЕСТВА', bold=True, align='center', size=26))
    body.append(create_paragraph('находящегося в помещении по адресу:', align='center', size=24))
    body.append(create_paragraph(full_address, align='center', size=24))
    body.append(create_paragraph(f'кадастровый номер {prop["cadastral_number"]}, общая площадь {prop["area"]} м2', align='center', size=24))
    body.append(create_paragraph('', size=24))
    
    # Формируем опись имущества из JSON
    inventory_rows = [['№ п/п', 'Наименование имущества', 'Количество', 'Состояние']]
    for i, item in enumerate(data['inventory'], 1):
        inventory_rows.append([str(i), item, '1 шт.', ''])
    # Добавляем пустые строки до 10
    for i in range(len(data['inventory']) + 1, 11):
        inventory_rows.append([str(i), '', '', ''])
    
    body.append(create_table(inventory_rows, font_size=20))
    body.append(create_paragraph('', size=24))
    body.append(create_paragraph('Имущество передано Арендатору в исправном состоянии. Претензий по количеству и состоянию имущества Стороны друг к другу не имеют.', size=24))
    body.append(create_paragraph('', size=24))
    # Подписи под описью
    signature_rows = [
        ['АРЕНДОДАТЕЛЬ:', 'АРЕНДАТОР:'],
        [landlord['full_name'], tenant['full_name']],
        ['', ''],
        ['___________________ / ___________', '___________________ / ___________'],
        ['(подпись)                    (дата)', '(подпись)                    (дата)'],
    ]
    body.append(create_table(signature_rows, font_size=20))
    body.append(create_paragraph('', size=24))
    # Новая страница - Приложение 2
    body.append(create_paragraph('', size=24))
    body.append(create_paragraph('', size=24))
    body.append(create_paragraph('Приложение № 2', bold=True, align='center', size=26))
    body.append(create_paragraph('к Договору аренды помещения для проживания', align='center', size=24))
    body.append(create_paragraph('от «___» __________ 2025 г.', align='center', size=24))
    body.append(create_paragraph('', size=24))
    body.append(create_paragraph('ПОКАЗАНИЯ СЧЕТЧИКОВ', bold=True, align='center', size=26))
    body.append(create_paragraph('на дату передачи помещения по адресу:', align='center', size=24))
    body.append(create_paragraph(full_address, align='center', size=24))
    body.append(create_paragraph(f'кадастровый номер {prop["cadastral_number"]}, общая площадь {prop["area"]} м2', align='center', size=24))
    body.append(create_paragraph('', size=24))
    meters = data['meters']
    meters_rows = [
        ['Наименование счетчика', 'Номер счетчика', 'Показания на дату передачи', 'Дата снятия показаний'],
        ['Электроэнергия', meters['electricity']['number'], meters['electricity']['reading'], meters['electricity']['date']],
        ['Холодная вода', meters['cold_water']['number'], meters['cold_water']['reading'], meters['cold_water']['date']],
        ['Горячая вода', meters['hot_water']['number'], meters['hot_water']['reading'], meters['hot_water']['date']],
    ]
    body.append(create_table(meters_rows, font_size=20))
    body.append(create_paragraph('', size=24))
    body.append(create_paragraph('Показания счетчиков сняты совместно Арендодателем и Арендатором на дату передачи Помещения и зафиксированы в настоящем приложении. Претензий по показаниям Стороны друг к другу не имеют.', size=24))
    body.append(create_paragraph('', size=24))
    # Подписи под показаниями
    signature_rows_meters = [
        ['АРЕНДОДАТЕЛЬ:', 'АРЕНДАТОР:'],
        [landlord['full_name'], tenant['full_name']],
        ['', ''],
        ['___________________ / ___________', '___________________ / ___________'],
        ['(подпись)                    (дата)', '(подпись)                    (дата)'],
    ]
    body.append(create_table(signature_rows_meters, font_size=20))
    
    return '\n'.join(body)

def create_docx(filename, data_file='contract_data.json'):
    """Создает DOCX файл с договором"""
    
    # Загружаем данные из JSON
    data = load_contract_data(data_file)
    
    # Создаем временную директорию для файлов
    import tempfile
    import shutil
    
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Создаем структуру папок
        os.makedirs(os.path.join(temp_dir, '_rels'), exist_ok=True)
        os.makedirs(os.path.join(temp_dir, 'word', '_rels'), exist_ok=True)
        
        # [Content_Types].xml
        with open(os.path.join(temp_dir, '[Content_Types].xml'), 'w', encoding='utf-8') as f:
            f.write('''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
<Override PartName="/word/footer1.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml"/>
</Types>''')
        
        # _rels/.rels
        with open(os.path.join(temp_dir, '_rels', '.rels'), 'w', encoding='utf-8') as f:
            f.write('''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>''')
        
        # word/_rels/document.xml.rels
        with open(os.path.join(temp_dir, 'word', '_rels', 'document.xml.rels'), 'w', encoding='utf-8') as f:
            f.write('''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/footer" Target="footer1.xml"/>
</Relationships>''')
        
        # word/footer1.xml - нумерация страниц
        with open(os.path.join(temp_dir, 'word', 'footer1.xml'), 'w', encoding='utf-8') as f:
            f.write('''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:ftr xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
<w:p>
<w:pPr>
<w:jc w:val="center"/>
</w:pPr>
<w:r>
<w:fldChar w:fldCharType="begin"/>
</w:r>
<w:r>
<w:instrText xml:space="preserve"> PAGE </w:instrText>
</w:r>
<w:r>
<w:fldChar w:fldCharType="end"/>
</w:r>
</w:p>
</w:ftr>''')
        
        # word/document.xml
        document_xml = create_docx_structure()
        body_content = create_contract_body(data)
        # Добавляем ссылку на footer в sectPr
        document_xml = document_xml.replace('<w:sectPr>', '<w:sectPr><w:footerReference w:type="default" r:id="rId1"/>')
        document_xml = document_xml.format(body=body_content)
        
        with open(os.path.join(temp_dir, 'word', 'document.xml'), 'w', encoding='utf-8') as f:
            f.write(document_xml)
        
        # Создаем ZIP архив (DOCX)
        with zipfile.ZipFile(filename, 'w', zipfile.ZIP_DEFLATED) as docx:
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arc_name = os.path.relpath(file_path, temp_dir)
                    docx.write(file_path, arc_name)
        
        print(f"Договор успешно создан: {filename}")
        
    finally:
        # Удаляем временную директорию
        shutil.rmtree(temp_dir)

if __name__ == '__main__':
    # Создаем папку для документов если её нет
    os.makedirs('doc', exist_ok=True)
    
    # Добавляем дату и время к имени файла
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    output_file = f'doc/Договор_аренды_квартиры_v{timestamp}.docx'
    create_docx(output_file)

