class TyreDeltaToast {
    constructor(iconCache, timeout = 8000) {
        this.iconCache = iconCache;
        this.timeout = timeout;
        this.toastElement = document.getElementById('tyreDeltaToast');
        this.toast = null;
        this.initializeToast();
    }

    initializeToast() {
        this.toast = new bootstrap.Toast(this.toastElement, {
            delay: this.timeout,
            autohide: true
        });
    }

    show(data) {
        this.populateToastContent(data);
        this.toast.show();
    }

    hide() {
        this.toast.hide();
    }

    // Helper method to get the correct icon parameter
    getIconParam(tyreType) {
        return tyreType === 'Slick' ? 'Soft' : tyreType;
    }

    // Helper method to safely render icon
    renderIcon(tyreType) {
        const iconParam = this.getIconParam(tyreType);
        const icon = this.iconCache.getIcon(iconParam);

        // Handle different icon return types
        if (typeof icon === 'string') {
            return icon;
        } else if (icon && icon.outerHTML) {
            // SVG element
            return icon.outerHTML;
        } else if (icon && typeof icon.toString === 'function') {
            return icon.toString();
        }

        return ''; // fallback
    }

    populateToastContent(data) {
        // Populate delta cards
        const cardsContainer = document.getElementById('tyreDeltaCards');
        cardsContainer.innerHTML = '';

        data['tyre-delta-messages'].forEach((message, index) => {
            const card = this.createDeltaCard(message, index);
            cardsContainer.appendChild(card);
        });
    }

    createDeltaCard(message, index) {
        const col = document.createElement('div');
        col.className = 'col-md-6';

        const card = document.createElement('div');
        card.className = 'card tyre-delta-card';

        const cardBody = document.createElement('div');
        cardBody.className = 'card-body tyre-delta-card-body';

        // Left half - Icon section
        const iconSection = document.createElement('div');
        iconSection.className = 'tyre-delta-icon-section';

        const iconContainer = document.createElement('div');
        iconContainer.className = 'tyre-delta-icon-container';
        iconContainer.innerHTML = this.renderIcon(message['other-tyre-type']);

        iconSection.appendChild(iconContainer);

        // Right half - Content section
        const contentSection = document.createElement('div');
        contentSection.className = 'tyre-delta-content-section';

        // Tyre type name
        const tyreName = document.createElement('div');
        tyreName.className = 'tyre-delta-tyre-name';
        tyreName.textContent = message['other-tyre-type'];

        // Delta label
        const deltaLabel = document.createElement('div');
        deltaLabel.className = 'tyre-delta-label';
        deltaLabel.textContent = 'Time Delta';

        // Delta value
        const deltaValue = document.createElement('div');
        deltaValue.className = 'tyre-delta-value';
        const deltaSign = message['tyre-delta'] > 0 ? '+' : '';
        deltaValue.textContent = `${deltaSign}${message['tyre-delta'].toFixed(3)}s`;

        // Add color coding for delta
        if (message['tyre-delta'] > 0) {
            deltaValue.classList.add('tyre-delta-positive');
        } else if (message['tyre-delta'] < 0) {
            deltaValue.classList.add('tyre-delta-negative');
        } else {
            deltaValue.classList.add('tyre-delta-neutral');
        }

        contentSection.appendChild(tyreName);
        contentSection.appendChild(deltaLabel);
        contentSection.appendChild(deltaValue);

        cardBody.appendChild(iconSection);
        cardBody.appendChild(contentSection);
        card.appendChild(cardBody);
        col.appendChild(card);

        return col;
    }

    // Method to check if toast is currently showing
    isShowing() {
        return this.toastElement.classList.contains('show');
    }

    // Method to add event listeners
    onShow(callback) {
        this.toastElement.addEventListener('show.bs.toast', callback);
    }

    onHide(callback) {
        this.toastElement.addEventListener('hide.bs.toast', callback);
    }

    onShown(callback) {
        this.toastElement.addEventListener('shown.bs.toast', callback);
    }

    onHidden(callback) {
        this.toastElement.addEventListener('hidden.bs.toast', callback);
    }
}
