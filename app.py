from werkzeug.security import generate_password_hash
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from dotenv import load_dotenv
from mysql.connector import Error
import mysql.connector
import os

app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
load_dotenv()


def create_db_connection():
    db_config = {
        'user': os.getenv('USER'),
        'password': os.getenv('PASSWORD'),
        'host': os.getenv('HOST'),
        'port': os.getenv('PORT'),
        'database': os.getenv('DATABASE'),
    }
    try:
        connection = mysql.connector.connect(**db_config)
        if connection.is_connected():
            return connection
    except Error as e:
        print(f"Erro ao conectar ao MySQL: {e}")
        return None

@app.route('/')
def inicio():
    render_template('disciplina.html')

@app.route('/disciplina')
def disciplina():
    return render_template('disciplina.html')

@app.route('/aluno')
def aluno():
    return render_template('aluno.html')

@app.route('/curso')
def curso():
    return render_template('curso.html')

@app.route('/professor')
def professor():
    return render_template('professor.html')


#----------------Disciplinas------------------------
@app.route('/disciplinas', methods=['GET'])
def listar_disciplinas():
    connection = create_db_connection()
    if not connection:
        return jsonify({'error': 'Erro ao conectar ao banco de dados'}), 500
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM lucas_disciplina")
    disciplinas = cursor.fetchall()
    cursor.close()
    connection.close()
    return jsonify(disciplinas)

@app.route('/disciplinas/<int:id>', methods=['GET'])
def get_disciplina_by_id(id):
    connection = create_db_connection()
    if not connection:
        return jsonify({'error': 'Erro ao conectar ao banco de dados'}), 500
    
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM lucas_disciplina WHERE id = %s", (id,))
    disciplina = cursor.fetchone()  # Usamos fetchone porque esperamos um único resultado
    
    cursor.close()
    connection.close()

    if disciplina:
        return jsonify(disciplina)
    else:
        return jsonify({'error': 'Disciplina não encontrada'}), 404

    return jsonify(disciplinas)

@app.route('/disciplinas', methods=['POST'])
def criar_disciplina():
    dados = request.json
    print(dados)
    nome = dados.get('nome')
    carga_horaria = dados.get('carga_horaria')
    if not nome or not carga_horaria:
        return jsonify({'error': 'Nome e carga horária são obrigatórios'}), 400
    connection = create_db_connection()
    if not connection:
        return jsonify({'error': 'Erro ao conectar ao banco de dados'}), 500
    cursor = connection.cursor()
    try:
        cursor.execute("INSERT INTO lucas_disciplina (nome, carga_horaria) VALUES (%s, %s)", (nome, carga_horaria))
        connection.commit()
        disciplina_id = cursor.lastrowid
        cursor.close()
        connection.close()
        return jsonify({'id': disciplina_id, 'nome': nome, 'carga_horaria': carga_horaria}), 201
    except mysql.connector.Error as e:
        connection.rollback()
        cursor.close()
        connection.close()
        return jsonify({'error': str(e)}), 500

@app.route('/disciplinas/<int:id>', methods=['PUT'])
def editar_disciplina(id):
    dados = request.json
    nome = dados.get('nome')
    carga_horaria = dados.get('carga_horaria')
    
    if not nome or not carga_horaria:
        return jsonify({'error': 'Nome e carga horária são obrigatórios'}), 400
    
    connection = create_db_connection()
    if not connection:
        return jsonify({'error': 'Erro ao conectar ao banco de dados'}), 500

    cursor = connection.cursor()
    try:
        # Atualiza os dados da disciplina no banco de dados
        cursor.execute(
            "UPDATE lucas_disciplina SET nome = %s, carga_horaria = %s WHERE id = %s",
            (nome, carga_horaria, id)
        )
        connection.commit()
        
        # Verificar se a disciplina foi realmente alterada
        if cursor.rowcount == 0:
            return jsonify({'error': 'Disciplina não encontrada'}), 404
        
        cursor.close()
        connection.close()
        return jsonify({'id': id, 'nome': nome, 'carga_horaria': carga_horaria}), 200
    except mysql.connector.Error as e:
        connection.rollback()
        cursor.close()
        connection.close()
        return jsonify({'error': str(e)}), 500
    
