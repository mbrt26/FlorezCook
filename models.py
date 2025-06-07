import os
import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, Date, Text, ForeignKey, DateTime, Numeric
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from flask_login import UserMixin

Base = declarative_base()

class Cliente(Base):
    __tablename__ = "clientes"

    id = Column(Integer, primary_key=True, index=True)
    nombre_comercial = Column(String(255), nullable=False)
    razon_social = Column(String(255))
    tipo_identificacion = Column(String(50))  # NIT, CC, etc.
    numero_identificacion = Column(String(50), index=True, unique=True)
    email = Column(String(255))
    telefono = Column(String(50))
    direccion = Column(String(255))
    ciudad = Column(String(100))
    departamento = Column(String(100))
    fecha_creacion = Column(DateTime, default=datetime.datetime.utcnow)
    fecha_modificacion = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Relación con Pedido
    pedidos = relationship("Pedido", back_populates="cliente_asociado")

    def __repr__(self):
        return f"<Cliente(id={self.id}, nombre='{self.nombre_comercial}', nit='{self.numero_identificacion}')>"

class Producto(Base):
    __tablename__ = "productos"

    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String(100), unique=True, nullable=False)
    referencia_de_producto = Column(String(255), nullable=False)
    gramaje_g = Column(Float, nullable=False)
    formulacion_grupo = Column(String(100))
    categoria_linea = Column(String(100))
    descripcion = Column(Text)
    precio_unitario = Column(Numeric(10, 2), default=0)  # Cambio de Float a Numeric para coincidir con DECIMAL(10,2)
    unidad_medida = Column(String(20), default='unidad')  # Ajustado a VARCHAR(20)
    estado = Column(String(20), default='activo')  # Ajustado a VARCHAR(20) y valor por defecto
    fecha_creacion = Column(DateTime, default=datetime.datetime.utcnow)
    fecha_modificacion = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Relación con PedidoProducto
    pedidos = relationship("PedidoProducto", back_populates="producto_asociado")

    def __repr__(self):
        return f"<Producto(id={self.id}, codigo='{self.codigo}', referencia='{self.referencia_de_producto}')>"

class Pedido(Base):
    __tablename__ = "pedidos"

    id = Column(Integer, primary_key=True, index=True)
    fecha_creacion = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Información del cliente
    numero_identificacion_cliente_ingresado = Column(String(50), index=True)
    nombre_cliente_ingresado = Column(String(255), nullable=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=True)
    cliente_asociado = relationship("Cliente", back_populates="pedidos")
    
    # Campos de despacho
    despacho_tipo = Column(String(50))
    despacho_sede = Column(String(255))
    direccion_entrega = Column(String(255))
    ciudad_entrega = Column(String(100))
    departamento_entrega = Column(String(100))
    despacho_horario_atencion = Column(String(100))
    observaciones_despacho = Column(Text)
    
    # Campos de estado y control
    alerta = Column(String(255))
    estado_pedido_general = Column(String(50), default="En Proceso")

    # Relación con PedidoProducto
    items = relationship("PedidoProducto", back_populates="pedido_asociado", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Pedido(id={self.id}, cliente_id={self.cliente_id}, estado='{self.estado_pedido_general}')>"

class PedidoProducto(Base):
    __tablename__ = "pedido_productos"

    id = Column(Integer, primary_key=True, index=True)
    pedido_id = Column(Integer, ForeignKey("pedidos.id", ondelete="CASCADE"))
    producto_id = Column(Integer, ForeignKey("productos.id"))
    fecha_pedido_item = Column(Date, nullable=False)  # AGREGADO: Columna faltante que existe en BD
    cantidad = Column(Float, nullable=False)
    gramaje_g_item = Column(Float)
    peso_total_g_item = Column(Float)
    grupo_item = Column(String(100))
    linea_item = Column(String(100))
    observaciones_item = Column(Text)
    fecha_de_entrega_item = Column(Date)
    estado_del_pedido_item = Column(String(50), default="Pendiente")
    fecha_creacion = Column(DateTime, default=datetime.datetime.utcnow)
    fecha_modificacion = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)  # AGREGADO: También faltaba

    # Relaciones
    pedido_asociado = relationship("Pedido", back_populates="items")
    producto_asociado = relationship("Producto", back_populates="pedidos")

    def __repr__(self):
        return f"<PedidoProducto(id={self.id}, pedido_id={self.pedido_id}, producto_id={self.producto_id})>"

class User(UserMixin):
    def __init__(self, id, role='user'):
        self.id = id
        self.role = role

    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)
