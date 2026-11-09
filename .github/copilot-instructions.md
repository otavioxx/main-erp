## 1. Registro de alterações e documentação

- Considere o CHANGELOG.md como histórico oficial das versões publicadas.
- Utilize o DEVLOG.md para registrar o progresso técnico do desenvolvimento.
- Registre no DEVLOG funcionalidades, correções, melhorias e decisões técnicas relevantes.
- Registre no CHANGELOG somente alterações relevantes para o usuário final.
- Organize o CHANGELOG em: Added, Changed, Fixed, Removed e Security.
- Utilize a seção [Unreleased] para alterações ainda não publicadas.
- Não remova ou reescreva registros anteriores.
- Não duplique informações desnecessariamente entre documentos.
- Atualize a documentação somente quando houver alterações relevantes.
- Nunca invente funcionalidades, resultados ou alterações.
- Não altere números de versão automaticamente.

## 2. Alterações de código

- Analise o código existente antes de modificá-lo.
- Preserve a arquitetura e os padrões estabelecidos.
- Prefira alterações pequenas, localizadas e objetivas.
- Reutilize funcionalidades e componentes existentes.
- Não reescreva arquivos inteiros sem necessidade.
- Não remova funcionalidades sem autorização.
- Não crie abstrações, dependências ou arquivos desnecessários.
- Não altere arquivos fora do escopo solicitado.
- Preserve a compatibilidade com dados e funcionalidades existentes.
- Não introduza soluções temporárias sem justificativa.

## 3. Fluxo de trabalho

1. Identifique os arquivos envolvidos.
2. Analise as implementações relacionadas.
3. Identifique dependências e possíveis efeitos colaterais.
4. Implemente a solução mais simples e adequada.
5. Execute os testes pertinentes.
6. Verifique se a implementação funcionou.
7. Atualize o DEVLOG.md e, quando aplicável, o CHANGELOG.md.
8. Informe os arquivos alterados, testes executados e eventuais limitações.

## 4. Banco de dados e integridade

- Preserve a integridade e a consistência dos dados.
- Analise impactos antes de alterar estruturas ou relacionamentos.
- Não execute operações destrutivas sem autorização.
- Preserve a compatibilidade com bancos de dados existentes.
- Considere migrações sempre que houver alterações estruturais.
- Não comprometa mecanismos de backup e restauração.
- Trate transações e falhas de operações adequadamente.

## 5. Dependências e arquitetura

- Prefira bibliotecas e recursos já disponíveis no projeto.
- Consulte o ambiente e as dependências antes de instalar novos pacotes.
- Não adicione dependências para resolver problemas simples.
- Evite duplicação de código e responsabilidades.
- Preserve a separação entre interface, lógica de negócio e acesso a dados.
- Não introduza mudanças arquiteturais sem necessidade ou autorização.

## 6. Testes e qualidade

- Utilize Ruff como referência para lint e formatação Python.
- Crie ou atualize testes quando necessário.
- Execute somente os testes pertinentes à alteração, ampliando a verificação quando houver impactos relevantes.
- Não ignore falhas de testes sem investigar.
- Não desative ou enfraqueça testes para aprovar uma implementação.
- Não declare uma funcionalidade como concluída sem verificar seu comportamento.
- Diferencie testes executados, não executados e resultados esperados.

## 7. Segurança

- Nunca exponha credenciais, tokens, chaves ou informações sensíveis.
- Não armazene segredos diretamente no código.
- Não remova mecanismos de proteção existentes.
- Valide entradas e operações que envolvam arquivos e dados.
- Não execute comandos destrutivos sem autorização.
- Preserve a segurança dos backups e dos processos de restauração.

## 8. Git e versionamento

- Não execute commits, pushes, merges ou releases sem autorização.
- Não descarte alterações existentes do usuário.
- Verifique o estado do Git antes de operações que possam afetar arquivos.
- Preserve o histórico de versões.
- Siga o padrão Conventional Commits quando solicitado a preparar mensagens de commit.
- Não altere arquivos de configuração do Git sem necessidade.

## 9. Interface e experiência do usuário

- Preserve a identidade visual estabelecida no projeto.
- Mantenha consistência entre telas, componentes e interações.
- Evite duplicar componentes ou estilos.
- Priorize interfaces claras, intuitivas e consistentes.
- Preserve acessibilidade, legibilidade e usabilidade.
- Não altere comportamentos existentes sem avaliar seus impactos.

## 10. Comunicação e respostas

- Utilize português brasileiro nas respostas e documentações.
- Seja objetivo, técnico e evite explicações repetitivas.
- Não apresente análises extensas quando uma resposta direta for suficiente.
- Informe claramente os arquivos modificados.
- Informe os testes executados e seus resultados.
- Sinalize problemas não resolvidos e limitações.
- Não afirme que uma operação foi realizada sem confirmação.
- Ao fornecer código para substituição, apresente o código completo de cada arquivo afetado.
- Não gere documentação, relatórios ou arquivos adicionais sem necessidade.