@app.route('/disciplinas/<int:id>', methods=['DELETE'])
def excluir_disciplina(id):
    connection = create_db_connection()
    if not connection:
        return jsonify({'error': 'Erro ao conectar ao banco de dados'}), 500

    cursor = connection.cursor()
    try:
        # Deleta a disciplina do banco de dados
        cursor.execute("DELETE FROM lucas_disciplina WHERE id = %s", (id,))
        connection.commit()

        # Verificar se a disciplina foi realmente excluída
        if cursor.rowcount == 0:
            return jsonify({'error': 'Disciplina não encontrada'}), 404
        
        cursor.close()
        connection.close()
        return jsonify({'message': 'Disciplina excluída com sucesso'}), 200
    except mysql.connector.Error as e:
        connection.rollback()
        cursor.close()
        connection.close()
        return jsonify({'error': str(e)}), 500

#----------------Cursos------------------------------
@app.route('/cursos', methods=['GET'])
def listar_cursos():
    connection = create_db_connection()
    if not connection:
        return jsonify({'error': 'Erro ao conectar ao banco de dados'}), 500
    
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM lucas_curso")
    cursos = cursor.fetchall()

    for curso in cursos:
        # Se o campo 'disciplinas' for uma string separada por vírgulas, convertemos em uma lista de IDs
        disciplinas_ids = curso['disciplinas'].split(',')

        # Consulta para pegar as cargas horárias das disciplinas associadas
        cursor.execute(f"SELECT carga_horaria FROM lucas_disciplina WHERE id IN ({','.join(['%s']*len(disciplinas_ids))})", tuple(disciplinas_ids))
        disciplinas = cursor.fetchall()

        # Calcular a carga horária total
        carga_horaria_total = sum(disciplina['carga_horaria'] for disciplina in disciplinas)

        # Adicionar a carga horária total ao curso
        curso['carga_horaria_total'] = carga_horaria_total

    cursor.close()
    connection.close()
    return jsonify(cursos)

@app.route('/cursos/<int:id>', methods=['GET'])
def listar_curso_por_id(id):
    connection = create_db_connection()
    if not connection:
        return jsonify({'error': 'Erro ao conectar ao banco de dados'}), 500
    
    cursor = connection.cursor(dictionary=True)
    
    # Consulta para pegar o curso com o ID especificado
    cursor.execute("SELECT * FROM lucas_curso WHERE id = %s", (id,))
    curso = cursor.fetchone()  # Usamos fetchone porque esperamos um único resultado

    if curso:
        # Se 'disciplinas' for uma string separada por vírgulas, convertemos em uma lista de IDs
        disciplinas_ids = curso['disciplinas'].split(',')
        
        # Consulta para pegar as cargas horárias das disciplinas associadas
        cursor.execute(f"SELECT carga_horaria FROM lucas_disciplina WHERE id IN ({','.join(['%s']*len(disciplinas_ids))})", tuple(disciplinas_ids))
        disciplinas = cursor.fetchall()
        
        # Calcular a carga horária total
        carga_horaria_total = sum(disciplina['carga_horaria'] for disciplina in disciplinas)
        
        # Adicionar a carga horária total ao curso
        curso['carga_horaria_total'] = carga_horaria_total
        cursor.close()
        connection.close()
        return jsonify(curso)  # Retorna os dados do curso com a carga horária total
    else:
        cursor.close()
        connection.close()
        return jsonify({'error': 'Curso não encontrado'}), 404  # Caso o curso não seja encontrado

