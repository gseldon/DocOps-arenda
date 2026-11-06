# -*- coding: utf-8 -*-
"""
Минимальный генератор DOCX без внешних зависимостей.

Общий код для create_contract.py и create_summary.py: абзацы, таблицы,
разрыв страницы и упаковка пакета OOXML (zip).
"""

import re
import zipfile
from datetime import datetime, timezone
from xml.sax.saxutils import escape

W_NS = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
R_NS = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'

# A4, поля как в исходных скриптах. Ширина текста = 11906 - 1701 - 850
PAGE_W, PAGE_H = 11906, 16838
MARGIN_LEFT, MARGIN_RIGHT = 1701, 850
TEXT_WIDTH = PAGE_W - MARGIN_LEFT - MARGIN_RIGHT

_ALIGNS = ('left', 'center', 'right', 'both')
# Управляющие символы, недопустимые в XML 1.0
_INVALID_XML = re.compile('[\x00-\x08\x0b\x0c\x0e-\x1f￾￿]')


def esc(text):
    """Экранирует текст для вставки в XML (&, <, >) и убирает недопустимые символы."""
    return escape(_INVALID_XML.sub('', str(text)))


def _rpr(bold, size):
    return '{}<w:sz w:val="{}"/><w:szCs w:val="{}"/>'.format(
        '<w:b/>' if bold else '', size, size)


def paragraph(text='', bold=False, align='both', size=24):
    """Абзац с одним фрагментом текста."""
    jc = align if align in _ALIGNS else 'both'
    rpr = _rpr(bold, size)
    return ('<w:p><w:pPr><w:jc w:val="{jc}"/><w:rPr>{rpr}</w:rPr></w:pPr>'
            '<w:r><w:rPr>{rpr}</w:rPr><w:t xml:space="preserve">{text}</w:t></w:r></w:p>'
            ).format(jc=jc, rpr=rpr, text=esc(text))


def paragraph_split(left, right, size=24):
    """Строка с текстом у левого края и текстом у правого (табуляция по правому краю)."""
    rpr = _rpr(False, size)
    return ('<w:p><w:pPr><w:tabs><w:tab w:val="right" w:pos="{pos}"/></w:tabs>'
            '<w:rPr>{rpr}</w:rPr></w:pPr>'
            '<w:r><w:rPr>{rpr}</w:rPr><w:t xml:space="preserve">{left}</w:t><w:tab/>'
            '<w:t xml:space="preserve">{right}</w:t></w:r></w:p>'
            ).format(pos=TEXT_WIDTH, rpr=rpr, left=esc(left), right=esc(right))


def page_break():
    """Разрыв страницы."""
    return '<w:p><w:r><w:br w:type="page"/></w:r></w:p>'


_BORDER = '<w:{side} w:val="single" w:sz="4" w:space="0" w:color="000000"/>'


def _borders(sides):
    return ''.join(_BORDER.format(side=s) for s in sides)


def table(rows, font_size=24, widths=None):
    """
    Таблица с рамками. Сетка строится по числу колонок самой широкой строки.
    Если в строке ячеек меньше, последняя ячейка растягивается на остаток.
    widths - список ширин колонок в twips (сумма не обязана совпадать с шириной текста).
    """
    ncols = max(len(r) for r in rows)
    if widths is None:
        base = TEXT_WIDTH // ncols
        widths = [base] * ncols
        widths[-1] += TEXT_WIDTH - base * ncols
    if len(widths) != ncols:
        raise ValueError('Число ширин ({}) не равно числу колонок ({})'.format(len(widths), ncols))
    total = sum(widths)

    grid = ''.join('<w:gridCol w:w="{}"/>'.format(w) for w in widths)
    cell_borders = _borders(('top', 'left', 'bottom', 'right'))
    rpr = '<w:sz w:val="{0}"/><w:szCs w:val="{0}"/>'.format(font_size)

    rows_xml = []
    for row in rows:
        cells = list(row)
        cells_xml = []
        for i, cell in enumerate(cells):
            last = i == len(cells) - 1
            span = ncols - len(cells) + 1 if last else 1
            width = sum(widths[i:i + span])
            span_xml = '<w:gridSpan w:val="{}"/>'.format(span) if span > 1 else ''
            cells_xml.append(
                '<w:tc><w:tcPr><w:tcW w:w="{w}" w:type="dxa"/>{span}'
                '<w:tcBorders>{b}</w:tcBorders></w:tcPr>'
                '<w:p><w:r><w:rPr>{rpr}</w:rPr><w:t xml:space="preserve">{t}</w:t></w:r></w:p></w:tc>'
                .format(w=width, span=span_xml, b=cell_borders, rpr=rpr, t=esc(cell)))
        rows_xml.append('<w:tr>{}</w:tr>'.format(''.join(cells_xml)))

    return ('<w:tbl><w:tblPr><w:tblStyle w:val="TableGrid"/>'
            '<w:tblW w:w="{total}" w:type="dxa"/>'
            '<w:tblBorders>{b}</w:tblBorders><w:tblLayout w:type="fixed"/></w:tblPr>'
            '<w:tblGrid>{grid}</w:tblGrid>{rows}</w:tbl>'
            ).format(total=total,
                     b=_borders(('top', 'left', 'bottom', 'right', 'insideH', 'insideV')),
                     grid=grid, rows=''.join(rows_xml))


