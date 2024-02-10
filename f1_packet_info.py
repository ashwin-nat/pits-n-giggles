# MIT License
#
# Copyright (c) [2024] [Ashwin Natarajan]
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import struct
from typing import Tuple

# ------------------ COMMON HEADER ---------------------------------------------

header_format_string = "<HBBBBBQfIIBB"
F1_23_PACKET_HEADER_LEN: int = struct.calcsize(header_format_string)

'''
    H # packet format
    B # year
    B # major
    B # minor
    B # ver
    B # pktID
    Q # sessionID
    f # session time
    I # uint32
    I # uint32
    B # carIndex
    B # sec car index
'''

# ------------------ EVENT 0 - MOTION ------------------------------------------

motion_format_string = "<ffffffhhhhhhffffff"
F1_23_MOTION_PACKET_PER_CAR_LEN: int = struct.calcsize(motion_format_string)

'''
    f # float - World space X position - metres
    f # float - World space Y position
    f # float - World space Z position
    f # float - Velocity in world space X – metres/s
    f # float - Velocity in world space Y
    f # float - Velocity in world space Z
    h # int16 - World space forward X direction (normalised)
    h # int16 - World space forward Y direction (normalised)
    h # int16 - World space forward Z direction (normalised)
    h # int16 - World space right X direction (normalised)
    h # int16 - World space right Y direction (normalised)
    h # int16 - World space right Z direction (normalised)
    f # float - Lateral G-Force component
    f # float - Longitudinal G-Force component
    f # float - Vertical G-Force component
    f # float - Yaw angle in radians
    f # float - Pitch angle in radians
    f # float - Roll angle in radians
'''

# ------------------ EVENT 1 - SESSION------------------------------------------

marshal_zone_format_str = "<fb"
marshal_zone_packet_len = struct.calcsize(marshal_zone_format_str)
'''
    f # float - Fraction (0..1) of way through the lap the marshal zone starts
    b # int8  - -1 = invalid/unknown, 0 = none, 1 = green, 2 = blue, 3 = yellow
'''

weather_forecast_sample_format_str = "<BBBbbbbB"
weather_forecast_sample_packet_len = struct.calcsize(weather_forecast_sample_format_str)
'''
    B # uint8  -    0 = unknown, 1 = P1, 2 = P2, 3 = P3, 4 = Short P, 5 = Q1
                //  6 = Q2, 7 = Q3, 8 = Short Q, 9 = OSQ, 10 = R, 11 = R2
                //  12 = R3, 13 = Time Trial
    B # uint8  - Time in minutes the forecast is for
    B # uint8  - Weather - 0 = clear, 1 = light cloud, 2 = overcast
                        // 3 = light rain, 4 = heavy rain, 5 = storm
    b # int8   - Track temp. in degrees Celsius
    b # int8   - Track temp. change - 0 = up, 1 = down, 2 = no change
    b # int8   - Air temp. in degrees celsius
    b # int8   - Air temp. change - 0 = up, 1 = down, 2 = no change
    B # uint8  - Rain percentage (0-100)

'''

packet_session_section_0_format_str = ("<BbbbHBbBHHBBBBBB")
F1_23_SESSION_SECTION_0_PACKET_LEN = struct.calcsize(packet_session_section_0_format_str)

packet_session_section_2_format_str = "<BBB"
F1_23_SESSION_SECTION_2_PACKET_LEN = struct.calcsize(packet_session_section_2_format_str)