@app.route('/cursos', methods=['POST'])
def criar_curso():
    dados = request.json
    nome = dados.get('nome')
    disciplinas_ids = dados.get('disciplinas')  # Lista de IDs das disciplinas
    if not nome or not disciplinas_ids:
        return jsonify({'error': 'Nome do curso e disciplinas são obrigatórios'}), 400
    
    # Converte a lista de disciplinas para uma string separada por vírgulas
    disciplinas_str = ','.join(map(str, disciplinas_ids))
    
    # Calcular carga horária total (soma das cargas horárias das disciplinas associadas)
    connection = create_db_connection()
    if not connection:
        return jsonify({'error': 'Erro ao conectar ao banco de dados'}), 500
    
    cursor = connection.cursor()
    try:
        # Obter carga horária total das disciplinas
        cursor.execute("SELECT SUM(carga_horaria) FROM lucas_disciplina WHERE id IN (%s)", (disciplinas_str,))
        resultado = cursor.fetchone()
        carga_horaria_total = resultado[0] if resultado[0] is not None else 0
        
        # Inserir o curso no banco de dados
        cursor.execute(
            "INSERT INTO lucas_curso (nome, carga_horaria_total, disciplinas) VALUES (%s, %s, %s)",
            (nome, carga_horaria_total, disciplinas_str)
        )
        connection.commit()
        curso_id = cursor.lastrowid
        cursor.close()
        connection.close()
        return jsonify({'id': curso_id, 'nome': nome, 'carga_horaria_total': carga_horaria_total, 'disciplinas': disciplinas_ids}), 201
    except mysql.connector.Error as e:
        connection.rollback()
        cursor.close()
        connection.close()
        return jsonify({'error': str(e)}), 500

@app.route('/cursos/<int:id>', methods=['PUT'])
def editar_curso(id):
    dados = request.json
    nome = dados.get('nome')
    disciplinas_ids = dados.get('disciplinas')
    if not nome or not disciplinas_ids:
        return jsonify({'error': 'Nome do curso e disciplinas são obrigatórios'}), 400
    
    disciplinas_str = ','.join(map(str, disciplinas_ids))
    
    connection = create_db_connection()
    if not connection:
        return jsonify({'error': 'Erro ao conectar ao banco de dados'}), 500
    
    cursor = connection.cursor()
    try:
        # Obter carga horária total das disciplinas
        cursor.execute("SELECT SUM(carga_horaria) FROM lucas_disciplina WHERE id IN (%s)", (disciplinas_str,))
        resultado = cursor.fetchone()
        carga_horaria_total = resultado[0] if resultado[0] is not None else 0
        
        # Atualizar o curso no banco de dados
        cursor.execute(
            "UPDATE lucas_curso SET nome = %s, carga_horaria_total = %s, disciplinas = %s WHERE id = %s",
            (nome, carga_horaria_total, disciplinas_str, id)
        )
        connection.commit()
        
        if cursor.rowcount == 0:
            return jsonify({'error': 'Curso não encontrado'}), 404
        
        cursor.close()
        connection.close()
        return jsonify({'id': id, 'nome': nome, 'carga_horaria_total': carga_horaria_total, 'disciplinas': disciplinas_ids}), 200
    except mysql.connector.Error as e:
        connection.rollback()
        cursor.close()
        connection.close()
        return jsonify({'error': str(e)}), 500

@app.route('/cursos/<int:id>', methods=['DELETE'])
def excluir_curso(id):
    connection = create_db_connection()
    if not connection:
        return jsonify({'error': 'Erro ao conectar ao banco de dados'}), 500

    cursor = connection.cursor()
    try:
        cursor.execute("DELETE FROM lucas_curso WHERE id = %s", (id,))
        connection.commit()

        if cursor.rowcount == 0:
            return jsonify({'error': 'Curso não encontrado'}), 404
        
        cursor.close()
        connection.close()
        return jsonify({'message': 'Curso excluído com sucesso'}), 200
    except mysql.connector.Error as e:
        connection.rollback()
        cursor.close()
        connection.close()
        return jsonify({'error': str(e)}), 500

