#!/usr/bin/env python3
"""
Script para generar datos de prueba para FlorezCook
Genera clientes, productos y pedidos de prueba realistas
"""

import sys
import os
import random
from datetime import datetime, timedelta
from decimal import Decimal

# Agregar el directorio del proyecto al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models import Cliente, Producto, Pedido, PedidoProducto
from config import database as db_config

# Datos de prueba realistas para el sector alimentario
CLIENTES_DATOS = [
    {
        "nombre_comercial": "Restaurante El Sabor Bogotano",
        "razon_social": "El Sabor Bogotano S.A.S.",
        "tipo_identificacion": "NIT",
        "numero_identificacion": "900123456-1",
        "email": "pedidos@elsaborbogotano.com",
        "telefono": "3101234567",
        "direccion": "Calle 93 #15-45",
        "ciudad": "Bogotá",
        "departamento": "Cundinamarca"
    },
    {
        "nombre_comercial": "Hotel Plaza Real",
        "razon_social": "Plaza Real Hoteles Ltda.",
        "tipo_identificacion": "NIT",
        "numero_identificacion": "800987654-2",
        "email": "compras@plazareal.com",
        "telefono": "3209876543",
        "direccion": "Carrera 13 #85-32",
        "ciudad": "Bogotá",
        "departamento": "Cundinamarca"
    },
    {
        "nombre_comercial": "Café Central",
        "razon_social": "María González",
        "tipo_identificacion": "CC",
        "numero_identificacion": "52456789",
        "email": "maria@cafecentral.com",
        "telefono": "3156789123",
        "direccion": "Avenida 19 #104-28",
        "ciudad": "Bogotá",
        "departamento": "Cundinamarca"
    },
    {
        "nombre_comercial": "Panadería La Esperanza",
        "razon_social": "La Esperanza Pan y Café S.A.S.",
        "tipo_identificacion": "NIT",
        "numero_identificacion": "901234567-3",
        "email": "gerencia@laesperanza.com",
        "telefono": "3187654321",
        "direccion": "Calle 127 #7-83",
        "ciudad": "Bogotá",
        "departamento": "Cundinamarca"
    },
    {
        "nombre_comercial": "Restaurante Medellín Gourmet",
        "razon_social": "Medellín Gourmet S.A.S.",
        "tipo_identificacion": "NIT",
        "numero_identificacion": "890567123-4",
        "email": "pedidos@medellingourmet.com",
        "telefono": "3043456789",
        "direccion": "Carrera 70 #52-40",
        "ciudad": "Medellín",
        "departamento": "Antioquia"
    },
    {
        "nombre_comercial": "Cafetería Universidad Nacional",
        "razon_social": "Juan Carlos Pérez",
        "tipo_identificacion": "CC",
        "numero_identificacion": "80123456",
        "email": "jcarlos@unal.edu.co",
        "telefono": "3112345678",
        "direccion": "Ciudad Universitaria",
        "ciudad": "Bogotá",
        "departamento": "Cundinamarca"
    },
    {
        "nombre_comercial": "Hotel Cali Real",
        "razon_social": "Hoteles del Valle S.A.",
        "tipo_identificacion": "NIT",
        "numero_identificacion": "805432198-5",
        "email": "compras@hotelcalireal.com",
        "telefono": "3023456789",
        "direccion": "Avenida 6N #15-25",
        "ciudad": "Cali",
        "departamento": "Valle del Cauca"
    },
    {
        "nombre_comercial": "Supermercado Mi Barrio",
        "razon_social": "Distribuidora Mi Barrio Ltda.",
        "tipo_identificacion": "NIT",
        "numero_identificacion": "812345678-6",
        "email": "compras@mibarrio.com",
        "telefono": "3145678901",
        "direccion": "Calle 45 Sur #78-12",
        "ciudad": "Bogotá",
        "departamento": "Cundinamarca"
    }
]

