/**
 * Check whether a driver is still an active competitor (not DNF or DSQ).
 *
 * @param {Object} driver - A driver data object.
 * @returns {boolean} True if the driver is active.
 */
function _isActiveCar(driver) {
    const status = driver?.["driver-info"]?.["dnf-status"] ?? "";
    return status !== "DNF" && status !== "DSQ";
}

/**
 * Return a rival's effective delta-to-leader, adjusted if they are currently
 * in the pit lane.
 *
 * A rival's stored delta is a snapshot from when their data was last updated.
 * If they are mid-pit, their real gap is still growing. We estimate their gap
 * at pit exit by adding their remaining pit time loss.
 *
 * Example: rival is 5 s behind with 8 s of a 20 s pit already served.
 *   remaining = 12 s  →  effectiveDelta = 17 s.
 *
 * @param {Object} driver       - Rival driver data object.
 * @param {number} pitLossMs    - Total expected pit time loss in milliseconds.
 * @returns {number} Effective delta-to-leader in milliseconds.
 */
function _getRivalEffectiveDelta(driver, pitLossMs) {
    const pitInfo       = driver["pit-info"] ?? {};
    const rawDelta      = driver["delta-info"]["delta-to-leader"];
    const timerActive   = pitInfo["pit-lane-timer-active"] ?? false;

    if (!timerActive) {
        return rawDelta;
    }

    const timeSpentMs   = pitInfo["pit-lane-timer-ms"] ?? 0;
    const remainingMs   = Math.max(pitLossMs - timeSpentMs, 0);
    return rawDelta + remainingMs;
}

/**
 * Insert a predicted pit-rejoin position into each driver's data (mutates input).
 *
 * Handles two mid-pit scenarios:
 *
 *  1. Ref on track, rival pitting: the rival's effective delta is inflated by
 *     their remaining pit time so they are slotted behind their pit-exit
 *     position, not their stale on-track position.
 *
 *  2. Ref already pitting: only the *remaining* pit time loss
 *     (total − elapsed) is added to the ref's projected gap, so the
 *     prediction tightens in real time as the ref moves through the pit lane.
 *
 * DNF / DSQ cars are skipped during the rejoin-position search, because their
 * deltas are stale and they will never physically occupy a racing position.
 * They still receive a pit-rejoin-position value equal to their current
 * listed position (they don't move).
 *
 * @param {Object[]} drivers  - Full grid of driver data objects, sorted by
 *                              position (ascending). Each object must contain
 *                              at minimum:
 *                                "driver-info": { index, position, dnf-status }
 *                                "delta-info":  { delta-to-leader }
 *                                "tyre-info":   {}
 *                              and optionally:
 *                                "pit-info": { pit-lane-timer-active,
 *                                              pit-lane-timer-ms }
 * @param {number|null} pitLoss - Estimated pit stop time loss in **seconds**.
 *                                Pass null to skip all calculations.
 * @param {number} refIndex     - The `driver-info.index` value of the
 *                                reference (POV) driver.
 */
function insertRejoinPositions(drivers, pitLoss, refIndex) {
    if (pitLoss === null) {
        return;
    }

    // Convert pit loss to milliseconds to match the units used in delta fields.
    const pitLossMs = pitLoss * 1000;

    // Locate the reference driver row.
    const refDriver = drivers.find(d => d["driver-info"]["index"] === refIndex);
    if (!refDriver) {
        return;
    }

    // Compute how much pit time the ref car has already served (0 if not yet
    // in pits). Guard with pit-lane-timer-active so we don't accidentally use
    // a stale timer value from a previous stint.
    const refPitInfo            = refDriver["pit-info"] ?? {};
    const pitLaneTimerActive    = refPitInfo["pit-lane-timer-active"] ?? false;
    const timeAlreadyInPitMs    = pitLaneTimerActive
        ? (refPitInfo["pit-lane-timer-ms"] ?? 0)
        : 0;

    // Remaining time the ref car still has to spend in the pits.
    // Clamped to 0 so we never project a negative (beneficial) pit stop.
    const remainingPitLossMs    = Math.max(pitLossMs - timeAlreadyInPitMs, 0);

    // Projected gap to leader after pit exit, using only the remaining loss.
    const refDelta      = refDriver["delta-info"]["delta-to-leader"];
    const projectedGap  = refDelta + remainingPitLossMs;

    // Walk the field to find where the ref slots back in. We look for the
    // first active rival whose effective gap exceeds the ref's projected gap —
    // the ref rejoins just ahead of that car.
    let rejoinIndex         = null;
    let lastActiveIndex     = null;

    for (let i = 0; i < drivers.length; i++) {
        const rival = drivers[i];
        if (!_isActiveCar(rival) || rival === refDriver) {
            continue;
        }

        lastActiveIndex = i;

        const rivalEffectiveDelta = _getRivalEffectiveDelta(rival, pitLossMs);
        if (projectedGap < rivalEffectiveDelta) {
            rejoinIndex = Math.max(i - 1, 0);
            break;
        }
    }

    // No rival found with a larger gap — the ref rejoins behind the last
    // active car on track.
    if (rejoinIndex === null) {
        rejoinIndex = lastActiveIndex ?? 0;
    }

    // rejoinIndex is 0-based and points to the car the ref slots in behind.
    // +1 converts to 1-based positions, +1 again places the ref after that car.
    const rejoinPosition = rejoinIndex + 2;

    // For every driver that is NOT the ref, store their current position as
    // the rejoin estimate (they are unaffected by the ref's stop). For the
    // ref driver, store the computed rejoin position.
    //
    // DNF / DSQ cars keep whatever position they currently show.
    for (const driver of drivers) {
        if (driver === refDriver) {
            driver["tyre-info"]["pit-rejoin-position"] = rejoinPosition;
        } else {
            driver["tyre-info"]["pit-rejoin-position"] =
                driver["driver-info"]["position"];
        }
    }
}