#----------------------Professores-----------------------
@app.route('/professores', methods=['GET'])
def listar_professores():
    connection = create_db_connection()
    if not connection:
        return jsonify({'error': 'Erro ao conectar ao banco de dados'}), 500
    
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM lucas_professor")
    professores = cursor.fetchall()
    cursor.close()
    connection.close()
    return jsonify(professores)

@app.route('/professores', methods=['POST'])
def criar_professor():
    dados = request.json
    print(dados)
    nome = dados.get('nome')
    telefone = dados.get('telefone')
    usuario = dados.get('usuario')
    senha = dados.get('senha')
    disciplinas_ids = dados.get('disciplinas')  # Lista de IDs das disciplinas
    if not nome or not usuario or not senha or not disciplinas_ids:
        return jsonify({'error': 'Nome, usuário, senha e disciplinas são obrigatórios'}), 400
    
    # Gerar o hash da senha
    senha_hash = generate_password_hash(senha)
    
    disciplinas_str = ','.join(map(str, disciplinas_ids))
    
    connection = create_db_connection()
    if not connection:
        return jsonify({'error': 'Erro ao conectar ao banco de dados'}), 500
    
    cursor = connection.cursor()
    try:
        cursor.execute(
            "INSERT INTO lucas_professor (nome, telefone, usuario, senha, disciplinas) VALUES (%s, %s, %s, %s, %s)",
            (nome, telefone, usuario, senha_hash, disciplinas_str)
        )
        connection.commit()
        professor_id = cursor.lastrowid
        cursor.close()
        connection.close()
        return jsonify({'id': professor_id, 'nome': nome, 'usuario': usuario, 'disciplinas': disciplinas_ids}), 201
    except mysql.connector.Error as e:
        connection.rollback()
        cursor.close()
        connection.close()
        return jsonify({'error': str(e)}), 500

@app.route('/professores/<int:id>', methods=['PUT'])
def editar_professor(id):
    dados = request.json
    nome = dados.get('nome')
    telefone = dados.get('telefone')
    usuario = dados.get('usuario')
    senha = dados.get('senha')
    disciplinas_ids = dados.get('disciplinas')
    
    if not nome or not usuario or not disciplinas_ids:
        return jsonify({'error': 'Nome, usuário e disciplinas são obrigatórios'}), 400
    
    # Se a senha for fornecida, a mesma será atualizada
    senha_hash = generate_password_hash(senha) if senha else None
    disciplinas_str = ','.join(map(str, disciplinas_ids))
    
    connection = create_db_connection()
    if not connection:
        return jsonify({'error': 'Erro ao conectar ao banco de dados'}), 500
    
    cursor = connection.cursor()
    try:
        # Atualizar professor no banco de dados
        if senha_hash:
            cursor.execute(
                "UPDATE lucas_professor SET nome = %s, telefone = %s, usuario = %s, senha = %s, disciplinas = %s WHERE id = %s",
                (nome, telefone, usuario, senha_hash, disciplinas_str, id)
            )
        else:
            cursor.execute(
                "UPDATE lucas_professor SET nome = %s, telefone = %s, usuario = %s, disciplinas = %s WHERE id = %s",
                (nome, telefone, usuario, disciplinas_str, id)
            )
        connection.commit()
        
        if cursor.rowcount == 0:
            return jsonify({'error': 'Professor não encontrado'}), 404
        
        cursor.close()
        connection.close()
        return jsonify({'id': id, 'nome': nome, 'usuario': usuario, 'disciplinas': disciplinas_ids}), 200
    except mysql.connector.Error as e:
        connection.rollback()
        cursor.close()
        connection.close()
        return jsonify({'error': str(e)}), 500

@app.route('/professores/<int:id>', methods=['DELETE'])
def excluir_professor(id):
    connection = create_db_connection()
    if not connection:
        return jsonify({'error': 'Erro ao conectar ao banco de dados'}), 500

    cursor = connection.cursor()
    try:
        cursor.execute("DELETE FROM lucas_professor WHERE id = %s", (id,))
        connection.commit()

        if cursor.rowcount == 0:
            return jsonify({'error': 'Professor não encontrado'}), 404
        
        cursor.close()
        connection.close()
        return jsonify({'message': 'Professor excluído com sucesso'}), 200
    except mysql.connector.Error as e:
        connection.rollback()
        cursor.close()
        connection.close()
        return jsonify({'error': str(e)}), 500