PRODUCTOS_DATOS = [
    # Categoría: Panes
    {
        "codigo": "PAN001",
        "referencia_de_producto": "Pan Francés Clásico",
        "gramaje_g": 60,
        "formulacion_grupo": "Panes Tradicionales",
        "categoria_linea": "Panadería",
        "descripcion": "Pan francés tradicional de corteza crujiente y miga suave",
        "presentacion1": "Unidad",
        "presentacion2": "Docena",
        "precio_unitario": Decimal("1500.00"),
        "unidad_medida": "unidad"
    },
    {
        "codigo": "PAN002",
        "referencia_de_producto": "Pan Integral Artesanal",
        "gramaje_g": 80,
        "formulacion_grupo": "Panes Integrales",
        "categoria_linea": "Panadería",
        "descripcion": "Pan integral con semillas de girasol y chía",
        "presentacion1": "Unidad",
        "presentacion2": "Media docena",
        "precio_unitario": Decimal("2200.00"),
        "unidad_medida": "unidad"
    },
    {
        "codigo": "PAN003",
        "referencia_de_producto": "Croissant Mantequilla",
        "gramaje_g": 45,
        "formulacion_grupo": "Hojaldres",
        "categoria_linea": "Panadería",
        "descripcion": "Croissant de mantequilla hojaldre francés",
        "presentacion1": "Unidad",
        "presentacion2": "Caja x6",
        "precio_unitario": Decimal("2800.00"),
        "unidad_medida": "unidad"
    },
    
    # Categoría: Tortas
    {
        "codigo": "TORTA001",
        "referencia_de_producto": "Torta Chocolate Premium",
        "gramaje_g": 1200,
        "formulacion_grupo": "Tortas Gourmet",
        "categoria_linea": "Repostería",
        "descripcion": "Torta de chocolate con ganache y decoración premium",
        "presentacion1": "Entera",
        "presentacion2": "Por porciones",
        "precio_unitario": Decimal("45000.00"),
        "unidad_medida": "unidad"
    },
    {
        "codigo": "TORTA002",
        "referencia_de_producto": "Torta Tres Leches",
        "gramaje_g": 1000,
        "formulacion_grupo": "Tortas Húmedas",
        "categoria_linea": "Repostería",
        "descripcion": "Torta tres leches con merengue suizo",
        "presentacion1": "Entera",
        "presentacion2": "Individual",
        "precio_unitario": Decimal("38000.00"),
        "unidad_medida": "unidad"
    },
    {
        "codigo": "TORTA003",
        "referencia_de_producto": "Cheesecake Frutos Rojos",
        "gramaje_g": 800,
        "formulacion_grupo": "Cheesecakes",
        "categoria_linea": "Repostería",
        "descripcion": "Cheesecake de queso crema con salsa de frutos rojos",
        "presentacion1": "Entera",
        "presentacion2": "Porción",
        "precio_unitario": Decimal("42000.00"),
        "unidad_medida": "unidad"
    },
    
    # Categoría: Galletas
    {
        "codigo": "GAL001",
        "referencia_de_producto": "Galletas Chocolate Chip",
        "gramaje_g": 25,
        "formulacion_grupo": "Galletas Dulces",
        "categoria_linea": "Galletería",
        "descripcion": "Galletas con chips de chocolate belga",
        "presentacion1": "Unidad",
        "presentacion2": "Paquete x12",
        "precio_unitario": Decimal("800.00"),
        "unidad_medida": "unidad"
    },
    {
        "codigo": "GAL002",
        "referencia_de_producto": "Galletas Avena y Pasas",
        "gramaje_g": 30,
        "formulacion_grupo": "Galletas Saludables",
        "categoria_linea": "Galletería",
        "descripcion": "Galletas de avena con pasas sin conservantes",
        "presentacion1": "Unidad",
        "presentacion2": "Bolsa x20",
        "precio_unitario": Decimal("900.00"),
        "unidad_medida": "unidad"
    },
    {
        "codigo": "GAL003",
        "referencia_de_producto": "Galletas Saladas Romero",
        "gramaje_g": 20,
        "formulacion_grupo": "Galletas Saladas",
        "categoria_linea": "Galletería",
        "descripcion": "Galletas saladas con romero y aceite de oliva",
        "presentacion1": "Unidad",
        "presentacion2": "Paquete x15",
        "precio_unitario": Decimal("700.00"),
        "unidad_medida": "unidad"
    },
    
    # Categoría: Pasteles Individuales
    {
        "codigo": "PAST001",
        "referencia_de_producto": "Cupcake Red Velvet",
        "gramaje_g": 80,
        "formulacion_grupo": "Cupcakes Gourmet",
        "categoria_linea": "Repostería Individual",
        "descripcion": "Cupcake red velvet con frosting cream cheese",
        "presentacion1": "Unidad",
        "presentacion2": "Caja x6",
        "precio_unitario": Decimal("4500.00"),
        "unidad_medida": "unidad"
    },
    {
        "codigo": "PAST002",
        "referencia_de_producto": "Muffin Arándanos",
        "gramaje_g": 70,
        "formulacion_grupo": "Muffins",
        "categoria_linea": "Repostería Individual",
        "descripcion": "Muffin con arándanos frescos y streusel",
        "presentacion1": "Unidad",
        "presentacion2": "Caja x4",
        "precio_unitario": Decimal("3800.00"),
        "unidad_medida": "unidad"
    },
    {
        "codigo": "PAST003",
        "referencia_de_producto": "Éclair Vainilla",
        "gramaje_g": 65,
        "formulacion_grupo": "Choux",
        "categoria_linea": "Repostería Individual",
        "descripcion": "Éclair relleno de crema pastelera de vainilla",
        "presentacion1": "Unidad",
        "presentacion2": "Caja x3",
        "precio_unitario": Decimal("4200.00"),
        "unidad_medida": "unidad"
    }
]

