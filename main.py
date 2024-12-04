from flask import Flask, render_template, request, jsonify, session, send_file, url_for, flash, redirect
from logging.handlers import RotatingFileHandler
from werkzeug.utils import secure_filename
from dotenv import set_key, dotenv_values, load_dotenv
import uuid
import os
import re
import sys
import glob
import json
import subprocess
import threading
import fitz
import webview  # PyWebView para criar a janela de desktop
import logging

app = Flask(__name__)
app.secret_key = 'RB_BC_2O2A'

# Caminho base para a pasta de permissões
ROBOS_FOLDER = r"\\ibc124\PROJETO_RPA\Robôs"
PERMISSIONS_FOLDER = r"\\ibc124\PROJETO_RPA\Permissões"
LOGS_FOLDER = "./logs"

# Extensões permitidas
ALLOWED_EXTENSIONS = {'txt', 'csv', 'xlsx', 'json'}
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

processo_robos = {}

# Configuração básica do logger
logging.basicConfig(filename=os.path.join(LOGS_FOLDER, 'pdf_extraction.log'), level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Diretório para armazenar os logs
os.makedirs(LOGS_FOLDER, exist_ok=True)

@app.route('/api/save_log', methods=['POST'])
def save_log():
    try:
        data = request.json
        if not data:
            return jsonify({'status': 'error', 'message': 'Dados de log ausentes.'}), 400

        robot_name = data.get('robot_name', 'unknown_robot')
        log_message = data.get('message', '')
        log_level = data.get('level', 'info')

        # Obter o nome do usuário da sessão
        user_name = session.get('username', 'unknown_user')

        # Define o arquivo de log com base no nome do robô
        log_file = os.path.join(LOGS_FOLDER, f"{robot_name}.log")

        # Salva o log no arquivo correspondente, incluindo o nome do usuário
        try:
            with open(log_file, 'a') as log_f:
                log_f.write(f"{log_level.upper()}: [User: {user_name}] {log_message}\n")
        except IOError as e:
            return jsonify({'status': 'error', 'message': f'Erro ao escrever no arquivo de log: {str(e)}'}), 500

        return jsonify({'status': 'success', 'message': 'Log salvo com sucesso!'}), 200

    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Erro ao salvar log: {str(e)}'}), 500

@app.route('/set_robot_name/<robot_name>', methods=['POST'])
def set_robot_name(robot_name):
    session['robot_name'] = robot_name
    return jsonify({'status': 'success', 'message': f'Nome do robô definido como {robot_name}.'})

@app.route('/iniciar_rastreamento', methods=['POST'])
def iniciar_rastreamento():
    api_key = request.json.get('api_key')

    if not api_key:
        return jsonify({'status': 'error', 'message': 'Chave de API ausente.'}), 400

    try:
        # Iniciar o processo de automação usando a chave de API fornecida
        from main import main
        main(api_key)
        return jsonify({'status': 'success', 'message': 'Rastreamento iniciado.'}), 200

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

def extrair_sistemas_do_pdf(conteudo_pdf):
    try:
        # Ajuste da regex para ser mais flexível
        match = re.search(
            r"2\.\s*Sistemas utilizados\s*([\s\S]*?)\s*3\.\s*Descrição do Processo Automatizado",
            conteudo_pdf, 
            re.IGNORECASE
        )
        
        if match:
            sistemas_texto = match.group(1)
            
            # Capturar itens na forma de lista, independentemente do marcador (hífen, asterisco, etc.)
            sistemas = re.findall(r"(?:-\s*|\*\s*)([^\n\r]+)", sistemas_texto)
            sistemas = [sistema.strip() for sistema in sistemas if sistema.strip()]
            
            print(f"Sistemas Utilizados Encontrados: {sistemas}")  # Log para depuração
            return sistemas
        else:
            print("Seção de 'Sistemas utilizados' não encontrada no PDF.")
            return []
    except Exception as e:
        print(f"Erro ao extrair sistemas do PDF: {e}")
        return []
    
@app.route('/api/get_sistemas/<robot_name>', methods=['GET'])
def get_sistemas(robot_name):
    """
    Rota para obter os sistemas a partir do PDF de um robô específico.
    """
    try:
        # Construção do caminho do PDF usando ROBOS_FOLDER e o nome do robô
        pdf_path = os.path.join(ROBOS_FOLDER, robot_name, f"{robot_name}.pdf")

        print(f"Tentando acessar o PDF no caminho: {pdf_path}")  # Log de depuração

        if not os.path.exists(pdf_path):
            print(f"PDF não encontrado no caminho: {pdf_path}")
            return jsonify({'message': 'PDF do robô não encontrado.'}), 404

        # Lê o conteúdo do PDF
        pdf_content = ler_pdf_como_texto(pdf_path)

        # Extrai os sistemas do conteúdo do PDF
        sistemas = extrair_sistemas_do_pdf(pdf_content)

        if sistemas:
            return jsonify({'sistemas': sistemas}), 200
        else:
            return jsonify({'message': 'Nenhum sistema encontrado no PDF.'}), 200

    except Exception as e:
        print(f"Erro ao processar o PDF: {e}")  # Log de erro
        return jsonify({'message': f'Erro ao processar o PDF: {str(e)}'}), 500

def ler_pdf_como_texto(pdf_path):
    """
    Função para ler o conteúdo do PDF como texto usando PyMuPDF.
    """
    try:
        pdf_content = ""

        # Abre o PDF e extrai o texto de todas as páginas
        with fitz.open(pdf_path) as pdf:
            for page_num in range(pdf.page_count):
                page = pdf.load_page(page_num)
                pdf_content += page.get_text()

        return pdf_content.strip()

    except Exception as e:
        print(f"Erro ao ler o PDF: {e}")
        return ""  # Retorna string vazia em caso de erro

# Função para configurar o logger
def configurar_logger(robot_name):
    if not os.path.exists(LOGS_FOLDER):
        os.makedirs(LOGS_FOLDER)

    log_file = os.path.join(LOGS_FOLDER, f"{robot_name}.log")

    # Configura o logger com um RotatingFileHandler
    logger = logging.getLogger(robot_name)

    if not logger.hasHandlers():
        handler = RotatingFileHandler(log_file, maxBytes=5000000, backupCount=5)
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

    return logger

def carregar_logs():
    logs = {}
    for log_file in glob.glob(os.path.join(LOGS_FOLDER, "*.log")):
        with open(log_file, 'r') as file:
            robot_name = os.path.basename(log_file).replace('.log', '')
            logs[robot_name] = file.readlines()
    return logs

def salvar_env_na_pasta_do_robo(robot_name):

    # Caminho completo para a pasta do robô dentro de ROBOS_FOLDER
    robot_folder = os.path.join(ROBOS_FOLDER, robot_name)

    # Verifica se a pasta do robô existe; caso contrário, cria a pasta
    if not os.path.exists(robot_folder):
        os.makedirs(robot_folder)

    # Define o caminho completo para o arquivo .env dentro da pasta do robô
    dotenv_path = os.path.join(robot_folder, '.env')

    # Cria o arquivo .env se ele não existir e carrega as variáveis de ambiente existentes
    if not os.path.exists(dotenv_path):
        open(dotenv_path, 'w').close()
    load_dotenv(dotenv_path)

    return dotenv_path  # Retorna o caminho para o .env caso precise usá-lo em outras funções

@app.route('/api/save_system_credentials', methods=['POST'])
def save_system_credentials():
    data = request.json
    robot_name = session.get('robot_name')  # Obtém o nome do robô da sessão

    if not robot_name:
            return jsonify({'status': 'error', 'message': 'Nome do robô não encontrado na sessão.'}), 400

    dotenv_path = salvar_env_na_pasta_do_robo(robot_name)  # Obtém o caminho do .env do robô


    if not data or not isinstance(data, dict):
        return jsonify({'status': 'error', 'message': 'Dados inválidos.'}), 400

    try:
        # Agora escreve as credenciais
        with open(dotenv_path, 'a') as f:
            for sistema, credenciais in data.items():
                if not isinstance(credenciais, dict):
                    continue

                username = credenciais.get('username')
                password = credenciais.get('password')
                api_key = credenciais.get('api_key')

                if username:
                    f.write(f"{sistema}_USERNAME={username}\n")
                if password:
                    f.write(f"{sistema}_PASSWORD={password}\n")
                if api_key:
                    f.write(f"{sistema}_API_KEY={api_key}\n")

        return jsonify({'status': 'success', 'message': 'Credenciais salvas com sucesso!'}), 200

    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Erro ao salvar credenciais: {str(e)}'}), 500
  
@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        # Capturar dados do formulário
        username = request.form.get('username')
        new_password = request.form.get('new_password')

        # Caminho da pasta de permissões do usuário
        permissions_path = os.path.join(PERMISSIONS_FOLDER, username)

        # Verificar se a pasta do usuário existe
        if not os.path.exists(permissions_path):
            os.makedirs(permissions_path)  # Criar a pasta se não existir

        # Caminho do arquivo de credenciais
        credentials_file = os.path.join(permissions_path, 'credenciais.txt')

        # Criar ou atualizar o arquivo de credenciais com a nova senha
        with open(credentials_file, 'w') as file:
            file.write(f'username={username}\npassword={new_password}')

        # Redirecionar para a página de login com mensagem de sucesso
        flash('Senha redefinida com sucesso!', 'success')
        return redirect(url_for('login'))

    return render_template('forgot_password.html')  # Página de redefinição de senha

# Função para verificar credenciais de usuário
def check_credentials(username, password):
    """
    Verifica se o arquivo de credenciais do usuário existe e se o username e password estão corretos.
    """
    caminho_credenciais = os.path.join(PERMISSIONS_FOLDER, username, 'credenciais.txt')
    
    if os.path.exists(caminho_credenciais):
        # Lê o arquivo de credenciais
        with open(caminho_credenciais, 'r') as file:
            credentials = {}
            for line in file:
                key, value = line.strip().split('=')
                credentials[key] = value
            
            # Verifica se as credenciais são válidas
            if credentials.get('username') == username and credentials.get('password') == password:
                return True
    return False

# Função para listar robôs com base no JSON de permissões do usuário
def listar_robos(username):
    """
    Função para listar todos os robôs que o usuário tem permissão para acessar,
    com base no arquivo robos.json na pasta do usuário.
    """
    robos = []
    caminho_robos = os.path.join(PERMISSIONS_FOLDER, username, 'robos.json')
    
    if os.path.exists(caminho_robos):
        with open(caminho_robos, 'r') as file:
            data = json.load(file)
            robo_nomes = data.get('robos', [])
            
            # Carrega os detalhes de cada robô, incluindo o `process_name`
            for robot_name in robo_nomes:
                # Aqui chamamos uma função que recupera o nome do processo
                process_name = carregar_detalhes_do_robo(robot_name)  # Exemplo de função para obter detalhes
                robos.append({
                    'name': robot_name,
                    'process_name': process_name
                })
    return robos

def carregar_detalhes_do_robo(robot_name):
    """
    Carrega detalhes do robô a partir de um arquivo PDF localizado na pasta do robô,
    extraindo informações do conteúdo do PDF. Retorna uma mensagem caso o PDF esteja ausente.
    """
    # Verifica se robot_name é um dicionário e extrai o 'name' se for o caso
    if isinstance(robot_name, dict):
        robot_name = robot_name.get('name', 'NomeDesconhecido')  # Usa 'NomeDesconhecido' como fallback

    # Define o caminho para a pasta do robô e o arquivo PDF esperado
    robot_folder = os.path.join(ROBOS_FOLDER, robot_name)
    pdf_path = os.path.join(robot_folder, f'{robot_name}.pdf')
    
    print("Robot Folder Path:", robot_folder)
    print("Expected PDF Path:", pdf_path)

    # Verifica se a pasta do robô existe
    if not os.path.exists(robot_folder):
        print(f"Pasta do robô '{robot_folder}' não encontrada.")
        return {
            'nome': robot_name,
            'processo': 'Pasta do robô não encontrada.',
            'unidade': 'Desconhecida',
            'cargo_executor': 'Nenhum executor disponível',
            'sistemas_utilizados': []
        }

    # Verifica se o PDF específico existe
    if not os.path.exists(pdf_path):
        print(f"Arquivo PDF não encontrado: {pdf_path}")
        return {
            'nome': robot_name,
            'processo': 'PDF de detalhes não encontrado.',
            'unidade': 'Desconhecida',
            'cargo_executor': 'Nenhum executor disponível',
            'sistemas_utilizados': []
        }

    # Se o PDF existir, prossegue com a extração dos detalhes
    try:
        with fitz.open(pdf_path) as pdf:
            text = ""
            for page in pdf:
                text += page.get_text()

            # Extração dos detalhes do texto do PDF
            processo_match = re.search(r"Processo:\s*(.*)", text, re.IGNORECASE)
            unidade_match = re.search(r"Unidade:\s*(.*)", text, re.IGNORECASE)
            cargo_match = re.search(r"Cargo Executor:\s*(.*)", text, re.IGNORECASE)

            processo = processo_match.group(1).strip() if processo_match else 'Não especificado'
            unidade = unidade_match.group(1).strip() if unidade_match else 'Não especificada'
            cargo_executor = cargo_match.group(1).strip() if cargo_match else 'Nenhum executor disponível'

            # Tentativa de extrair os sistemas utilizados
            sistemas_inicio = text.find("Sistemas utilizados")
            if sistemas_inicio != -1:
                sistemas_text = text[sistemas_inicio:].split("\n")[1:]
                sistemas_utilizados = [s.strip() for s in sistemas_text if s.strip()]
            else:
                sistemas_utilizados = []

            print(f"Processo: {processo}, Unidade: {unidade}, Cargo Executor: {cargo_executor}, Sistemas Utilizados: {sistemas_utilizados}")

            return {
                'nome': robot_name,
                'processo': processo,
                'unidade': unidade,
                'cargo_executor': cargo_executor,
                'sistemas_utilizados': sistemas_utilizados
            }

    except Exception as e:
        print(f"Erro ao ler o PDF {pdf_path}: {e}")
        return {
            'nome': robot_name,
            'processo': 'Erro ao carregar as informações do PDF.',
            'unidade': 'Desconhecida',
            'cargo_executor': 'Nenhum executor disponível',
            'sistemas_utilizados': []
        }
    
# Função para execução de executáveis com feedback
def executar_robo(robot_name, robot_executable_path):
    logger = configurar_logger(robot_name)

    try:
        # Executa o robô passando o caminho da planilha como argumento
        process = subprocess.Popen(
            [robot_executable_path],
            shell=True,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
 		creationflags=subprocess.CREATE_NEW_CONSOLE
        )

        stdout, stderr = process.communicate()

        if process.returncode == 0:
            logger.info(f"Robô {robot_name} executado com sucesso. Saída: {stdout.strip()}")
            return True, 'Executado com sucesso.'
        else:
            logger.error(f"Erro ao executar o robô {robot_name}. Erro: {stderr.strip()}")
            return False, f"Erro ao executar o robô. Detalhes: {stderr.strip()}"
    except Exception as e:
        logger.error(f"Erro inesperado ao executar o robô {robot_name}: {e}")
        return False, f"Erro inesperado: {e}"

# Função para contar execuções e erros nos logs
def contar_execucoes_erros(log_file_path):
    execucoes = 0
    erros = 0
    log_lines = []

    # Ler o arquivo de log
    with open(log_file_path, 'r') as file:
        lines = file.readlines()

    # Analisar cada linha para contar execuções e erros
    for line in lines:
        log_lines.append(line.strip())  # Armazena todas as linhas para exibir no template
        if "INFO" in line:
            execucoes += 1
        elif "ERROR" in line:
            erros += 1

    return execucoes, erros, log_lines

@app.route('/api/get_robot_details/<robot_name>', methods=['GET'])
def get_robot_details(robot_name):
    robot_data = carregar_detalhes_do_robo(robot_name)
    return jsonify(robot_data)

# Rota para exibir a página do robô
@app.route('/robo/<robot_name>', methods=['GET', 'POST'])
def robo_page(robot_name):
    # Armazena o nome do robô na sessão
    session['robot_name'] = robot_name

    # Carrega os detalhes do robô a partir da ficha técnica (PDF)
    robot_info = carregar_detalhes_do_robo(robot_name)

    # Verifica se há sistemas listados na ficha técnica, garante que seja uma lista
    sistemas = robot_info.get('sistemas_utilizados', [])
    if not isinstance(sistemas, list):
        sistemas = []

    # Filtra sistemas para garantir que não haja valores None
    sistemas = [sistema if sistema is not None else '' for sistema in sistemas]

    if request.method == 'POST':
        # Processa as credenciais enviadas pelo formulário
        credenciais = {}
        for sistema in sistemas:
            usuario = request.form.get(f'usuario_{sistema}')
            senha = request.form.get(f'senha_{sistema}')
            chave_api = request.form.get(f'chave_api_{sistema}')
            credenciais[sistema] = {
                'usuario': usuario,
                'senha': senha,
                'chave_api': chave_api
            }

        # Salva as credenciais conforme a lógica (pode ser em arquivo .env ou banco de dados)
        save_system_credentials(robot_name, credenciais)

        flash('Credenciais salvas com sucesso!', 'success')
        return redirect(url_for('robo_page', robot_name=robot_name))

    # Prepara os dados para o template
    robot_data = {
        'robot_name': robot_name,
        'robot_processo': robot_info.get('processo', 'N/A'),
        'robot_unidade': robot_info.get('unidade', 'N/A'),
        'robot_cargo_executor': robot_info.get('cargo_executor', 'N/A'),
        'sistemas': sistemas  # Passa os sistemas para o template
    }

    return render_template('robo.html', **robot_data)

@app.route('/api/execute_robot', methods=['POST'])
def execute_robot():
    robot_name = session.get('robot_name')  # Obtém o nome do robô da sessão
    app.logger.info(f"Nome do robô obtido da sessão: {robot_name}")

    if not robot_name:
        app.logger.error("Nome do robô não encontrado na sessão.")
        return jsonify({'status': 'error', 'message': 'Nome do robô não encontrado na sessão.'}), 400

    # Caminho completo do executável do robô
    robot_executable_path = os.path.join(ROBOS_FOLDER, robot_name, f"{robot_name}.exe")
    app.logger.info(f"Caminho do executável do robô: {robot_executable_path}")

    # Verifica se o executável do robô existe
    if not os.path.exists(robot_executable_path):
        app.logger.error("Executável do robô não encontrado.")
        return jsonify({'status': 'error', 'message': 'Executável do robô não encontrado.'}), 404

    try:
        # Executa o robô usando subprocess
        processo = subprocess.Popen(
            [robot_executable_path],
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        processo_robos[robot_name] = processo  # Armazena o processo em execução


        stdout, stderr = processo.communicate()

        # Verifica o código de retorno para saber se a execução foi bem-sucedida
        if processo.returncode == 0:
            return jsonify({'status': 'success', 'message': 'Robô executado com sucesso.', 'output': stdout.strip()})
        else:
            return jsonify({'status': 'error', 'message': f'Erro na execução do robô. Detalhes: {stderr.strip()}'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Erro ao tentar executar o robô: {str(e)}'}), 500

@app.route('/api/cancel_robot_execution', methods=['POST'])
def cancel_robot_execution():
    robot_name = session.get('robot_name')
    app.logger.info(f"Tentativa de interrupção da execução do robô: {robot_name}")

    if not robot_name or robot_name not in processo_robos:
        app.logger.error(f"Processo de robô {robot_name} não encontrado.")
        return jsonify({'status': 'error', 'message': 'Processo de robô não encontrado.'}), 404

    processo = processo_robos[robot_name]
    try:
        # Verifica se o processo ainda está em execução
        if processo.poll() is None:
            app.logger.info(f"Enviando sinal de término para o processo do robô {robot_name}.")
            processo.terminate()  # Envia o sinal de término para o processo
            processo.wait(timeout=5)  # Aguarda o processo terminar por até 5 segundos

            # Se o processo ainda estiver ativo, força o término
            if processo.poll() is None:
                app.logger.warning(f"Processo do robô {robot_name} não terminou, forçando término.")
                processo.kill()

            app.logger.info(f"Execução do robô {robot_name} interrompida com sucesso.")
            processo_robos.pop(robot_name, None)  # Remove o processo da lista
            return jsonify({'status': 'success', 'message': 'Execução do robô interrompida com sucesso.'})
        else:
            app.logger.info(f"Processo do robô {robot_name} já está finalizado.")
            processo_robos.pop(robot_name, None)
            return jsonify({'status': 'success', 'message': 'O processo do robô já estava finalizado.'})
    except subprocess.TimeoutExpired:
        app.logger.error(f"Tempo limite excedido ao tentar interromper o processo do robô {robot_name}.")
        return jsonify({'status': 'error', 'message': 'Tempo limite excedido ao tentar interromper o robô.'}), 500
    except Exception as e:
        app.logger.error(f"Erro ao tentar interromper o processo do robô {robot_name}: {str(e)}")
        return jsonify({'status': 'error', 'message': f'Erro ao tentar interromper o robô: {str(e)}'}), 500

# Rota de login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Recebe os dados do login
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        # Verifica as credenciais
        if check_credentials(username, password):
            session['username'] = username  # Salva o usuário na sessão
            return jsonify({
                'status': 'success',
                'message': f'Bem-vindo, {username}!',
                'username': username
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Credenciais inválidas.'
            }), 401

    # Renderiza a página de login para requisições GET
    return render_template('login.html')
    
@app.route('/home')
def home():
    # Simula a lista de robôs associados ao usuário
    robot_names = listar_robos(session.get('username'))
    
    # Obtém os detalhes de cada robô
    robots_details = []
    for robot_name in robot_names:
        details = carregar_detalhes_do_robo(robot_name)
        robots_details.append(details)
    
    # Passa os detalhes para o template
    return render_template('home.html', robots=robots_details)

@app.route('/relatorios')
def relatorios():
    robots = []
    logs = {}

    if os.path.exists(LOGS_FOLDER):
        for log_file in os.listdir(LOGS_FOLDER):
            if log_file.endswith('.log'):
                robot_name = os.path.splitext(log_file)[0]
                log_file_path = os.path.join(LOGS_FOLDER, log_file)
                
                execucoes, erros, log_lines = contar_execucoes_erros(log_file_path)
                robots.append({'name': robot_name, 'executions': execucoes, 'errors': erros})
                logs[robot_name] = log_lines  # Inclui as linhas de log para o template

    # Define os arrays de nomes, execuções e erros
    robot_names = [robot['name'] for robot in robots]
    robot_executions = [robot['executions'] for robot in robots]
    robot_errors = [robot['errors'] for robot in robots]

    # Verifique se logs está vazio ou não
    if not logs:
        logs = {}

    return render_template(
        'relatorios.html', 
        robot_names=robot_names, 
        robot_executions=robot_executions, 
        robot_errors=robot_errors, 
        logs=logs  # Passa logs ao template
    )

@app.route('/download_log/<robot_name>')
def download_log(robot_name):
    log_path = os.path.join(LOGS_FOLDER, f"{robot_name}.log")
    
    if os.path.exists(log_path):
        return send_file(log_path, as_attachment=True)
    else:
        return "Log não encontrado", 404

# Rota para retornar os robôs do usuário logado
@app.route('/api/robos', methods=['GET'])
def api_listar_robos():
    """
    API que retorna a lista de robôs e as permissões associadas ao usuário logado.
    """
    username = session.get('username')  # Obtém o username da sessão
    if not username:
        return jsonify({'status': 'error', 'message': 'Usuário não está logado.'}), 401
    
    robos = listar_robos(username)
    return jsonify(robos)

# Rota para obter o nome do usuário logado
@app.route('/api/get_user_robots', methods=['GET'])
def get_user_robots():
    username = session.get('username')
    if username:
        robot_names = listar_robos(username)  # Função que busca os nomes dos robôs do usuário
        robots_details = []
        for robot_name in robot_names:
            details = carregar_detalhes_do_robo(robot_name)  # Obtém detalhes do robô
            robots_details.append(details)
        return jsonify({'robots': robots_details})
    else:
        return jsonify({'status': 'error', 'message': 'Usuário não está logado.'}), 401

@app.route('/api/get_username', methods=['GET'])
def get_username():
    # Verifica se o nome do usuário está armazenado na sessão
    username = session.get('username', 'Usuário Desconhecido')
    return jsonify({'username': username})

@app.route('/api/get_logged_in_user', methods=['GET'])
def get_logged_in_user():
    # Verifica se o nome do usuário está na sessão
    username = session.get('username')
    
    if username:
        # Retorna o nome do usuário se ele estiver logado
        return jsonify({'username': username})
    else:
        # Se o usuário não estiver logado, retorna uma mensagem de erro
        return jsonify({'username': None, 'message': 'Usuário não está logado.'}), 401

# Rota para realizar logout
@app.route('/logout', methods=['POST'])
def logout():
    """
    Rota para deslogar o usuário, removendo-o da sessão.
    """
    session.pop('username', None)
    return jsonify({'status': 'success', 'message': 'Usuário deslogado com sucesso.'})

# Função para iniciar o Flask em segundo plano
def run_flask():
    app.run(debug=True, use_reloader=False)

if __name__ == '__main__':
    # Executa o Flask em um thread separado
    flask_thread = threading.Thread(target=lambda: app.run(debug=True, use_reloader=False))
    flask_thread.daemon = True
    flask_thread.start()

    # Inicializa a janela do PyWebView
    webview.create_window(
        title='Orquestrador de Robôs', 
        url='http://127.0.0.1:5000/login',
        width=1200,
        height=800,
        resizable=True
    )
    
    webview.start()