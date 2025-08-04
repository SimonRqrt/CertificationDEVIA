# Guide de Design Web Django - Style Pawatech

## Analyse du Design

Le site Pawatech présente un design moderne et professionnel avec les caractéristiques suivantes :

- **Layout minimaliste** avec beaucoup d'espace blanc
- **Typographie moderne** avec des titres en gras et du texte lisible
- **Design responsive** adapté aux mobiles et desktop
- **Sections bien structurées** avec une hiérarchie claire
- **Images de qualité** intégrées harmonieusement
- **Palette de couleurs** sobre (noir, blanc, nuances de gris)
- **Animations subtiles** et transitions fluides

## Structure Django

### 1. Configuration du projet

```python
# settings.py
import os

# Configuration des fichiers statiques
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR / "static",
]
STATIC_ROOT = BASE_DIR / "staticfiles"

# Configuration des médias
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Apps installées
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'main',  # Notre app principale
]
```

### 2. Structure des URLs

```python
# urls.py (projet principal)
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('main.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# main/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
]
```

### 3. Modèles Django

```python
# main/models.py
from django.db import models

class Company(models.Model):
    name = models.CharField(max_length=100)
    tagline = models.CharField(max_length=200)
    description = models.TextField()
    hero_image = models.ImageField(upload_to='hero/')
    
    def __str__(self):
        return self.name

class Statistic(models.Model):
    label = models.CharField(max_length=100)
    value = models.CharField(max_length=50)
    description = models.CharField(max_length=200, blank=True)
    
    def __str__(self):
        return f"{self.label}: {self.value}"

class Feature(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    icon = models.ImageField(upload_to='features/', blank=True)
    
    def __str__(self):
        return self.title

class TeamMember(models.Model):
    name = models.CharField(max_length=100)
    position = models.CharField(max_length=100)
    photo = models.ImageField(upload_to='team/')
    
    def __str__(self):
        return self.name
```

### 4. Vues Django

```python
# main/views.py
from django.shortcuts import render
from .models import Company, Statistic, Feature, TeamMember

def home(request):
    context = {
        'company': Company.objects.first(),
        'statistics': Statistic.objects.all(),
        'features': Feature.objects.all()[:6],
        'team_members': TeamMember.objects.all()[:4],
    }
    return render(request, 'main/home.html', context)
```

## Templates HTML

### Template de base

```html
<!-- main/templates/main/base.html -->
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}{% endblock %}</title>
    {% load static %}
    <link rel="stylesheet" href="{% static 'css/style.css' %}">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
</head>
<body>
    {% block content %}
    {% endblock %}
    
    <script src="{% static 'js/main.js' %}"></script>
</body>
</html>
```

### Template de la page d'accueil

```html
<!-- main/templates/main/home.html -->
{% extends 'main/base.html' %}
{% load static %}

{% block title %}{{ company.name }} - {{ company.tagline }}{% endblock %}

{% block content %}
<!-- Section Hero -->
<section class="hero">
    <div class="container">
        <div class="hero-content">
            <div class="hero-text">
                <h1 class="hero-title">
                    <span class="title-line">Emerging markets</span>
                    <span class="title-line">iGaming platform</span>
                </h1>
                <p class="hero-subtitle">
                    Licensor of Africa's biggest<br>
                    sportsbook brand
                </p>
            </div>
            {% if company.hero_image %}
            <div class="hero-image">
                <img src="{{ company.hero_image.url }}" alt="{{ company.name }}">
            </div>
            {% endif %}
        </div>
    </div>
</section>

<!-- Section Overview -->
<section class="overview">
    <div class="container">
        <div class="section-header">
            <h2>Overview</h2>
        </div>
        <div class="overview-content">
            <p class="overview-text">
                {{ company.description }}
            </p>
        </div>
    </div>
</section>

<!-- Section Tech -->
<section class="tech-section">
    <div class="container">
        <div class="tech-header">
            <h2>tech</h2>
        </div>
        <div class="tech-grid">
            {% for feature in features %}
            <div class="tech-card">
                <h3>{{ feature.title }}</h3>
                <p>{{ feature.description }}</p>
            </div>
            {% endfor %}
        </div>
    </div>
</section>

<!-- Section Statistics -->
<section class="stats-section">
    <div class="container">
        <div class="stats-grid">
            {% for stat in statistics %}
            <div class="stat-item">
                <div class="stat-value">{{ stat.value }}</div>
                <div class="stat-label">{{ stat.label }}</div>
            </div>
            {% endfor %}
        </div>
    </div>
</section>

<!-- Section Mission -->
<section class="mission-section">
    <div class="container">
        <div class="mission-content">
            <div class="mission-text">
                <h2>betpawa Brand mission</h2>
                <h3>Make betting friendly</h3>
                <p>We are committed to user-centric design and our priority is giving users a seamless experience. We believe in acting in a responsible manner and do not participate in aggressive marketing, cross-selling, spam notifications and VIPs.</p>
            </div>
            <div class="mission-image">
                <img src="{% static 'images/team-office.jpg' %}" alt="Team in office">
            </div>
        </div>
    </div>
</section>

<!-- Footer -->
<footer class="footer">
    <div class="container">
        <div class="footer-content">
            <h2>Get in touch</h2>
            <p>For media, talent or any other inquiries, please get in touch with us below.</p>
        </div>
    </div>
</footer>
{% endblock %}
```

## CSS Styling