packet_session_section_4_format_str = ("<"
    "B" # uint8   - 0 = Perfect, 1 = Approximate
    "B" # uint8   - AI Difficulty rating - 0-110
    "I" # uint32  - Identifier for season - persists across saves
    "I" # uint32  - Identifier for weekend - persists across saves
    "I" # uint32  - Identifier for session - persists across saves
    "B" # uint8   - Ideal lap to pit on for current strategy (player)
    "B" # uint8   - Latest lap to pit on for current strategy (player)
    "B" # uint8   - Predicted position to rejoin at (player)
    "B" # uint8   -m_steeringAssist;            // 0 = off, 1 = on
    "B" # uint8   -       m_brakingAssist;             // 0 = off, 1 = low, 2 = medium, 3 = high
    "B" # uint8   -        m_gearboxAssist;             // 1 = manual, 2 = manual & suggested gear, 3 = auto
    "B" # uint8    -       m_pitAssist;                 // 0 = off, 1 = on
    "B" # uint8    -       m_pitReleaseAssist;          // 0 = off, 1 = on
    "B" # uint8    -       m_ERSAssist;                 // 0 = off, 1 = on
    "B" # uint8    -       m_DRSAssist;                 // 0 = off, 1 = on
    "B" # uint8    -       m_dynamicRacingLine;         // 0 = off, 1 = corners only, 2 = full
    "B" # uint8    -       m_dynamicRacingLineType;     // 0 = 2D, 1 = 3D
    "B" # uint8    -       m_gameMode;                  // Game mode id - see appendix
    "B" # uint8    -       m_ruleSet;                   // Ruleset - see appendix
    "I" # uint32   - Local time of day - minutes since midnight
    "B" # uint8    - m_sessionLength;             // 0 = None, 2 = Very Short, 3 = Short, 4 = Medium
                                                # // 5 = Medium Long, 6 = Long, 7 = Full
    "B" # uint8    -       m_speedUnitsLeadPlayer;             // 0 = MPH, 1 = KPH
    "B" # uint8    -       m_temperatureUnitsLeadPlayer;       // 0 = Celsius, 1 = Fahrenheit
    "B" # uint8    -       m_speedUnitsSecondaryPlayer;        // 0 = MPH, 1 = KPH
    "B" # uint8    -       m_temperatureUnitsSecondaryPlayer;  // 0 = Celsius, 1 = Fahrenheit
    "B" # uint8    -       m_numSafetyCarPeriods;              // Number of safety cars called during session
    "B" # uint8    -       m_numVirtualSafetyCarPeriods;       // Number of virtual safety cars called
    "B" # uint8    -       m_numRedFlagPeriods;                // Number of red flags called during session
)
F1_23_SESSION_SECTION_4_PACKET_LEN = struct.calcsize(packet_session_section_4_format_str)

