// Coach AI - JavaScript Interactions

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
    document.querySelectorAll('.tech-card, .stat-item, .service-card, .visual-card').forEach(el => {
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

    // Animation des statistiques (compteur)
    function animateCounter(element, target, duration = 2000) {
        const start = 0;
        const startTimestamp = performance.now();
        
        function step(currentTimestamp) {
            const elapsed = currentTimestamp - startTimestamp;
            const progress = Math.min(elapsed / duration, 1);
            
            // Fonction d'ease-out
            const easedProgress = 1 - Math.pow(1 - progress, 3);
            
            const current = Math.floor(start + (target - start) * easedProgress);
            element.textContent = current;
            
            if (progress < 1) {
                requestAnimationFrame(step);
            } else {
                element.textContent = target;
            }
        }
        
        requestAnimationFrame(step);
    }

    // Observer pour déclencher l'animation des statistiques
    const statsObserver = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const statValue = entry.target.querySelector('.stat-value');
                const value = statValue.textContent.trim();
                
                // Si c'est un nombre, animer le compteur
                if (/^\d+$/.test(value)) {
                    const targetValue = parseInt(value);
                    statValue.textContent = '0';
                    animateCounter(statValue, targetValue);
                }
                
                statsObserver.unobserve(entry.target);
            }
        });
    }, { threshold: 0.5 });

    document.querySelectorAll('.stat-item').forEach(stat => {
        statsObserver.observe(stat);
    });

    // Effet hover pour les cartes
    document.querySelectorAll('.visual-card, .tech-card, .service-card').forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-8px)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });
    });

    // Vérification du statut des services
    function checkServiceStatus() {
        const services = [
            { url: '/api/v1/auth/', element: document.querySelector('[href="/api/v1/auth/"]') },
            { url: 'http://localhost:8000/docs', element: document.querySelector('[href="http://localhost:8000"]') },
            { url: 'http://localhost:8502/', element: document.querySelector('[href="http://localhost:8502"]') }
        ];

        services.forEach(service => {
            if (service.element) {
                fetch(service.url, { mode: 'no-cors' })
                    .then(() => {
                        service.element.style.opacity = '1';
                        service.element.parentElement.classList.add('service-online');
                    })
                    .catch(() => {
                        service.element.style.opacity = '0.6';
                        service.element.parentElement.classList.add('service-offline');
                    });
            }
        });
    }

    // Vérifier le statut des services au chargement
    setTimeout(checkServiceStatus, 1000);

    // Ajouter des classes CSS pour les statuts
    const style = document.createElement('style');
    style.textContent = `
        .service-online::before {
            content: "🟢";
            margin-right: 8px;
        }
        .service-offline::before {
            content: "🔴";
            margin-right: 8px;
        }
    `;
    document.head.appendChild(style);

    console.log('Coach AI - Interface chargée avec succès!');
});