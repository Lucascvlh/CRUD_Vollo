from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from dotenv import load_dotenv
from mysql.connector import Error
from functools import wraps
import mysql.connector
import datetime
import jwt
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

def gerar_token(usuario_id):
    payload = {
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1),  # Expira em 1 hora
        'iat': datetime.datetime.utcnow(),
        'sub': str(usuario_id)
    }
    return jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].split(" ")[1]  # Pega o token após "Bearer "
        if not token:
            return jsonify({'message': 'Token é necessário!'}), 401

        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            current_user = data['sub']
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token expirou!'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Token inválido!'}), 401

        return f(*args, **kwargs)
    return decorated

@app.route('/')
def login_page():
    return render_template('login.html')

@app.route('/cadastro')
def cadastro_page():
    return render_template('cadastro.html')

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'message':'Credenciais inválidas!'}),401

    connection = create_db_connection()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM lucas_tbuser WHERE username = %s AND password = %s", (username, password))
            user = cursor.fetchone()
            if user:
                token = gerar_token(user['id'])
                return jsonify({'token': token}), 200
            else:
                return jsonify({'message': 'Nome de usuário ou senha inválidos'}), 401
        except Error as e:
            print(f"Erro ao executar a consulta: {e}")
            
            return jsonify({'message': 'Erro ao tentar realizar o login'}), 500
        finally:
            cursor.close()
            connection.close()
    else:
        return jsonify({'message': 'Erro de conexão'}), 500

@app.route('/usuarios', methods=['POST'])
@token_required
def create_user():
    data = request.json
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not username or not email or not password:
        return jsonify({'error': 'nome, email e senha são obrigatórios'}), 400

    try:
        connection = create_db_connection()
        cursor = connection.cursor()
        cursor.execute("INSERT INTO lucas_tbuser (username, email, password) VALUES (%s, %s, %s)", (username, email, password))
        connection.commit()
        return jsonify({'message': 'Usuário criado com sucesso'}), 201
    except Error as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

@app.route('/usuarios/<int:id>', methods=['PUT'])
@token_required
def update_user(id):
    data = request.json
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    try:
        connection = create_db_connection()
        cursor = connection.cursor(dictionary=True)

        # Verificar se o usuário existe e obter os valores atuais
        cursor.execute("SELECT * FROM lucas_tbuser WHERE id = %s", (id,))
        user = cursor.fetchone()
        if not user:
            return jsonify({'message': 'Usuário não encontrado'}), 404

        # Se não foram fornecidos novos valores, usar os valores atuais
        if not username:
            username = user['username']
        if not email:
            email = user['email']
        if not password:
            password = user['password']

        # Atualizar os valores no banco de dados
        update_query = "UPDATE lucas_tbuser SET username = %s, email = %s, password = %s WHERE id = %s"
        cursor.execute(update_query, (username, email, password, id))
        connection.commit()

        return jsonify({'message': 'Usuário atualizado com sucesso'}), 200
    except Error as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

@app.route('/usuarios/<int:id>', methods=['DELETE'])
@token_required
def delete_user(id):
    try:
        connection = create_db_connection()
        cursor = connection.cursor()
        cursor.execute("DELETE FROM lucas_tbuser WHERE id = %s", (id,))
        connection.commit()

        if cursor.rowcount == 0:
            return jsonify({'message': 'Usuário não encontrado'}), 404

        return jsonify({'message': 'Usuário deletado com sucesso'}), 200
    except Error as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

@app.route('/usuarios', methods=['GET'])
@token_required
def get_users():
    try:
        connection = create_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM lucas_tbuser")
        usuarios = cursor.fetchall()
        return jsonify(usuarios), 200
    except Error as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

@app.route('/usuario/<int:id>', methods=['GET'])
@token_required
def get_user(id):
    try:
        connection = create_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM lucas_tbuser WHERE id = %s", (id,))
        usuario = cursor.fetchone()
        return jsonify(usuario), 200
    except Error as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

if __name__ == '__main__':
    app.run(debug=True)