```css
/* static/css/style.css */

/* Reset et base */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    line-height: 1.6;
    color: #333;
    background-color: #fff;
}

.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 20px;
}

/* Section Hero */
.hero {
    min-height: 100vh;
    display: flex;
    align-items: center;
    padding: 80px 0;
}

.hero-content {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 60px;
    align-items: center;
}

.hero-title {
    font-size: clamp(3rem, 8vw, 6rem);
    font-weight: 700;
    line-height: 1.1;
    margin-bottom: 20px;
}

.title-line {
    display: block;
}

.hero-subtitle {
    font-size: 1.25rem;
    color: #666;
    font-weight: 400;
}

.hero-image img {
    width: 100%;
    height: auto;
    border-radius: 12px;
}

/* Section Overview */
.overview {
    padding: 100px 0;
    background-color: #f8f9fa;
}

.section-header h2 {
    font-size: 2.5rem;
    font-weight: 600;
    margin-bottom: 40px;
}

.overview-text {
    font-size: 1.1rem;
    line-height: 1.8;
    color: #555;
    max-width: 800px;
}

/* Section Tech */
.tech-section {
    padding: 100px 0;
}

.tech-header h2 {
    font-size: 2.5rem;
    font-weight: 600;
    margin-bottom: 60px;
    color: #000;
}

.tech-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
    gap: 40px;
}

.tech-card h3 {
    font-size: 1.3rem;
    font-weight: 600;
    margin-bottom: 15px;
}

.tech-card p {
    color: #666;
    line-height: 1.7;
}

/* Section Statistics */
.stats-section {
    padding: 80px 0;
    background-color: #000;
    color: #fff;
}

.stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 40px;
}

.stat-item {
    text-align: center;
}

.stat-value {
    font-size: 3rem;
    font-weight: 700;
    margin-bottom: 10px;
}

.stat-label {
    font-size: 1.1rem;
    color: #ccc;
}

/* Section Mission */
.mission-section {
    padding: 100px 0;
}

.mission-content {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 60px;
    align-items: center;
}

.mission-text h2 {
    font-size: 2.5rem;
    font-weight: 600;
    margin-bottom: 20px;
}

.mission-text h3 {
    font-size: 1.8rem;
    font-weight: 500;
    margin-bottom: 25px;
    color: #333;
}

.mission-text p {
    font-size: 1.1rem;
    line-height: 1.7;
    color: #666;
}

.mission-image img {
    width: 100%;
    height: auto;
    border-radius: 12px;
}

/* Footer */
.footer {
    padding: 80px 0;
    background-color: #f8f9fa;
    text-align: center;
}

.footer h2 {
    font-size: 2rem;
    font-weight: 600;
    margin-bottom: 20px;
}

.footer p {
    font-size: 1.1rem;
    color: #666;
}

/* Responsive Design */
@media (max-width: 768px) {
    .hero-content,
    .mission-content {
        grid-template-columns: 1fr;
        gap: 40px;
    }
    
    .hero-title {
        font-size: 2.5rem;
    }
    
    .tech-grid {
        grid-template-columns: 1fr;
    }
    
    .stats-grid {
        grid-template-columns: repeat(2, 1fr);
    }
}

@media (max-width: 480px) {
    .container {
        padding: 0 15px;
    }
    
    .hero,
    .overview,
    .tech-section,
    .mission-section {
        padding: 60px 0;
    }
    
    .stats-grid {
        grid-template-columns: 1fr;
        gap: 30px;
    }
}

/* Animations */
@keyframes fadeInUp {
    from {
        opacity: 0;
        transform: translateY(30px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

.hero-content,
.tech-card,
.stat-item {
    animation: fadeInUp 0.8s ease-out;
}
```

## JavaScript pour les interactions

```javascript
// static/js/main.js

document.addEventListener('DOMContentLoaded', function() {
    // Animation au scroll
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-in');
            }
        });
    }, observerOptions);

    // Observer les éléments à animer
    document.querySelectorAll('.tech-card, .stat-item, .mission-text').forEach(el => {
        observer.observe(el);
    });

    // Smooth scroll pour les liens d'ancrage
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
});
```

## Administration Django

```python
# main/admin.py
from django.contrib import admin
from .models import Company, Statistic, Feature, TeamMember

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ['name', 'tagline']

@admin.register(Statistic)
class StatisticAdmin(admin.ModelAdmin):
    list_display = ['label', 'value']

@admin.register(Feature)
class FeatureAdmin(admin.ModelAdmin):
    list_display = ['title']

@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    list_display = ['name', 'position']
```

## Déploiement et optimisations

### Configuration pour la production

```python
# settings/production.py
import os
from .base import *

DEBUG = False
ALLOWED_HOSTS = ['votre-domaine.com']

# Configuration des fichiers statiques pour la production
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

# Configuration des médias avec un CDN (optionnel)
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
```

### Optimisations des performances

1. **Compression des images** : Utilisez Pillow pour optimiser les images
2. **Minification CSS/JS** : Utilisez django-compressor
3. **Cache** : Implémentez le cache Django pour les vues
4. **CDN** : Servez les fichiers statiques via un CDN

### Commandes utiles

```bash
# Créer et appliquer les migrations
python manage.py makemigrations
python manage.py migrate

# Créer un superutilisateur
python manage.py createsuperuser

# Collecter les fichiers statiques
python manage.py collectstatic

# Lancer le serveur de développement
python manage.py runserver
```

## Points clés du design Pawatech

1. **Simplicité** : Design épuré avec focus sur le contenu
2. **Typographie** : Police moderne (Inter) avec hiérarchies claires
3. **Espacement** : Utilisation généreuse de l'espace blanc
4. **Responsive** : Adaptation parfaite aux différents écrans
5. **Performance** : Images optimisées et code léger
6. **Accessibilité** : Contrastes respectés et navigation claire

