# \erp\utils\helpers.py
import os
import re
from datetime import datetime

from PyQt6.QtGui import QValidator
from PyQt6.QtWidgets import QComboBox, QDoubleSpinBox, QLineEdit, QSpinBox, QTextEdit

from mainerp.data.money import de_centavos, para_centavos


def formatar_moeda(valor):
    """Formata valor para formato monetário brasileiro"""
    return f"R$ {float(valor):.2f}".replace(".", ",")


def formatar_data(data, formato_origem="%Y-%m-%d", formato_destino="%d/%m/%Y"):
    """Formata data entre diferentes formatos"""
    if data is None:
        return ""

    if hasattr(data, "strftime"):
        return data.strftime(formato_destino)

    if isinstance(data, str):
        try:
            data_obj = datetime.strptime(data, formato_origem)
            return data_obj.strftime(formato_destino)
        except ValueError:
            return data

    return str(data)


def validar_data(data_str, formato="%d/%m/%Y"):
    """Valida se a string está no formato especificado"""
    if not data_str:
        return False
    try:
        datetime.strptime(data_str, formato)
        return True
    except ValueError:
        return False


def validar_quantidade(quantidade, estoque_disponivel):
    """Valida se a quantidade é válida para o estoque"""
    try:
        quantidade = int(quantidade)
        return 1 <= quantidade <= estoque_disponivel
    except (ValueError, TypeError):
        return False


def calcular_subtotal(preco, quantidade):
    """Calcula subtotal de um item"""
    subtotal_centavos = para_centavos(preco) * int(quantidade)
    return float(de_centavos(subtotal_centavos))


def aplicar_desconto_total(subtotal, desconto):
    """Aplica desconto ao subtotal"""
    total_centavos = max(0, para_centavos(subtotal) - para_centavos(desconto))
    return float(de_centavos(total_centavos))


def criar_pasta_se_nao_existir(caminho):
    """Cria pasta se não existir"""
    if not os.path.exists(caminho):
        os.makedirs(caminho)
    return caminho


def limpar_mascara(texto):
    """Remove máscaras de CNPJ, CPF, telefone"""
    return re.sub(r"[^0-9]", "", texto)


def aplicar_mascara_cnpj(cnpj):
    """Aplica máscara de CNPJ"""
    cnpj_limpo = limpar_mascara(cnpj)
    return f"{cnpj_limpo[:2]}.{cnpj_limpo[2:5]}.{cnpj_limpo[5:8]}/{cnpj_limpo[8:12]}-{cnpj_limpo[12:]}"


def converter_data_string(data_str, formato_origem="%Y-%m-%d"):
    """Converte string para objeto date"""
    if not data_str:
        return None

    try:
        if hasattr(data_str, "strftime"):
            return data_str

        if isinstance(data_str, str):
            return datetime.strptime(data_str, formato_origem).date()

        return None
    except ValueError:
        return None


class UpperCaseValidator(QValidator):
    """Validador que converte texto para maiúscula"""

    def validate(self, input_str, pos):
        return (QValidator.State.Acceptable, input_str.upper(), pos)


# ============================================================================
# WIDGETS BÁSICOS (sem conversão para maiúscula)
# ============================================================================


class SelectAllDoubleSpinBox(QDoubleSpinBox):
    """QDoubleSpinBox que seleciona todo o conteúdo ao receber foco"""

    def focusInEvent(self, event):
        super().focusInEvent(event)
        line_edit = self.lineEdit()
        if line_edit is not None:
            line_edit.selectAll()


class SelectAllLineEdit(QLineEdit):
    """QLineEdit que seleciona todo o conteúdo ao receber foco"""

    def focusInEvent(self, event):
        super().focusInEvent(event)
        self.selectAll()


class SelectAllSpinBox(QSpinBox):
    """QSpinBox que seleciona todo o conteúdo ao receber foco"""

    def focusInEvent(self, event):
        super().focusInEvent(event)
        self.selectAll()


# ============================================================================
# WIDGETS COM CONVERSÃO AUTOMÁTICA PARA MAIÚSCULA
# ============================================================================


class UpperCaseLineEdit(QLineEdit):
    """QLineEdit que converte automaticamente para maiúscula e remove quebras de linha"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.textChanged.connect(self._converter_maiuscula)

    def _converter_maiuscula(self):
        cursor_pos = self.cursorPosition()
        texto_atual = self.text()
        # Remove quebras de linha e converte para maiúscula
        texto_processado = texto_atual.replace("\n", " ").replace("\r", " ").upper()

        if texto_atual != texto_processado:
            self.blockSignals(True)
            self.setText(texto_processado)
            self.setCursorPosition(cursor_pos)
            self.blockSignals(False)


class UpperCaseSelectAllLineEdit(SelectAllLineEdit):
    """QLineEdit que seleciona tudo no foco E converte para maiúscula e remove quebras de linha"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.textChanged.connect(self._converter_maiuscula)

    def _converter_maiuscula(self):
        cursor_pos = self.cursorPosition()
        texto_atual = self.text()
        # Remove quebras de linha e converte para maiúscula
        texto_processado = texto_atual.replace("\n", " ").replace("\r", " ").upper()

        if texto_atual != texto_processado:
            self.blockSignals(True)
            self.setText(texto_processado)
            self.setCursorPosition(cursor_pos)
            self.blockSignals(False)


