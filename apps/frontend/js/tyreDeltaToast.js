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
        // If there's already a toast showing, destroy it first
        if (this.toast && this.isShowing()) {
            this.destroyToast();
        }

        // Create a new toast instance
        this.initializeToast();

        // Populate content and show
        this.populateToastContent(data);
        this.toast.show();
    }

    hide() {
        if (this.toast) {
            this.toast.hide();
        }
    }

    destroyToast() {
        if (this.toast) {
            // Hide the toast immediately
            this.toast.hide();

            // Dispose of the Bootstrap toast instance
            this.toast.dispose();

            // Remove any Bootstrap classes that might be lingering
            this.toastElement.classList.remove('show', 'showing', 'hide');

            // Clear the toast reference
            this.toast = null;
        }
    }

    // Helper method to get the correct icon parameter
    getIconParam(tyreType) {
        return tyreType === 'Slick' ? 'Soft' : tyreType;
    }

    // Helper method to safely render icon
    renderIcon(tyreType, container) {
        const iconParam = this.getIconParam(tyreType);
        const icon = this.iconCache.getIcon(iconParam);

        // Clear existing content
        while (container.firstChild) {
            container.removeChild(container.firstChild);
        }

        // Handle different icon return types
        if (icon && icon.nodeType === Node.ELEMENT_NODE) {
            // SVG element - clone and append
            container.appendChild(icon.cloneNode(true));
        } else if (typeof icon === 'string') {
            // String content - create text node
            container.appendChild(document.createTextNode(icon));
        }
    }

    populateToastContent(data) {
        const messages = data['tyre-delta-messages'];

        // Populate up to 2 cards
        for (let i = 0; i < Math.min(messages.length, 2); i++) {
            const message = messages[i];
            const cardIndex = i + 1;

            // Get elements
            const iconContainer = document.getElementById(`iconContainer${cardIndex}`);
            const tyreName = document.getElementById(`tyreName${cardIndex}`);
            const deltaValue = document.getElementById(`deltaValue${cardIndex}`);

            // Set icon
            this.renderIcon(message['other-tyre-type'], iconContainer);

            // Set tyre name
            tyreName.textContent = message['other-tyre-type'];

            // Set delta value
            const deltaSign = message['tyre-delta'] > 0 ? '+' : '';
            deltaValue.textContent = `${deltaSign}${message['tyre-delta'].toFixed(3)}s`;

            // Remove existing color classes
            deltaValue.classList.remove('tyre-delta-positive', 'tyre-delta-negative', 'tyre-delta-neutral');

            // Add appropriate color class
            if (message['tyre-delta'] > 0) {
                deltaValue.classList.add('tyre-delta-positive');
            } else if (message['tyre-delta'] < 0) {
                deltaValue.classList.add('tyre-delta-negative');
            } else {
                deltaValue.classList.add('tyre-delta-neutral');
            }
        }
    }

    // Method to check if toast is currently showing
    isShowing() {
        return this.toastElement.classList.contains('show') ||
               this.toastElement.classList.contains('showing');
    }
}
