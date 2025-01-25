class IconCache {
    constructor() {
        this.cache = {};
        this.iconMappings = {
            "Soft": "/tyre-icons/soft.svg",
            "Super Soft": "/tyre-icons/super-soft.svg",
            "Medium": "/tyre-icons/medium.svg",
            "Hard": "/tyre-icons/hard.svg",
            "Intermediate": "/tyre-icons/intermediate.svg",
            "Wet": "/tyre-icons/wet.svg"
        };
        this.loadIcons();
    }

    async loadIcons() {
        const loadPromises = Object.entries(this.iconMappings).map(async ([key, url]) => {
            try {
                const response = await fetch(url);
                const svgText = await response.text();
                this.cache[key] = svgText;
                console.log("Successfully fetched icon", key);
            } catch (error) {
                console.error(`Failed to load icon for ${key}:`, error);
            }
        });
        await Promise.all(loadPromises);
    }

    createSVGElement(svgString) {
        const div = document.createElement('div');
        div.innerHTML = svgString.trim();
        div.firstChild.setAttribute('width', '25');
        div.firstChild.setAttribute('height', '25');
        div.firstChild.setAttribute('style', 'display: inline-block; vertical-align: middle;');
        return div.firstChild;
    }

    getIcon(key) {
        const icon = this.cache[key];
        return icon ? this.createSVGElement(icon) : null;
    }
}