class UpperCaseTextEdit(QTextEdit):
    """QTextEdit que converte automaticamente para maiúscula e remove quebras de linha"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.textChanged.connect(self._converter_maiuscula)

    def _converter_maiuscula(self):
        cursor = self.textCursor()
        posicao = cursor.position()
        texto_atual = self.toPlainText()
        # Remove quebras de linha e converte para maiúscula
        texto_processado = texto_atual.replace("\n", " ").replace("\r", " ").upper()

        if texto_atual != texto_processado:
            self.blockSignals(True)
            self.setPlainText(texto_processado)
            cursor.setPosition(min(posicao, len(texto_processado)))
            self.setTextCursor(cursor)
            self.blockSignals(False)


class UpperCaseComboBox(QComboBox):
    """QComboBox editável que converte entrada para maiúscula e remove quebras de linha"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setEditable(True)
        line_edit = self.lineEdit()
        if line_edit is not None:
            line_edit.textChanged.connect(self._converter_maiuscula)

    def _converter_maiuscula(self):
        line_edit = self.lineEdit()
        if not self.isEditable() or line_edit is None:
            return

        cursor_pos = line_edit.cursorPosition()
        texto_atual = line_edit.text()
        # Remove quebras de linha e converte para maiúscula
        texto_processado = texto_atual.replace("\n", " ").replace("\r", " ").upper()

        if texto_atual != texto_processado:
            line_edit.blockSignals(True)
            line_edit.setText(texto_processado)
            line_edit.setCursorPosition(cursor_pos)
            line_edit.blockSignals(False)


# ============================================================================
# FUNÇÕES DE CONVENIÊNCIA PARA APLICAR MAIÚSCULA EM WIDGETS EXISTENTES
# ============================================================================


def aplicar_maiuscula_widget(widget):
    """
    Aplica conversão automática para maiúscula e remoção de quebras de linha em um widget existente
    Útil para widgets que já estão criados e você não quer trocar o tipo
    """
    if isinstance(widget, QLineEdit):
        widget.textChanged.connect(lambda: _converter_texto_maiuscula(widget))
    elif isinstance(widget, QTextEdit):
        widget.textChanged.connect(lambda: _converter_texto_maiuscula_textedit(widget))
    elif isinstance(widget, QComboBox) and widget.isEditable():
        line_edit = widget.lineEdit()
        if line_edit is not None:
            line_edit.textChanged.connect(lambda: _converter_texto_maiuscula(line_edit))


def _converter_texto_maiuscula(line_edit):
    """Função auxiliar para converter texto em QLineEdit para maiúscula e remover quebras de linha"""
    cursor_pos = line_edit.cursorPosition()
    texto_atual = line_edit.text()
    # Remove quebras de linha e converte para maiúscula
    texto_processado = texto_atual.replace("\n", " ").replace("\r", " ").upper()

    if texto_atual != texto_processado:
        line_edit.blockSignals(True)
        line_edit.setText(texto_processado)
        line_edit.setCursorPosition(cursor_pos)
        line_edit.blockSignals(False)


def _converter_texto_maiuscula_textedit(text_edit):
    """Função auxiliar para converter texto em QTextEdit para maiúscula e remover quebras de linha"""
    cursor = text_edit.textCursor()
    posicao = cursor.position()
    texto_atual = text_edit.toPlainText()
    # Remove quebras de linha e converte para maiúscula
    texto_processado = texto_atual.replace("\n", " ").replace("\r", " ").upper()

    if texto_atual != texto_processado:
        text_edit.blockSignals(True)
        text_edit.setPlainText(texto_processado)
        cursor.setPosition(min(posicao, len(texto_processado)))
        text_edit.setTextCursor(cursor)
        text_edit.blockSignals(False)


def aplicar_maiuscula_formulario(form_widget):
    """
    Aplica conversão automática para maiúscula e remoção de quebras de linha
    em todos os campos de texto de um formulário
    """
    for child in form_widget.findChildren(QLineEdit):
        aplicar_maiuscula_widget(child)

    for child in form_widget.findChildren(QTextEdit):
        aplicar_maiuscula_widget(child)

    for child in form_widget.findChildren(QComboBox):
        if child.isEditable():
            aplicar_maiuscula_widget(child)
