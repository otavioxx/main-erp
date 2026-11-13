# Cópia externa e teste de restauração

Este procedimento reduz o risco de perda de dados em um computador pessoal. Ele não
substitui uma avaliação de integridade dos dados nem garante recuperação em todos os
casos. Os backups não são criptografados pelo PLUMA: proteja o acesso às cópias.

## Criar e guardar cópias externas

1. No ERP, acesse **Configurações > Criar Backup**. Selecione uma pasta em uma unidade
   externa ou crie o ZIP em uma pasta local e copie-o para outro dispositivo. Aguarde a
   confirmação de conclusão e confira que o arquivo está presente no destino.
2. Se usar uma pasta sincronizada, confirme que a sincronização terminou e que é possível
   acessar o arquivo em outro dispositivo. Uma pasta local ainda não sincronizada não é
   uma cópia externa.
3. Mantenha pelo menos duas cópias de datas diferentes e, quando possível, uma unidade
   desconectada. Proteja-as contra acesso não autorizado e não apague a única cópia
   anterior antes de verificar a nova.
4. Repita a cópia com a frequência adequada à quantidade de trabalho que você aceita
   perder, por exemplo, após cada dia de uso. Periodicamente, teste uma cópia externa
   seguindo o procedimento abaixo; registre a data e o resultado sem anotar dados de
   clientes. Se o teste falhar, preserve a cópia e procure suporte.

Os backups automáticos em `dados\backups` ficam no mesmo computador que o banco e não
protegem contra perda do dispositivo. Não copie `erp.db` diretamente enquanto o sistema
estiver aberto: use o ZIP manual ou um snapshot já criado pelo aplicativo.

## O que cada backup contém

| Tipo | Conteúdo | Recuperação |
|---|---|---|
| Manual (`backup_erp_*.zip`) | Snapshot do banco, `README.txt` e, se existir no diretório de trabalho, `config.ini`. | A restauração usa apenas o banco contido no ZIP. |
| Automático (`backup_automatico_*.db`) | Snapshot do banco SQLite. | Pode ser selecionado como arquivo `.db` na restauração. |
| Antes de migração ou restauração (`pre_migracao_*.db`, `pre_restore_*.db`) | Snapshot do banco anterior à operação. | Pode ser selecionado como arquivo `.db`; preserve-o para diagnóstico em caso de falha. |

O banco inclui os registros armazenados nele, inclusive os dados da empresa. Arquivos
separados, como `config.json`, `backup_settings.json`, relatórios e outros documentos,
não são restaurados por esse fluxo. Copie os arquivos separados necessários em segurança
à parte e verifique-os manualmente; não sobrescreva configurações de produção durante
um teste. O `config.ini` eventualmente incluído no ZIP não é aplicado pela restauração.

## Testar uma cópia sem alterar o banco em uso

Este roteiro para Windows usa o código do projeto e seu ambiente Python já instalado.
Use uma versão do ERP compatível com o backup, preferencialmente a mesma da instalação
de origem. Ele isola os **dados**, não instala uma segunda cópia do aplicativo nem testa
o instalador ou o launcher. O teste utiliza uma cópia real que pode conter informações
sensíveis: faça-o somente em um computador confiável.

1. Feche todas as instâncias do PLUMA. Não use o atalho normal para este teste: ele
   pode abrir os dados de produção. Abra uma **nova** janela do PowerShell na raiz do
   projeto e confirme que `.venv\Scripts\python.exe` existe.
2. Crie uma pasta de teste nova e defina `MAINERP_DATA` apenas nessa janela. Use os
   comandos abaixo; não substitua o caminho gerado pelo diretório de dados de produção:

   ```powershell
   $teste = Join-Path $env:TEMP ("MainERP-teste-" + [guid]::NewGuid().ToString("N"))
   New-Item -ItemType Directory -Path $teste | Out-Null
   $env:MAINERP_DATA = $teste
   Write-Output "Pasta isolada: $teste"
   .\.venv\Scripts\python.exe .\main.py
   ```

3. **Antes de selecionar ou restaurar qualquer arquivo**, confira nas mensagens do
   console que `Dados` é exatamente a pasta isolada exibida e que `Banco` está dentro
   dela. Se não estiverem, pare e não restaure. A pasta nova começa com um banco vazio.
4. Em **Configurações > Restaurar Backup**, selecione o ZIP da cópia externa, clique
   em **Verificar Backup** e, se estiver válido, em **Restaurar Backup**. Confirme
   somente depois de verificar que está na instância isolada. A aplicação fecha após
   preparar a restauração.
5. Na mesma janela do PowerShell, execute novamente
   `.\.venv\Scripts\python.exe .\main.py`. Confira novamente o caminho `Dados`. A
   restauração deve ser aplicada antes da abertura; a execução direta não reinicia
   automaticamente pelo launcher.
6. Confira alguns registros e totais esperados nas telas, sem alterar os dados originais.
   Essa comparação complementa a verificação de integridade, mas não garante todas as
   regras de negócio. Se houver erro, não repita a restauração sem investigar; preserve
   o ZIP original, o banco de teste, a pendência e os snapshots para suporte.
7. Feche o ERP de teste e a janela do PowerShell para descartar a variável de ambiente
   daquela sessão. A pasta de teste permanece no caminho exibido e contém dados
   sensíveis: após confirmar que não precisa dela para diagnóstico, remova somente essa
   pasta gerada. Não remova nem altere a pasta de dados de produção ou a cópia externa.

Para validar a instalação e atualização completas de um cliente, use também um ambiente
separado e siga o procedimento de distribuição; este teste não comprova esse fluxo.
