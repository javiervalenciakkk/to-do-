from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)

database_url = os.environ.get('DATABASE_URL', 'sqlite:///tareas.db')
if database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Tarea(db.Model):
    __tablename__ = 'tareas'
    
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False)
    descripcion = db.Column(db.Text, default='')
    completada = db.Column(db.Boolean, default=False)
    prioridad = db.Column(db.String(20), default='basico')
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_vencimiento = db.Column(db.DateTime, nullable=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'titulo': self.titulo,
            'descripcion': self.descripcion,
            'completada': self.completada,
            'prioridad': self.prioridad,
            'fecha_creacion': self.fecha_creacion.isoformat(),
            'fecha_vencimiento': self.fecha_vencimiento.isoformat() if self.fecha_vencimiento else None
        }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/tareas', methods=['GET'])
def obtener_tareas():
    try:
        tareas = Tarea.query.order_by(Tarea.fecha_creacion.desc()).all()
        return jsonify([tarea.to_dict() for tarea in tareas]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tareas', methods=['POST'])
def crear_tarea():
    try:
        datos = request.get_json()
        
        if not datos or not datos.get('titulo'):
            return jsonify({'error': 'Título requerido'}), 400
        
        nueva_tarea = Tarea(
            titulo=datos['titulo'],
            descripcion=datos.get('descripcion', ''),
            prioridad=datos.get('prioridad', 'basico')
        )
        
        db.session.add(nueva_tarea)
        db.session.commit()
        
        return jsonify({
            'mensaje': 'Tarea creada',
            'tarea': nueva_tarea.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/tareas/<int:id>', methods=['GET'])
def obtener_tarea(id):
    try:
        tarea = Tarea.query.get_or_404(id)
        return jsonify(tarea.to_dict()), 200
    except:
        return jsonify({'error': 'Tarea no encontrada'}), 404

@app.route('/api/tareas/<int:id>', methods=['PUT'])
def actualizar_tarea(id):
    try:
        tarea = Tarea.query.get_or_404(id)
        datos = request.get_json()
        
        if 'titulo' in datos:
            tarea.titulo = datos['titulo']
        if 'descripcion' in datos:
            tarea.descripcion = datos['descripcion']
        if 'completada' in datos:
            tarea.completada = datos['completada']
        if 'prioridad' in datos:
            tarea.prioridad = datos['prioridad']
        
        db.session.commit()
        
        return jsonify({
            'mensaje': 'Tarea actualizada',
            'tarea': tarea.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/tareas/<int:id>', methods=['DELETE'])
def eliminar_tarea(id):
    try:
        tarea = Tarea.query.get_or_404(id)
        db.session.delete(tarea)
        db.session.commit()
        return jsonify({'mensaje': 'Tarea eliminada'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/estadisticas', methods=['GET'])
def estadisticas():
    try:
        total = Tarea.query.count()
        completadas = Tarea.query.filter_by(completada=True).count()
        pendientes = total - completadas
        
        return jsonify({
            'total': total,
            'completadas': completadas,
            'pendientes': pendientes,
            'porcentaje': (completadas / total * 100) if total > 0 else 0
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Recurso no encontrado'}), 404

@app.errorhandler(500)
def server_error(error):
    return jsonify({'error': 'Error interno del servidor'}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