'''
    # skipped header
    # SECTION 0 -------------------------------------------------
    B # uint8   - Weather - 0 = clear, 1 = light cloud, 2 = overcast
               // 3 = light rain, 4 = heavy rain, 5 = storm
    b # int8    - Track temp. in degrees celsius
    b # int8    - Air temp. in degrees celsius
    b # uint8   - Total number of laps in this race
    H # uint16  - Track length in metres
    B # uint8   - 0 = unknown, 1 = P1, 2 = P2, 3 = P3, 4 = Short P
                // 5 = Q1, 6 = Q2, 7 = Q3, 8 = Short Q, 9 = OSQ
                // 10 = R, 11 = R2, 12 = R3, 13 = Time Trial
    b # int8    - -1 for unknown, see appendix
    B # uint8   - Formula, 0 = F1 Modern, 1 = F1 Classic, 2 = F2,
                // 3 = F1 Generic, 4 = Beta, 5 = Supercars 6 = Esports, 7 = F2 2021
    H # uint16  - Time left in session in seconds
    H # uint16  - Session duration in seconds
    B # uint8   - Pit speed limit in kilometres per hour
    B # uint8   - Whether the game is paused - network game only
    B # uint8   - Whether the player is spectating
    B # uint8   - Index of the car being spectated
    B # uint8   - SLI Pro support, 0 = inactive, 1 = active
    B # uint8   - Number of marshal zones to follow



    # SECTION 1 ----------------------------------------------
    MarshalZone     m_marshalZones[21];             // List of marshal zones - max 21

    # SECTION 2 ----------------------------------------------
    B # uint8   - 0 = no safety car, 1 = full 2 = virtual, 3 = formation lap
    B # uint8   - 0 = offline, 1 = online
    B # uint8   - Number of weather forecast samples to follow


    # SECTION 3 ----------------------------------------------
    WeatherForecastSample m_weatherForecastSamples[56];   // Array of weather forecast samples



    # SECTION 4 ----------------------------------------------
    B # uint8   - 0 = Perfect, 1 = Approximate
    B # uint8   - AI Difficulty rating - 0-110
    I # uint32  - Identifier for season - persists across saves
    I # uint32  - Identifier for weekend - persists across saves
    I # uint32  - Identifier for session - persists across saves
    B # uint8   - Ideal lap to pit on for current strategy (player)
    B # uint8   - Latest lap to pit on for current strategy (player)
    B # uint8   - Predicted position to rejoin at (player)
    B # uint8   -m_steeringAssist;            // 0 = off, 1 = on
    B # uint8   -       m_brakingAssist;             // 0 = off, 1 = low, 2 = medium, 3 = high
    B # uint8   -        m_gearboxAssist;             // 1 = manual, 2 = manual & suggested gear, 3 = auto
    B # uint8    -       m_pitAssist;                 // 0 = off, 1 = on
    B # uint8    -       m_pitReleaseAssist;          // 0 = off, 1 = on
    B # uint8    -       m_ERSAssist;                 // 0 = off, 1 = on
    B # uint8    -       m_DRSAssist;                 // 0 = off, 1 = on
    B # uint8    -       m_dynamicRacingLine;         // 0 = off, 1 = corners only, 2 = full
    B # uint8    -       m_dynamicRacingLineType;     // 0 = 2D, 1 = 3D
    B # uint8    -       m_gameMode;                  // Game mode id - see appendix
    B # uint8    -       m_ruleSet;                   // Ruleset - see appendix
    I # uint32   - Local time of day - minutes since midnight
    B # uint8    - m_sessionLength;             // 0 = None, 2 = Very Short, 3 = Short, 4 = Medium
                                                // 5 = Medium Long, 6 = Long, 7 = Full
    B # uint8    -       m_speedUnitsLeadPlayer;             // 0 = MPH, 1 = KPH
    B # uint8    -       m_temperatureUnitsLeadPlayer;       // 0 = Celsius, 1 = Fahrenheit
    B # uint8    -       m_speedUnitsSecondaryPlayer;        // 0 = MPH, 1 = KPH
    B # uint8    -       m_temperatureUnitsSecondaryPlayer;  // 0 = Celsius, 1 = Fahrenheit
    B # uint8    -       m_numSafetyCarPeriods;              // Number of safety cars called during session
    B # uint8    -       m_numVirtualSafetyCarPeriods;       // Number of virtual safety cars called
    B # uint8    -       m_numRedFlagPeriods;                // Number of red flags called during session

'''

# ------------------ EVENT 2 - LAP DATA ----------------------------------------

lap_time_packet_format_str = ("<"
    "I" # uint32 - Last lap time in milliseconds
    "I" # uint32 - Current time around the lap in milliseconds
    "H" # uint16 - Sector 1 time in milliseconds
    "B" # uint8  - Sector 1 whole minute part
    "H" # uint16 - Sector 2 time in milliseconds
    "B" # uint8  - Sector 2 whole minute part
    "H" # uint16 - Time delta to car in front in milliseconds
    "H" # uint16 - Time delta to race leader in milliseconds
    "f" # float  - Distance vehicle is around current lap in metres - could be negative if line hasn't been crossed yet
    "f" # float  - Total distance travelled in session in metres - could be negative if line hasn't been crossed yet
    "f" # float  - Delta in seconds for safety car
    "B" # uint8  - Car race position
    "B" # uint8  - Current lap number
    "B" # uint8  - 0 = none, 1 = pitting, 2 = in pit area
    "B" # uint8  - Number of pit stops taken in this race
    "B" # uint8  - 0 = sector1, 1 = sector2, 2 = sector3
    "B" # uint8  - Current lap invalid - 0 = valid, 1 = invalid
    "B" # uint8  - Accumulated time penalties in seconds to be added
    "B" # uint8  - Accumulated number of warnings issued
    "B" # uint8  - Accumulated number of corner cutting warnings issued
    "B" # uint8  - Num drive through pens left to serve
    "B" # uint8  - Num stop go pens left to serve
    "B" # uint8  - Grid position the vehicle started the race in
    "B" # uint8  - Status of driver - 0 = in garage, 1 = flying lap 2 = in lap, 3 = out lap, 4 = on track
    "B" # uint8  - Result status - 0 = invalid, 1 = inactive, 2 = active 3 = finished, 4 = didnotfinish, 5 = disqualified
                  #                        // 6 = not classified, 7 = retired
    "B" # uint8  - Pit lane timing, 0 = inactive, 1 = active
    "H" # uint16 - If active, the current time spent in the pit lane in ms
    "H" # uint16 - Time of the actual pit stop in ms
    "B" # uint8  - Whether the car should serve a penalty at this stop
)
F1_23_LAP_DATA_PACKET_PER_CAR_LEN:int = struct.calcsize(lap_time_packet_format_str)

