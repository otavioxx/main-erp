# Backup e recuperação

Este guia orienta a criação de cópias externas e a verificação periódica da restauração.
Para detalhes técnicos sobre formatos, verificações e limites, consulte
[Banco de dados, backups e restauração](banco_e_backups.md).

## Manter uma cópia externa

1. No PLUMA, abra **Configurações > Criar Backup**.
2. Escolha um destino externo disponível no diálogo e conclua a criação do backup.
3. Confirme que o arquivo foi criado no destino escolhido e mantenha-o protegido.
4. Repita periodicamente e após mudanças importantes nos dados.

Os backups automáticos ficam no mesmo computador que o banco e não substituem uma cópia
externa. Os backups manuais não são criptografados pelo aplicativo; proteja o acesso ao
local e aos arquivos.

O ZIP manual contém um snapshot do banco e um `README.txt`; pode incluir `config.ini` se
esse arquivo estiver presente no diretório de trabalho. Não é uma cópia completa da pasta de
dados: relatórios e configurações não são restaurados junto com o banco.

## Testar uma restauração

Teste a recuperação periodicamente em uma instalação e pasta de dados isoladas, nunca sobre
o banco de produção:

1. Prepare um ambiente de teste separado e defina `MAINERP_DATA` para uma pasta exclusiva
   desse teste, conforme o [guia de desenvolvimento](desenvolvimento.md).
2. Use a função de restauração nas Configurações para selecionar a cópia externa.
3. Após o reinício do aplicativo, confira se os dados esperados estão presentes e se os
   totais importantes correspondem à origem conhecida.
4. Encerre o ambiente de teste sem substituir os dados de produção.

A restauração é aplicada na próxima inicialização. Feche os outros programas que possam
estar usando o banco antes de restaurar. Se houver uma falha, preserve o banco, o backup e
os arquivos pendentes; não presuma que o estado anterior foi restaurado automaticamente.
Consulte o [guia técnico](banco_e_backups.md) antes de qualquer nova tentativa.
