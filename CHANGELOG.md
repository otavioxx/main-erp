# Histórico de versões

## 0.09 - 2026-11-07

- Configurado o launcher e o instalador para consultar atualizações públicas no GitHub
  Releases por padrão, preservando URLs personalizadas e a opção de desativar atualizações.
- Publicado o manifesto e o pacote da versão no GitHub para distribuição e atualização online.

## 0.08 - 2026-11-07

- Corrigida a exibição e a entrada dos valores de venda.
- Cálculos e persistência monetária em centavos para vendas, parcelas, recebimentos,
  produtos, pedidos e condicionais, preservando a compatibilidade das telas existentes.
- Pagamento parcial do saldo final passa a criar uma parcela para o valor restante.
- Banco de dados atualizado por migrações aditivas, com backup automático antes das
  alterações de esquema.

## 0.07

- Primeira versão distribuída pelo instalador com releases versionadas, atualização local
  e rollback automático.
