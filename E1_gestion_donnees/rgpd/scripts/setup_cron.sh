#!/bin/bash
# Configuration CRON pour scripts RGPD automatisés
# Usage: sudo bash setup_cron.sh

set -e

SCRIPT_DIR="/Users/sims/Documents/Simplon_DEV_IA/Certification/CertificationDEVIA/E1_gestion_donnees/rgpd/scripts"
LOG_DIR="/var/log/rgpd"
PYTHON_PATH="/usr/bin/python3"

echo "🔧 Configuration CRON RGPD - Coach IA"
echo "======================================"

# Vérification permissions root
if [[ $EUID -ne 0 ]]; then
   echo "❌ Ce script doit être exécuté en tant que root"
   echo "Usage: sudo bash setup_cron.sh"
   exit 1
fi

# Création répertoires logs avec bonnes permissions
echo "📁 Création répertoires logs..."
mkdir -p $LOG_DIR
mkdir -p $LOG_DIR/reports
chown -R www-data:www-data $LOG_DIR
chmod -R 755 $LOG_DIR

# Vérification scripts Python
echo "🐍 Vérification scripts Python..."
for script in "cleanup_users.py" "cleanup_activities.py"; do
    if [[ ! -f "$SCRIPT_DIR/$script" ]]; then
        echo "❌ Script manquant: $script"
        exit 1
    fi
    chmod +x "$SCRIPT_DIR/$script"
    echo "✅ $script - permissions OK"
done

# Test scripts en mode dry-run
echo "🧪 Test scripts en mode dry-run..."
cd "$SCRIPT_DIR"

echo "Test cleanup_users.py..."
$PYTHON_PATH cleanup_users.py --dry-run --verbose > /tmp/test_users.log 2>&1
if [[ $? -eq 0 ]]; then
    echo "✅ cleanup_users.py - test OK"
else
    echo "❌ cleanup_users.py - erreur test"
    cat /tmp/test_users.log
    exit 1
fi

echo "Test cleanup_activities.py..."
$PYTHON_PATH cleanup_activities.py --dry-run --verbose > /tmp/test_activities.log 2>&1
if [[ $? -eq 0 ]]; then
    echo "✅ cleanup_activities.py - test OK"
else
    echo "❌ cleanup_activities.py - erreur test"
    cat /tmp/test_activities.log
    exit 1
fi

# Création fichier CRON
echo "⏰ Configuration CRON jobs..."

CRON_FILE="/tmp/rgpd_cron"
cat > $CRON_FILE << EOF
# RGPD Automated Cleanup - Coach IA
# Généré automatiquement le $(date)

# Nettoyage utilisateurs dormants - Hebdomadaire (Dimanche 02:00)
0 2 * * 0 $PYTHON_PATH $SCRIPT_DIR/cleanup_users.py >> $LOG_DIR/cleanup_users.log 2>&1

# Nettoyage activités anciennes - Mensuel (1er du mois 01:00)  
0 1 1 * * $PYTHON_PATH $SCRIPT_DIR/cleanup_activities.py >> $LOG_DIR/cleanup_activities.log 2>&1

# Rotation logs RGPD - Quotidien (04:00)
0 4 * * * /usr/sbin/logrotate -f /etc/logrotate.d/rgpd

# Test scripts en dry-run - Hebdomadaire (Mercredi 12:00)
0 12 * * 3 $PYTHON_PATH $SCRIPT_DIR/cleanup_users.py --dry-run --verbose >> $LOG_DIR/test_users.log 2>&1
5 12 * * 3 $PYTHON_PATH $SCRIPT_DIR/cleanup_activities.py --dry-run --verbose >> $LOG_DIR/test_activities.log 2>&1

EOF

# Installation CRON pour utilisateur www-data
crontab -u www-data $CRON_FILE
echo "✅ CRON jobs installés pour utilisateur www-data"

