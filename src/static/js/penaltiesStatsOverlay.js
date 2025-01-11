class PenaltiesStatsWidget {
    constructor() {
      // Elements for displaying the penalties stats
      this.pitLaneSpeedLimitSpan = document.getElementById('pit-speed-limit');
      this.trackTempSpan = document.getElementById('track-temp');
      this.airTempSpan = document.getElementById('air-temp');
      this.trackLimitsWarningsSpan = document.getElementById('track-limits-warnings');
    }

    // Method to update the UI with the penalties stats
    update(penaltiesStats, gameYear) {
      // Update the individual penalty stats
      this.updatePenaltiesStats(penaltiesStats, gameYear);
    }

    // Method to update the penalties stats in the UI
    updatePenaltiesStats(pensStats, gameYear) {
      const airTemp = pensStats['air-temperature'];
      const trackTemp = pensStats['track-temperature'];
      const trackLimits = pensStats['corner-cutting-warnings'];

      // Set air and track temperature values or default to "---" if not available
      this.airTempSpan.textContent = (airTemp !== null && airTemp !== undefined) ? `${airTemp} °C` : "---";
      this.trackTempSpan.textContent = (trackTemp !== null && trackTemp !== undefined) ? `${trackTemp} °C` : "---";
      this.trackLimitsWarningsSpan.textContent = (trackLimits !== null && trackLimits !== undefined) ? trackLimits : "---";

      // Update Pit Lane Speed Limit
      const pitLaneSpeedLimit = pensStats['pit-speed-limit'];
      this.pitLaneSpeedLimitSpan.textContent = (pitLaneSpeedLimit !== null && pitLaneSpeedLimit !== undefined) ? pitLaneSpeedLimit : "--";

      // Ensure pit speed limit element is visible if there's a value
      this.pitLaneSpeedLimitSpan.style.display = (pitLaneSpeedLimit !== null && pitLaneSpeedLimit !== undefined) ? "inline-flex" : "none";
    }
  }

  // Usage:
  const penaltiesWidget = new PenaltiesStatsWidget('penaltiesStatsContainer');
  penaltiesWidget.update({
    'air-temperature': 25,
    'track-temperature': 30,
    'corner-cutting-warnings': 2,
    'pit-speed-limit': 80
  });
