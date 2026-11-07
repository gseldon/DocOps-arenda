/* Конструктор договора аренды.
 * Состояние хранится в схеме contract_data.json, поэтому импорт/экспорт .json
 * совместимы с командной строкой. Документ собирает локальный сервер (webapp.py).
 * Пользовательские данные выводятся только через textContent. */
'use strict';

(function () {
  // ------------------------------------------------------------------ утилиты
  const $ = (id) => document.getElementById(id);

  function h(tag, attrs, children) {
    const el = document.createElement(tag);
    if (attrs) {
      for (const k of Object.keys(attrs)) {
        const v = attrs[k];
        if (v === undefined || v === null || v === false) continue;
        if (k === 'class') el.className = v;
        else if (k === 'text') el.textContent = v;
        else if (k.startsWith('on')) el.addEventListener(k.slice(2).toLowerCase(), v);
        else el.setAttribute(k, v === true ? '' : v);
      }
    }
    for (const c of [].concat(children || [])) {
      if (c === null || c === undefined || c === false) continue;
      el.appendChild(typeof c === 'string' || typeof c === 'number' ? document.createTextNode(String(c)) : c);
    }
    return el;
  }

  const SVG_NS = 'http://www.w3.org/2000/svg';
  function svg(w, paths, extra) {
    const s = document.createElementNS(SVG_NS, 'svg');
    s.setAttribute('width', w); s.setAttribute('height', w);
    s.setAttribute('viewBox', extra && extra.box || '0 0 16 16');
    s.setAttribute('fill', 'none'); s.setAttribute('aria-hidden', 'true');
    for (const d of paths) {
      const p = document.createElementNS(SVG_NS, d.circle ? 'circle' : 'path');
      for (const k of Object.keys(d)) if (k !== 'circle') p.setAttribute(k, d[k]);
      s.appendChild(p);
    }
    return s;
  }
  const ICON_CHECK = () => svg(12, [{ d: 'M2.5 6.2L5 8.5l4.5-5', stroke: 'currentColor', 'stroke-width': '1.6', 'stroke-linecap': 'round', 'stroke-linejoin': 'round' }], { box: '0 0 12 12' });
  const ICON_X = () => svg(14, [{ d: 'M4 4l8 8M12 4l-8 8', stroke: 'currentColor', 'stroke-width': '1.5', 'stroke-linecap': 'round' }]);
  const ICON_PLUS = () => svg(16, [{ d: 'M8 3v10M3 8h10', stroke: 'currentColor', 'stroke-width': '1.6', 'stroke-linecap': 'round' }]);

  const clone = (o) => JSON.parse(JSON.stringify(o));
  function getPath(obj, path) {
    let cur = obj;
    for (const k of path.split('.')) {
      if (cur === null || typeof cur !== 'object' || !(k in cur)) return undefined;
      cur = cur[k];
    }
    return cur;
  }
  function setPath(obj, path, value) {
    const keys = path.split('.');
    let cur = obj;
    for (let i = 0; i < keys.length - 1; i++) {
      if (cur[keys[i]] === null || typeof cur[keys[i]] !== 'object') cur[keys[i]] = {};
      cur = cur[keys[i]];
    }
    if (value === undefined) delete cur[keys[keys.length - 1]];
    else cur[keys[keys.length - 1]] = value;
  }
  function deepMerge(base, extra) {
    for (const k of Object.keys(extra || {})) {
      const v = extra[k];
      if (v && typeof v === 'object' && !Array.isArray(v) && base[k] && typeof base[k] === 'object' && !Array.isArray(base[k])) deepMerge(base[k], v);
      else base[k] = v;
    }
    return base;
  }

  const MONTHS = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня', 'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря'];
  function parseDate(v) {
    const m = /^(\d{2})\.(\d{2})\.(\d{4})$/.exec(String(v || '').trim());
    if (!m) return null;
    const d = +m[1], mo = +m[2], y = +m[3];
    const dt = new Date(y, mo - 1, d);
    return (y > 1900 && dt.getMonth() === mo - 1 && dt.getDate() === d) ? { d, mo, y } : null;
  }
  const longDate = (v) => { const p = parseDate(v); return p ? p.d + ' ' + MONTHS[p.mo - 1] + ' ' + p.y + ' г.' : ''; };
  const quotedDate = (v) => { const p = parseDate(v); return p ? '«' + String(p.d).padStart(2, '0') + '» ' + MONTHS[p.mo - 1] + ' ' + p.y + ' г.' : ''; };
  const fmtInt = (n) => String(n).replace(/\B(?=(\d{3})+(?!\d))/g, ' ');
  const isBlank = (v) => v === undefined || v === null || String(v).trim() === '';

  // ------------------------------------------------------------------ проверки
  const re = (r, msg) => (v) => (r.test(String(v)) ? '' : msg);
  const V = {
    date: (v) => (/^\d{2}\.\d{2}\.\d{4}$/.test(v) ? (parseDate(v) ? '' : 'Такой даты нет') : 'Формат ДД.ММ.ГГГГ'),
    name: (v) => (String(v).trim().split(/\s+/).length >= 2 ? '' : 'Фамилия и имя полностью'),
    ps: re(/^\d{4}$/, 'Серия — 4 цифры'),
    pn: re(/^\d{6}$/, 'Номер — 6 цифр'),
    bik: re(/^\d{9}$/, 'БИК — 9 цифр'),
    acc: re(/^\d{20}$/, 'Счёт — 20 цифр'),
    inn: re(/^(\d{10}|\d{12})$/, 'ИНН — 10 или 12 цифр'),
    kpp: re(/^\d{9}$/, 'КПП — 9 цифр'),
    phone: (v) => (String(v).replace(/\D/g, '').length === 11 ? '' : '11 цифр, например +7 900 123 45 67'),
    email: re(/^[^\s@]+@[^\s@]+\.[^\s@]+$/, 'Проверьте адрес'),
    cad: re(/^\d{2}:\d{2}:\d{6,7}:\d+$/, 'Формат 77:01:0001001:1000'),
    time: re(/^([01]\d|2[0-3]):[0-5]\d$/, 'Формат ЧЧ:ММ'),
    dec: re(/^\d+([.,]\d+)?$/, 'Число, например 45 или 45,5'),
    int: (v) => (Number.isInteger(v) && v >= 1 && v <= 999 ? '' : 'Целое число от 1 до 999'),
    day: (v) => (Number.isInteger(v) && v >= 1 && v <= 31 ? '' : 'Число от 1 до 31'),
    money: (v) => (Number.isInteger(v) && v >= 1 && v <= 999999 ? '' : 'Целое число рублей от 1 до 999 999'),
    rate: (v) => (typeof v === 'number' && v > 0 && v <= 100 ? '' : 'Число больше 0, например 0,1'),
  };
  const NUMERIC = { int: 1, day: 1, money: 1, rate: 1 };
  const MAXLEN = { date: 10, ps: 4, pn: 6, bik: 9, acc: 20, inn: 12, kpp: 9, time: 5 };
  const INPUTMODE = { int: 'numeric', day: 'numeric', money: 'numeric', rate: 'decimal', dec: 'decimal', ps: 'numeric', pn: 'numeric', bik: 'numeric', acc: 'numeric', inn: 'numeric', kpp: 'numeric', phone: 'tel', email: 'email', date: 'numeric' };

  // ------------------------------------------------------------------ поля
  // f(path, label, options): v — формат/проверка, opt — необязательное, adv — в «Дополнительно»
  const f = (path, label, o) => Object.assign({ path, label, ph: '', at: '' }, o || {});
  const OWNERSHIP = ['единоличной собственности', 'общей долевой собственности', 'общей совместной собственности'];

  const STEPS = [
    { id: 'contract', title: 'Условия', where: 'Шапка · п. 1.4 · п. 2 · п. 8',
      lead: 'Когда и где подписываете, с какого дня и на какой срок сдаёте квартиру.',
      places: ['Шапка', 'п. 1.4', 'п. 2.3', 'п. 8.4'],
      fields: [
        f('contract.conclusion_date', 'Дата заключения', { v: 'date', ph: 'ДД.ММ.ГГГГ', at: 'шапка' }),
        f('contract.conclusion_city', 'Город заключения', { opt: true, ph: 'как у квартиры', at: 'шапка', hint: 'Пусто — берётся город квартиры' }),
        f('contract.start_date', 'Начало аренды', { v: 'date', ph: 'ДД.ММ.ГГГГ', at: 'п. 1.4' }),
        f('contract.duration_months', 'Срок, мес.', { v: 'int', ph: '11', at: 'п. 1.4' }),
        f('contract.keys_count', 'Комплектов ключей', { v: 'int', ph: '1', at: 'п. 2.3' }),
        f('contract.prolongation_months', 'Пролонгация, мес.', { v: 'int', opt: true, ph: 'как срок', at: 'п. 8.4' }),
      ] },
    { id: 'landlord', title: 'Арендодатель', where: 'Реквизиты · подписи',
      lead: 'Данные собственника — как в паспорте.', places: ['Реквизиты сторон', 'п. 9 · подписи'],
      fields: [
        f('landlord.full_name', 'ФИО', { v: 'name', ph: 'Иванов Иван Иванович', at: 'реквизиты, подписи', wide: true }),
        f('landlord.passport_series', 'Серия паспорта', { v: 'ps', ph: '0000', at: 'реквизиты' }),
        f('landlord.passport_number', 'Номер паспорта', { v: 'pn', ph: '000000', at: 'реквизиты' }),
        f('landlord.passport_issued_by', 'Кем выдан', { ph: 'ГУ МВД России по …', at: 'реквизиты', wide: true }),
        f('landlord.passport_issued_date', 'Дата выдачи', { v: 'date', ph: 'ДД.ММ.ГГГГ', at: 'реквизиты' }),
        f('landlord.phone', 'Телефон', { v: 'phone', ph: '+7', at: 'реквизиты' }),
        f('landlord.registration_address', 'Адрес регистрации', { ph: 'г. …, ул. …, д. …', at: 'реквизиты', wide: true }),
        f('landlord.email', 'E-mail', { v: 'email', opt: true, ph: 'name@mail.ru', at: 'реквизиты' }),
      ] },
    { id: 'tenant', title: 'Арендатор', where: 'Реквизиты · подписи',
      lead: 'Данные жильца — как в паспорте. Телефон нужен для уведомлений.', places: ['Реквизиты сторон', 'п. 9 · подписи'],
      fields: [
        f('tenant.full_name', 'ФИО', { v: 'name', ph: 'Петров Пётр Петрович', at: 'реквизиты, подписи', wide: true }),
        f('tenant.date_of_birth', 'Дата рождения', { v: 'date', ph: 'ДД.ММ.ГГГГ', at: 'реквизиты' }),
        f('tenant.phone', 'Телефон', { v: 'phone', ph: '+7', at: 'реквизиты' }),
        f('tenant.passport_series', 'Серия паспорта', { v: 'ps', ph: '0000', at: 'реквизиты' }),
        f('tenant.passport_number', 'Номер паспорта', { v: 'pn', ph: '000000', at: 'реквизиты' }),
        f('tenant.passport_issued_by', 'Кем выдан', { ph: 'ГУ МВД России по …', at: 'реквизиты', wide: true }),
        f('tenant.passport_issued_date', 'Дата выдачи', { v: 'date', ph: 'ДД.ММ.ГГГГ', at: 'реквизиты' }),
        f('tenant.email', 'E-mail', { v: 'email', opt: true, ph: 'name@mail.ru', at: 'реквизиты' }),
        f('tenant.registration_address', 'Адрес регистрации', { ph: 'г. …, ул. …, д. …', at: 'реквизиты', wide: true }),
      ] },
    { id: 'property', title: 'Квартира', where: 'п. 1 · приложения',
      lead: 'Адрес и данные из выписки ЕГРН.', places: ['Шапка', 'п. 1.1', 'Приложения 1–2'],
      fields: [
        f('property.address.city', 'Город', { ph: 'Москва', at: 'п. 1.1' }),
        f('property.address.street', 'Улица', { ph: 'ул. …', at: 'п. 1.1' }),
        f('property.address.house', 'Дом', { ph: '10', at: 'п. 1.1' }),
        f('property.address.building', 'Корпус', { opt: true, ph: '2', at: 'п. 1.1' }),
        f('property.address.apartment', 'Квартира', { ph: '42', at: 'п. 1.1' }),
        f('property.address.floor', 'Этаж', { opt: true, ph: '5', at: 'п. 1.1' }),
        f('property.cadastral_number', 'Кадастровый номер', { v: 'cad', ph: '77:01:0000000:000', at: 'п. 1.1' }),
        f('property.area', 'Площадь, м²', { v: 'dec', ph: '45', at: 'п. 1.1' }),
        f('property.type', 'Тип помещения', { ph: 'Квартира', at: 'п. 1.1', adv: true }),
        f('property.ownership', 'Форма собственности', { select: OWNERSHIP, at: 'п. 1.2', adv: true }),
      ] },
    { id: 'financial', title: 'Платежи', where: 'п. 3 · п. 6',
      lead: 'Сколько и когда платить. Суммы прописью договор добавит сам.', places: ['п. 3.1–3.4', 'п. 6.1'],
      fields: [
        f('financial.monthly_rent', 'Аренда в месяц, ₽', { v: 'money', ph: '60000', at: 'п. 3.1' }),
        f('financial.security_deposit', 'Обеспечительный платёж, ₽', { v: 'money', ph: '30000', at: 'п. 3.2' }),
        f('financial.payment_period_start', 'Оплата с числа', { v: 'day', ph: '18', at: 'п. 3.1' }),
        f('financial.payment_period_end', 'по число', { v: 'day', ph: '20', at: 'п. 3.1' }),
        f('financial.first_payment_deadline', 'Первый платёж до', { v: 'date', ph: 'ДД.ММ.ГГГГ', at: 'п. 3.1' }),
        f('financial.deposit_deadline', 'Залог до', { v: 'date', ph: 'ДД.ММ.ГГГГ', at: 'п. 3.2' }),
        f('financial.penalty_rate', 'Пени, % в день', { v: 'rate', ph: '0,1', at: 'п. 6.1' }),
        f('financial.sbp_phone', 'Телефон для СБП', { v: 'phone', ph: '+7', at: 'п. 3.4' }),
      ] },
    { id: 'bank', title: 'Реквизиты', where: 'п. 3.4',
      lead: 'Счёт для перевода, если оплата не по СБП.', places: ['п. 3.4'],
      fields: [
        f('bank_details.recipient', 'Получатель', { v: 'name', ph: 'ФИО полностью', at: 'п. 3.4', wide: true }),
        f('bank_details.account_number', 'Номер счёта', { v: 'acc', ph: '20 цифр', at: 'п. 3.4', wide: true, mono: true }),
        f('bank_details.bank_name', 'Банк', { ph: 'ПАО «…»', at: 'п. 3.4' }),
        f('bank_details.bik', 'БИК', { v: 'bik', ph: '9 цифр', at: 'п. 3.4', mono: true }),
        f('bank_details.correspondent_account', 'Корр. счёт', { v: 'acc', ph: '20 цифр', at: 'п. 3.4', mono: true }),
        f('bank_details.inn', 'ИНН банка', { v: 'inn', ph: '10 цифр', at: 'п. 3.4', mono: true }),
        f('bank_details.kpp', 'КПП', { v: 'kpp', opt: true, ph: '9 цифр', at: 'п. 3.4', adv: true, mono: true }),
        f('bank_details.payment_purpose', 'Назначение платежа', { opt: true, ph: 'Перевод по договору аренды…', at: 'п. 3.4', adv: true, wide: true }),
      ] },
    { id: 'inventory', title: 'Опись имущества', where: 'Приложение 1',
      lead: 'Мебель и техника, которые остаются в квартире. Серийный номер и состояние — если есть; пустые ячейки можно заполнить при передаче.',
      places: ['Приложение № 1 · таблица'], fields: [] },
    { id: 'meters', title: 'Счётчики', where: 'Приложение 2',
      lead: 'Номера и показания на день передачи ключей. Можно оставить пустыми и вписать при передаче.', places: ['Приложение № 2'],
      fields: [
        f('meters.electricity.number', 'Электричество · №', { opt: true, ph: 'номер счётчика', at: 'Приложение 2', mono: true }),
        f('meters.electricity.reading', 'Показания', { opt: true, ph: 'кВт·ч', at: 'Приложение 2' }),
        f('meters.cold_water.number', 'Холодная вода · №', { opt: true, ph: 'номер счётчика', at: 'Приложение 2', mono: true }),
        f('meters.cold_water.reading', 'Показания', { opt: true, ph: 'м³', at: 'Приложение 2' }),
        f('meters.hot_water.number', 'Горячая вода · №', { opt: true, ph: 'номер счётчика', at: 'Приложение 2', mono: true }),
        f('meters.hot_water.reading', 'Показания', { opt: true, ph: 'м³', at: 'Приложение 2' }),
        f('meters.electricity.date', 'Дата показаний: электричество', { opt: true, ph: 'дата начала аренды', at: 'Приложение 2', adv: true }),
        f('meters.cold_water.date', 'Дата показаний: холодная вода', { opt: true, ph: 'дата начала аренды', at: 'Приложение 2', adv: true }),
        f('meters.hot_water.date', 'Дата показаний: горячая вода', { opt: true, ph: 'дата начала аренды', at: 'Приложение 2', adv: true }),
      ] },
    { id: 'rules', title: 'Правила', where: 'п. 1.6 · п. 5 · п. 7 · п. 8',
      lead: 'Сроки уведомлений и условия проживания.', places: ['п. 1.6', 'п. 5', 'п. 7.2', 'п. 8'],
      fields: [
        f('rules.max_additional_residents', 'Доп. жильцов, не более', { v: 'int', ph: '1', at: 'п. 1.6' }),
        f('rules.animals_allowed_by_default', 'Животные', { bool: ['Запрещены', 'Разрешены'], at: 'п. 1.6' }),
        f('rules.meters_submission_day', 'Показания до числа', { v: 'day', ph: '15', at: 'п. 5' }),
        f('rules.utility_payment_days', 'Оплата счетов, раб. дн.', { v: 'int', ph: '5', at: 'п. 7.2' }),
        f('rules.termination_notice_days', 'Уведомление о расторжении, дн.', { v: 'int', ph: '30', at: 'п. 8' }),
        f('rules.deposit_return_days', 'Возврат залога, дн.', { v: 'int', ph: '10', at: 'п. 8' }),
        f('rules.notification_days_for_residents', 'Уведомить о новых жильцах за, дн.', { v: 'int', ph: '3', at: 'п. 1.6', adv: true }),
        f('rules.meters_submission_time', 'Показания до, время', { v: 'time', ph: '23:00', at: 'п. 5', adv: true }),
        f('rules.eviction_days', 'Освободить квартиру за, дн.', { v: 'int', ph: '7', at: 'п. 8', adv: true }),
        f('rules.prolongation_notice_days', 'Уведомление о пролонгации, дн.', { v: 'int', opt: true, ph: 'как расторжение', at: 'п. 8', adv: true }),
        f('rules.indexation_notice_days', 'Уведомление об индексации, дн.', { v: 'int', opt: true, ph: 'как расторжение', at: 'п. 3', adv: true }),
      ] },
  ];
  const FIELD_BY_PATH = {};
  const STEP_OF_PATH = {};
  STEPS.forEach((s) => s.fields.forEach((fd) => { FIELD_BY_PATH[fd.path] = fd; STEP_OF_PATH[fd.path] = s.id; }));

  // ------------------------------------------------------------------ данные
  function emptyData() {
    return {
      contract: { conclusion_date: '', conclusion_city: '', start_date: '', duration_months: 11, keys_count: 1 },
      landlord: { full_name: '', passport_series: '', passport_number: '', passport_issued_by: '', passport_issued_date: '', registration_address: '', phone: '', email: '' },
      tenant: { full_name: '', date_of_birth: '', passport_series: '', passport_number: '', passport_issued_by: '', passport_issued_date: '', registration_address: '', phone: '', email: '' },
      property: { type: 'Квартира', address: { city: '', street: '', house: '', building: '', apartment: '', floor: '' }, cadastral_number: '', area: '', ownership: OWNERSHIP[0] },
      financial: { monthly_rent: '', security_deposit: '', payment_period_start: '', payment_period_end: '', first_payment_deadline: '', deposit_deadline: '', penalty_rate: 0.1, sbp_phone: '' },
      bank_details: { recipient: '', account_number: '', payment_purpose: '', bik: '', bank_name: '', correspondent_account: '', inn: '', kpp: '' },
      inventory: [],
      meters: { electricity: { number: '', reading: '', date: '' }, cold_water: { number: '', reading: '', date: '' }, hot_water: { number: '', reading: '', date: '' } },
      rules: { max_additional_residents: 1, notification_days_for_residents: 3, animals_allowed_by_default: false, meters_submission_day: 15, meters_submission_time: '23:00', utility_payment_days: 5, termination_notice_days: 30, eviction_days: 7, deposit_return_days: 10 },
    };
  }

  function normalizeItem(it) {
    if (typeof it === 'string') it = { name: it };
    it = it || {};
    return { name: String(it.name || ''), serial: String(it.serial || ''), quantity: Number.isInteger(it.quantity) && it.quantity > 0 ? it.quantity : 1, condition: String(it.condition || '') };
  }

  function fromJson(obj) {
    const d = deepMerge(emptyData(), clone(obj || {}));
    d.inventory = Array.isArray(d.inventory) ? d.inventory.map(normalizeItem) : [];
    return d;
  }

  /** Данные для сервера и файла .json: пустые необязательные числа убираются, даты счётчиков подставляются. */
  function toJson() {
    const d = clone(state.data);
    for (const p of ['contract.prolongation_months', 'rules.prolongation_notice_days', 'rules.indexation_notice_days']) {
      if (isBlank(getPath(d, p))) setPath(d, p, undefined);
    }
    for (const m of ['electricity', 'cold_water', 'hot_water']) {
      if (isBlank(d.meters[m].date)) d.meters[m].date = longDate(d.contract.start_date);
    }
    d.inventory = d.inventory.filter((it) => !isBlank(it.name)).map((it) => {
      const o = { name: it.name.trim(), serial: it.serial.trim(), quantity: it.quantity, condition: it.condition.trim() };
      return o;
    });
    return d;
  }

  // ------------------------------------------------------------------ состояние
  const STORE_KEY = 'docops-arenda:draft';
  const NOSAVE_KEY = 'docops-arenda:nosave';
  const state = {
    data: emptyData(),
    step: 'contract',
    focus: null,
    touched: {},        // путь -> поле покидали хотя бы раз
    serverErrors: {},   // путь -> сообщение
    serverList: [],     // ошибки без поля
    save: true,
    busy: false,
  };

  function storageGet(k) { try { return window.localStorage.getItem(k); } catch (e) { return null; } }
  function storageSet(k, v) { try { if (v === null) window.localStorage.removeItem(k); else window.localStorage.setItem(k, v); } catch (e) { /* приватный режим */ } }

  let saveTimer = null;
  function persist() {
    if (!state.save) return;
    clearTimeout(saveTimer);
    saveTimer = setTimeout(() => storageSet(STORE_KEY, JSON.stringify({ data: state.data, step: state.step })), 300);
  }

  // ------------------------------------------------------------------ проверка поля
  function fieldError(fd, value) {
    const v = value === undefined ? getPath(state.data, fd.path) : value;
    if (isBlank(v)) return '';
    if (state.serverErrors[fd.path]) return state.serverErrors[fd.path];
    if (fd.v && V[fd.v]) {
      const msg = V[fd.v](v);
      if (msg) return msg;
    }
    if (fd.path === 'financial.payment_period_start') {
      const end = state.data.financial.payment_period_end;
      if (Number.isInteger(v) && Number.isInteger(end) && v > end) return 'Не позже, чем «по число»';
    }
    return '';
  }
  const isOk = (fd) => !isBlank(getPath(state.data, fd.path)) && !fieldError(fd);

  function stepStats(step) {
    if (step.id === 'inventory') {
      const n = state.data.inventory.filter((it) => !isBlank(it.name)).length;
      return { req: 0, ok: 0, count: n + ' шт.', done: n > 0 };
    }
    const req = step.fields.filter((fd) => !fd.opt && !fd.select && !fd.bool);
    const ok = req.filter(isOk).length;
    const optBad = step.fields.some((fd) => fd.opt && fieldError(fd));
    if (!req.length) {
      const filled = step.fields.filter((fd) => !fd.adv && !isBlank(getPath(state.data, fd.path))).length;
      const total = step.fields.filter((fd) => !fd.adv).length;
      return { req: 0, ok: 0, count: 'необяз.', done: filled === total && !optBad };
    }
    return { req: req.length, ok, count: ok + '/' + req.length, done: ok === req.length && !optBad };
  }

  function totals() {
    let req = 0, ok = 0, optBad = 0;
    for (const s of STEPS) {
      const st = stepStats(s);
      req += st.req; ok += st.ok;
      optBad += s.fields.filter((fd) => fd.opt && fieldError(fd)).length;
    }
    const badInv = state.data.inventory.filter((it) => isBlank(it.name) && (it.serial || it.condition)).length;
    return { req, ok, left: req - ok + optBad + badInv };
  }

  // ------------------------------------------------------------------ значения поля
  function displayValue(fd) {
    const v = getPath(state.data, fd.path);
    if (v === undefined || v === null) return '';
    if (fd.v === 'rate' && typeof v === 'number') return String(v).replace('.', ',');
    return String(v);
  }

  function parseInput(fd, raw) {
    if (fd.v === 'date') {
      const g = raw.replace(/\D/g, '').slice(0, 8);
      return g.slice(0, 2) + (g.length > 2 ? '.' + g.slice(2, 4) : '') + (g.length > 4 ? '.' + g.slice(4) : '');
    }
    if (NUMERIC[fd.v]) {
      const t = raw.replace(/\s/g, '');
      if (t === '') return '';
      if (fd.v === 'rate') return /^\d+([.,]\d+)?$/.test(t) ? parseFloat(t.replace(',', '.')) : raw;
      return /^\d+$/.test(t) ? parseInt(t, 10) : raw;
    }
    return raw;
  }

  // ------------------------------------------------------------------ навигация
  function renderSteps() {
    const list = $('steps');
    list.textContent = '';
    STEPS.forEach((s, i) => {
      const st = stepStats(s);
      const btn = h('button', {
        class: 'step', type: 'button', 'aria-current': s.id === state.step ? 'step' : null,
        onclick: () => goStep(s.id),
      }, [
        h('span', { class: 'dot' + (st.done ? ' done' : '') }, [st.done ? ICON_CHECK() : String(i + 1)]),
        h('span', { class: 'step-text' }, [
          h('span', { class: 'step-title', text: s.title }),
          h('span', { class: 'step-where', text: s.where }),
        ]),
        h('span', { class: 'step-count', text: st.count }),
      ]);
      list.appendChild(h('li', null, [btn]));
    });
    const t = totals();
    $('progress').max = Math.max(t.req, 1);
    $('progress').value = t.ok;
    $('progress-text').textContent = t.ok + ' из ' + t.req;
  }

  function goStep(id, focusPath) {
    state.step = id;
    state.focus = null;
    state.scrollToStep = true;
    renderAll(true);
    persist();
    setView('form');
    const card = $('form');
    if (focusPath) {
      const el = card.querySelector('[data-path="' + focusPath + '"]');
      if (el) {
        const det = el.closest('details');
        if (det) det.open = true;
        el.focus();
        return;
      }
    }
    if (card.getBoundingClientRect().top < 0) card.scrollIntoView({ block: 'start' });
    const title = $('form-title');
    if (title) title.focus({ preventScroll: true });
  }

  // ------------------------------------------------------------------ форма
  const fieldEls = {}; // путь -> {wrap, input, msg}

  function renderField(fd) {
    let input;
    if (fd.select || fd.bool) {
      const cur = getPath(state.data, fd.path);
      const opts = fd.bool ? [['false', fd.bool[0]], ['true', fd.bool[1]]] : fd.select.map((o) => [o, o]);
      if (fd.select && !isBlank(cur) && fd.select.indexOf(cur) < 0) opts.push([cur, cur]); // значение из импортированного .json
      input = h('select', { class: 'inp', 'data-path': fd.path }, opts.map(([v, t]) => h('option', { value: v, text: t })));
      input.value = fd.bool ? String(!!cur) : (cur || fd.select[0]);
      input.addEventListener('change', () => {
        setPath(state.data, fd.path, fd.bool ? input.value === 'true' : input.value);
        changed(fd.path);
      });
    } else {
      input = h('input', {
        class: 'inp' + (fd.mono ? ' mono' : ''), 'data-path': fd.path, placeholder: fd.ph,
        inputmode: INPUTMODE[fd.v] || null, maxlength: MAXLEN[fd.v] || null, autocomplete: 'off', spellcheck: 'false',
      });
      input.value = displayValue(fd);
      input.addEventListener('input', () => {
        let v = parseInput(fd, input.value);
        if (fd.v === 'date' && v !== input.value) {
          const atEnd = input.selectionStart === input.value.length;
          input.value = v;
          if (atEnd) input.setSelectionRange(v.length, v.length);
        }
        if (typeof v === 'string' && !NUMERIC[fd.v]) v = v.replace(/^\s+/, '');
        delete state.serverErrors[fd.path];
        setPath(state.data, fd.path, v);
        changed(fd.path);
      });
      input.addEventListener('blur', () => {
        state.touched[fd.path] = true;
        state.focus = null;
        updateField(fd);
        renderPreview();
      });
    }
    input.addEventListener('focus', () => { state.focus = fd.path; renderPreview(); });
    const msg = h('span');
    const wrap = h('label', { class: 'fld' + (fd.wide ? ' wide' : '') }, [
      h('span', { class: 'lbl' }, [fd.label, fd.opt ? h('span', { class: 'opt', text: 'необязательно' }) : null]),
      input, msg,
    ]);
    fieldEls[fd.path] = { wrap, input, msg, fd };
    updateField(fd);
    return wrap;
  }

  function updateField(fd) {
    const el = fieldEls[fd.path];
    if (!el) return;
    const err = fieldError(fd);
    const showErr = !!err && (state.focus !== fd.path || !!state.serverErrors[fd.path]) &&
      (state.touched[fd.path] || !!state.serverErrors[fd.path] || state.focus !== fd.path);
    const empty = !fd.opt && isBlank(getPath(state.data, fd.path));
    el.wrap.className = 'fld' + (fd.wide ? ' wide' : '') + (showErr ? ' bad' : (empty ? ' empty' : ''));
    el.input.setAttribute('aria-invalid', showErr ? 'true' : 'false');
    el.msg.className = showErr ? 'err' : 'at';
    el.msg.textContent = showErr ? err : '→ ' + fd.at + (fd.hint ? ' · ' + fd.hint : '');
  }

  function renderForm() {
    const step = STEPS.find((s) => s.id === state.step);
    const idx = STEPS.indexOf(step);
    const card = $('form');
    card.textContent = '';
    for (const k of Object.keys(fieldEls)) delete fieldEls[k];

    card.appendChild(h('div', { class: 'form-head' }, [
      h('span', { class: 'eyebrow', text: 'Шаг ' + (idx + 1) + ' из ' + STEPS.length }),
      h('h1', { id: 'form-title', tabindex: '-1', text: step.title }),
      h('p', { class: 'lead', text: step.lead }),
      h('div', { class: 'places' }, step.places.map((p) => h('span', { class: 'place', text: p }))),
    ]));

    if (step.id === 'inventory') card.appendChild(renderInventory());
    else {
      const main = step.fields.filter((fd) => !fd.adv);
      const adv = step.fields.filter((fd) => fd.adv);
      card.appendChild(h('div', { class: 'grid' }, main.map(renderField)));
      if (adv.length) {
        const openAdv = adv.some((fd) => fieldError(fd) || state.serverErrors[fd.path] || (!fd.opt && isBlank(getPath(state.data, fd.path))));
        card.appendChild(h('details', { class: 'more', open: openAdv || null }, [
          h('summary', { text: 'Дополнительно · ' + adv.length }),
          h('div', { class: 'grid' }, adv.map(renderField)),
        ]));
      }
    }

    const next = STEPS[idx + 1];
    card.appendChild(h('div', { class: 'form-foot' }, [
      h('button', { class: 'btn ghost', type: 'button', disabled: idx === 0 || null, onclick: () => goStep(STEPS[idx - 1].id) }, '← Назад'),
      next ? h('button', { class: 'btn primary', type: 'button', onclick: () => goStep(next.id) }, 'Далее: ' + next.title + ' →') : null,
    ]));
  }

  // опись
  function renderInventory() {
    const inv = state.data.inventory;
    const rows = [h('div', { class: 'inv-row inv-head' }, [
      h('span', { text: '№' }), h('span', { text: 'Наименование' }),
      h('span', { class: 'h-sn' }, ['Серийный номер ', h('span', { class: 'opt', text: 'если есть' })]),
      h('span', { text: 'Кол-во' }),
      h('span', { class: 'h-cond' }, ['Состояние ', h('span', { class: 'opt', text: 'если нужно' })]),
      h('span'),
    ])];

    const cell = (cls, value, label, ph, onInput, extra) => {
      const i = h('input', Object.assign({ class: 'inp ' + cls, 'aria-label': label, placeholder: ph, autocomplete: 'off' }, extra || {}));
      i.value = value;
      i.addEventListener('input', () => onInput(i));
      return i;
    };
    const qtyValue = (i) => { const n = parseInt(i.value.replace(/\D/g, ''), 10); return Number.isInteger(n) && n > 0 ? n : 1; };

    inv.forEach((it, i) => {
      const n = i + 1;
      const upd = (key, val) => { it[key] = val; changed('inventory'); };
      rows.push(h('div', { class: 'inv-row' }, [
        h('span', { class: 'inv-n', text: String(n) }),
        cell('', it.name, 'Наименование, пункт ' + n, 'наименование', (el) => upd('name', el.value)),
        cell('mono sn', it.serial, 'Серийный номер, пункт ' + n, 'с/н — нет', (el) => upd('serial', el.value)),
        cell('qty', String(it.quantity), 'Количество, пункт ' + n, '1', (el) => upd('quantity', qtyValue(el)), { inputmode: 'numeric', maxlength: '3' }),
        cell('cond', it.condition, 'Состояние, пункт ' + n, 'состояние', (el) => upd('condition', el.value)),
        h('button', { class: 'icobtn', type: 'button', 'aria-label': 'Удалить пункт ' + n, onclick: () => { inv.splice(i, 1); changed('inventory', true); } }, [ICON_X()]),
      ]));
    });

    const draft = { name: '', serial: '', quantity: 1, condition: '' };
    const add = () => {
      if (isBlank(draft.name)) { newName.focus(); return; }
      inv.push(normalizeItem({ name: draft.name.trim(), serial: draft.serial.trim(), quantity: draft.quantity, condition: draft.condition.trim() }));
      changed('inventory', true);
      const fresh = $('form').querySelector('.inv-new input');
      if (fresh) fresh.focus();
    };
    const onKey = (e) => { if (e.key === 'Enter') { e.preventDefault(); add(); } };
    const newName = cell('', '', 'Новый предмет: наименование', 'Например, холодильник', (el) => { draft.name = el.value; });
    const newRow = h('div', { class: 'inv-row inv-new' }, [
      h('span', { class: 'inv-n', text: String(inv.length + 1) }),
      newName,
      cell('mono sn', '', 'Новый предмет: серийный номер', 'серийный номер', (el) => { draft.serial = el.value; }),
      cell('qty', '1', 'Новый предмет: количество', '1', (el) => { draft.quantity = qtyValue(el); }, { inputmode: 'numeric', maxlength: '3' }),
      cell('cond', '', 'Новый предмет: состояние', 'состояние', (el) => { draft.condition = el.value; }),
      h('button', { class: 'icobtn add', type: 'button', 'aria-label': 'Добавить предмет', onclick: add }, [ICON_PLUS()]),
    ]);
    newRow.querySelectorAll('input').forEach((el) => el.addEventListener('keydown', onKey));
    rows.push(newRow);
    rows.push(h('span', { class: 'at', text: '→ Приложение № 1 — таблица: № · наименование · серийный номер («—», если нет) · кол-во · состояние' }));
    return h('div', { class: 'inv' }, rows);
  }

  // ------------------------------------------------------------------ предпросмотр
  function renderPreview() {
    const d = state.data;
    const doc = $('doc');
    const scroll = doc.scrollTop;
    doc.textContent = '';

    const tok = (path, opts) => {
      const fd = FIELD_BY_PATH[path];
      const v = getPath(d, path);
      const on = STEP_OF_PATH[path] === state.step ? ' on' : '';
      const hit = state.focus === path ? ' hit' : '';
      if (!isBlank(v)) {
        let t = String(v);
        if (opts && opts.fmt && !fieldError(fd)) t = opts.fmt(v);
        return h('span', { class: 'f' + on + hit, text: t });
      }
      if (opts && opts.fallback) return h('span', { class: 'f' + hit, text: opts.fallback });
      if (fd && fd.opt) return h('span', { class: 'b' + hit, text: '________' });
      return h('span', { class: 'e' + on + hit, text: (fd ? fd.label : path).replace(' · №', '').replace(/, (мес|₽|м²|дн)\.?$/, '').toLowerCase() });
    };
    const blk = (steps, tagStep, tagText, children) => h('div', { class: 'blk ' + (steps.indexOf(state.step) >= 0 ? 'on' : 'dim') }, [
      h('button', { class: 'tag', type: 'button', onclick: () => goStep(tagStep), text: tagText }),
    ].concat(children));
    const P = (children, cls) => h('p', { class: cls || null }, children);
    const money = (v) => fmtInt(v) + ' ₽';

    const city = d.property.address.city;
    doc.appendChild(blk(['contract', 'property'], 'contract', 'Условия', [
      P(['Договор аренды помещения для проживания'], 'title'),
      h('p', { class: 'city-line' }, [
        h('span', null, ['г. ', tok('contract.conclusion_city', { fallback: city || undefined })]),
        tok('contract.conclusion_date', { fmt: quotedDate }),
      ]),
    ]));

    const party = (who, title, dob) => h('div', null, [
      P([title], 'h'),
      P([tok(who + '.full_name'), dob ? ', ' : '', dob ? tok(who + '.date_of_birth') : '', dob ? ' г.р.' : '',
        ', паспорт ', tok(who + '.passport_series'), ' № ', tok(who + '.passport_number'),
        ', выдан ', tok(who + '.passport_issued_by'), ' ', tok(who + '.passport_issued_date'),
        '. Адрес регистрации: ', tok(who + '.registration_address'),
        '. Тел. ', tok(who + '.phone'), ', e-mail ', tok(who + '.email')]),
    ]);
    doc.appendChild(blk(['landlord', 'tenant'], state.step === 'tenant' ? 'tenant' : 'landlord', 'Стороны', [
      h('div', { class: 'cols' }, [party('landlord', 'Арендодатель'), party('tenant', 'Арендатор', true)]),
    ]));

    const a = 'property.address.';
    const addrParts = ['г. ', tok(a + 'city'), ', ', tok(a + 'street'), ', д. ', tok(a + 'house')];
    if (!isBlank(d.property.address.building) || state.step === 'property') addrParts.push(', корп. ', tok(a + 'building'));
    addrParts.push(', кв. ', tok(a + 'apartment'));
    if (!isBlank(d.property.address.floor) || state.step === 'property') addrParts.push(', этаж ', tok(a + 'floor'));
    doc.appendChild(blk(['property', 'contract', 'rules'], 'property', 'Квартира', [
      P(['1. Предмет Договора'], 'h'),
      P(['1.1. Арендодатель предоставляет, а Арендатор принимает во временное пользование помещение (', tok('property.type'), ') по адресу: ']
        .concat(addrParts, ['; кадастровый номер ', tok('property.cadastral_number'), ', общая площадь ', tok('property.area'), ' м².'])),
      P(['1.2. Помещение принадлежит Арендодателю на праве ', tok('property.ownership'), '.']),
      P(['1.4. Срок аренды — ', tok('contract.duration_months'), ' мес. с ', tok('contract.start_date', { fmt: longDate }), '.']),
      P(['1.6. Совместно с Арендатором могут проживать не более ', tok('rules.max_additional_residents'), ' чел. (уведомление за ',
        tok('rules.notification_days_for_residents'), ' дн.). Животные: ',
        h('span', { class: 'f' + (state.step === 'rules' ? ' on' : '') + (state.focus === 'rules.animals_allowed_by_default' ? ' hit' : ''), text: d.rules.animals_allowed_by_default ? 'разрешены' : 'запрещены' }), '.']),
    ]));

    doc.appendChild(blk(['contract'], 'contract', 'Условия', [
      P(['2. Приёмка — передача Помещения'], 'h'),
      P(['2.3. Арендатору передаётся ', tok('contract.keys_count'), ' компл. ключей.']),
    ]));

    doc.appendChild(blk(['financial', 'bank'], state.step === 'bank' ? 'bank' : 'financial', 'Платежи', [
      P(['3. Расчёты'], 'h'),
      P(['3.1. Арендная плата — ', tok('financial.monthly_rent', { fmt: money }), ' в месяц, вносится с ', tok('financial.payment_period_start'),
        ' по ', tok('financial.payment_period_end'), ' число. Первый платёж — до ', tok('financial.first_payment_deadline'), '.']),
      P(['3.2. Обеспечительный платёж — ', tok('financial.security_deposit', { fmt: money }), ', до ', tok('financial.deposit_deadline'), '.']),
      P(['3.4. Оплата по СБП на номер ', tok('financial.sbp_phone'), ' или на счёт ', tok('bank_details.account_number'),
        ', получатель ', tok('bank_details.recipient'), ', ', tok('bank_details.bank_name'), ', БИК ', tok('bank_details.bik'),
        ', к/с ', tok('bank_details.correspondent_account'), ', ИНН ', tok('bank_details.inn'), ', КПП ', tok('bank_details.kpp'), '.']),
    ]));

    doc.appendChild(blk(['rules'], 'rules', 'Правила', [
      P(['4–5. Права и обязанности Сторон'], 'h'),
      P(['Арендатор ежемесячно до ', tok('rules.meters_submission_day'), ' числа, до ', tok('rules.meters_submission_time'), ', передаёт показания приборов учёта…']),
    ]));
    doc.appendChild(blk(['financial'], 'financial', 'Платежи', [
      P(['6. Ответственность Сторон'], 'h'),
      P(['За просрочку платежа начисляются пени ', tok('financial.penalty_rate', { fmt: (v) => String(v).replace('.', ',') }), '% от суммы долга за каждый день.']),
    ]));
    doc.appendChild(blk(['rules', 'contract'], 'rules', 'Правила', [
      P(['7–8. Коммунальные платежи. Расторжение'], 'h'),
      P(['Счета оплачиваются в течение ', tok('rules.utility_payment_days'), ' раб. дней. О расторжении Сторона уведомляет за ',
        tok('rules.termination_notice_days'), ' дн.; Арендатор освобождает Помещение в течение ', tok('rules.eviction_days'),
        ' дн.; обеспечительный платёж возвращается в течение ', tok('rules.deposit_return_days'), ' дн. Договор продлевается на ',
        tok('contract.prolongation_months', { fallback: isBlank(d.contract.duration_months) ? undefined : String(d.contract.duration_months) }), ' мес.']),
    ]));
    doc.appendChild(blk(['landlord', 'tenant'], state.step === 'tenant' ? 'tenant' : 'landlord', 'Стороны', [
      P(['9. Подписи Сторон'], 'h'),
      h('div', { class: 'cols' }, [
        P(['Арендодатель', h('br'), '______ / ', tok('landlord.full_name')]),
        P(['Арендатор', h('br'), '______ / ', tok('tenant.full_name')]),
      ]),
    ]));

    doc.appendChild(h('hr'));

    const invOn = state.step === 'inventory' ? ' on' : '';
    const items = d.inventory.filter((it) => !isBlank(it.name));
    const C = (t, cls) => h('span', { class: 'c' }, [cls ? h('span', { class: cls, text: t }) : t]);
    const rows = [h('div', { class: 'th' }, [C('№'), C('Наименование'), C('Серийный №'), C('Кол.'), C('Состояние')])];
    items.forEach((it, i) => rows.push(h('div', null, [
      C(String(i + 1)), C(it.name, 'f' + invOn),
      it.serial.trim() ? C(it.serial, 'f' + invOn) : C('—', 'b'),
      C(it.quantity + ' шт.', 'f' + invOn),
      it.condition.trim() ? C(it.condition, 'f' + invOn) : C(''),
    ])));
    if (!items.length) rows.push(h('div', null, [C('1'), C('______________', 'b'), C('', null), C('', null), C('', null)]));
    doc.appendChild(blk(['inventory', 'property'], 'inventory', 'Опись', [
      P(['Приложение № 1 · Опись имущества'], 'h'),
      h('div', { class: 'dt' }, rows),
    ]));

    const meter = (title, key) => P([title + ': № ', tok('meters.' + key + '.number'), ', показания ', tok('meters.' + key + '.reading'),
      ' на ', tok('meters.' + key + '.date', { fallback: longDate(d.contract.start_date) || undefined })]);
    doc.appendChild(blk(['meters', 'property'], 'meters', 'Счётчики', [
      P(['Приложение № 2 · Показания счётчиков'], 'h'),
      meter('Электроэнергия', 'electricity'), meter('Холодная вода', 'cold_water'), meter('Горячая вода', 'hot_water'),
    ]));

    doc.scrollTop = scroll;
    if (state.scrollToStep) {
      state.scrollToStep = false;
      const first = doc.querySelector('.blk.on');
      if (first) {
        const dr = doc.getBoundingClientRect(), br = first.getBoundingClientRect();
        if (br.top < dr.top || br.top > dr.bottom - 80) doc.scrollTop += br.top - dr.top - 12;
      }
    }
    const hit = doc.querySelector('.hit');
    if (hit) {
      const dr = doc.getBoundingClientRect(), hr = hit.getBoundingClientRect();
      if (hr.top < dr.top || hr.bottom > dr.bottom) doc.scrollTop += hr.top - dr.top - dr.height / 3;
    }
  }

  // ------------------------------------------------------------------ готовность
  function renderReady() {
    const t = totals();
    const ready = t.left === 0 && !state.serverList.length;
    $('ready').className = 'ready' + (ready ? ' ok' : '');
    const title = $('ready-title');
    title.textContent = '';
    title.appendChild(ready
      ? svg(20, [{ circle: 1, cx: '10', cy: '10', r: '9', fill: '#2B50D8' }, { d: 'M6 10.3l2.6 2.4L14 7.5', stroke: '#fff', 'stroke-width': '1.8', 'stroke-linecap': 'round', 'stroke-linejoin': 'round' }], { box: '0 0 20 20' })
      : svg(20, [{ circle: 1, cx: '10', cy: '10', r: '8.25', stroke: '#B9B9B1', 'stroke-width': '1.5', 'stroke-dasharray': '3 3' }], { box: '0 0 20 20' }));
    title.appendChild(document.createTextNode(ready ? 'Обязательные пункты заполнены — договор готов' : 'Осталось заполнить или исправить: ' + t.left));
    $('btn-contract').disabled = !ready || state.busy;
    $('btn-summary').disabled = !ready || state.busy;

    const list = $('server-errors');
    list.textContent = '';
    const shown = state.serverList.concat(Object.keys(state.serverErrors).filter((p) => !FIELD_BY_PATH[p]).map((p) => ({ path: p, message: state.serverErrors[p] })));
    list.hidden = !shown.length;
    shown.forEach((e) => {
      const step = stepForPath(e.path);
      list.appendChild(h('li', null, [
        step ? h('button', { type: 'button', onclick: () => goStep(step), text: (e.path ? e.path + ': ' : '') + e.message }) : (e.path ? e.path + ': ' : '') + e.message,
      ]));
    });
  }

  function stepForPath(path) {
    if (!path) return null;
    if (STEP_OF_PATH[path]) return STEP_OF_PATH[path];
    if (path.startsWith('inventory')) return 'inventory';
    const prefix = { contract: 'contract', landlord: 'landlord', tenant: 'tenant', property: 'property', financial: 'financial', bank_details: 'bank', meters: 'meters', rules: 'rules' };
    return prefix[path.split('.')[0]] || null;
  }

  // ------------------------------------------------------------------ обновление
  function changed(path, rebuildForm) {
    if (path === 'financial.payment_period_end' && fieldEls['financial.payment_period_start']) updateField(FIELD_BY_PATH['financial.payment_period_start']);
    if (FIELD_BY_PATH[path]) updateField(FIELD_BY_PATH[path]);
    state.serverList = [];
    if (rebuildForm) renderForm();
    renderSteps();
    renderPreview();
    renderReady();
    persist();
  }

  function renderAll(withForm) {
    if (withForm) renderForm();
    renderSteps();
    renderPreview();
    renderReady();
  }

  // ------------------------------------------------------------------ сервер
  async function download(kind) {
    if (state.busy) return;
    state.busy = true;
    renderReady();
    try {
      const resp = await fetch('/api/' + kind, {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(toJson()),
      });
      if (resp.status === 422 || resp.status === 400) {
        const body = await resp.json();
        applyServerErrors(body.errors || []);
        toast('Проверьте отмеченные поля');
        return;
      }
      if (!resp.ok) throw new Error('HTTP ' + resp.status);
      const blob = await resp.blob();
      const cd = resp.headers.get('Content-Disposition') || '';
      const m = /filename\*=UTF-8''([^;]+)/.exec(cd);
      saveBlob(blob, m ? decodeURIComponent(m[1]) : kind + '.docx');
      if (state.save) toast('Документ скачан. Удалить черновик из этого браузера?', [['Удалить', () => { storageSet(STORE_KEY, null); toast('Черновик удалён из браузера'); }]]);
      else toast('Документ скачан');
    } catch (e) {
      toast('Не удалось связаться с локальным сервером. Он запущен? (' + e.message + ')');
    } finally {
      state.busy = false;
      renderReady();
    }
  }

  function applyServerErrors(errors) {
    state.serverErrors = {};
    state.serverList = [];
    for (const e of errors) {
      if (e.path && (FIELD_BY_PATH[e.path] || stepForPath(e.path))) state.serverErrors[e.path] = e.message;
      else state.serverList.push(e);
    }
    const first = errors.map((e) => e.path).find((p) => stepForPath(p));
    if (first) goStep(stepForPath(first), FIELD_BY_PATH[first] ? first : null);
    else renderAll(true);
  }

  function saveBlob(blob, name) {
    const url = URL.createObjectURL(blob);
    const a = h('a', { href: url, download: name });
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }

  // ------------------------------------------------------------------ уведомления
  let toastTimer = null;
  function toast(text, actions) {
    const el = $('toast');
    el.textContent = '';
    el.appendChild(h('span', { text }));
    for (const [label, fn] of actions || []) {
      el.appendChild(h('button', { class: 'btn small', type: 'button', onclick: () => { el.hidden = true; fn(); } }, label));
    }
    el.appendChild(h('button', { class: 'btn ghost small', type: 'button', 'aria-label': 'Закрыть', onclick: () => { el.hidden = true; } }, [ICON_X()]));
    el.hidden = false;
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => { el.hidden = true; }, actions ? 12000 : 5000);
  }

  // ------------------------------------------------------------------ вкладки (телефон)
  function setView(view) {
    document.body.dataset.view = view;
    $('tab-form').setAttribute('aria-selected', String(view === 'form'));
    $('tab-doc').setAttribute('aria-selected', String(view === 'doc'));
  }

  // ------------------------------------------------------------------ загрузка данных
  function loadData(obj, message) {
    state.data = fromJson(obj);
    state.touched = {};
    state.serverErrors = {};
    state.serverList = [];
    STEPS.forEach((s) => s.fields.forEach((fd) => { if (!isBlank(getPath(state.data, fd.path))) state.touched[fd.path] = true; }));
    renderAll(true);
    persist();
    if (message) toast(message);
  }

  // ------------------------------------------------------------------ запуск
  function init() {
    state.save = storageGet(NOSAVE_KEY) !== '1';
    $('chk-save').checked = state.save;
    $('draft-note').textContent = state.save ? 'Черновик хранится в этом браузере' : 'Черновик не сохраняется';

    const saved = state.save ? storageGet(STORE_KEY) : null;
    if (saved) {
      try {
        const obj = JSON.parse(saved);
        state.data = fromJson(obj.data);
        if (STEPS.some((s) => s.id === obj.step)) state.step = obj.step;
        STEPS.forEach((s) => s.fields.forEach((fd) => { if (!isBlank(getPath(state.data, fd.path))) state.touched[fd.path] = true; }));
      } catch (e) { /* испорченный черновик — начинаем с чистого листа */ }
    }

    $('chk-save').addEventListener('change', (e) => {
      state.save = e.target.checked;
      storageSet(NOSAVE_KEY, state.save ? null : '1');
      if (!state.save) storageSet(STORE_KEY, null); else persist();
      $('draft-note').textContent = state.save ? 'Черновик хранится в этом браузере' : 'Черновик не сохраняется';
    });

    const confirmBox = $('confirm-clear');
    $('btn-clear').addEventListener('click', () => { confirmBox.hidden = false; $('btn-clear').hidden = true; $('btn-clear-no').focus(); });
    $('btn-clear-no').addEventListener('click', () => { confirmBox.hidden = true; $('btn-clear').hidden = false; $('btn-clear').focus(); });
    $('btn-clear-yes').addEventListener('click', () => {
      confirmBox.hidden = true; $('btn-clear').hidden = false;
      storageSet(STORE_KEY, null);
      state.step = 'contract';
      loadData(emptyData(), 'Все данные стёрты');
    });

    $('btn-example').addEventListener('click', async () => {
      try {
        const resp = await fetch('/example.json');
        if (!resp.ok) throw new Error('HTTP ' + resp.status);
        loadData(await resp.json(), 'Загружен пример с вымышленными данными');
      } catch (e) { toast('Не удалось загрузить пример: ' + e.message); }
    });

    const fileInput = $('file-json');
    $('btn-open').addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', () => {
      const file = fileInput.files && fileInput.files[0];
      fileInput.value = '';
      if (!file) return;
      const reader = new FileReader();
      reader.onload = () => {
        try {
          const obj = JSON.parse(String(reader.result));
          if (!obj || typeof obj !== 'object' || Array.isArray(obj)) throw new Error('ожидается объект');
          loadData(obj, 'Загружено: ' + file.name);
        } catch (e) { toast('Не удалось прочитать ' + file.name + ': ' + e.message); }
      };
      reader.readAsText(file, 'utf-8');
    });

    $('btn-save').addEventListener('click', () => {
      const blob = new Blob([JSON.stringify(toJson(), null, 2) + '\n'], { type: 'application/json' });
      saveBlob(blob, 'contract_data.json');
    });

    $('btn-contract').addEventListener('click', () => download('contract'));
    $('btn-summary').addEventListener('click', () => download('summary'));
    $('tab-form').addEventListener('click', () => setView('form'));
    $('tab-doc').addEventListener('click', () => setView('doc'));

    renderAll(true);
  }

  init();
}());