# ------------------ EVENT 4 - PARTICIPANTS ----------------------------------------
participant_format_string = ("<"
    "B" # uint8      m_aiControlled;      // Whether the vehicle is AI (1) or Human (0) controlled
    "B" # uint8      m_driverId;       // Driver id - see appendix, 255 if network human
    "B" # uint8      m_networkId;       // Network id – unique identifier for network players
    "B" # uint8      m_teamId;            // Team id - see appendix
    "B" # uint8      m_myTeam;            // My team flag – 1 = My Team, 0 = otherwise
    "B" # uint8      m_raceNumber;        // Race number of the car
    "B" # uint8      m_nationality;       // Nationality of the driver
    "48s" # char       m_name[48];          // Name of participant in UTF-8 format – null terminated
                                    # // Will be truncated with … (U+2026) if too long
    "B" # uint8      m_yourTelemetry;     // The player's UDP setting, 0 = restricted, 1 = public
    "B" # uint8      m_showOnlineNames;   // The player's show online names setting, 0 = off, 1 = on
    "B" # uint8      m_platform;          // 1 = Steam, 3 = PlayStation, 4 = Xbox, 6 = Origin, 255 = unknown
)
F1_23_PER_PARTICIPANT_INFO_LEN = struct.calcsize(participant_format_string)

# ------------------ EVENT 5 - CAR SETUPS ----------------------------------------
car_setups_format_string = ("<"
    "B" # uint8     m_frontWing;                // Front wing aero
    "B" # uint8     m_rearWing;                 // Rear wing aero
    "B" # uint8     m_onThrottle;               // Differential adjustment on throttle (percentage)
    "B" # uint8     m_offThrottle;              // Differential adjustment off throttle (percentage)
    "f" # float     m_frontCamber;              // Front camber angle (suspension geometry)
    "f" # float     m_rearCamber;               // Rear camber angle (suspension geometry)
    "f" # float     m_frontToe;                 // Front toe angle (suspension geometry)
    "f" # float     m_rearToe;                  // Rear toe angle (suspension geometry)
    "B" # uint8     m_frontSuspension;          // Front suspension
    "B" # uint8     m_rearSuspension;           // Rear suspension
    "B" # uint8     m_frontAntiRollBar;         // Front anti-roll bar
    "B" # uint8     m_rearAntiRollBar;          // Front anti-roll bar
    "B" # uint8     m_frontSuspensionHeight;    // Front ride height
    "B" # uint8     m_rearSuspensionHeight;     // Rear ride height
    "B" # uint8     m_brakePressure;            // Brake pressure (percentage)
    "B" # uint8     m_brakeBias;                // Brake bias (percentage)
    "f" # float     m_rearLeftTyrePressure;     // Rear left tyre pressure (PSI)
    "f" # float     m_rearRightTyrePressure;    // Rear right tyre pressure (PSI)
    "f" # float     m_frontLeftTyrePressure;    // Front left tyre pressure (PSI)
    "f" # float     m_frontRightTyrePressure;   // Front right tyre pressure (PSI)
    "f" # uint8     m_ballast;                  // Ballast
    "B" # float     m_fuelLoad;                 // Fuel load
)
F1_23_CAR_SETUPS_LEN = struct.calcsize(car_setups_format_string)

