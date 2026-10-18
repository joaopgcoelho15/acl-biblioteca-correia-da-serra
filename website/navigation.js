(() => {
    const header = document.querySelector('.site-header');
    const toggle = header?.querySelector('.nav-toggle');
    if (!toggle) return;
    const mobile = matchMedia('(max-width: 700px)');
    const close = () => {
        header.classList.remove('nav-open');
        toggle.setAttribute('aria-expanded', 'false');
    };
    header.classList.add('has-navigation-toggle');
    toggle.hidden = false;
    toggle.addEventListener('click', () => {
        const open = toggle.getAttribute('aria-expanded') !== 'true';
        toggle.setAttribute('aria-expanded', String(open));
        header.classList.toggle('nav-open', open);
    });
    document.addEventListener('keydown', event => {
        if (event.key === 'Escape' && header.classList.contains('nav-open')) {
            close();
            toggle.focus();
        }
    });
    document.addEventListener('pointerdown', event => {
        if (!header.contains(event.target)) close();
    });
    mobile.addEventListener('change', close);
})();
