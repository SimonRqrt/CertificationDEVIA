#!/usr/bin/env python3
"""
Script pour corriger le parser Django pour détecter les formats multiples de semaines
"""

# Fonction parse_training_schedule corrigée
CORRECTED_PARSER = '''def parse_training_schedule(agent_response_text):
    """
    Parse la réponse de l'agent IA pour extraire le planning d'entraînement sous forme de tableau structuré.
    Retourne un dictionnaire avec les données du planning.
    """
    # Rechercher les tableaux dans le texte
    lines = agent_response_text.split('\\n')
    schedule_data = []
    
    current_week = 1
    current_day = ""
    
    for line in lines:
        line = line.strip()
        
        # Détecter une nouvelle semaine - formats multiples
        week_patterns = [
            r'## Semaine (\\d+)',        # Format: ## Semaine 2
            r'# Semaine (\\d+)',         # Format: # Semaine 2  
            r'Semaine (\\d+)',           # Format: Semaine 2
            r'SEMAINE (\\d+)',           # Format: SEMAINE 2
            r'Week (\\d+)',              # Format: Week 2 (anglais)
            r'semaine du',               # Format: semaine du [Date] 
        ]
        
        for pattern in week_patterns:
            week_match = re.search(pattern, line, re.IGNORECASE)
            if week_match and pattern != r'semaine du':
                current_week = int(week_match.group(1))
                break
            elif pattern == r'semaine du' and 'semaine du' in line.lower():
                # Pour "semaine du [date]", on incrémente
                current_week += 1
                break
            
        # Détecter une ligne de tableau Markdown
        if '|' in line and line.count('|') >= 3:
            cells = [cell.strip() for cell in line.split('|') if cell.strip()]
            if len(cells) >= 3 and not all('-' in cell for cell in cells):  # Ignorer les séparateurs
                # Parser selon le nombre de colonnes
                if len(cells) >= 4:
                    schedule_data.append({
                        'week': current_week,
                        'day': cells[0],
                        'type': cells[1],
                        'duration': cells[2],
                        'description': cells[3] if len(cells) > 3 else '',
                        'intensity': cells[4] if len(cells) > 4 else ''
                    })
        
        # Détecter format texte (ex: "Lundi: Endurance - 45 min")
        elif ':' in line:
            day_match = re.match(r'(Lundi|Mardi|Mercredi|Jeudi|Vendredi|Samedi|Dimanche|Jour \\d+)\\s*:\\s*(.+)', line, re.IGNORECASE)
            if day_match:
                day = day_match.group(1)
                content = day_match.group(2)
                
                # Extraire type et durée
                duration_match = re.search(r'(\\d+)\\s*(min|h|km)', content, re.IGNORECASE)
                duration = duration_match.group(0) if duration_match else ''
                
                # Extraire type d'entraînement
                training_types = ['endurance', 'fractionné', 'interval', 'récupération', 'repos', 'sortie longue', 'tempo']
                training_type = ''
                for t_type in training_types:
                    if t_type.lower() in content.lower():
                        training_type = t_type.title()
                        break
                
                schedule_data.append({
                    'week': current_week,
                    'day': day,
                    'type': training_type,
                    'duration': duration,
                    'description': content,
                    'intensity': ''
                })
    
    # Calculer les statistiques correctement
    weeks = set(s['week'] for s in schedule_data)
    active_sessions = [s for s in schedule_data if s['type'] and s['type'].lower() not in ['repos', '-', '']]
    
    return {
        'schedule': schedule_data,
        'total_weeks': len(weeks) if weeks else 1,
        'total_sessions': len(active_sessions),
        'sessions_per_week': len(active_sessions) // max(len(weeks), 1) if weeks else len(active_sessions)
    }'''

print("Parser corrigé créé.")
print(CORRECTED_PARSER)