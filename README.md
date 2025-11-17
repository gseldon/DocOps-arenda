# СИСТЕМА ГЕНЕРАЦИИ ДОГОВОРОВ АРЕНДЫ

Автоматизированная система для создания договоров аренды квартиры и сводок в формате DOCX.

## СТРУКТУРА ПРОЕКТА

```
/home/rydkins/arenda/
├── contract_data.json          # Файл с РЕАЛЬНЫМИ персональными данными (в .gitignore)
├── contract_data.template.json # Шаблон для заполнения (отслеживается Git)
├── create_contract.py          # Скрипт генерации договора
├── create_summary.py           # Скрипт генерации сводки
├── requirements.txt            # Зависимости проекта
├── README.md                   # Документация
├── .gitignore                  # Исключения для Git
├── doc/                        # Сгенерированные документы (в .gitignore)
│   ├── Договор_аренды_квартиры_v{timestamp}.docx
│   └── summary/                # Сгенерированные сводки
│       ├── СВОДКА_ДОГОВОРА.md
│       └── СВОДКА_ДОГОВОРА_v{timestamp}.docx
└── example/                    # Папка с примерами документов
    ├── arenda_dogovor.docx
    ├── Obrazets_dogovora_arendy_kvartiry_s_mebelyu_i_bytovoy_tekhnikoy.docx
    ├── Договор_аренды.pdf
    └── Найм-договор.doc
```

## ФАЙЛ С ДАННЫМИ: contract_data.json

Все персональные данные и параметры договора хранятся в JSON файле для удобства редактирования.

### Структура данных:

#### 1. ИНФОРМАЦИЯ О ДОГОВОРЕ
```json
"contract": {
  "conclusion_date": "18.11.2025",    // Дата заключения
  "start_date": "19.11.2025",          // Дата начала аренды
  "duration_months": 11,                // Срок аренды в месяцах
  "keys_count": 1                       // Количество комплектов ключей
}
```

#### 2. ДАННЫЕ АРЕНДОДАТЕЛЯ
```json
"landlord": {
  "full_name": "Иванов Иван Иванович",
  "passport_series": "1234",
  "passport_number": "567890",
  "passport_issued_by": "ГУ МВД России по г. Москве",
  "passport_issued_date": "01.01.2010",
  "registration_address": "г. Москва, ул. Примерная, д. 1, кв. 1",
  "phone": "+7 900 123 45 67",
  "email": "landlord@example.com"
}
```

#### 3. ДАННЫЕ АРЕНДАТОРА
```json
"tenant": {
  "full_name": "Петров Петр Петрович",
  "date_of_birth": "01.01.1990",
  "passport_series": "4321",
  "passport_number": "098765",
  "passport_issued_by": "ГУ МВД России по г. Москве",
  "passport_issued_date": "15.06.2015",
  "registration_address": "г. Москва, ул. Другая, д. 5, кв. 10",
  "phone": "+7 901 234 56 78",
  "email": "tenant@example.com"
}
```

#### 4. ДАННЫЕ О ПОМЕЩЕНИИ
```json
"property": {
  "type": "Квартира",
  "address": {
    "city": "Москва",
    "street": "ул. Примерная",
    "house": "10",
    "building": "2",
    "apartment": "42",
    "floor": "5"
  },
  "cadastral_number": "77:01:0001001:1000",
  "area": "45",
  "ownership": "единоличной собственности"
}
```

#### 5. ФИНАНСОВЫЕ УСЛОВИЯ
```json
"financial": {
  "monthly_rent": 60000,
  "monthly_rent_text": "шестьдесят тысяч",
  "security_deposit": 30000,
  "security_deposit_text": "тридцать тысяч",
  "payment_period_start": 18,
  "payment_period_end": 20,
  "first_payment_deadline": "20.11.2025",
  "deposit_deadline": "20.11.2025",
  "penalty_rate": 0.1,
  "sbp_phone": "+7 900 123 45 67"
}
```

#### 6. БАНКОВСКИЕ РЕКВИЗИТЫ
```json
"bank_details": {
  "recipient": "Иванов Иван Иванович",
  "account_number": "40817810100001234567",
  "payment_purpose": "Перевод средств по договору № 1234567890 Иванов Иван Иванович НДС не облагается",
  "bik": "044525225",
  "bank_name": "ПАО Сбербанк",
  "correspondent_account": "30101810400000000225",
  "inn": "1234567890",
  "kpp": "123456789"
}
```

#### 7. ОПИСЬ ИМУЩЕСТВА
```json
"inventory": [
  "Шкаф-купе IKEA с зеркалом",
  "Микроволновая печь (оранжевая)",
  "Комод IKEA черный",
  "Стиральная машинка Candy Smart"
]
```

#### 8. ПОКАЗАНИЯ СЧЕТЧИКОВ
```json
"meters": {
  "electricity": {
    "number": "",
    "reading": "",
    "date": "19 ноября 2025 г."
  },
  "cold_water": {
    "number": "",
    "reading": "",
    "date": "19 ноября 2025 г."
  },
  "hot_water": {
    "number": "",
    "reading": "",
    "date": "19 ноября 2025 г."
  }
}
```

