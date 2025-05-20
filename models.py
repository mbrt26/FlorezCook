import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, Date, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

DATABASE_URL = "sqlite:///florez_cook.db" # El archivo de la base de datos se creará en la misma carpeta

Base = declarative_base()

class Cliente(Base):
    __tablename__ = "clientes"

    id = Column(Integer, primary_key=True, index=True)
    nombre_comercial = Column(String, nullable=False)
    razon_social = Column(String, nullable=False)
    tipo_identificacion = Column(String, nullable=False) # "NIT", "Cedula Ciudadania", "Cedula Extranjería"
    numero_identificacion = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, nullable=False)
    telefono = Column(String, nullable=False)
    direccion = Column(String, nullable=False)
    ciudad = Column(String, nullable=False)
    departamento = Column(String, nullable=False)

    # Campos de Dirección desglosados de Zoho
    direccion_linea1 = Column(String)
    direccion_linea2 = Column(String, nullable=True)
    direccion_codigo_postal = Column(String, nullable=True)
    direccion_pais = Column(String) # En Zoho es un campo, aquí lo mantenemos
    direccion_latitud = Column(Float, nullable=True)
    direccion_longitud = Column(Float, nullable=True)

    # Relación con Pedidos: Un cliente puede tener muchos pedidos
    pedidos = relationship("Pedido", back_populates="cliente_asociado")

    def __repr__(self):
        return f"<Cliente(id={self.id}, nombre_comercial='{self.nombre_comercial}', numero_identificacion='{self.numero_identificacion}')>"

    def to_dict(self):
        return {
            'id': self.id,
            'nombre_comercial': self.nombre_comercial,
            'razon_social': self.razon_social,
            'tipo_identificacion': self.tipo_identificacion,
            'numero_identificacion': self.numero_identificacion,
            'email': self.email,
            'telefono': self.telefono,
            'direccion': self.direccion,
            'ciudad': self.ciudad,
            'departamento': self.departamento
        }

class Producto(Base):
    __tablename__ = "productos"

    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String, unique=True, nullable=False)
    referencia_de_producto = Column(String, nullable=False)
    gramaje_g = Column(Float, nullable=False)
    formulacion_grupo = Column(String) # Picklist de Zoho: "BAGEL TRADICIONAL", "BAGEL INTEGRAL", etc.
    categoria_linea = Column(String) # Picklist de Zoho: "Laminados", "Maquila", etc.

    # Relación con PedidoProducto: Un producto puede estar en muchos items de pedido
    items_pedido = relationship("PedidoProducto", back_populates="producto_asociado")

    def __repr__(self):
        return f"<Producto(id={self.id}, codigo='{self.codigo}', referencia='{self.referencia_de_producto}')>"

class Pedido(Base):
    __tablename__ = "pedidos"

    id = Column(Integer, primary_key=True, index=True)
    fecha_creacion = Column(DateTime, default=datetime.datetime.utcnow) # Similar a Added_Time de Zoho
    
    # Información del cliente tal como se ingresó/buscó en el formulario de pedido de Zoho
    # Esto es importante para replicar la lógica de "Paso 2. Lógica Principal"
    numero_identificacion_cliente_ingresado = Column(String, index=True) 
    nombre_cliente_ingresado = Column(String, nullable=True) # Puede ser "Su Empresa" inicialmente o el nombre del cliente nuevo

    # FK al cliente registrado (si existe o se crea durante el proceso del pedido)
    # Es nullable=True porque un pedido podría iniciar sin un cliente formalmente en la tabla Clientes
    # hasta que se complete la sección de registro.
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=True) 
    cliente_asociado = relationship("Cliente", back_populates="pedidos")

    alerta = Column(Text, nullable=True) # Campo Alerta del formulario Pedidos de Zoho

    # Sección de Despacho del formulario Pedidos de Zoho
    despacho_tipo = Column(String) # Picklist: "DOMICILIO", "RECOGER EN PLANTA", "FLOTA"
    despacho_sede = Column(String, nullable=True)
    # Dirección de Entrega (puede ser diferente a la del cliente)
    direccion_entrega = Column(String, nullable=True)
    ciudad_entrega = Column(String, nullable=True)
    departamento_entrega = Column(String, nullable=True)
    despacho_horario_atencion = Column(String, nullable=True)
    observaciones_despacho = Column(Text, nullable=True) # Campo Observaciones de la sección Despacho
    
    ESTADOS_PEDIDO = ["En Proceso", "Programado", "Anulado", "Entregado", "Facturado"]
    estado_pedido_general = Column(String, default="En Proceso") # Picklist: "En Proceso", "Programado", "Anulado", "Entregado", "Facturado"

    # Relación con PedidoProducto (los items del pedido)
    # cascade="all, delete-orphan" significa que si se borra un Pedido, se borran sus items asociados
    items = relationship("PedidoProducto", back_populates="pedido_asociado", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Pedido(id={self.id}, cliente_id={self.cliente_id}, estado='{self.estado_pedido_general}')>"

class PedidoProducto(Base): # Representa los items del subformulario "Pedido" en Zoho
    __tablename__ = "pedido_productos" # La tabla que une Pedidos y Productos con detalles adicionales

    id = Column(Integer, primary_key=True, index=True)
    pedido_id = Column(Integer, ForeignKey("pedidos.id"), nullable=False)
    producto_id = Column(Integer, ForeignKey("productos.id"), nullable=False)

    # Campos que se copian o calculan al momento de agregar el producto al pedido,
    # basados en la lógica de "InfoProductos" y la estructura del subformulario en Zoho.
    fecha_pedido_item = Column(Date, nullable=False, default=datetime.date.today) # "Fecha Pedido" del subformulario
    cantidad = Column(Float, nullable=False, default=0)
    gramaje_g_item = Column(Float) # Se copiará de Productos.Gramaje_g
    peso_total_g_item = Column(Float) # Se calculará: Cantidad * Gramaje_g_item
    grupo_item = Column(String) # Se copiará de Productos.Formulacion (Grupo)
    linea_item = Column(String) # Se copiará de Productos.Categoria (Linea)
    
    observaciones_item = Column(Text, nullable=True) # "Observaciones" del subformulario
    fecha_de_entrega_item = Column(Date, nullable=False) # "Fecha de Entrega" del subformulario
    estado_del_pedido_item = Column(String) # "Estado del Pedido" del subformulario, puede heredar del pedido principal o ser específico

    # Relaciones
    pedido_asociado = relationship("Pedido", back_populates="items")
    producto_asociado = relationship("Producto", back_populates="items_pedido")

    def __repr__(self):
        return f"<PedidoProducto(id={self.id}, pedido_id={self.pedido_id}, producto_id={self.producto_id}, cantidad={self.cantidad})>"

# --- Función para crear la base de datos y las tablas ---
def crear_base_de_datos():
    engine = create_engine(DATABASE_URL)
    Base.metadata.create_all(bind=engine) # Crea las tablas si no existen
    print(f"Base de datos '{DATABASE_URL}' y tablas creadas si no existían.")

if __name__ == "__main__":
    crear_base_de_datos()
    
    # Ejemplo de cómo podrías iniciar una sesión para interactuar con la BD (esto iría en tu lógica de app)
    # engine = create_engine(DATABASE_URL)
    # SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    # db = SessionLocal()
    # print("Sesión de base de datos lista para usar (ejemplo).")
    # # Aquí podrías añadir objetos, consultarlos, etc.
    # db.close()
