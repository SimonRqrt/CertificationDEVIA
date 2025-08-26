(function() {
    // Attendre que Swagger/ReDoc ait rendu le DOM
    const onReady = (cb) => (document.readyState === 'loading') ? 
      document.addEventListener('DOMContentLoaded', cb) : cb();
  
    onReady(() => {
      // 1) Balises ARIA et landmarks
      const root = document.querySelector('body');
      if (root) root.setAttribute('role', 'document');
  
      // Swagger UI / ReDoc containers
      const main = document.querySelector('#swagger-ui') || document.querySelector('redoc');
      if (main) {
        main.setAttribute('role', 'main');
        main.setAttribute('aria-label', 'Documentation de l’API');
      }
  
      // 2) Boutons Try it out / Execute / Clear avec aria-label explicite
      const labelize = () => {
        document.querySelectorAll('button').forEach((btn) => {
          const txt = (btn.innerText || btn.textContent || '').trim().toLowerCase();
          if (!btn.getAttribute('aria-label')) {
            if (txt.includes('try it out')) btn.setAttribute('aria-label', 'Activer le formulaire interactif de cet endpoint');
            if (txt.includes('execute'))   btn.setAttribute('aria-label', 'Exécuter l’appel API avec les paramètres saisis');
            if (txt.includes('clear'))     btn.setAttribute('aria-label', 'Effacer les champs et la réponse');
            if (txt.includes('authorize')) btn.setAttribute('aria-label', 'Ouvrir la fenêtre d’authentification');
          }
        });
      };
      labelize();
  
      // 3) Focus visuel cohérent : si un élément reçoit le focus sans style, on lui ajoute une classe
      document.addEventListener('focusin', (e) => {
        const el = e.target;
        if (el && el.matches('a, button, input, select, textarea')) {
          el.classList.add('a11y-focused');
        }
      });
  
      // 4) Nav clavier : assurer un ordre logique (fallback)
      const anchors = Array.from(document.querySelectorAll('a, button, input, select, textarea'))
        .filter(el => !el.hasAttribute('disabled') && el.offsetParent !== null);
      anchors.forEach((el, i) => {
        if (!el.hasAttribute('tabindex')) el.setAttribute('tabindex', '0');
      });
  
      // 5) Observer mutations pour re-étiqueter les boutons rendus dynamiquement
      const obs = new MutationObserver(() => labelize());
      obs.observe(document.body, { childList: true, subtree: true });
    });
  })();
  