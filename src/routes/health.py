"""
Health Check Endpoint
Provides system health status for monitoring and load balancers
"""

from flask import Blueprint, jsonify
import psutil
import docker
import time
import logging

health_bp = Blueprint('health', __name__)

logger = logging.getLogger(__name__)

@health_bp.route('/health', methods=['GET'])
def health_check():
    """
    Comprehensive health check endpoint
    Returns system status and health metrics
    """
    try:
        health_status = {
            'status': 'healthy',
            'timestamp': time.time(),
            'checks': {}
        }
        
        # Check database connection
        try:
            from src.models.user import db
            db.engine.execute('SELECT 1')
            health_status['checks']['database'] = 'healthy'
        except Exception as e:
            health_status['checks']['database'] = f'unhealthy: {str(e)}'
            health_status['status'] = 'degraded'
        
        # Check Docker daemon
        try:
            client = docker.from_env()
            client.ping()
            health_status['checks']['docker'] = 'healthy'
        except Exception as e:
            health_status['checks']['docker'] = f'unhealthy: {str(e)}'
            health_status['status'] = 'degraded'
        
        # Check system resources
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            health_status['checks']['system'] = {
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'disk_percent': disk.percent,
                'status': 'healthy'
            }
            
            # Alert if resources are critically low
            if cpu_percent > 90 or memory.percent > 90 or disk.percent > 90:
                health_status['checks']['system']['status'] = 'warning'
                health_status['status'] = 'degraded'
                
        except Exception as e:
            health_status['checks']['system'] = f'unhealthy: {str(e)}'
            health_status['status'] = 'degraded'
        
        # Determine overall status
        if health_status['status'] == 'healthy':
            return jsonify(health_status), 200
        else:
            return jsonify(health_status), 503
            
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': time.time()
        }), 503

@health_bp.route('/health/ready', methods=['GET'])
def readiness_check():
    """
    Readiness check for Kubernetes/container orchestration
    Returns 200 if service is ready to accept traffic
    """
    try:
        # Check if all critical services are available
        from src.models.user import db
        db.engine.execute('SELECT 1')
        
        return jsonify({
            'status': 'ready',
            'timestamp': time.time()
        }), 200
        
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return jsonify({
            'status': 'not ready',
            'error': str(e),
            'timestamp': time.time()
        }), 503

@health_bp.route('/health/live', methods=['GET'])
def liveness_check():
    """
    Liveness check for Kubernetes/container orchestration
    Returns 200 if service is alive (basic functionality)
    """
    return jsonify({
        'status': 'alive',
        'timestamp': time.time()
    }), 200

@health_bp.route('/metrics', methods=['GET'])
def metrics():
    """
    Prometheus-style metrics endpoint
    Returns system and application metrics
    """
    try:
        # System metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Docker metrics
        try:
            client = docker.from_env()
            containers = client.containers.list()
            running_containers = len([c for c in containers if c.status == 'running'])
            total_containers = len(containers)
        except:
            running_containers = 0
            total_containers = 0
        
        # Application metrics (you can extend this)
        metrics_data = {
            'system_cpu_percent': cpu_percent,
            'system_memory_percent': memory.percent,
            'system_disk_percent': disk.percent,
            'docker_containers_running': running_containers,
            'docker_containers_total': total_containers,
            'timestamp': time.time()
        }
        
        return jsonify(metrics_data), 200
        
    except Exception as e:
        logger.error(f"Metrics collection failed: {e}")
        return jsonify({
            'error': str(e),
            'timestamp': time.time()
        }), 500

