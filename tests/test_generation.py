# -*- coding: utf-8 -*-
"""Тесты генерации. Запуск из корня проекта: python3 -m unittest discover -s tests"""

import copy
import json
import os
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import contract_utils as cu  # noqa: E402
import create_contract  # noqa: E402
import create_summary  # noqa: E402

EXAMPLE = os.path.join(ROOT, 'example', 'contract_data.example.json')
TEMPLATE = os.path.join(ROOT, 'contract_data.template.json')
W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'


def example():
    with open(EXAMPLE, encoding='utf-8') as f:
        return json.load(f)


def build(module_body, data):
    return module_body(cu.with_defaults(data))


class NumberWords(unittest.TestCase):
    def test_nominative(self):
        self.assertEqual(cu.number_to_words(11), 'одиннадцать')
        self.assertEqual(cu.number_to_words(60000), 'шестьдесят тысяч')
        self.assertEqual(cu.number_to_words(21001, 'nom', 'f'), 'двадцать одна тысяча одна')
        self.assertEqual(cu.number_to_words(1, 'nom', 'n'), 'одно')

    def test_genitive(self):
        self.assertEqual(cu.number_to_words(10, 'gen'), 'десяти')
        self.assertEqual(cu.number_to_words(5, 'gen'), 'пяти')
        self.assertEqual(cu.number_to_words(7, 'gen'), 'семи')

    def test_counted(self):
        self.assertEqual(cu.counted(11, 'month'), '11 (одиннадцать) месяцев')
        self.assertEqual(cu.counted(12, 'month'), '12 (двенадцать) месяцев')
        self.assertEqual(cu.counted(1, 'person'), '1 (одно) дополнительное совершеннолетнее лицо')
        self.assertEqual(cu.counted(3, 'day'), '3 (три) дня')
        self.assertEqual(cu.counted(10, 'cal_day', 'gen'), '10 (десяти) календарных дней')
        self.assertEqual(cu.counted(1, 'cal_day', 'gen'), '1 (одного) календарного дня')
        self.assertEqual(cu.counted(5, 'work_day', 'gen'), '5 (пяти) рабочих дней')

    def test_money(self):
        self.assertEqual(cu.money(60000), '60 000 (шестьдесят тысяч) рублей')
        self.assertEqual(cu.money(60001), '60 001 (шестьдесят тысяч один) рубль')

    def test_out_of_range(self):
        with self.assertRaises(ValueError):
            cu.number_to_words(1000000)

    def test_percent(self):
        self.assertEqual(cu.fmt_percent(0.1), '0,1')
        self.assertEqual(cu.fmt_percent(1), '1')