_XML_DECL = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'

_CONTENT_TYPES = _XML_DECL + (
    '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
    '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
    '<Default Extension="xml" ContentType="application/xml"/>'
    '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
    '<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>'
    '<Override PartName="/word/footer1.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml"/>'
    '<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>'
    '<Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>'
    '</Types>')

_ROOT_RELS = _XML_DECL + (
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
    '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>'
    '<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>'
    '</Relationships>')

_DOC_RELS = _XML_DECL + (
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/footer" Target="footer1.xml"/>'
    '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
    '</Relationships>')

_STYLES = _XML_DECL + (
    '<w:styles xmlns:w="{ns}">'
    '<w:docDefaults><w:rPrDefault><w:rPr>'
    '<w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:eastAsia="Times New Roman" w:cs="Times New Roman"/>'
    '<w:sz w:val="24"/><w:szCs w:val="24"/><w:lang w:val="ru-RU"/>'
    '</w:rPr></w:rPrDefault>'
    '<w:pPrDefault><w:pPr><w:spacing w:after="0" w:line="240" w:lineRule="auto"/></w:pPr></w:pPrDefault>'
    '</w:docDefaults>'
    '<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/><w:qFormat/></w:style>'
    '<w:style w:type="table" w:default="1" w:styleId="TableNormal"><w:name w:val="Normal Table"/>'
    '<w:uiPriority w:val="99"/><w:semiHidden/><w:unhideWhenUsed/>'
    '<w:tblPr><w:tblInd w:w="0" w:type="dxa"/><w:tblCellMar>'
    '<w:top w:w="0" w:type="dxa"/><w:left w:w="108" w:type="dxa"/>'
    '<w:bottom w:w="0" w:type="dxa"/><w:right w:w="108" w:type="dxa"/>'
    '</w:tblCellMar></w:tblPr></w:style>'
    '<w:style w:type="table" w:styleId="TableGrid"><w:name w:val="Table Grid"/>'
    '<w:basedOn w:val="TableNormal"/><w:uiPriority w:val="59"/>'
    '<w:tblPr><w:tblBorders>{borders}</w:tblBorders></w:tblPr></w:style>'
    '</w:styles>').format(
        ns=W_NS, borders=_borders(('top', 'left', 'bottom', 'right', 'insideH', 'insideV')))

_FOOTER = _XML_DECL + (
    '<w:ftr xmlns:w="{ns}"><w:p><w:pPr><w:jc w:val="center"/></w:pPr>'
    '<w:r><w:fldChar w:fldCharType="begin"/></w:r>'
    '<w:r><w:instrText xml:space="preserve"> PAGE </w:instrText></w:r>'
    '<w:r><w:fldChar w:fldCharType="separate"/></w:r>'
    '<w:r><w:t>1</w:t></w:r>'
    '<w:r><w:fldChar w:fldCharType="end"/></w:r>'
    '</w:p></w:ftr>').format(ns=W_NS)


def _document_xml(body):
    # footerReference обязан быть ПЕРВЫМ дочерним элементом sectPr
    return _XML_DECL + (
        '<w:document xmlns:w="{w}" xmlns:r="{r}"><w:body>{body}'
        '<w:sectPr><w:footerReference w:type="default" r:id="rId1"/>'
        '<w:pgSz w:w="{pw}" w:h="{ph}"/>'
        '<w:pgMar w:top="1134" w:right="{mr}" w:bottom="1134" w:left="{ml}" '
        'w:header="708" w:footer="708" w:gutter="0"/></w:sectPr>'
        '</w:body></w:document>').format(
            w=W_NS, r=R_NS, body=body, pw=PAGE_W, ph=PAGE_H,
            mr=MARGIN_RIGHT, ml=MARGIN_LEFT)


def _core_xml(title):
    now = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    return _XML_DECL + (
        '<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
        'xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" '
        'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
        '<dc:title>{title}</dc:title>'
        '<dcterms:created xsi:type="dcterms:W3CDTF">{now}</dcterms:created>'
        '<dcterms:modified xsi:type="dcterms:W3CDTF">{now}</dcterms:modified>'
        '</cp:coreProperties>').format(title=esc(title), now=now)


_APP_XML = _XML_DECL + (
    '<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties">'
    '<Application>DocOps-arenda</Application></Properties>')


def write_docx(path, body, title=''):
    """
    Записывает DOCX прямо в zip, без временных папок.
    [Content_Types].xml идёт первым в архиве, как требуют строгие читатели.
    """
    parts = [
        ('[Content_Types].xml', _CONTENT_TYPES),
        ('_rels/.rels', _ROOT_RELS),
        ('word/document.xml', _document_xml(body)),
        ('word/_rels/document.xml.rels', _DOC_RELS),
        ('word/styles.xml', _STYLES),
        ('word/footer1.xml', _FOOTER),
        ('docProps/core.xml', _core_xml(title)),
        ('docProps/app.xml', _APP_XML),
    ]
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as docx:
        for name, content in parts:
            docx.writestr(name, content.encode('utf-8'))
