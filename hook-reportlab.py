# hook-reportlab.py
from PyInstaller.utils.hooks import collect_submodules

# Coletar todos os módulos de barcode
hiddenimports = collect_submodules('reportlab.graphics.barcode')

# Adicionar módulos específicos que podem ser importados dinamicamente
hiddenimports += [
    'reportlab.graphics.barcode.usps',
    'reportlab.graphics.barcode.code39',
    'reportlab.graphics.barcode.code128',
    'reportlab.graphics.barcode.code93',
    'reportlab.graphics.barcode.common',
    'reportlab.graphics.barcode.widgets',
    'reportlab.graphics.charts.barcharts',
    'reportlab.graphics.charts.linecharts',
    'reportlab.graphics.charts.piecharts',
    'reportlab.graphics.widgets',
    'reportlab.lib.colors',
    'reportlab.lib.styles',
    'reportlab.pdfbase.ttfonts',
    'reportlab.pdfbase.pdfmetrics',
    'reportlab.pdfgen.canvas'
]

# Ignorar módulos que não existem mas são tentados pelo ReportLab
excludedimports = [
    'reportlab.graphics.barcode.usps4s',
    'reportlab.graphics.barcode.usps4st',
    'reportlab.graphics.barcode.fourstate'
]
