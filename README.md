# MainERP - Sistema de Gestão Empresarial

## 📋 Descrição
Sistema completo de gestão empresarial desenvolvido em Python com interface PyQt6.

## 🛠️ Tecnologias
- Python 3.8+
- PyQt6 - Interface gráfica
- SQLite - Banco de dados
- PyInstaller - Empacotamento

## 📦 Instalação e Execução

### Pré-requisitos
- Python 3.8 ou superior
- pip (gerenciador de pacotes Python)

### 1. Clonar o repositório
git clone https://github.com/otavioxx/MainERP.git
cd erp

### 2. Instalar dependências
pip install -r requirements.txt

### 3. Executar em modo desenvolvimento
python -m main

## 🚀 Compilação

### Compilar para executável

# Na pasta raiz, use o script de build no terminal
python build.py

### Estrutura de compilação
erp/
├── main.py                 # Ponto de entrada principal
├── main.spec              # Configuração do PyInstaller
├── build.py               # Script de build personalizado
├── requirements.txt       # Dependências do projeto
├── database/              # Módulos de banco de dados
├── models/                # Modelos de dados
├── views/                 # Interfaces gráficas
├── utils/                 # Utilitários e helpers
├── relatorios/            # Geração de relatórios
└── config.py             # Configurações do sistema

### Estrutura do banco de dados
O sistema utiliza SQLite com tabelas principais:
- clientes - Cadastro de clientes
- produtos - Controle de produtos e estoque
- fornecedores - Cadastro de fornecedores
- vendas - Registro de vendas
- pedidos - Pedidos de compra
- duplicatas - Contas a receber
- condicionais - Produtos em consignação

## 🎯 Funcionalidades Principais

### 📊 Gestão de Vendas
- Registro completo de vendas
- Geração automática de duplicatas
- Controle de parcelamentos
- Relatórios de vendas

### 📦 Controle de Estoque
- Cadastro de produtos
- Controle de entrada/saída
- Preços de custo e venda
- Alertas de estoque baixo

### 💰 Financeiro
- Controle de recebíveis
- Gestão de duplicatas
- Relatórios financeiros

### 🔄 Condicionais
- Controle de produtos em consignação
- COnversão de Condicional em Venda
- Devolução de itens
- Relatórios de condicionais ativas

## 🔧 Desenvolvimento

### Estrutura do Projeto
erp/
├── main.py              # Entry point principal
├── config.py            # Configurações
├── database.py          # Conexão com banco
├── styles.py            # Temas e estilos
├── views/               # Interfaces
│   ├── main_window.py   # Janela principal
│   ├── venda_view.py    # Módulo de vendas
│   └── ... outros módulos
├── models/              # Modelos de dados
│   ├── cliente.py       # Modelo Cliente
│   ├── produto.py       # Modelo Produto
│   └── ... outros modelos
├── utils/               # Utilitários
│   ├── helpers.py       # Funções auxiliares
│   ├── database_utils.py # Utils de banco
│   └── ... outros utils
└── relatorios/          # Geração de relatórios

## 🐛 Solução de Problemas

### Erro comum: Múltiplas instâncias
O sistema previne múltiplas execuções. Se ocorrer erro:
- Verifique processos ativos no Gerenciador de Tarefas
- Delete arquivo .lock em ~/.erp_lock/ se necessário

### Problemas de banco de dados
- Verifique se a pasta database existe
- Confirme permissões de escrita
- Execute verificação de integridade

## 📄 Licença

Proprietário - Digital Solutions
Todos os direitos reservados.