# ------------------ EVENT 6 - CAR TELEMETRY ----------------------------------------
# car_telemetry_format_string = ("<"
#     "H" # uint16    m_speed;                    // Speed of car in kilometres per hour
#     "f" # float     m_throttle;                 // Amount of throttle applied (0.0 to 1.0)
#     "f" # float     m_steer;                    // Steering (-1.0 (full lock left) to 1.0 (full lock right))
#     "f" # float     m_brake;                    // Amount of brake applied (0.0 to 1.0)
#     "f" # uint8     m_clutch;                   // Amount of clutch applied (0 to 100)
#     "b" # int8      m_gear;                     // Gear selected (1-8, N=0, R=-1)
#     "H" # uint16    m_engineRPM;                // Engine RPM
#     "B" # uint8     m_drs;                      // 0 = off, 1 = on
#     "B" # uint8     m_revLightsPercent;         // Rev lights indicator (percentage)
#     "H" # uint16    m_revLightsBitValue;        // Rev lights (bit 0 = leftmost LED, bit 14 = rightmost LED)
#     "4H" # uint16    m_brakesTemperature[4];     // Brakes temperature (celsius)
#     "4B" # uint8     m_tyresSurfaceTemperature[4]; // Tyres surface temperature (celsius)
#     "4B" # uint8     m_tyresInnerTemperature[4]; // Tyres inner temperature (celsius)
#     "H" # uint16    m_engineTemperature;        // Engine temperature (celsius)
#     "4f" # float     m_tyresPressure[4];         // Tyres pressure (PSI)
#     "4B" # uint8     m_surfaceType[4];           // Driving surface, see appendices
# )

car_telemetry_format_string = ("<"
    "H" # uint16    m_speed;                    // Speed of car in kilometres per hour
    "f" # float     m_throttle;                 // Amount of throttle applied (0.0 to 1.0)
    "f" # float     m_steer;                    // Steering (-1.0 (full lock left) to 1.0 (full lock right))
    "f" # float     m_brake;                    // Amount of brake applied (0.0 to 1.0)
    "B" # uint8     m_clutch;                   // Amount of clutch applied (0 to 100)
    "b" # int8      m_gear;                     // Gear selected (1-8, N=0, R=-1)
    "H" # uint16    m_engineRPM;                // Engine RPM
    "B" # uint8     m_drs;                      // 0 = off, 1 = on
    "B" # uint8     m_revLightsPercent;         // Rev lights indicator (percentage)
    "H" # uint16    m_revLightsBitValue;        // Rev lights (bit 0 = leftmost LED, bit 14 = rightmost LED)
    "4H" # uint16    m_brakesTemperature[4];     // Brakes temperature (celsius)
    "4B" # uint8     m_tyresSurfaceTemperature[4]; // Tyres surface temperature (celsius)
    "4B" # uint8     m_tyresInnerTemperature[4]; // Tyres inner temperature (celsius)
    "H" # uint16    m_engineTemperature;        // Engine temperature (celsius)
    "4f" # float     m_tyresPressure[4];         // Tyres pressure (PSI)
    "4B" # uint8     m_surfaceType[4];           // Driving surface, see appendices
)
F1_23_CAR_TELEMETRY_LEN = struct.calcsize(car_telemetry_format_string)

# ------------------ EVENT 7 - CAR STATUS ----------------------------------------