# Configuration logrotate
echo "📝 Configuration rotation logs..."
cat > /etc/logrotate.d/rgpd << EOF
$LOG_DIR/*.log {
    daily
    rotate 90
    compress
    delaycompress
    missingok
    notifempty
    create 644 www-data www-data
    postrotate
        # Notification rotation logs RGPD
        echo "Logs RGPD rotated: \$(date)" >> $LOG_DIR/rotation.log
    endscript
}

$LOG_DIR/audit_*.jsonl {
    monthly
    rotate 36
    compress
    delaycompress
    missingok
    notifempty
    create 644 www-data www-data
    # Conservation 3 ans audit trail RGPD
}
EOF

echo "✅ Logrotate configuré - conservation 90j logs, 3 ans audit"

# Script de monitoring
echo "📊 Création script monitoring..."
cat > $SCRIPT_DIR/monitor_rgpd.py << 'EOF'
#!/usr/bin/env python3
"""
Monitoring des processus RGPD
Alerte si scripts non exécutés dans les délais
"""

import os
import json
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText

def check_last_execution():
    """Vérification dernière exécution scripts"""
    log_dir = "/var/log/rgpd"
    alerts = []
    
    # Vérification users cleanup (hebdomadaire)
    users_log = f"{log_dir}/cleanup_users.log"
    if os.path.exists(users_log):
        stat = os.stat(users_log)
        last_modified = datetime.fromtimestamp(stat.st_mtime)
        if datetime.now() - last_modified > timedelta(days=8):
            alerts.append(f"cleanup_users.py non exécuté depuis {(datetime.now() - last_modified).days} jours")
    
    # Vérification activities cleanup (mensuel)
    activities_log = f"{log_dir}/cleanup_activities.log"
    if os.path.exists(activities_log):
        stat = os.stat(activities_log)
        last_modified = datetime.fromtimestamp(stat.st_mtime)
        if datetime.now() - last_modified > timedelta(days=32):
            alerts.append(f"cleanup_activities.py non exécuté depuis {(datetime.now() - last_modified).days} jours")
    
    return alerts

def send_alert(alerts):
    """Envoi email alerte admin"""
    if not alerts:
        return
    
    subject = "ALERTE RGPD - Scripts non exécutés"
    body = "Alertes détectées:\n\n" + "\n".join(f"- {alert}" for alert in alerts)
    
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = 'rgpd@coach-ia.app'
    msg['To'] = 'admin@coach-ia.app'
    
    # TODO: Configuration SMTP
    print(f"ALERTE RGPD: {alerts}")

if __name__ == '__main__':
    alerts = check_last_execution()
    if alerts:
        send_alert(alerts)
EOF

chmod +x $SCRIPT_DIR/monitor_rgpd.py

# Ajout monitoring au CRON
echo "# Monitoring RGPD - Quotidien 08:00" >> $CRON_FILE
echo "0 8 * * * $PYTHON_PATH $SCRIPT_DIR/monitor_rgpd.py >> $LOG_DIR/monitoring.log 2>&1" >> $CRON_FILE

# Réinstallation CRON avec monitoring
crontab -u www-data $CRON_FILE

# Affichage CRON installé
echo ""
echo "📋 CRON jobs installés:"
echo "======================"
crontab -u www-data -l | grep -v "^#"

# Documentation finale
echo ""
echo "✅ Configuration RGPD terminée avec succès!"
echo ""
echo "📚 Commandes utiles:"
echo "==================="
echo "# Vérifier CRON:"
echo "sudo crontab -u www-data -l"
echo ""
echo "# Tester scripts manuellement:"
echo "cd $SCRIPT_DIR"
echo "$PYTHON_PATH cleanup_users.py --dry-run --verbose"
echo "$PYTHON_PATH cleanup_activities.py --dry-run --verbose"
echo ""
echo "# Consulter logs:"
echo "tail -f $LOG_DIR/cleanup_users.log"
echo "tail -f $LOG_DIR/cleanup_activities.log"
echo ""
echo "# Audit trail:"
echo "tail -f $LOG_DIR/audit_users.jsonl"
echo "tail -f $LOG_DIR/audit_activities.jsonl"
echo ""
echo "🔒 Conformité RGPD: Scripts automatisés selon procédures"
echo "📅 Prochaine exécution: Dimanche 02:00 (users) + 1er du mois 01:00 (activities)"

# Nettoyage
rm -f $CRON_FILE /tmp/test_*.log

echo ""
echo "🎯 Installation terminée - RGPD compliance automatisée ✅"