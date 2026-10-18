(() => {
    const form = document.querySelector(".filter-form[data-options-url]");
    if (!form) return;
    const query = form.querySelector('input[name="q"]');
    const indices = new Map();
    const mobile = matchMedia('(max-width: 900px)');
    const disclosure = document.querySelector('.filters-disclosure');
    if (disclosure) {
        disclosure.open = !mobile.matches;
        mobile.addEventListener('change', () => {
            if (opened) opened.close();
            disclosure.open = !mobile.matches;
        });
    }
    const normalize = value => value.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLocaleLowerCase();
    let timer, pending, opened;

    for (const select of form.querySelectorAll("select[data-search-label]")) {
        const wrapper = document.createElement("div");
        wrapper.className = "index-menu";
        const trigger = document.createElement("button");
        trigger.type = "button";
        trigger.className = `index-trigger ${select.className}`;
        trigger.textContent = (select.selectedOptions[0] || select.options[0]).textContent.trim();
        trigger.setAttribute("aria-haspopup", "listbox");
        trigger.setAttribute("aria-expanded", "false");
        trigger.id = `${select.id}-trigger`;
        const label = form.querySelector(`label[for="${select.id}"]`);
        label.htmlFor = trigger.id;
        label.id = `${select.id}-label`;
        trigger.setAttribute("aria-labelledby", `${label.id} ${trigger.id}`);
        const popup = document.createElement("dialog");
        popup.className = "index-popup";
        popup.hidden = true;
        popup.setAttribute('aria-labelledby', `${select.id}-popup-title`);
        const heading = document.createElement('div');
        heading.className = 'index-popup-heading';
        const title = document.createElement('strong');
        title.id = `${select.id}-popup-title`;
        title.textContent = label.textContent;
        const dismiss = document.createElement('button');
        dismiss.type = 'button';
        dismiss.className = 'index-dismiss';
        dismiss.textContent = '\u00d7';
        dismiss.setAttribute('aria-label', select.dataset.closeLabel);
        dismiss.title = select.dataset.closeLabel;
        heading.append(title, dismiss);
        const input = document.createElement("input");
        input.type = "search";
        input.autocomplete = "off";
        input.placeholder = select.dataset.searchPlaceholder;
        input.setAttribute("aria-label", select.dataset.searchLabel);
        input.setAttribute("role", "combobox");
        input.setAttribute("aria-autocomplete", "list");
        input.setAttribute("aria-expanded", "false");
        const list = document.createElement("div");
        list.id = `${select.id}-options`;
        list.className = "index-options";
        list.setAttribute("role", "listbox");
        if (select.multiple) list.setAttribute("aria-multiselectable", "true");
        list.setAttribute("aria-labelledby", label.id);
        input.setAttribute("aria-controls", list.id);
        trigger.setAttribute("aria-controls", list.id);
        const empty = document.createElement("em");
        empty.className = "index-empty";
        empty.textContent = select.dataset.emptyLabel;
        empty.setAttribute("role", "status");
        let rows = [], active = -1, renderedTerm = '';
        const activate = index => {
            rows.forEach(row => row.classList.remove("is-highlighted"));
            active = index;
            input.removeAttribute("aria-activedescendant");
            if (rows[index]) {
                rows[index].classList.add("is-highlighted");
                input.setAttribute("aria-activedescendant", rows[index].id);
                rows[index].scrollIntoView({block: "nearest"});
            }
        };
        const close = (focus = false) => {
            if (popup.open) popup.close();
            popup.hidden = true;
            list.replaceChildren();
            rows = [];
            active = -1;
            wrapper.classList.remove("is-open");
            trigger.setAttribute("aria-expanded", "false");
            input.setAttribute("aria-expanded", "false");
            input.removeAttribute("aria-activedescendant");
            if (opened === menu) opened = null;
            if (focus) trigger.focus();
            document.body.classList.toggle('index-modal-open', Boolean(document.querySelector('.index-popup[open][data-modal="true"]')));
        };
        dismiss.addEventListener('click', () => close(true));
        popup.addEventListener('cancel', event => {
            event.preventDefault();
            close(true);
        });
        popup.addEventListener('click', event => {
            if (event.target !== popup) return;
            const rect = popup.getBoundingClientRect();
            if (event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom) close(true);
        });
        const choose = option => {
            if (option.disabled) return;
            if (select.multiple) {
                if (!option.value) {
                    for (const item of select.options) item.selected = !item.value;
                } else {
                    option.selected = !option.selected;
                    select.options[0].selected = !Array.from(select.selectedOptions).some(item => item.value);
                }
                render();
                scheduleOptions();
                if (!mobile.matches || document.activeElement === input) input.focus();
                return;
            }
            select.value = option.value;
            close();
            select.dispatchEvent(new Event("change", {bubbles: true}));
        };
        const render = () => {
            const chosen = Array.from(select.selectedOptions).filter(option => option.value);
            const caption = chosen.length ? chosen.map(option => option.dataset.label || option.textContent.trim()).join("; ") : select.options[0].textContent.trim();
            trigger.textContent = mobile.matches && chosen.length > 1 ? `${chosen.length} ${select.dataset.selectedLabel}` : caption;
            trigger.title = caption;
            if (!select.multiple && chosen.length) trigger.textContent = chosen[0].textContent.trim();
            trigger.classList.toggle("has-value", chosen.length > 0);
            trigger.classList.toggle("is-default", chosen.length === 0);
            trigger.classList.toggle("has-missing-value", chosen.length === 1 && chosen[0].value === "_sem_valor");
            // Only build option rows for the open menu, not every hidden index.
            if (popup.hidden) return;
            const term = normalize(input.value.trim());
            const scroll = term === renderedTerm ? list.scrollTop : 0;
            renderedTerm = term;
            const fragment = document.createDocumentFragment();
            rows = [];
            let matches = 0;
            Array.from(select.options).forEach((option, index) => {
                if (term && !normalize(option.dataset.label || option.textContent).includes(term)) return;
                matches++;
                const row = document.createElement("div");
                row.className = "index-option";
                if (!option.value || option.value === "_sem_valor") row.classList.add("is-default");
                row.id = `${select.id}-option-${index}`;
                const optionLabel = document.createElement('span');
                optionLabel.className = 'index-option-label';
                optionLabel.textContent = option.dataset.label || option.textContent.trim();
                row.append(optionLabel);
                const count = option.textContent.trim().match(/\(\d+\/\d+\)$/);
                if (option.value && count) {
                    const counter = document.createElement('span');
                    counter.className = 'index-option-count';
                    counter.textContent = ` ${count[0]}`;
                    row.append(counter);
                }
                if (select.multiple && option.value) {
                    const checkbox = document.createElement("input");
                    checkbox.type = "checkbox";
                    checkbox.checked = option.selected;
                    checkbox.disabled = option.disabled;
                    checkbox.tabIndex = -1;
                    checkbox.setAttribute("aria-hidden", "true");
                    row.prepend(checkbox);
                }
                row.setAttribute("role", "option");
                row.setAttribute("aria-selected", String(option.selected));
                row.setAttribute("aria-disabled", String(option.disabled));
                row.addEventListener("click", () => choose(option));
                if (!option.disabled) rows.push(row);
                fragment.append(row);
            });
            list.replaceChildren(fragment);
            list.scrollTop = scroll;
            empty.hidden = matches > 0;
            active = -1;
            input.removeAttribute("aria-activedescendant");
        };
        const open = (text = "") => {
            if (opened) opened.close();
            opened = menu;
            input.value = text;
            popup.hidden = false;
            popup.dataset.modal = String(mobile.matches);
            wrapper.classList.add("is-open");
            trigger.setAttribute("aria-expanded", "true");
            input.setAttribute("aria-expanded", "true");
            render();
            if (mobile.matches) {
                popup.showModal();
                document.body.classList.add('index-modal-open');
                dismiss.focus({preventScroll:true});
            } else {
                popup.show();
                input.focus();
            }
        };
        const menu = {close, render, open};
        indices.set(select.name, menu);
        trigger.addEventListener("click", () => popup.hidden ? open() : close());
        trigger.addEventListener("keydown", event => {
            if (event.key === "ArrowDown" || event.key === "ArrowUp") {
                event.preventDefault();
                open();
                activate(event.key === "ArrowDown" ? 0 : rows.length - 1);
            } else if (event.key.length === 1 && event.key !== " " && !event.ctrlKey && !event.metaKey && !event.altKey) {
                event.preventDefault();
                open(event.key);
            }
        });
        input.addEventListener("input", render);
        input.addEventListener("keydown", event => {
            if (event.key === "Escape") { event.preventDefault(); close(true); }
            if (event.key === "ArrowDown" || event.key === "ArrowUp") {
                event.preventDefault();
                if (rows.length) activate(active < 0 ? (event.key === "ArrowDown" ? 0 : rows.length - 1) : (active + (event.key === "ArrowDown" ? 1 : -1) + rows.length) % rows.length);
            }
            if (event.key === "Enter") {
                event.preventDefault();
                if (rows[active]) rows[active].click();
                else if (rows.length === 1) rows[0].click();
            }
        });
        wrapper.addEventListener("focusout", event => {
            if (popup.open && popup.dataset.modal === 'true') return;
            if (!wrapper.contains(event.relatedTarget)) close();
        });
        popup.append(heading, input, list, empty);
        if (select.multiple) {
            const apply = document.createElement("button");
            apply.type = "button";
            apply.className = "index-apply";
            apply.textContent = mobile.matches ? select.dataset.doneLabel : select.dataset.applyLabel;
            // Keep the menu open when a browser does not focus clicked buttons.
            apply.addEventListener("pointerdown", event => event.preventDefault());
            apply.addEventListener("mousedown", event => event.preventDefault());
            apply.addEventListener("click", () => mobile.matches ? close(true) : form.requestSubmit());
            mobile.addEventListener('change', () => {
                apply.textContent = mobile.matches ? select.dataset.doneLabel : select.dataset.applyLabel;
                render();
            });
            popup.append(apply);
        }
        list.addEventListener("mousedown", event => event.preventDefault());
        wrapper.append(trigger, popup);
        select.after(wrapper);
        select.hidden = true;
        render();
    }
    document.addEventListener("pointerdown", event => {
        if (opened && !event.target.closest(".index-menu.is-open")) opened.close();
    });
    const requestedIndex = new URLSearchParams(location.search).get('index');
    if (indices.has(requestedIndex)) {
        if (disclosure) disclosure.open = true;
        indices.get(requestedIndex).open();
    }

    const fitViewport = () => {
        const viewport = window.visualViewport;
        document.documentElement.style.setProperty('--index-viewport-height', `${viewport?.height || innerHeight}px`);
        document.documentElement.style.setProperty('--index-viewport-top', `${viewport?.offsetTop || 0}px`);
    };
    fitViewport();
    window.visualViewport?.addEventListener('resize', fitViewport);
    window.visualViewport?.addEventListener('scroll', fitViewport);

    const imageDialog = document.createElement('dialog');
    imageDialog.className = 'catalog-image-dialog';
    const imageClose = document.createElement('button');
    imageClose.type = 'button';
    imageClose.className = 'index-dismiss';
    imageClose.textContent = '\u00d7';
    const enlarged = document.createElement('img');
    imageDialog.append(imageClose, enlarged);
    document.body.append(imageDialog);
    imageClose.addEventListener('click', () => imageDialog.close());
    imageDialog.addEventListener('click', event => {
        if (event.target === imageDialog) imageDialog.close();
    });
    for (const preview of document.querySelectorAll('.record-catalog-preview')) {
        preview.setAttribute('role', 'button');
        preview.setAttribute('aria-haspopup', 'dialog');
        preview.setAttribute('aria-label', preview.dataset.imageLabel);
        const showImage = () => {
            enlarged.src = preview.querySelector('img').src;
            enlarged.alt = preview.dataset.imageLabel;
            imageDialog.setAttribute('aria-label', preview.dataset.imageLabel);
            imageClose.setAttribute('aria-label', preview.dataset.closeLabel);
            imageClose.title = preview.dataset.closeLabel;
            imageDialog.showModal();
        };
        preview.addEventListener('click', showImage);
        preview.addEventListener('keydown', event => {
            if (event.key === 'Enter' || event.key === ' ') {
                event.preventDefault();
                showImage();
            }
        });
    }

    async function updateOptions() {
        const controller = new AbortController();
        pending = controller;
        const params = new URLSearchParams(new FormData(form));
        try {
            const response = await fetch(`${form.dataset.optionsUrl}?${params}`, {signal: controller.signal});
            if (!response.ok) return;
            const payload = await response.json();
            if (pending !== controller) return;
            for (const [name, options] of Object.entries(payload.options)) {
                const select = form.elements.namedItem(name);
                if (!(select instanceof HTMLSelectElement)) continue;
                const counts = new Map(options.map(option => [option.value, option]));
                for (const option of select.options) {
                    const match = counts.get(option.value);
                    if (!match) continue;
                    option.disabled = !match.available && !option.selected;
                    option.textContent = `${option.dataset.label} (${match.count}/${match.total})`;
                }
                indices.get(name)?.render();
            }
        } catch (error) {
            // Native GET submission remains available if live counts cannot load.
            if (error.name !== "AbortError") return;
        }
    }
    function scheduleOptions() {
        clearTimeout(timer);
        if (pending) pending.abort();
        timer = setTimeout(updateOptions, 350);
    }
    query.addEventListener("input", () => {
        query.classList.toggle("has-value", Boolean(query.value.trim()));
        scheduleOptions();
    });
    const lower = form.elements.namedItem("date_from");
    const upper = form.elements.namedItem("date_to");
    const error = form.querySelector(".period-error");
    const validatePeriod = () => {
        const invalid = lower.value && upper.value && Number(lower.value) > Number(upper.value);
        upper.setCustomValidity(invalid ? error.textContent : "");
        error.hidden = !invalid;
        return !invalid;
    };
    for (const field of [lower, upper]) field.addEventListener("input", () => {
        field.classList.toggle("has-value", Boolean(field.value));
        if (validatePeriod()) scheduleOptions();
    });
    form.addEventListener("submit", event => {
        if (!validatePeriod()) event.preventDefault();
    });
    validatePeriod();
})();
