
# Centralizador RPA

**Centralizador RPA** é uma aplicação web desenvolvida para facilitar o gerenciamento e a execução de automações de processos robóticos (RPA). O sistema oferece uma interface amigável para visualizar, executar e monitorar automações, além de gerenciar relatórios e logs.

---

## 🛠️ Funcionalidades

- **Autenticação**: Sistema de login com suporte a recuperação de senha.
- **Dashboard Interativa**: Página inicial para gerenciar e executar automações.
- **Relatórios e Logs**: Acompanhamento detalhado das execuções, com acesso aos relatórios e logs gerados.
- **Gerenciamento de Robôs**: Adição e configuração de novas automações através da interface.
- **Interface Web Responsiva**: Desenvolvido para funcionar em diferentes dispositivos.

---

## 📁 Estrutura do Projeto

```plaintext
PROJETO RPA/
├── build/                # Arquivos gerados após o build
├── dist/                 # Distribuição final da aplicação
├── logs/                 # Logs gerados durante a execução
├── static/               # Arquivos estáticos (CSS, JS, imagens)
├── templates/            # Templates HTML da aplicação
│   ├── forgot_password.html # Página para recuperação de senha
│   ├── home.html            # Página inicial (dashboard)
│   ├── login.html           # Página de login
│   ├── relatorios.html      # Página para visualização de relatórios
│   └── robo.html            # Página para gerenciamento de robôs
├── .gitignore            # Arquivos e pastas ignorados pelo Git
├── centralizador.spec    # Configuração para geração do executável
├── icon.ico              # Ícone do aplicativo
└── main.py               # Script principal da aplicação
```

---

## 🚀 Instalação e Configuração

### Pré-requisitos
- Python 3.8 ou superior
- Pip instalado

### 1. Clone o Repositório
```bash
git clone https://github.com/htmleiene/centralizador-rpa.git
cd centralizador-rpa
```

### 2. Instale as Dependências
```bash
pip install -r requirements.txt
```

### 3. Execute o Sistema
No diretório raiz do projeto, inicie a aplicação com:

```bash
python main.py
```

Acesse a interface no navegador em: [http://localhost:5000](http://localhost:5000).

---

## 🌐 Estrutura da Interface Web

### Templates Disponíveis
- **Login:** Permite que usuários se autentiquem no sistema.
- **Dashboard:** Apresenta um resumo das automações disponíveis e executadas.
- **Relatórios:** Exibe os relatórios gerados pelas automações.
- **Gerenciamento de Robôs:** Permite adicionar e configurar robôs.

---

## 🔧 Desenvolvimento

### Adicionar Novos Robôs
1. Insira o código da automação na pasta apropriada.
2. Configure o arquivo `robo.html` para incluir o robô na interface.

---