car_status_format_string = ("<"
    "B" # uint8       m_tractionControl;          // Traction control - 0 = off, 1 = medium, 2 = full
    "B" # uint8       m_antiLockBrakes;           // 0 (off) - 1 (on)
    "B" # uint8       m_fuelMix;                  // Fuel mix - 0 = lean, 1 = standard, 2 = rich, 3 = max
    "B" # uint8       m_frontBrakeBias;           // Front brake bias (percentage)
    "B" # uint8       m_pitLimiterStatus;         // Pit limiter status - 0 = off, 1 = on
    "f" # float       m_fuelInTank;               // Current fuel mass
    "f" # float       m_fuelCapacity;             // Fuel capacity
    "f" # float       m_fuelRemainingLaps;        // Fuel remaining in terms of laps (value on MFD)
    "H" # uint16      m_maxRPM;                   // Cars max RPM, point of rev limiter
    "H" # uint16      m_idleRPM;                  // Cars idle RPM
    "B" # uint8       m_maxGears;                 // Maximum number of gears
    "B" # uint8       m_drsAllowed;               // 0 = not allowed, 1 = allowed
    "H" # uint16      m_drsActivationDistance;    // 0 = DRS not available, non-zero - DRS will be available
                                            # // in [X] metres
    "B" # uint8       m_actualTyreCompound;       // F1 Modern - 16 = C5, 17 = C4, 18 = C3, 19 = C2, 20 = C1
                        #   // 21 = C0, 7 = inter, 8 = wet
                        #   // F1 Classic - 9 = dry, 10 = wet
                        #   // F2 – 11 = super soft, 12 = soft, 13 = medium, 14 = hard
                        #   // 15 = wet
    "B" # uint8       m_visualTyreCompound;       // F1 visual (can be different from actual compound)
                                            # // 16 = soft, 17 = medium, 18 = hard, 7 = inter, 8 = wet
                                            # // F1 Classic – same as above
                                            # // F2 ‘19, 15 = wet, 19 – super soft, 20 = soft
                                            # // 21 = medium , 22 = hard
    "B" # uint8       m_tyresAgeLaps;             // Age in laps of the current set of tyres
    "b" # int8        m_vehicleFiaFlags;       // -1 = invalid/unknown, 0 = none, 1 = green
                                            # // 2 = blue, 3 = yellow
    "f" # float       m_enginePowerICE;           // Engine power output of ICE (W)
    "f" # float       m_enginePowerMGUK;          // Engine power output of MGU-K (W)
    "f" # float       m_ersStoreEnergy;           // ERS energy store in Joules
    "B" # uint8       m_ersDeployMode;            // ERS deployment mode, 0 = none, 1 = medium
                        #   // 2 = hotlap, 3 = overtake
    "f" # float       m_ersHarvestedThisLapMGUK;  // ERS energy harvested this lap by MGU-K
    "f" # float       m_ersHarvestedThisLapMGUH;  // ERS energy harvested this lap by MGU-H
    "f" # float       m_ersDeployedThisLap;       // ERS energy deployed this lap
    "B" # uint8       m_networkPaused;            // Whether the car is paused in a network game
)
F1_23_CAR_STATUS_LEN = struct.calcsize(car_status_format_string)

# ------------------ EVENT 8 - FINAL CLASSIFICATION ----------------------------------------

final_classification_per_car_format_string = ("<"
    "B" # uint8     m_position;              // Finishing position
    "B" # uint8     m_numLaps;               // Number of laps completed
    "B" # uint8     m_gridPosition;          // Grid position of the car
    "B" # uint8     m_points;                // Number of points scored
    "B" # uint8     m_numPitStops;           // Number of pit stops made
    "B" # uint8     m_resultStatus;          // Result status - 0 = invalid, 1 = inactive, 2 = active
                                    #    // 3 = finished, 4 = didnotfinish, 5 = disqualified
                                    #    // 6 = not classified, 7 = retired
    "I" # uint32    m_bestLapTimeInMS;       // Best lap time of the session in milliseconds
    "d" # double    m_totalRaceTime;         // Total race time in seconds without penalties
    "B" # uint8     m_penaltiesTime;         // Total penalties accumulated in seconds
    "B" # uint8     m_numPenalties;          // Number of penalties applied to this driver
    "B" # uint8     m_numTyreStints;         // Number of tyres stints up to maximum
    "8B" # uint8     m_tyreStintsActual[8];   // Actual tyres used by this driver
    "8B" # uint8     m_tyreStintsVisual[8];   // Visual tyres used by this driver
    "8B" # uint8     m_tyreStintsEndLaps[8];  // The lap number stints end on
)
F1_23_FINAL_CLASSIFICATION_PER_CAR_LEN = struct.calcsize(final_classification_per_car_format_string)

# ------------------ EVENT 9 - LOBBY INFO ----------------------------------------