class Validation(unittest.TestCase):
    def test_example_is_valid(self):
        self.assertEqual(cu.validate(example()), [])

    def test_template_placeholders_rejected(self):
        with open(TEMPLATE, encoding='utf-8') as f:
            errors = cu.validate(json.load(f))
        self.assertTrue(errors)
        self.assertTrue(any('заглушка' in e for e in errors))

    def test_missing_field(self):
        data = example()
        del data['tenant']['full_name']
        self.assertTrue(any('tenant.full_name' in e for e in cu.validate(data)))

    def test_bad_formats(self):
        data = example()
        data['contract']['start_date'] = '2025-11-19'
        data['bank_details']['bik'] = '123'
        data['financial']['monthly_rent'] = '60000'
        errors = ' '.join(cu.validate(data))
        self.assertIn('contract.start_date', errors)
        self.assertIn('bank_details.bik', errors)
        self.assertIn('financial.monthly_rent', errors)

    def test_cli_reports_errors(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad = os.path.join(tmp, 'bad.json')
            with open(bad, 'w', encoding='utf-8') as f:
                f.write('{}')
            code = cu.run_cli('x', tmp, 'x', lambda d, p: None, ['--data', bad])
            self.assertEqual(code, 1)
            self.assertEqual(cu.run_cli('x', tmp, 'x', lambda d, p: None,
                                        ['--data', os.path.join(tmp, 'none.json')]), 1)
            self.assertEqual(cu.run_cli('x', tmp, 'x', lambda d, p: None,
                                        ['--data', EXAMPLE, '--check']), 0)


class Generation(unittest.TestCase):
    def generate(self, data, module):
        tmp = tempfile.mkdtemp()
        self.addCleanup(lambda: __import__('shutil').rmtree(tmp, ignore_errors=True))
        src = os.path.join(tmp, 'data.json')
        with open(src, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)
        out = os.path.join(tmp, 'out.docx')
        module.create_docx(out, src)
        return out

    def check_package(self, path):
        with zipfile.ZipFile(path) as z:
            self.assertIsNone(z.testzip())
            names = z.namelist()
            self.assertEqual(names[0], '[Content_Types].xml')
            for name in names:
                ET.fromstring(z.read(name))  # каждая часть - корректный XML
            doc = ET.fromstring(z.read('word/document.xml'))
            text = ''.join(t.text or '' for t in doc.iter(W + 't'))
        sect = doc.find('.//' + W + 'sectPr')
        self.assertEqual(sect[0].tag, W + 'footerReference')
        for tbl in doc.iter(W + 'tbl'):
            cols = len(tbl.find(W + 'tblGrid'))
            for tr in tbl.findall(W + 'tr'):
                span = 0
                for tc in tr.findall(W + 'tc'):
                    gs = tc.find(W + 'tcPr/' + W + 'gridSpan')
                    span += int(gs.get(W + 'val')) if gs is not None else 1
                self.assertEqual(span, cols)
        return doc, text

    def test_contract_package(self):
        doc, text = self.check_package(self.generate(example(), create_contract))
        self.assertEqual(len(doc.findall('.//' + W + 'br[@' + W + 'type="page"]')), 2)
        self.assertIn('11 (одиннадцать) месяцев', text)
        self.assertIn('не позднее 19 ноября 2025 г.', text)
        self.assertIn('«18» ноября 2025 г.', text)
        self.assertIn('30 000 (тридцать тысяч) рублей', text)
        self.assertIn('в размере 0,1%', text)

    def test_summary_package(self):
        _, text = self.check_package(self.generate(example(), create_summary))
        self.assertIn('ПАО «Пример-банк»', text)
        self.assertNotIn('Т-Банк', text)

    def test_values_follow_json(self):
        data = example()
        data['contract'].update(duration_months=12, start_date='01.03.2026', conclusion_date='25.02.2026')
        data['financial'].update(monthly_rent=72500, security_deposit=40000, penalty_rate=0.5,
                                 first_payment_deadline='05.03.2026', deposit_deadline='03.03.2026')
        for meter in data['meters'].values():
            meter['date'] = '1 марта 2026 г.'
        data['rules'].update(deposit_return_days=14, eviction_days=21, termination_notice_days=45)
        _, text = self.check_package(self.generate(data, create_contract))
        for expected in ('12 (двенадцать) месяцев', '1 марта 2026 г.', '5 марта 2026 г.',
                         '3 марта 2026 г.', '72 500 (семьдесят две тысячи пятьсот) рублей',
                         '40 000 (сорок тысяч) рублей', '0,5%',
                         '14 (четырнадцати) календарных дней', '21 (двадцати одного) календарного дня',
                         '45 (сорок пять) календарных дней', '«25» февраля 2026 г.'):
            self.assertIn(expected, text)
        for stale in ('2025', '(тридцать тысяч)'):
            self.assertNotIn(stale, text)

    def test_special_characters_are_escaped(self):
        data = example()
        data['bank_details']['bank_name'] = 'ООО «Альфа & Партнёры» <test>'
        data['inventory'][0] = 'Стол & стулья'
        for module in (create_contract, create_summary):
            _, text = self.check_package(self.generate(data, module))
            self.assertIn('Альфа & Партнёры» <test>', text)

    def test_optional_fields_blank(self):
        data = example()
        data['property']['address']['building'] = ''
        data['tenant']['phone'] = ''
        data['tenant']['passport_issued_by'] = ''
        _, text = self.check_package(self.generate(data, create_contract))
        self.assertNotIn('корп.', text)
        self.assertIn('Тел.: ____', text)


if __name__ == '__main__':
    unittest.main()