#-----------------------Alunos---------------------------
@app.route('/alunos', methods=['GET'])
def listar_alunos():
    connection = create_db_connection()
    if not connection:
        return jsonify({'error': 'Erro ao conectar ao banco de dados'}), 500
    
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM lucas_aluno")
    alunos = cursor.fetchall()
    cursor.close()
    connection.close()
    return jsonify(alunos)

@app.route('/alunos', methods=['POST'])
def criar_aluno():
    dados = request.json
    nome = dados.get('nome')
    cpf = dados.get('cpf')
    endereco = dados.get('endereco')
    senha = dados.get('senha')
    curso_id = dados.get('curso_id')
    
    if not nome or not cpf or not senha or not curso_id:
        return jsonify({'error': 'Nome, CPF, senha e curso são obrigatórios'}), 400
    
    connection = create_db_connection()
    if not connection:
        return jsonify({'error': 'Erro ao conectar ao banco de dados'}), 500
    
    cursor = connection.cursor()
    try:
        cursor.execute(
            "INSERT INTO lucas_aluno (nome, cpf, endereco, senha, curso_id) VALUES (%s, %s, %s, %s, %s)",
            (nome, cpf, endereco, senha, curso_id)
        )
        connection.commit()
        aluno_id = cursor.lastrowid
        cursor.close()
        connection.close()
        return jsonify({'id': aluno_id, 'nome': nome, 'cpf': cpf, 'curso_id': curso_id}), 201
    except mysql.connector.Error as e:
        connection.rollback()
        cursor.close()
        connection.close()
        return jsonify({'error': str(e)}), 500

@app.route('/alunos/<int:id>', methods=['PUT'])
def editar_aluno(id):
    dados = request.json
    nome = dados.get('nome')
    cpf = dados.get('cpf')
    endereco = dados.get('endereco')
    senha = dados.get('senha')
    curso_id = dados.get('curso_id')
    
    if not nome or not cpf or not senha or not curso_id:
        return jsonify({'error': 'Nome, CPF, senha e curso são obrigatórios'}), 400
    
    connection = create_db_connection()
    if not connection:
        return jsonify({'error': 'Erro ao conectar ao banco de dados'}), 500
    
    cursor = connection.cursor()
    try:
        cursor.execute(
            "UPDATE lucas_aluno SET nome = %s, cpf = %s, endereco = %s, senha = %s, curso_id = %s WHERE id = %s",
            (nome, cpf, endereco, senha, curso_id, id)
        )
        connection.commit()
        
        if cursor.rowcount == 0:
            return jsonify({'error': 'Aluno não encontrado'}), 404
        
        cursor.close()
        connection.close()
        return jsonify({'id': id, 'nome': nome, 'cpf': cpf, 'curso_id': curso_id}), 200
    except mysql.connector.Error as e:
        connection.rollback()
        cursor.close()
        connection.close()
        return jsonify({'error': str(e)}), 500

@app.route('/alunos/<int:id>', methods=['DELETE'])
def excluir_aluno(id):
    connection = create_db_connection()
    if not connection:
        return jsonify({'error': 'Erro ao conectar ao banco de dados'}), 500

    cursor = connection.cursor()
    try:
        cursor.execute("DELETE FROM lucas_aluno WHERE id = %s", (id,))
        connection.commit()

        if cursor.rowcount == 0:
            return jsonify({'error': 'Aluno não encontrado'}), 404
        
        cursor.close()
        connection.close()
        return jsonify({'message': 'Aluno excluído com sucesso'}), 200
    except mysql.connector.Error as e:
        connection.rollback()
        cursor.close()
        connection.close()
        return jsonify({'error': str(e)}), 500

if '__main__' == __name__:
    app.run(debug=True, port=4000)