lobby_info_format_string = ("<"
    "B" # uint8     m_aiControlled;      // Whether the vehicle is AI (1) or Human (0) controlled
    "B" # uint8     m_teamId;            // Team id - see appendix (255 if no team currently selected)
    "B" # uint8     m_nationality;       // Nationality of the driver
    "B" # uint8     m_platform;          // 1 = Steam, 3 = PlayStation, 4 = Xbox, 6 = Origin, 255 = unknown
    "48s" # char      m_name[48];	  // Name of participant in UTF-8 format – null terminated
                                #    // Will be truncated with ... (U+2026) if too long
    "B" # uint8     m_carNumber;         // Car number of the player
    "B" # uint8     m_readyStatus;       // 0 = not ready, 1 = ready, 2 = spectating
)
F1_23_LOBBY_INFO_PER_PLAYER_LEN = struct.calcsize(lobby_info_format_string)

# ------------------ EVENT 10 - CAR DAMAGE ----------------------------------------

car_damage_packet_format_string = ("<"
    "4f" # float     m_tyresWear[4];                     // Tyre wear (percentage)
    "4B" # uint8     m_tyresDamage[4];                   // Tyre damage (percentage)
    "4B" # uint8     m_brakesDamage[4];                  // Brakes damage (percentage)
    "B" # uint8     m_frontLeftWingDamage;              // Front left wing damage (percentage)
    "B" # uint8     m_frontRightWingDamage;             // Front right wing damage (percentage)
    "B" # uint8     m_rearWingDamage;                   // Rear wing damage (percentage)
    "B" # uint8     m_floorDamage;                      // Floor damage (percentage)
    "B" # uint8     m_diffuserDamage;                   // Diffuser damage (percentage)
    "B" # uint8     m_sidepodDamage;                    // Sidepod damage (percentage)
    "B" # uint8     m_drsFault;                         // Indicator for DRS fault, 0 = OK, 1 = fault
    "B" # uint8     m_ersFault;                         // Indicator for ERS fault, 0 = OK, 1 = fault
    "B" # uint8     m_gearBoxDamage;                    // Gear box damage (percentage)
    "B" # uint8     m_engineDamage;                     // Engine damage (percentage)
    "B" # uint8     m_engineMGUHWear;                   // Engine wear MGU-H (percentage)
    "B" # uint8     m_engineESWear;                     // Engine wear ES (percentage)
    "B" # uint8     m_engineCEWear;                     // Engine wear CE (percentage)
    "B" # uint8     m_engineICEWear;                    // Engine wear ICE (percentage)
    "B" # uint8     m_engineMGUKWear;                   // Engine wear MGU-K (percentage)
    "B" # uint8     m_engineTCWear;                     // Engine wear TC (percentage)
    "B" # uint8     m_engineBlown;                      // Engine blown, 0 = OK, 1 = fault
    "B" # uint8     m_engineSeized;                     // Engine seized, 0 = OK, 1 = fault
)
F1_23_DAMAGE_PER_CAR_PACKET_LEN = struct.calcsize(car_damage_packet_format_string)

# ------------------ EVENT 11 - SESSION HISTORY ----------------------------------------
session_history_lap_history_data_format_string = ("<"
    "I" # uint32    m_lapTimeInMS;           // Lap time in milliseconds
    "H" # uint16    m_sector1TimeInMS;       // Sector 1 time in milliseconds
    "B" # uint8     m_sector1TimeMinutes;    // Sector 1 whole minute part
    "H" # uint16    m_sector2TimeInMS;       // Sector 2 time in milliseconds
    "B" # uint8     m_sector1TimeMinutes;    // Sector 2 whole minute part
    "H" # uint16    m_sector3TimeInMS;       // Sector 3 time in milliseconds
    "B" # uint8     m_sector3TimeMinutes;    // Sector 3 whole minute part
    "B" # uint8     m_lapValidBitFlags;      // 0x01 bit set-lap valid,      0x02 bit set-sector 1 valid
                                    #    // 0x04 bit set-sector 2 valid, 0x08 bit set-sector 3 valid
)
F1_23_SESSION_HISTORY_LAP_HISTORY_DATA_LEN = struct.calcsize(session_history_lap_history_data_format_string)

