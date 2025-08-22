class IconCache {
    constructor() {
        this.cache = {};
        this.iconMappings = {
            "Soft": "/tyre-icons/soft.svg",
            "Super Soft": "/tyre-icons/super-soft.svg",
            "Medium": "/tyre-icons/medium.svg",
            "Hard": "/tyre-icons/hard.svg",
            "Intermediate": "/tyre-icons/intermediate.svg",
            "Inters": "/tyre-icons/intermediate.svg",
            "Wet": "/tyre-icons/wet.svg"
        };
        this.loadIcons();
    }

    async loadIcons() {
        const loadPromises = Object.entries(this.iconMappings).map(async ([key, url]) => {
            try {
                const response = await fetch(url);
                if (!response.ok) {
                    throw new Error(`HTTP error! Status: ${response.status}`);
                }
                const svgText = await response.text();
                this.cache[key] = svgText;
                console.debug("Successfully fetched icon", key);
            } catch (error) {
                console.error(`Failed to load icon for ${key}:`, error);
            }
        });
        await Promise.all(loadPromises);
    }

    createSVGElement(svgString) {
        // Step 1: Create a temporary <div> element
        const div = document.createElement('div');

        // Step 2: Assign the provided SVG string to the innerHTML of the <div>
        // The `.trim()` ensures there are no leading/trailing whitespaces that might cause issues.
        div.innerHTML = svgString.trim();

        // Step 3: Use querySelector to locate the <svg> element within the parsed content
        // This is necessary because the SVG string might:
        // - Contain leading/trailing whitespace (making div.firstChild a text node).
        // - Be wrapped in other tags (e.g., <div><svg>...</svg></div>).
        const svgElement = div.querySelector('svg');

        // Step 4: Check if an <svg> element was found
        if (!svgElement) {
            // If no <svg> element is found, throw an error
            // This ensures the function fails gracefully if the input string is invalid.
            throw new Error('Invalid SVG string: No <svg> element found');
        }

        // Step 5: Modify the <svg> element's attributes
        // Set the width and height to 25 (or whatever size you prefer).
        svgElement.setAttribute('width', '25');
        svgElement.setAttribute('height', '25');

        // Add a style attribute for inline-block display and vertical alignment
        svgElement.setAttribute('style', 'display: inline-block; vertical-align: middle;');

        // Step 6: Return the <svg> element
        // This allows the caller to use the processed SVG element in their app.
        return svgElement;
    }

    getIcon(key) {
        const icon = this.cache[key];
        return icon ? this.createSVGElement(icon) : null;
    }
}
