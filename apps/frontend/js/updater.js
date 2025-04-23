/**
 * Checks if there's a newer version of the app available on GitHub
 * @param {string} currentVersion - The current app version (e.g. "1.0.0")
 * @param {function} callback - Callback function that receives the update information
 */
function checkForNewVersion(currentVersion, callback) {
    const repoApiUrl = 'https://api.github.com/repos/ashwin-nat/pits-n-giggles/releases/latest';

    fetch(repoApiUrl)
        .then(response => {
            if (!response.ok) {
                throw new Error(`GitHub API returned ${response.status}: ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            const latestVersion = data.tag_name;
            const isNewer = compareVersions(latestVersion, currentVersion) > 0;

            const updateInfo = {
                currentVersion: currentVersion,
                latestVersion: latestVersion,
                hasUpdate: isNewer,
                releaseUrl: data.html_url,
                releaseName: data.name,
                releaseDate: data.published_at,
                releaseNotes: data.body,
                assets: data.assets.map(asset => ({
                    name: asset.name,
                    size: asset.size,
                    downloadUrl: asset.browser_download_url,
                    contentType: asset.content_type,
                    downloadCount: asset.download_count
                }))
            };

            callback(null, updateInfo);
        })
        .catch(error => {
            callback(error, null);
        });
}

/**
 * Compare two version strings
 * @param {string} v1 - First version string (e.g. "1.2.3")
 * @param {string} v2 - Second version string (e.g. "1.3.0")
 * @returns {number} - 1 if v1 > v2, -1 if v1 < v2, 0 if equal
 */
function compareVersions(v1, v2) {
    const parts1 = v1.replace(/^v/, '').split('.').map(Number);
    const parts2 = v2.replace(/^v/, '').split('.').map(Number);

    // Compare each part of the version
    for (let i = 0; i < Math.max(parts1.length, parts2.length); i++) {
        const part1 = parts1[i] || 0;
        const part2 = parts2[i] || 0;

        if (part1 > part2) return 1;
        if (part1 < part2) return -1;
    }

    return 0; // Versions are equal
}