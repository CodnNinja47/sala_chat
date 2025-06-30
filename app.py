from flask import Flask, request
from flask_cors import CORS
from flask_socketio import SocketIO, join_room, leave_room, emit
import random
import string
import eventlet
eventlet.monkey_patch()  # Muy importante para compatibilidad con WebSockets en Railway

app = Flask(__name__)
CORS(app)  # Habilita CORS para todo
socketio = SocketIO(app, cors_allowed_origins="http://192.168.10.13:443/")  # CORS para Socket.IO

# Diccionario en memoria para controlar las salas y sus usuarios
salas = {}

def generar_codigo_sala(longitud=4):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=longitud))

@app.route("/")
def home():
    return "API de Salas Virtuales Activa"

@socketio.on('crear_sala')
def crear_sala():
    codigo = generar_codigo_sala()
    salas[codigo] = {
        'usuarios': [],
        'mensajes': []
    }
    emit('sala_creada', {'codigo': codigo})

@socketio.on('unirse')
def unirse(data):
    codigo = data['codigo']
    nombre = data['nombre']

    if codigo not in salas:
        emit('error', {'mensaje': 'La sala no existe'})
        return

    if len(salas[codigo]['usuarios']) >= 4:
        emit('error', {'mensaje': 'La sala está llena'})
        return

    join_room(codigo)
    salas[codigo]['usuarios'].append(nombre)
    emit('unido', {'mensaje': f'{nombre} se unió a la sala {codigo}'}, room=codigo)

@socketio.on('mensaje')
def mensaje(data):
    codigo = data['codigo']
    texto = data['texto']
    nombre = data['nombre']

    if codigo in salas:
        salas[codigo]['mensajes'].append((nombre, texto))
        emit('nuevo_mensaje', {'nombre': nombre, 'texto': texto}, room=codigo)

@socketio.on('salir')
def salir(data):
    codigo = data['codigo']
    nombre = data['nombre']

    if codigo in salas and nombre in salas[codigo]['usuarios']:
        salas[codigo]['usuarios'].remove(nombre)
        leave_room(codigo)
        emit('usuario_salio', {'mensaje': f'{nombre} salió de la sala'}, room=codigo)

        # Si la sala queda vacía, se elimina
        if not salas[codigo]['usuarios']:
            del salas[codigo]

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000)
