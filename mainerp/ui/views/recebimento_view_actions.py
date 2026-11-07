"""Componentes de RecebimentoView."""

import logging

from PyQt6.QtWidgets import (
    QMessageBox,
)

from mainerp.core.exceptions import ErroERP
from mainerp.data.models.duplicata import Duplicata
from mainerp.domain.utils.export_utils import ExportUtils
from mainerp.domain.utils.helpers import (
    validar_data,
)
from mainerp.reports.print_comprovante_recebimento import PrintComprovanteRecebimento
from mainerp.reports.print_relat_recebimento import PrintRelatRecebimento
from mainerp.ui.dialogs.recebimento_dialog import RecebimentoDialog
from mainerp.ui.mixins.component_mixin import ComponentMixin

logger = logging.getLogger(__name__)


__all__ = ["_RecebimentoViewActions"]


class _RecebimentoViewActions(ComponentMixin):
    def _receber_duplicata(self):
        """Processa recebimento de duplicata"""
        duplicata = self._get_duplicata_selecionada()
        if not duplicata:
            QMessageBox.warning(self, "Aviso", "Selecione uma duplicata para receber")
            return

        # Verificar se já está paga
        if duplicata[7] == "pago":  # status na posição 7
            QMessageBox.warning(self, "Aviso", "Esta duplicata já está paga")
            return

        dialog = RecebimentoDialog(duplicata, self)
        if dialog.exec():
            valor_recebido, data_recebimento, forma_pagamento = dialog.get_dados()
            try:
                # Processar recebimento
                dados_duplicata_paga = self._processar_recebimento_com_retorno(
                    duplicata, valor_recebido, data_recebimento, forma_pagamento
                )

                QMessageBox.information(
                    self, "Sucesso", "Recebimento processado com sucesso!"
                )

                # Perguntar sobre impressão
                if self._confirmar_impressao():
                    self._imprimir_comprovante_direto(dados_duplicata_paga)

                # Recarregar dados
                self._recarregar_dados_apos_recebimento()

            except Exception as e:
                QMessageBox.critical(
                    self, "Erro", f"Erro ao processar recebimento: {e!s}"
                )

    def _processar_recebimento_com_retorno(
        self, duplicata, valor_recebido, data_recebimento, forma_pagamento
    ):
        """Processa recebimento e retorna dados da duplicata paga"""
        duplicata_id = duplicata[0]
        venda_id = duplicata[2]
        cliente_id = duplicata[1]
        numero_parcela = duplicata[3]
        valor_original = duplicata[4]
        data_vencimento = duplicata[5]

        # Processar o recebimento
        success = Duplicata.marcar_como_paga(
            duplicata_id, valor_recebido, data_recebimento, forma_pagamento
        )

        if not success:
            raise ErroERP("Falha ao processar recebimento")

        # Buscar dados para comprovante
        cliente_venda = Duplicata.buscar_dados_cliente_venda(cliente_id, venda_id)

        if not cliente_venda:
            raise ErroERP("Dados do cliente/venda não encontrados")

        # Montar dados para comprovante
        dados_comprovante = {
            "id": duplicata_id,
            "venda_id": venda_id,
            "cliente_id": cliente_id,
            "numero_parcela": numero_parcela,
            "valor_original": float(valor_original),
            "valor_recebido": float(valor_recebido),
            "data_vencimento": data_vencimento,
            "data_pagamento": data_recebimento,
            "forma_pagamento": forma_pagamento,
            "cliente_nome": cliente_venda[0],
            "cpf_cnpj": cliente_venda[1],
            "endereco": cliente_venda[2],
            "venda_total": float(cliente_venda[3]) if cliente_venda[3] else 0,
            "data_venda": cliente_venda[4],
        }

        return dados_comprovante

    def _recarregar_dados_apos_recebimento(self):
        """Recarrega dados após recebimento - otimizado"""
        # Atualizar cache localmente primeiro
        duplicata_selecionada = self._get_duplicata_selecionada()
        venda_id = (
            duplicata_selecionada[2] if duplicata_selecionada is not None else None
        )

        if venda_id and venda_id in self._parcelas_cache:
            # Atualizar contagem no cache
            self._parcelas_cache[venda_id] += 1

        # Recarregar apenas se necessário
        self._carregar_duplicatas()

    def _imprimir_comprovante_direto(self, dados_duplicata):
        """Imprime comprovante usando dados diretos"""
        try:
            filename = PrintComprovanteRecebimento.gerar_comprovante(
                dados_duplicata, "relatorios"
            )
            if filename:
                if ExportUtils.abrir_arquivo(filename):
                    logger.info("Comprovante de recebimento gerado")
                else:
                    QMessageBox.information(
                        self,
                        "Sucesso",
                        f"Comprovante salvo em:\n{filename}\n\nNão foi possível abrir automaticamente.",
                    )
            else:
                QMessageBox.warning(
                    self, "Erro", "Não foi possível gerar o comprovante."
                )

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao gerar comprovante: {e!s}")

    def _confirmar_impressao(self):
        """Confirma se usuário quer imprimir comprovante"""
        resposta = QMessageBox.question(
            self,
            "Imprimir Comprovante",
            "Deseja imprimir o comprovante de pagamento?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        return resposta == QMessageBox.StandardButton.Yes

    def _imprimir_relatorio(self):
        """Imprime relatório de recebimentos"""
        try:
            status_filtro = self._get_status_selecionado()
            data_inicio_str = self.data_inicio.text().strip()
            data_fim_str = self.data_fim.text().strip()

            cliente_id = None

            if data_inicio_str and not validar_data(data_inicio_str):
                QMessageBox.warning(self, "Aviso", "Data inicial inválida")
                return
            if data_fim_str and not validar_data(data_fim_str):
                QMessageBox.warning(self, "Aviso", "Data final inválida")
                return

            filename = PrintRelatRecebimento.gerar_relatorio(
                data_inicio_str, data_fim_str, status_filtro, cliente_id, "relatorios"
            )

            if filename and ExportUtils.abrir_arquivo(filename):
                QMessageBox.information(
                    self, "Sucesso", f"Relatório exportado:\n{filename}"
                )
            else:
                QMessageBox.warning(
                    self,
                    "Arquivo salvo",
                    f"Arquivo salvo em: {filename}\nNão foi possível abrir automaticamente.",
                )
        except Exception as e:
            QMessageBox.critical(
                self, "Erro na Exportação", f"Erro ao exportar relatório:\n{e!s}"
            )

    def _marcar_campo_erro(self, campo):
        """Marca campo com erro visual"""
        campo.setProperty("class", "error")
        campo.style().unpolish(campo)
        campo.style().polish(campo)

    def _limpar_campo_erro(self, campo):
        """Remove marcação de erro do campo"""
        campo.setProperty("class", "")
        campo.style().unpolish(campo)
        campo.style().polish(campo)
