from flask import Blueprint, render_template, request, redirect, url_for, flash
from config.database import db_config
from models import Producto
from utils.helpers import get_current_year
import pandas as pd

productos_bp = Blueprint('productos', __name__, url_prefix='/productos')

# Ruta específica para manejar /productos sin barra final (evita redirect 308)
@productos_bp.route('', methods=['GET'], strict_slashes=False)
@productos_bp.route('/')
def lista():
    """Lista de productos"""
    db = db_config.get_session()
    try:
        productos = db.query(Producto).all()
        current_year = get_current_year()
        return render_template('productos_list.html', productos=productos, current_year=current_year)
    finally:
        db.close()

@productos_bp.route('/agregar', methods=['GET', 'POST'])
def agregar():
    """Agregar nuevo producto"""
    db = db_config.get_session()
    try:
        current_year = get_current_year()
        if request.method == 'POST':
            codigo = request.form.get('codigo')
            referencia = request.form.get('referencia_de_producto')
            gramaje = request.form.get('gramaje_g')
            grupo = request.form.get('formulacion_grupo')
            linea = request.form.get('categoria_linea')
            
            if not codigo or not referencia or not gramaje:
                flash('Todos los campos obligatorios deben ser completados.', 'danger')
                return render_template('producto_form.html', current_year=current_year, modo='agregar')
            
            prod = Producto(
                codigo=codigo, 
                referencia_de_producto=referencia, 
                gramaje_g=gramaje, 
                formulacion_grupo=grupo, 
                categoria_linea=linea
            )
            db.add(prod)
            db.commit()
            flash('Producto agregado correctamente.', 'success')
            return redirect(url_for('productos.lista'))
        
        return render_template('producto_form.html', current_year=current_year, modo='agregar')
    finally:
        db.close()

@productos_bp.route('/editar/<int:producto_id>', methods=['GET', 'POST'])
def editar(producto_id):
    """Editar producto existente"""
    db = db_config.get_session()
    try:
        prod = db.query(Producto).get(producto_id)
        current_year = get_current_year()
        
        if not prod:
            flash('Producto no encontrado.', 'danger')
            return redirect(url_for('productos.lista'))
        
        if request.method == 'POST':
            prod.codigo = request.form.get('codigo')
            prod.referencia_de_producto = request.form.get('referencia_de_producto')
            prod.gramaje_g = request.form.get('gramaje_g')
            prod.formulacion_grupo = request.form.get('formulacion_grupo')
            prod.categoria_linea = request.form.get('categoria_linea')
            db.commit()
            flash('Producto actualizado correctamente.', 'success')
            return redirect(url_for('productos.lista'))
        
        return render_template('producto_form.html', producto=prod, current_year=current_year, modo='editar')
    finally:
        db.close()

@productos_bp.route('/eliminar/<int:producto_id>', methods=['POST'])
def eliminar(producto_id):
    """Eliminar producto"""
    db = db_config.get_session()
    try:
        prod = db.query(Producto).get(producto_id)
        if prod:
            db.delete(prod)
            db.commit()
            flash('Producto eliminado.', 'success')
        else:
            flash('Producto no encontrado.', 'danger')
        return redirect(url_for('productos.lista'))
    finally:
        db.close()

@productos_bp.route('/ver/<int:producto_id>')
def ver(producto_id):
    """Ver detalles de un producto"""
    db = db_config.get_session()
    try:
        producto = db.query(Producto).get(producto_id)
        if not producto:
            flash('Producto no encontrado', 'danger')
            return redirect(url_for('productos.lista'))
        return render_template('ver_producto.html', producto=producto)
    finally:
        db.close()

@productos_bp.route('/importar', methods=['GET', 'POST'])
def importar():
    """Importar productos desde Excel"""
    db = db_config.get_session()
    try:
        current_year = get_current_year()
        
        if request.method == 'POST':
            if 'archivo' not in request.files:
                return redirect(request.url)
            
            archivo = request.files['archivo']
            if archivo.filename == '':
                return redirect(request.url)
                
            if archivo:
                try:
                    # Leer el archivo Excel
                    df = pd.read_excel(archivo)
                    
                    # Validar columnas requeridas
                    columnas_requeridas = ['codigo', 'referencia_de_producto', 'gramaje_g', 'formulacion_grupo', 'categoria_linea']
                    for col in columnas_requeridas:
                        if col not in df.columns:
                            raise ValueError(f'Falta la columna requerida: {col}')
                    
                    # Procesar cada fila
                    resultados = {'exito': True, 'mensaje': 'Productos importados correctamente', 'errores': []}
                    for _, fila in df.iterrows():
                        try:
                            producto = Producto(
                                codigo=fila.get('codigo', ''),
                                referencia_de_producto=fila.get('referencia_de_producto', ''),
                                gramaje_g=float(fila.get('gramaje_g', 0)),
                                formulacion_grupo=fila.get('formulacion_grupo', ''),
                                categoria_linea=fila.get('categoria_linea', ''),
                                descripcion=fila.get('descripcion', ''),
                                precio_unitario=float(fila.get('precio_unitario', 0)) if pd.notna(fila.get('precio_unitario')) else 0,
                                unidad_medida=fila.get('unidad_medida', 'unidad'),
                                estado='Activo' if fila.get('estado', '').lower() in ['activo', '1', 'sí', 'si', 'true'] else 'Inactivo'
                            )
                            db.add(producto)
                            db.commit()
                        except Exception as e:
                            db.rollback()
                            resultados['errores'].append(f'Error en fila {_ + 2}: {str(e)}')
                    
                    if resultados['errores']:
                        resultados['exito'] = False
                        resultados['mensaje'] = 'Se produjeron algunos errores durante la importación'
                    
                    return render_template('importar_productos.html', 
                                         resultados=resultados,
                                         current_year=current_year)
                    
                except Exception as e:
                    error_msg = f'Error al procesar el archivo: {str(e)}'
                    return render_template('importar_productos.html', 
                                         resultados={'exito': False, 'mensaje': error_msg, 'errores': [error_msg]},
                                         current_year=current_year)
        
        return render_template('importar_productos.html', current_year=current_year)
    finally:
        db.close()

@productos_bp.route('/importar-productos')
def redirect_importar():
    """Redirige a la página de importación de productos"""
    return redirect(url_for('productos.importar'))