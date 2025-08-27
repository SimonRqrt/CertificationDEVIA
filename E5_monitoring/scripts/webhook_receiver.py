#!/usr/bin/env python3
"""
E5 Monitoring - Webhook receiver pour alertes Alertmanager
Critère C20: Surveillance des seuils et alertes

Usage: python3 E5_monitoring/scripts/webhook_receiver.py
"""

from flask import Flask, request, jsonify
import json
from datetime import datetime
import logging

app = Flask(__name__)

# Configuration des logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

alerts_received = []

@app.route('/webhook', methods=['POST'])
def webhook_default():
    """Webhook par défaut"""
    data = request.get_json()
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    logger.info(f"ALERTE REÇUE ({timestamp})")
    
    if data and 'alerts' in data:
        for alert in data['alerts']:
            alert_info = {
                'timestamp': timestamp,
                'alertname': alert.get('labels', {}).get('alertname', 'Unknown'),
                'service': alert.get('labels', {}).get('service', 'Unknown'), 
                'severity': alert.get('labels', {}).get('severity', 'Unknown'),
                'status': alert.get('status', 'Unknown'),
                'description': alert.get('annotations', {}).get('description', 'No description'),
                'summary': alert.get('annotations', {}).get('summary', 'No summary')
            }
            alerts_received.append(alert_info)
            
            print(f"""
============= ALERTE COACH AI =============
Timestamp: {alert_info['timestamp']}
Alerte: {alert_info['alertname']}
Service: {alert_info['service']} 
Sévérité: {alert_info['severity']}
Description: {alert_info['description']}
Résumé: {alert_info['summary']}
Status: {alert_info['status']}
============================================
            """)
    
    return jsonify({"status": "received", "count": len(data.get('alerts', []))})

@app.route('/webhook/critical', methods=['POST'])
def webhook_critical():
    """Webhook spécialisé pour alertes critiques"""
    data = request.get_json()
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    logger.info(f"ALERTE CRITIQUE REÇUE ({timestamp})")
    
    if data and 'alerts' in data:
        for alert in data['alerts']:
            alert_info = {
                'timestamp': timestamp,
                'alertname': alert.get('labels', {}).get('alertname', 'Unknown'),
                'service': alert.get('labels', {}).get('service', 'Unknown'), 
                'severity': alert.get('labels', {}).get('severity', 'Unknown'),
                'status': alert.get('status', 'Unknown'),
                'description': alert.get('annotations', {}).get('description', 'No description')
            }
            alerts_received.append(alert_info)
            
            print(f"""
======== ALERTE CRITIQUE ========
{alert_info['timestamp']}
{alert_info['alertname']} ({alert_info['severity']})
Service: {alert_info['service']}
{alert_info['description']}
Status: {alert_info['status']}
================================
            """)
    
    return jsonify({"status": "critical_received", "count": len(data.get('alerts', []))})

@app.route('/webhook/openai', methods=['POST'])
def webhook_openai():
    """Webhook spécialisé pour alertes OpenAI"""
    data = request.get_json()
    logger.info("Alerte OpenAI reçue")
    print(f"ALERTE OPENAI: {json.dumps(data, indent=2)}")
    return jsonify({"status": "openai_received"})

@app.route('/alerts', methods=['GET'])
def get_alerts():
    """API pour voir toutes les alertes reçues"""
    return jsonify({
        "total_alerts": len(alerts_received),
        "alerts": alerts_received[-10:]  # 10 dernières
    })

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "alerts_count": len(alerts_received)})

if __name__ == '__main__':
    print("Coach AI - Webhook Receiver")
    print("=" * 40)
    print("Écoute sur http://localhost:5001")
    print("Endpoints disponibles:")
    print("  • /webhook         - Alertes générales")
    print("  • /webhook/critical - Alertes critiques")
    print("  • /webhook/openai  - Alertes OpenAI")
    print("  • /alerts          - Voir alertes reçues")
    print("=" * 40)
    print("Presse Ctrl+C pour arrêter")
    print()
    
    app.run(host='0.0.0.0', port=5001, debug=False)