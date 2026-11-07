# MainERP - distribuição sem PyInstaller

## Como funciona

```
%LOCALAPPDATA%\MainERP\
  sistema\                  <- código e ferramentas (pode ser recriado a qualquer momento)
    runtime\                Python + bibliotecas (venv)
    launcher.pyw            o atalho aponta SEMPRE para ele
    releases\0.07\ 0.08\    uma pasta por versão (as 3 últimas são mantidas)
    current.txt             versão ativa
    atualizacoes\           coloque aqui o .zip de uma nova versão
    launcher.json           {"update_url": ""}  (atualização online, opcional)
    logs\                   launcher.log e sistema.log (erros aparecem aqui)
  dados\                    <- NUNCA é tocada por atualizações
    erp.db, config.json, backup_settings.json, backups\, relatorios\
```

## Primeira instalação

1. Python 3.12 instalado (python.org, com o "py launcher").
2. Dê dois cliques em `distribuicao\instalar.bat`.
3. Abra o MainERP pelo atalho (Área de Trabalho / Menu Iniciar). O banco começa vazio:
   restaure seu backup pela tela de Configurações; o sistema reinicia sozinho.
4. Confira os dados antes de apagar a pasta do executável antigo (PyInstaller).

O primeiro start com o banco restaurado cria automaticamente um backup em
`dados\backups\pre_migracao_*.db` e atualiza o esquema.

## Publicar uma atualização (no mesmo PC)

1. Altere o código e aumente `APP_VERSION` em `mainerp/core/config.py`.
2. Dê dois cliques em `distribuicao\publicar_atualizacao.bat`.
3. Abra o MainERP: a versão nova é instalada e aberta. Nada de empacotar.

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
