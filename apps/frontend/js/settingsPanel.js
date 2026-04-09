/**
 * Settings Panel Controller for the Driver View.
 *
 * Manages the slide-in settings panel with two tabs:
 *   - Columns: toggle race table column visibility via ColumnConfig
 *   - Display: general display preferences (delegated to ModalManager)
 */
class SettingsPanel {
    constructor() {
        this.panel = document.getElementById('settings-panel');
        this.config = new ColumnConfig();
        window.columnConfig = this.config;

        // Dynamic <style> element for column visibility CSS rules
        this.styleEl = document.createElement('style');
        this.styleEl.id = 'column-visibility-styles';
        document.head.appendChild(this.styleEl);

        this._initPanelToggle();
        this._initTabSwitching();
        this._populatePresets();
        this._populateToggles();
        this._initResetButton();
        this._initSaveButton();

        this.config.onChange(() => this._onConfigChange());
        this.config.checkAutoPreset();
        this._applyColumnVisibility();
    }

    // ── Panel open / close ───────────────────────────────────────────

    _initPanelToggle() {
        const panel = this.panel;

        document.getElementById('column-config-btn').addEventListener('click', (e) => {
            e.stopPropagation();
            this._switchTab('columns');
            panel.classList.toggle('open');
        });

        document.getElementById('settings-btn').addEventListener('click', (e) => {
            e.stopPropagation();
            this._switchTab('display');
            panel.classList.add('open');
            if (window.modalManager) window.modalManager.openSettingsModal();
        });

        document.getElementById('settings-panel-close-btn').addEventListener('click', () => {
            panel.classList.remove('open');
        });

        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') panel.classList.remove('open');
        });

        document.addEventListener('click', (e) => {
            if (panel.classList.contains('open') &&
                !panel.contains(e.target) &&
                !e.target.closest('#settings-btn') &&
                !e.target.closest('#column-config-btn')) {
                panel.classList.remove('open');
            }
        });
    }

    // ── Tabs ─────────────────────────────────────────────────────────

    _initTabSwitching() {
        this.panel.querySelectorAll('.panel-tab').forEach(tab => {
            tab.addEventListener('click', () => this._switchTab(tab.dataset.tab));
        });
    }

    _switchTab(tabName) {
        this.panel.querySelectorAll('.panel-tab').forEach(t =>
            t.classList.toggle('active', t.dataset.tab === tabName)
        );
        document.getElementById('tab-columns').style.display = tabName === 'columns' ? '' : 'none';
        document.getElementById('tab-display').style.display = tabName === 'display' ? '' : 'none';

        // Show the correct footer button per tab
        document.getElementById('reset-columns-btn').style.display = tabName === 'columns' ? '' : 'none';
        document.getElementById('saveSettings').style.display = tabName === 'display' ? '' : 'none';

        // Populate display settings when switching to the display tab
        if (tabName === 'display' && window.modalManager) {
            window.modalManager.openSettingsModal();
        }
    }

    // ── Presets ──────────────────────────────────────────────────────

    _populatePresets() {
        const container = document.getElementById('preset-buttons-container');
        container.textContent = '';

        ColumnConfig.PRESETS.forEach(preset => {
            const btn = document.createElement('button');
            btn.className = 'preset-btn' + (this.config.activePreset === preset.id ? ' active' : '');
            btn.dataset.presetId = preset.id;
            btn.innerHTML =
                `<span class="preset-emoji">${preset.emoji}</span>` +
                `<span class="preset-label">${preset.label}</span>`;
            btn.addEventListener('click', () => this.config.applyPreset(preset.id));
            container.appendChild(btn);
        });

        // Custom preset
        if (this.config.hasCustomPreset()) {
            const btn = document.createElement('button');
            btn.className = 'preset-btn' + (this.config.activePreset === 'custom' ? ' active' : '');
            btn.dataset.presetId = 'custom';
            btn.innerHTML =
                '<span class="preset-emoji">⭐</span>' +
                '<span class="preset-label">Custom</span>';
            btn.addEventListener('click', () => this.config.applyPreset('custom'));
            container.appendChild(btn);
        }

        // Save custom preset
        const saveContainer = document.getElementById('save-custom-preset-container');
        saveContainer.textContent = '';
        const saveBtn = document.createElement('button');
        saveBtn.className = 'save-custom-preset-btn';
        saveBtn.textContent = '\uD83D\uDCBE Save current as Custom';
        saveBtn.addEventListener('click', () => {
            this.config.saveCustomPreset();
            this._populatePresets();
            showToast('Custom preset saved');
        });
        saveContainer.appendChild(saveBtn);
    }

    // ── Column Toggles ──────────────────────────────────────────────

    _populateToggles() {
        const container = document.getElementById('column-toggles-container');
        container.textContent = '';

        ColumnConfig.COLUMN_GROUPS.forEach(group => {
            this._createToggle(container, group, false);
            if (group.children) {
                group.children.forEach(child => {
                    this._createToggle(container, child, true);
                });
            }
        });
    }

    _createToggle(container, item, isChild) {
        const div = document.createElement('div');
        div.className = 'column-toggle-item form-check form-switch' + (isChild ? ' ms-3' : '');

        const input = document.createElement('input');
        input.type = 'checkbox';
        input.className = 'form-check-input';
        input.id = 'col-toggle-' + item.id;
        input.checked = this.config.isUserEnabled(item.id);
        input.addEventListener('change', () => this.config.setUserVisible(item.id, input.checked));

        // Indeterminate state for parent groups with mixed children
        const parentGroup = ColumnConfig.COLUMN_GROUPS.find(g => g.id === item.id);
        if (parentGroup && parentGroup.children) {
            const state = this.config.getParentCheckState(item.id);
            input.indeterminate = state === 'indeterminate';
        }

        const label = document.createElement('label');
        label.className = 'form-check-label';
        label.htmlFor = input.id;
        label.textContent = item.label;

        div.appendChild(input);
        div.appendChild(label);
        container.appendChild(div);
    }

    // ── Reset ────────────────────────────────────────────────────────

    _initResetButton() {
        document.getElementById('reset-columns-btn').addEventListener('click', () => {
            this.config.resetToDefault();
            showToast('Columns reset to default');
        });
    }

    // ── Save display settings ────────────────────────────────────────

    _initSaveButton() {
        document.getElementById('saveSettings').addEventListener('click', () => {
            if (window.modalManager && window.modalManager.saveSettings()) {
                this.panel.classList.remove('open');
            }
        });
    }

    // ── Config change handler ────────────────────────────────────────

    _onConfigChange() {
        this._populatePresets();
        this._populateToggles();
        this._applyColumnVisibility();
    }

    // ── Column visibility via CSS ────────────────────────────────────

    _applyColumnVisibility() {
        const rules = [];
        ColumnConfig.COLUMN_GROUPS.forEach(group => {
            if (!this.config.isVisible(group.id)) {
                rules.push(
                    'th[data-col-group="' + group.id + '"], ' +
                    'td[data-col-group="' + group.id + '"] ' +
                    '{ display: none !important; }'
                );
            }
        });
        this.styleEl.textContent = rules.join('\n');
    }
}