#### 9. ПРАВИЛА И СРОКИ
```json
"rules": {
  "max_additional_residents": 1,
  "notification_days_for_residents": 3,
  "animals_allowed_by_default": false,
  "meters_submission_day": 15,
  "meters_submission_time": "23:00",
  "utility_payment_days": 5,
  "termination_notice_days": 30,
  "eviction_days": 7,
  "deposit_return_days": 10
}
```

## УСТАНОВКА

### Для новых пользователей:

```bash
# 1. Клонируйте репозиторий
git clone <url-репозитория>
cd arenda

# 2. Проверьте версию Python
python3 --version

# 3. (Опционально) Проверьте зависимости
cat requirements.txt
# Примечание: дополнительная установка не требуется

# 4. Создайте файл с вашими данными
cp contract_data.template.json contract_data.json

# 5. Отредактируйте файл с данными
nano contract_data.json
```

## ПЕРВОНАЧАЛЬНАЯ НАСТРОЙКА

### 1. Создание файла с данными

Скопируйте шаблон и заполните своими данными:

```bash
cp contract_data.template.json contract_data.json
nano contract_data.json
```

Замените все заглушки (`ФАМИЛИЯ ИМЯ ОТЧЕСТВО`, `DD.MM.YYYY`, `+7 XXX XXX XX XX` и т.д.) на реальные данные.

ВАЖНО: Файл `contract_data.json` с реальными данными автоматически игнорируется Git для безопасности!

## ИСПОЛЬЗОВАНИЕ

### 1. Редактирование данных

Отредактируйте файл `contract_data.json`:

```bash
nano contract_data.json
```

или откройте в любом текстовом редакторе.

### 2. Генерация договора

```bash
python3 create_contract.py
```

Будет создан файл: `Договор_аренды_квартиры_v{ДАТА}_{ВРЕМЯ}.docx`

### 3. Генерация сводки

```bash
python3 create_summary.py
```

Будет создан файл: `СВОДКА_ДОГОВОРА_v{ДАТА}_{ВРЕМЯ}.docx`

## ПРЕИМУЩЕСТВА СИСТЕМЫ

1. **Централизованные данные** - все данные в одном JSON файле
2. **Легкое редактирование** - изменяйте данные без редактирования кода
3. **Версионность** - каждый файл имеет дату и время создания
4. **Переиспользование** - один файл данных для договора и сводки
5. **Безопасность** - персональные данные отделены от кода

## ИЗМЕНЕНИЕ ПАРАМЕТРОВ

### Изменить арендную плату:
```json
"monthly_rent": 70000,
"monthly_rent_text": "семьдесят тысяч",
```

### Изменить срок аренды:
```json
"duration_months": 12,
```

### Добавить имущество:
```json
"inventory": [
  "Шкаф-купе IKEA с зеркалом",
  "Микроволновая печь (оранжевая)",
  "Комод IKEA черный",
  "Стиральная машинка Candy Smart",
  "Холодильник Samsung",
  "Диван-кровать"
]
```

### Изменить сроки оплаты:
```json
"payment_period_start": 15,
"payment_period_end": 18,
```

### Изменить день передачи показаний счетчиков:
```json
"meters_submission_day": 20,
"meters_submission_time": "20:00",
```

## БЕЗОПАСНОСТЬ

### ЗАЩИТА ПЕРСОНАЛЬНЫХ ДАННЫХ:

1. **Файл с реальными данными** (`contract_data.json`) автоматически добавлен в `.gitignore`
2. **Шаблон** (`contract_data.template.json`) содержит только примеры и отслеживается Git
3. **Сгенерированные документы** в папке `doc/` также игнорируются Git

### РЕКОМЕНДАЦИИ:

- Никогда не коммитьте файл `contract_data.json` с реальными данными
- Создавайте резервные копии `contract_data.json` в безопасном месте
- Проверяйте данные перед генерацией документов
- При публикации в публичный репозиторий используйте только `contract_data.template.json`

### ДЛЯ РАЗРАБОТЧИКОВ:

Если вы форкаете проект:

```bash
# 1. Клонируйте репозиторий
git clone <url>

# 2. Создайте свой файл с данными из шаблона
cp contract_data.template.json contract_data.json

# 3. Заполните реальными данными (файл автоматически игнорируется)
nano contract_data.json
```

## ТРЕБОВАНИЯ

- Python 3.6+
- Стандартные библиотеки Python (json, zipfile, datetime, os, shutil, tempfile)

Проект не требует установки дополнительных зависимостей через pip, так как использует только стандартные библиотеки Python.

### Проверка версии Python:

```bash
python3 --version
```

Если версия Python ниже 3.6, обновите Python до последней версии.

## ПОДДЕРЖКА

При возникновении проблем:
1. Проверьте корректность JSON синтаксиса
2. Убедитесь, что все обязательные поля заполнены
3. Проверьте кодировку файла (должна быть UTF-8)

## ВЕРСИЯ

Текущая версия: 2.0 (с использованием JSON для данных)
Дата обновления: 17.11.2025

