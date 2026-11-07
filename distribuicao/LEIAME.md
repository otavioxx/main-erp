# MainERP 0.08 - distribuição sem PyInstaller

## Novidades da versão 0.08

- Corrigida a exibição e a edição do valor no diálogo **Preço de Venda**.
- Valores monetários de vendas, parcelas, recebimentos, produtos, pedidos e
  condicionais são calculados e persistidos em centavos, reduzindo erros de
  arredondamento.
- Ao pagar parcialmente a última parcela, o saldo restante passa a gerar uma
  nova parcela.
- A atualização do banco é feita por migrações aditivas, com backup automático
  antes da alteração do esquema.

## Como funciona

```
%LOCALAPPDATA%\MainERP\
  sistema\                  <- código e ferramentas (pode ser recriado a qualquer momento)
    runtime\                Python + bibliotecas (venv)
    launcher.pyw            o atalho aponta SEMPRE para ele
    releases\<versão>\      uma pasta por versão (as 3 últimas são mantidas)
    current.txt             versão ativa
    atualizacoes\           coloque aqui o .zip de uma nova versão
    launcher.json           {"update_url": ""}  (atualização online, opcional)
    logs\                   launcher.log e sistema.log (erros aparecem aqui)
  dados\                    <- NUNCA é tocada por atualizações
    erp.db, config.json, backup_settings.json, backups\, relatorios\
```

## Primeira instalação

1. Python 3.10 ou superior instalado (recomendado: 3.12), com o "py launcher".
2. Dê dois cliques em `distribuicao\instalar.bat`.
3. Abra o MainERP pelo atalho (Área de Trabalho / Menu Iniciar).
4. Em uma instalação nova, restaure seu backup pela tela de Configurações; o sistema
   reinicia sozinho. Se estiver atualizando uma instalação existente, mantenha a pasta
   `dados\`: ela contém seu banco e suas configurações e não deve ser substituída.
5. Confira os dados antes de apagar a pasta do executável antigo (PyInstaller).

Na primeira inicialização com um banco restaurado ou existente que precise de migração,
o sistema cria um backup em `dados\backups\pre_migracao_*.db` antes de atualizar o esquema.

## Publicar uma atualização (no mesmo PC)

1. Altere o código e aumente `APP_VERSION` em `mainerp/core/config.py` (a release atual é
   `0.08`).
2. Atualize também a versão e a data exibidas na linha 54 de
   `mainerp\ui\views\main_window.py` (barra de status).
3. Dê dois cliques em `distribuicao\publicar_atualizacao.bat`.
4. Abra o MainERP: a versão nova é instalada e aberta. Nada de empacotar.

Se `requirements.txt` mudou, o launcher roda `pip install` sozinho (precisa de internet).
Se a versão nova falhar antes de abrir a janela, o launcher volta para a anterior
e marca a nova com um arquivo `.ruim` (apague-o para tentar de novo).

## Mudanças no banco (migrações)

Em `mainerp/data/database.py`: crie `_migracao_NNN_descricao`, registre em `MIGRACOES` com o
próximo número e mantenha a mudança ADITIVA (nova tabela/coluna). Cada migração roda
uma vez, em transação, depois de um backup automático. Exemplo: `_garantir_coluna`.

## Voltar para uma versão anterior

Edite `sistema\current.txt` com o número da versão (a pasta precisa existir em `releases\`).
O código volta; o banco continua como está (migrações aditivas não atrapalham).
Backups pré-migração ficam em `dados\backups\`.

## Atualização online (futuro)

1. Hospede `dist\MainERP-<versão>.zip` e `dist\version.json` (gerados pelo `criar_release.py`)
   em um servidor HTTPS ou pasta de rede.
2. Em `sistema\launcher.json`: `{"update_url": "https://seu-servidor/mainerp/version.json"}`.
3. A cada abertura o launcher consulta, baixa, confere o SHA256 e instala. Sem internet,
   abre a versão instalada. Para produção, o próximo passo é assinar os pacotes.

## Dados em outro local

Defina a variável de ambiente `MAINERP_DATA` com a pasta desejada.

## Desinstalar

Apague `sistema\` e os atalhos. `dados\` só deve ser apagada se você não precisar mais do banco.
