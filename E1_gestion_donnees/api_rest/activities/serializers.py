from rest_framework import serializers
from .models import Activity, ActivitySplit, GPSPoint


class ActivitySplitSerializer(serializers.ModelSerializer):
    """Serializer pour les splits d'activité"""
    pace_per_km = serializers.ReadOnlyField()
    
    class Meta:
        model = ActivitySplit
        fields = [
            'id', 'split_index', 'split_type',
            'distance_meters', 'duration_seconds',
            'average_speed', 'max_speed',
            'average_hr', 'max_hr',
            'elevation_gain', 'elevation_loss',
            'average_cadence', 'pace_per_km'
        ]


class GPSPointSerializer(serializers.ModelSerializer):
    """Serializer pour les points GPS"""
    
    class Meta:
        model = GPSPoint
        fields = [
            'id', 'latitude', 'longitude', 'altitude',
            'timestamp', 'elapsed_time',
            'speed', 'heart_rate', 'cadence', 'distance'
        ]


class ActivitySerializer(serializers.ModelSerializer):
    """Serializer pour les activités"""
    
    # Propriétés calculées
    duration_formatted = serializers.ReadOnlyField()
    distance_km = serializers.ReadOnlyField()
    average_speed_kmh = serializers.ReadOnlyField()
    pace_per_km = serializers.ReadOnlyField()
    
    # Relations
    splits = ActivitySplitSerializer(many=True, read_only=True)
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    # Statistiques
    splits_count = serializers.IntegerField(source='splits.count', read_only=True)
    gps_points_count = serializers.IntegerField(source='gps_points.count', read_only=True)
    
    class Meta:
        model = Activity
        fields = [
            # Identifiants
            'id', 'activity_id', 'garmin_id', 'strava_id',
            
            # Informations de base
            'activity_name', 'activity_type',
            'start_time', 'end_time', 'duration_seconds', 'distance_meters',
            
            # Vitesse et allure
            'average_speed', 'max_speed', 'average_pace',
            
            # Fréquence cardiaque
            'average_hr', 'max_hr',
            'hr_zone_1_time', 'hr_zone_2_time', 'hr_zone_3_time',
            'hr_zone_4_time', 'hr_zone_5_time',
            
            # Élévation
            'elevation_gain', 'elevation_loss',
            
            # Position GPS
            'start_latitude', 'start_longitude',
            'end_latitude', 'end_longitude',
            
            # Calories et effort
            'calories', 'training_load',
            'aerobic_effect', 'anaerobic_effect',
            
            # Données running
            'steps', 'average_cadence', 'max_cadence', 'stride_length',
            
            # Performances
            'vo2_max', 'fastest_1k', 'fastest_5k', 'fastest_10k',
            
            # Conditions météo
            'temperature', 'humidity', 'wind_speed',
            
            # Équipement et ressenti
            'device_name', 'perceived_exertion', 'notes',
            
            # Statut
            'is_race', 'is_workout', 'is_manual',
            
            # Métadonnées
            'created_at', 'updated_at', 'synced_at',
            
            # Propriétés calculées
            'duration_formatted', 'distance_km', 
            'average_speed_kmh', 'pace_per_km',
            
            # Relations
            'user_name', 'splits', 'splits_count', 'gps_points_count'
        ]
        read_only_fields = [
            'created_at', 'updated_at', 'user_name',
            'splits_count', 'gps_points_count'
        ]
    
    def validate_distance_meters(self, value):
        """Validation de la distance"""
        if value < 0:
            raise serializers.ValidationError("La distance ne peut pas être négative")
        if value > 300000:  # 300km max
            raise serializers.ValidationError("Distance trop importante (max 300km)")
        return value
    
    def validate_duration_seconds(self, value):
        """Validation de la durée"""
        if value < 0:
            raise serializers.ValidationError("La durée ne peut pas être négative")
        if value > 86400:  # 24h max
            raise serializers.ValidationError("Durée trop importante (max 24h)")
        return value
    
    def validate_average_hr(self, value):
        """Validation de la fréquence cardiaque moyenne"""
        if value and (value < 30 or value > 250):
            raise serializers.ValidationError("Fréquence cardiaque invalide (30-250 bpm)")
        return value
    
    def validate(self, data):
        """Validation croisée des champs"""
        # Vérifier cohérence des temps
        if data.get('end_time') and data.get('start_time'):
            if data['end_time'] <= data['start_time']:
                raise serializers.ValidationError(
                    "L'heure de fin doit être postérieure à l'heure de début"
                )
        
        # Vérifier cohérence HR max vs moyenne
        if data.get('max_hr') and data.get('average_hr'):
            if data['max_hr'] < data['average_hr']:
                raise serializers.ValidationError(
                    "La FC max ne peut pas être inférieure à la FC moyenne"
                )
        
        # Vérifier cohérence vitesse max vs moyenne
        if data.get('max_speed') and data.get('average_speed'):
            if data['max_speed'] < data['average_speed']:
                raise serializers.ValidationError(
                    "La vitesse max ne peut pas être inférieure à la vitesse moyenne"
                )
        
        return data


class ActivityListSerializer(serializers.ModelSerializer):
    """Serializer simplifié pour la liste des activités"""
    
    duration_formatted = serializers.ReadOnlyField()
    distance_km = serializers.ReadOnlyField()
    pace_per_km = serializers.ReadOnlyField()
    
    class Meta:
        model = Activity
        fields = [
            'id', 'activity_name', 'activity_type',
            'start_time', 'duration_seconds', 'distance_meters',
            'average_pace', 'average_hr',
            'calories', 'is_race', 'is_workout',
            'duration_formatted', 'distance_km', 'pace_per_km'
        ]


class ActivityStatsSerializer(serializers.Serializer):
    """Serializer pour les statistiques d'activités"""
    
    total_count = serializers.IntegerField()
    total_distance = serializers.FloatField()
    total_duration = serializers.IntegerField()
    avg_pace = serializers.FloatField()
    avg_hr = serializers.FloatField()
    
    # Champs calculés
    total_distance_km = serializers.SerializerMethodField()
    total_duration_formatted = serializers.SerializerMethodField()
    avg_pace_formatted = serializers.SerializerMethodField()
    
    def get_total_distance_km(self, obj):
        if obj.get('total_distance'):
            return round(obj['total_distance'] / 1000, 2)
        return 0
    
    def get_total_duration_formatted(self, obj):
        if obj.get('total_duration'):
            hours = obj['total_duration'] // 3600
            minutes = (obj['total_duration'] % 3600) // 60
            return f"{hours}h {minutes}min"
        return "0h 0min"
    
    def get_avg_pace_formatted(self, obj):
        if obj.get('avg_pace'):
            minutes = int(obj['avg_pace'] // 60)
            seconds = int(obj['avg_pace'] % 60)
            return f"{minutes}:{seconds:02d}"
        return None