def generar_clientes(db, cantidad=None):
    """Generar clientes de prueba"""
    clientes_creados = []
    clientes_a_crear = CLIENTES_DATOS[:cantidad] if cantidad else CLIENTES_DATOS
    
    for cliente_data in clientes_a_crear:
        # Verificar si el cliente ya existe
        cliente_existente = db.query(Cliente).filter_by(
            numero_identificacion=cliente_data["numero_identificacion"]
        ).first()
        
        if not cliente_existente:
            cliente = Cliente(**cliente_data)
            db.add(cliente)
            clientes_creados.append(cliente)
            print(f"✓ Cliente creado: {cliente_data['nombre_comercial']}")
        else:
            print(f"⚠ Cliente ya existe: {cliente_data['nombre_comercial']}")
    
    return clientes_creados

def generar_productos(db, cantidad=None):
    """Generar productos de prueba"""
    productos_creados = []
    productos_a_crear = PRODUCTOS_DATOS[:cantidad] if cantidad else PRODUCTOS_DATOS
    
    for producto_data in productos_a_crear:
        # Verificar si el producto ya existe
        producto_existente = db.query(Producto).filter_by(
            codigo=producto_data["codigo"]
        ).first()
        
        if not producto_existente:
            producto = Producto(**producto_data)
            db.add(producto)
            productos_creados.append(producto)
            print(f"✓ Producto creado: {producto_data['referencia_de_producto']}")
        else:
            print(f"⚠ Producto ya existe: {producto_data['referencia_de_producto']}")
    
    return productos_creados

