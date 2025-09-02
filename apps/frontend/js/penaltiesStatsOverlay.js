class PenaltiesStatsWidget {
  constructor() {
    // Elements for displaying the penalties stats
    this.pitLaneSpeedLimitSpan = document.getElementById('pit-speed-limit');
    this.trackTempSpan = document.getElementById('track-temp');
    this.airTempSpan = document.getElementById('air-temp');
    this.trackLimitsWarningsSpan = document.getElementById('track-limits-warnings');
    this.speedTrapSpan = document.getElementById('speed-trap-span');
    this.speedTrapDiv = document.getElementById('speed-trap-div');
  }

  // Method to update the UI with the penalties stats
  update(penaltiesStats, packetFormat) {
    // Update the individual penalty stats
    this.updatePenaltiesStats(penaltiesStats, packetFormat);
  }

  // Method to update the penalties stats in the UI
  updatePenaltiesStats(pensStats, packetFormat) {
    const airTemp = pensStats['air-temperature'];
    const trackTemp = pensStats['track-temperature'];
    const trackLimits = pensStats['corner-cutting-warnings'];
    const speedTrap = pensStats['speed-trap-record'];

    // Set air and track temperature values or default to "---" if not available
    this.airTempSpan.textContent = (airTemp !== null && airTemp !== undefined) ? `${airTemp} °C` : "---";
    this.trackTempSpan.textContent = (trackTemp !== null && trackTemp !== undefined) ? `${trackTemp} °C` : "---";
    this.trackLimitsWarningsSpan.textContent = (trackLimits !== null && trackLimits !== undefined) ? trackLimits : "---";

    // Update Pit Lane Speed Limit
    const pitLaneSpeedLimit = pensStats['pit-speed-limit'];
    this.pitLaneSpeedLimitSpan.textContent = (pitLaneSpeedLimit !== null && pitLaneSpeedLimit !== undefined) ? pitLaneSpeedLimit : "--";

    // Ensure pit speed limit element is visible if there's a value
    this.pitLaneSpeedLimitSpan.style.display = (pitLaneSpeedLimit !== null && pitLaneSpeedLimit !== undefined) ? "inline-flex" : "none";

    // speed trap support from F1 24 onwards
    if (packetFormat >= 2024) {
      this.speedTrapDiv.style.display = "";
      if (speedTrap !== null && speedTrap !== undefined && speedTrap !== 0.0) {
        this.speedTrapSpan.textContent = formatFloat(speedTrap);
      } else {
        this.speedTrapSpan.textContent = "---";
      }
    } else {
      this.speedTrapDiv.style.display = "none";
    }
  }
}

