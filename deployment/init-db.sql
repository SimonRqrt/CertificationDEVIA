-- Script d'initialisation PostgreSQL pour Coach IA
-- Ce script est exécuté automatiquement au premier démarrage

-- Créer des extensions utiles
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Vérifier la création de la base
SELECT 'Database coach_ia_db ready!' as message;