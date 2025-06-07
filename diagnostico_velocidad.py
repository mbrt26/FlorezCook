#!/usr/bin/env python3
"""
Script de Diagnóstico de Velocidad para FlorezCook
Analiza el rendimiento de la aplicación tanto local como en producción
"""

import time
import requests
import psutil
import os
import sys
from datetime import datetime
import json
import sqlite3
from config.database import db_config
from models import Cliente, Pedido, Producto
import concurrent.futures
from urllib.parse import urljoin

class DiagnosticoVelocidad:
    def __init__(self):
        self.resultados = {
            'timestamp': datetime.now().isoformat(),
            'tests_locales': {},
            'tests_remotos': {},
            'base_datos': {},
            'sistema': {},
            'recomendaciones': []
        }
        
        # URLs para pruebas - CORREGIDAS PARA FLOREZCOOK
        self.url_produccion = "https://florezcook-dot-appsindunnova.rj.r.appspot.com"
        self.url_local = "http://localhost:8080"
        
    def info_sistema(self):
        """Obtiene información del sistema local"""
        print("🖥️  DIAGNÓSTICO DEL SISTEMA LOCAL")
        print("=" * 50)
        
        try:
            # CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            # Memoria
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_available_gb = memory.available / (1024**3)
            
            # Disco
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            disk_free_gb = disk.free / (1024**3)
            
            self.resultados['sistema'] = {
                'cpu_percent': cpu_percent,
                'cpu_count': cpu_count,
                'memory_percent': memory_percent,
                'memory_available_gb': round(memory_available_gb, 2),
                'disk_percent': disk_percent,
                'disk_free_gb': round(disk_free_gb, 2)
            }
            
            print(f"🔧 CPU: {cpu_percent}% ({cpu_count} cores)")
            print(f"💾 RAM: {memory_percent}% usado ({memory_available_gb:.1f}GB disponible)")
            print(f"💿 Disco: {disk_percent}% usado ({disk_free_gb:.1f}GB libre)")
            
            # Alertas del sistema
            if cpu_percent > 80:
                self.resultados['recomendaciones'].append("⚠️ CPU alta - considera cerrar programas innecesarios")
            if memory_percent > 85:
                self.resultados['recomendaciones'].append("⚠️ Memoria alta - considera reiniciar la aplicación")
            if disk_percent > 90:
                self.resultados['recomendaciones'].append("⚠️ Disco lleno - limpia archivos innecesarios")
                
        except Exception as e:
            print(f"❌ Error obteniendo info del sistema: {e}")
            
    def test_base_datos(self):
        """Prueba la velocidad de la base de datos"""
        print("\n🗄️  DIAGNÓSTICO DE BASE DE DATOS")
        print("=" * 50)
        
        try:
            db = db_config.get_session()
            
            # Test 1: Conexión básica
            start_time = time.time()
            result = db.execute("SELECT 1").fetchone()
            conexion_time = (time.time() - start_time) * 1000
            
            # Test 2: Consulta de clientes
            start_time = time.time()
            clientes_count = db.query(Cliente).count()
            clientes_time = (time.time() - start_time) * 1000
            
            # Test 3: Consulta de pedidos
            start_time = time.time()
            pedidos_count = db.query(Pedido).count()
            pedidos_time = (time.time() - start_time) * 1000
            
            # Test 4: Consulta de productos
            start_time = time.time()
            productos_count = db.query(Producto).count()
            productos_time = (time.time() - start_time) * 1000
            
            # Test 5: Consulta compleja (JOIN)
            start_time = time.time()
            query = db.query(Pedido).join(Cliente).limit(10).all()
            join_time = (time.time() - start_time) * 1000
            
            self.resultados['base_datos'] = {
                'conexion_ms': round(conexion_time, 2),
                'clientes_count': clientes_count,
                'clientes_time_ms': round(clientes_time, 2),
                'pedidos_count': pedidos_count,
                'pedidos_time_ms': round(pedidos_time, 2),
                'productos_count': productos_count,
                'productos_time_ms': round(productos_time, 2),
                'join_time_ms': round(join_time, 2)
            }
            
            print(f"🔌 Conexión: {conexion_time:.1f}ms")
            print(f"👥 Clientes ({clientes_count}): {clientes_time:.1f}ms")
            print(f"📋 Pedidos ({pedidos_count}): {pedidos_time:.1f}ms")
            print(f"📦 Productos ({productos_count}): {productos_time:.1f}ms")
            print(f"🔗 JOIN complejo: {join_time:.1f}ms")
            
            # Alertas de base de datos
            if conexion_time > 500:
                self.resultados['recomendaciones'].append("⚠️ Conexión DB lenta - verifica Cloud SQL")
            if clientes_time > 1000:
                self.resultados['recomendaciones'].append("⚠️ Consulta clientes lenta - considera indexar")
            if join_time > 2000:
                self.resultados['recomendaciones'].append("⚠️ JOINs lentos - optimiza consultas")
                
            db.close()
            
        except Exception as e:
            print(f"❌ Error en test de base de datos: {e}")
            self.resultados['recomendaciones'].append(f"❌ Error DB: {e}")
            
    def test_url(self, url, endpoint="", timeout=10):
        """Prueba la velocidad de una URL específica"""
        full_url = urljoin(url, endpoint)
        try:
            start_time = time.time()
            response = requests.get(full_url, timeout=timeout)
            response_time = (time.time() - start_time) * 1000
            
            return {
                'url': full_url,
                'status_code': response.status_code,
                'response_time_ms': round(response_time, 2),
                'size_bytes': len(response.content),
                'headers': dict(response.headers),
                'success': response.status_code == 200
            }
        except requests.exceptions.Timeout:
            return {
                'url': full_url,
                'status_code': 'TIMEOUT',
                'response_time_ms': timeout * 1000,
                'error': 'Timeout'
            }
        except Exception as e:
            return {
                'url': full_url,
                'status_code': 'ERROR',
                'response_time_ms': 0,
                'error': str(e)
            }
            
    def test_endpoints_produccion(self):
        """Prueba los endpoints principales en producción"""
        print(f"\n🌐 DIAGNÓSTICO DE APLICACIÓN EN PRODUCCIÓN")
        print(f"URL: {self.url_produccion}")
        print("=" * 50)
        
        endpoints = [
            "/",
            "/clientes",
            "/productos", 
            "/pedidos",
            "/api/clientes/buscar?nit=123456789",
            "/health"
        ]
        
        resultados_produccion = {}
        
        for endpoint in endpoints:
            print(f"🔍 Probando {endpoint}...")
            resultado = self.test_url(self.url_produccion, endpoint)
            resultados_produccion[endpoint] = resultado
            
            if resultado.get('success'):
                print(f"   ✅ {resultado['response_time_ms']:.1f}ms - {resultado['size_bytes']} bytes")
            else:
                print(f"   ❌ {resultado.get('status_code', 'ERROR')} - {resultado.get('error', 'Unknown')}")
                
        self.resultados['tests_remotos']['produccion'] = resultados_produccion
        
        # Analizar resultados de producción
        tiempos = [r['response_time_ms'] for r in resultados_produccion.values() if r.get('success')]
        if tiempos:
            tiempo_promedio = sum(tiempos) / len(tiempos)
            tiempo_maximo = max(tiempos)
            
            print(f"\n📊 Estadísticas de producción:")
            print(f"   ⏱️  Tiempo promedio: {tiempo_promedio:.1f}ms")
            print(f"   🐌 Tiempo máximo: {tiempo_maximo:.1f}ms")
            
            if tiempo_promedio > 3000:
                self.resultados['recomendaciones'].append("🚨 Aplicación muy lenta en producción (+3s)")
            elif tiempo_promedio > 1500:
                self.resultados['recomendaciones'].append("⚠️ Aplicación lenta en producción (+1.5s)")
                
    def test_endpoints_local(self):
        """Prueba los endpoints principales en local"""
        print(f"\n🏠 DIAGNÓSTICO DE APLICACIÓN LOCAL")
        print(f"URL: {self.url_local}")
        print("=" * 50)
        
        # Verificar si el servidor local está corriendo
        try:
            test_response = requests.get(self.url_local, timeout=2)
            print("✅ Servidor local detectado")
        except:
            print("❌ Servidor local no disponible")
            print("💡 Inicia el servidor con: python app.py")
            return
            
        endpoints = [
            "/",
            "/clientes",
            "/productos",
            "/pedidos"
        ]
        
        resultados_local = {}
        
        for endpoint in endpoints:
            print(f"🔍 Probando {endpoint}...")
            resultado = self.test_url(self.url_local, endpoint)
            resultados_local[endpoint] = resultado
            
            if resultado.get('success'):
                print(f"   ✅ {resultado['response_time_ms']:.1f}ms")
            else:
                print(f"   ❌ {resultado.get('status_code', 'ERROR')}")
                
        self.resultados['tests_locales'] = resultados_local
        
    def analizar_redirecciones(self):
        """Analiza redirecciones que pueden causar lentitud"""
        print(f"\n🔄 ANÁLISIS DE REDIRECCIONES")
        print("=" * 50)
        
        # Probar URLs que pueden causar redirecciones
        urls_problematicas = [
            f"{self.url_produccion}/pedidos",  # Tu error 308
            f"{self.url_produccion}/clientes/",
            f"{self.url_produccion}/productos/",
        ]
        
        for url in urls_problematicas:
            try:
                # Usar allow_redirects=False para capturar redirecciones
                response = requests.get(url, allow_redirects=False, timeout=5)
                if response.status_code in [301, 302, 307, 308]:
                    print(f"🔄 {url} -> {response.status_code} (Redirección a: {response.headers.get('Location', 'Unknown')})")
                    self.resultados['recomendaciones'].append(f"🔄 Redirección detectada: {url} -> {response.status_code}")
                else:
                    print(f"✅ {url} -> {response.status_code} (Sin redirección)")
            except Exception as e:
                print(f"❌ Error probando {url}: {e}")
                
    def test_concurrencia(self):
        """Prueba cómo maneja la aplicación múltiples requests simultáneos"""
        print(f"\n⚡ TEST DE CONCURRENCIA")
        print("=" * 50)
        
        def hacer_request():
            return self.test_url(self.url_produccion, "/health")
            
        # Probar con 5 requests simultáneos
        print("🔍 Ejecutando 5 requests simultáneos...")
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(hacer_request) for _ in range(5)]
            resultados = [future.result() for future in concurrent.futures.as_completed(futures)]
            
        total_time = (time.time() - start_time) * 1000
        
        tiempos_individuales = [r['response_time_ms'] for r in resultados if r.get('success')]
        if tiempos_individuales:
            tiempo_promedio = sum(tiempos_individuales) / len(tiempos_individuales)
            print(f"⏱️  Tiempo total: {total_time:.1f}ms")
            print(f"⏱️  Tiempo promedio por request: {tiempo_promedio:.1f}ms")
            print(f"📊 Requests exitosos: {len(tiempos_individuales)}/5")
            
            if tiempo_promedio > 5000:
                self.resultados['recomendaciones'].append("🚨 Aplicación no maneja bien la concurrencia")
                
    def generar_reporte(self):
        """Genera un reporte completo"""
        print(f"\n📋 REPORTE COMPLETO DE VELOCIDAD")
        print("=" * 70)
        
        # Guardar resultados en archivo JSON
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"diagnostico_velocidad_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.resultados, f, indent=2, ensure_ascii=False)
            
        print(f"💾 Resultados guardados en: {filename}")
        
        # Mostrar recomendaciones
        if self.resultados['recomendaciones']:
            print(f"\n🎯 RECOMENDACIONES PRINCIPALES:")
            for i, rec in enumerate(self.resultados['recomendaciones'], 1):
                print(f"   {i}. {rec}")
        else:
            print(f"\n✅ No se detectaron problemas mayores de rendimiento")
            
        # Optimizaciones específicas para GCP
        print(f"\n🚀 OPTIMIZACIONES ESPECÍFICAS PARA GOOGLE CLOUD:")
        print(f"   1. 🔧 Verifica tu instancia de App Engine (F1 vs F2 vs F4)")
        print(f"   2. 🗄️ Optimiza Cloud SQL (instance class, connections)")
        print(f"   3. 🌐 Configura CDN para archivos estáticos")
        print(f"   4. 📊 Usa Cloud Monitoring para métricas en tiempo real")
        print(f"   5. 🏃‍♂️ Considera usar gunicorn con múltiples workers")
        
    def ejecutar_diagnostico_completo(self):
        """Ejecuta todos los tests de diagnóstico"""
        print("🚀 INICIANDO DIAGNÓSTICO COMPLETO DE VELOCIDAD")
        print("=" * 70)
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        try:
            self.info_sistema()
            self.test_base_datos()
            self.test_endpoints_produccion()
            self.test_endpoints_local()
            self.analizar_redirecciones()
            self.test_concurrencia()
            self.generar_reporte()
            
        except KeyboardInterrupt:
            print(f"\n⏹️  Diagnóstico interrumpido por el usuario")
        except Exception as e:
            print(f"\n❌ Error durante el diagnóstico: {e}")
            
        print(f"\n🏁 DIAGNÓSTICO COMPLETADO")

if __name__ == "__main__":
    diagnostico = DiagnosticoVelocidad()
    diagnostico.ejecutar_diagnostico_completo()