def generar_pedidos(db, clientes, productos, cantidad_pedidos=20):
    """Generar pedidos de prueba con productos aleatorios"""
    pedidos_creados = []
    estados_posibles = ["En Proceso", "Completado", "Pendiente", "Cancelado"]
    tipos_despacho = ["Domicilio", "Punto de venta", "Recogida en tienda"]
    sedes = ["Sede Principal", "Sede Norte", "Sede Sur", "Sede Centro"]
    
    for i in range(cantidad_pedidos):
        # Seleccionar cliente aleatorio
        cliente = random.choice(clientes)
        
        # Crear fechas aleatorias en los últimos 30 días
        fecha_base = datetime.now() - timedelta(days=random.randint(0, 30))
        fecha_entrega = fecha_base + timedelta(days=random.randint(1, 7))
        
        # Crear pedido
        pedido = Pedido(
            fecha_creacion=fecha_base,
            numero_identificacion_cliente_ingresado=cliente.numero_identificacion,
            nombre_cliente_ingresado=cliente.nombre_comercial,
            cliente_id=cliente.id,
            despacho_tipo=random.choice(tipos_despacho),
            despacho_sede=random.choice(sedes),
            direccion_entrega=cliente.direccion,
            ciudad_entrega=cliente.ciudad,
            departamento_entrega=cliente.departamento,
            despacho_horario_atencion="8:00 AM - 6:00 PM",
            observaciones_despacho=f"Pedido #{i+1} - Entrega preferencial en horario de mañana",
            estado_pedido_general=random.choice(estados_posibles)
        )
        
        db.add(pedido)
        db.flush()  # Para obtener el ID del pedido
        
        # Generar entre 1 y 5 productos por pedido
        num_productos = random.randint(1, 5)
        productos_pedido = random.sample(productos, min(num_productos, len(productos)))
        
        for producto in productos_pedido:
            cantidad = random.randint(1, 10)
            peso_total = producto.gramaje_g * cantidad
            
            # Determinar presentación
            presentaciones = ["Unidad", "Docena", "Media docena", "Caja x6", "Paquete x12"]
            presentacion = random.choice([producto.presentacion1, producto.presentacion2] + presentaciones)
            
            pedido_producto = PedidoProducto(
                pedido_id=pedido.id,
                producto_id=producto.id,
                fecha_pedido_item=fecha_base.date(),
                cantidad=cantidad,
                gramaje_g_item=producto.gramaje_g,
                peso_total_g_item=peso_total,
                grupo_item=producto.formulacion_grupo,
                linea_item=producto.categoria_linea,
                comentarios_item=presentacion,
                fecha_de_entrega_item=fecha_entrega.date(),
                estado_del_pedido_item=random.choice(["Pendiente", "En preparación", "Listo", "Entregado"])
            )
            
            db.add(pedido_producto)
        
        pedidos_creados.append(pedido)
        print(f"✓ Pedido #{i+1} creado para {cliente.nombre_comercial} con {len(productos_pedido)} productos")
    
    return pedidos_creados

def main():
    """Función principal para generar todos los datos de prueba"""
    print("🎯 Iniciando generación de datos de prueba para FlorezCook")
    print("=" * 60)
    
    # Conectar a la base de datos
    db_instance = db_config.DatabaseConfig()
    db = db_instance.get_session()
    
    try:
        # 1. Generar clientes
        print("\n📋 Generando clientes...")
        clientes = generar_clientes(db)
        
        # 2. Generar productos
        print("\n📦 Generando productos...")
        productos = generar_productos(db)
        
        # Confirmar cambios hasta ahora
        db.commit()
        print("\n💾 Clientes y productos guardados exitosamente")
        
        # 3. Obtener todos los clientes y productos para los pedidos
        todos_clientes = db.query(Cliente).all()
        todos_productos = db.query(Producto).all()
        
        if len(todos_clientes) == 0 or len(todos_productos) == 0:
            print("❌ Error: No hay clientes o productos disponibles para generar pedidos")
            return
        
        # 4. Generar pedidos
        print(f"\n📋 Generando pedidos con {len(todos_clientes)} clientes y {len(todos_productos)} productos...")
        pedidos = generar_pedidos(db, todos_clientes, todos_productos, 25)
        
        # Confirmar todos los cambios
        db.commit()
        
        print("\n" + "=" * 60)
        print("✅ GENERACIÓN COMPLETADA EXITOSAMENTE")
        print(f"📊 Resumen:")
        print(f"   • Clientes nuevos: {len(clientes)}")
        print(f"   • Productos nuevos: {len(productos)}")
        print(f"   • Pedidos nuevos: {len(pedidos)}")
        print(f"   • Total clientes en BD: {len(todos_clientes)}")
        print(f"   • Total productos en BD: {len(todos_productos)}")
        
    except Exception as e:
        print(f"❌ Error durante la generación: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    main()