session_history_tyre_stint_format_string = ("<"
    "B" # uint8     m_endLap;                // Lap the tyre usage ends on (255 of current tyre)
    "B" # uint8     m_tyreActualCompound;    // Actual tyres used by this driver
    "B" # uint8     m_tyreVisualCompound;    // Visual tyres used by this driver
)
F1_23_SESSION_HISTORY_TYRE_STINT_LEN = struct.calcsize(session_history_tyre_stint_format_string)

session_history_format_string = ("<"
    "B" # uint8         m_carIdx;                   // Index of the car this lap data relates to
    "B" # uint8         m_numLaps;                  // Num laps in the data (including current partial lap)
    "B" # uint8         m_numTyreStints;            // Number of tyre stints in the data

    "B" # uint8         m_bestLapTimeLapNum;        // Lap the best lap time was achieved on
    "B" # uint8         m_bestSector1LapNum;        // Lap the best Sector 1 time was achieved on
    "B" # uint8         m_bestSector2LapNum;        // Lap the best Sector 2 time was achieved on
    "B" # uint8         m_bestSector3LapNum;        // Lap the best Sector 3 time was achieved on
)
F1_23_SESSION_HISTORY_LEN = struct.calcsize(session_history_format_string)

# ------------------ EVENT 12 - TYRE SETS ----------------------------------------
tyre_set_data_per_set_format_string = ("<"
    "B" # uint8     m_actualTyreCompound;    // Actual tyre compound used
    "B" # uint8     m_visualTyreCompound;    // Visual tyre compound used
    "B" # uint8     m_wear;                  // Tyre wear (percentage)
    "B" # uint8     m_available;             // Whether this set is currently available
    "B" # uint8     m_recommendedSession;    // Recommended session for tyre set
    "B" # uint8     m_lifeSpan;              // Laps left in this tyre set
    "B" # uint8     m_usableLife;            // Max number of laps recommended for this compound
    "h" # int16     m_lapDeltaTime;          // Lap delta time in milliseconds compared to fitted set
    "B" # uint8     m_fitted;                // Whether the set is fitted or not
)
F1_23_TYRE_SET_DATA_PER_SET_LEN = struct.calcsize(tyre_set_data_per_set_format_string)

# ------------------ EVENT 13 - MOTION EX ----------------------------------------

motion_ex_format_string = ("<"
    # // Extra player car ONLY data
    "4f" # float         m_suspensionPosition[4];       // Note: All wheel arrays have the following order:
    "4f" # float         m_suspensionVelocity[4];       // RL, RR, FL, FR
    "4f" # float         m_suspensionAcceleration[4];	// RL, RR, FL, FR
    "4f" # float         m_wheelSpeed[4];           	// Speed of each wheel
    "4f" # float         m_wheelSlipRatio[4];           // Slip ratio for each wheel
    "4f" # float         m_wheelSlipAngle[4];           // Slip angles for each wheel
    "4f" # float         m_wheelLatForce[4];            // Lateral forces for each wheel
    "4f" # float         m_wheelLongForce[4];           // Longitudinal forces for each wheel
    "f" # float         m_heightOfCOGAboveGround;      // Height of centre of gravity above ground
    "f" # float         m_localVelocityX;         	// Velocity in local space – metres/s
    "f" # float         m_localVelocityY;         	// Velocity in local space
    "f" # float         m_localVelocityZ;         	// Velocity in local space
    "f" # float         m_angularVelocityX;		// Angular velocity x-component – radians/s
    "f" # float         m_angularVelocityY;            // Angular velocity y-component
    "f" # float         m_angularVelocityZ;            // Angular velocity z-component
    "f" # float         m_angularAccelerationX;        // Angular acceleration x-component – radians/s/s
    "f" # float         m_angularAccelerationY;	// Angular acceleration y-component
    "f" # float         m_angularAccelerationZ;        // Angular acceleration z-component
    "f" # float         m_frontWheelsAngle;            // Current front wheels angle in radians
    "4f" # float         m_wheelVertForce[4];           // Vertical forces for each wheel
)
F1_23_MOTION_EX_PACKET_LEN = struct.calcsize(motion_ex_format_string)