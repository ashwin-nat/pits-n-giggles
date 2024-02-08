# MIT License
#
# Copyright (c) [year] [Your Name]
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

# ------------------ EVENT 0 - MOTION ------------------------------------------
lap_data_format_string = "<IIHBHBHHfffBBBBBBBBBBBBBBBHHB"
F1_23_LAP_DATA_PACKET_PER_CAR_LEN:int = struct.calcsize(lap_data_format_string)



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
def generate_packet_session_section_1_format_str(num_marshal_zones: int) -> str:

    format_str = "<"

    # First, the marshal zones
    for i in range(num_marshal_zones):
        format_str += marshal_zone_format_str

    # Then m_safetyCarStatus, m_networkGame, m_numWeatherForecastSamples
    format_str += "BBB"
    return format_str

def generate_packet_session_section_2_format_str(num_w_samples: int) -> str:

    format_str = "<"

    # First, the weather forecast samples
    for i in range(num_w_samples):
        format_str += weather_forecast_sample_format_str

    # Then the remainder of the packet



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
    B # uint8   - 0 = no safety car, 1 = full 2 = virtual, 3 = formation lap
    B # uint8   - 0 = offline, 1 = online
    B # uint8   - Number of weather forecast samples to follow


    # SECTION 2 ----------------------------------------------
    WeatherForecastSample m_weatherForecastSamples[56];   // Array of weather forecast samples
    uint8           m_forecastAccuracy;          // 0 = Perfect, 1 = Approximate
    uint8           m_aiDifficulty;              // AI Difficulty rating - 0-110
    uint32          m_seasonLinkIdentifier;      // Identifier for season - persists across saves
    uint32          m_weekendLinkIdentifier;     // Identifier for weekend - persists across saves
    uint32          m_sessionLinkIdentifier;     // Identifier for session - persists across saves
    uint8           m_pitStopWindowIdealLap;     // Ideal lap to pit on for current strategy (player)
    uint8           m_pitStopWindowLatestLap;    // Latest lap to pit on for current strategy (player)
    uint8           m_pitStopRejoinPosition;     // Predicted position to rejoin at (player)
    uint8           m_steeringAssist;            // 0 = off, 1 = on
    uint8           m_brakingAssist;             // 0 = off, 1 = low, 2 = medium, 3 = high
    uint8           m_gearboxAssist;             // 1 = manual, 2 = manual & suggested gear, 3 = auto
    uint8           m_pitAssist;                 // 0 = off, 1 = on
    uint8           m_pitReleaseAssist;          // 0 = off, 1 = on
    uint8           m_ERSAssist;                 // 0 = off, 1 = on
    uint8           m_DRSAssist;                 // 0 = off, 1 = on
    uint8           m_dynamicRacingLine;         // 0 = off, 1 = corners only, 2 = full
    uint8           m_dynamicRacingLineType;     // 0 = 2D, 1 = 3D
    uint8           m_gameMode;                  // Game mode id - see appendix
    uint8           m_ruleSet;                   // Ruleset - see appendix
    uint32          m_timeOfDay;                 // Local time of day - minutes since midnight
    uint8           m_sessionLength;             // 0 = None, 2 = Very Short, 3 = Short, 4 = Medium
// 5 = Medium Long, 6 = Long, 7 = Full
    uint8           m_speedUnitsLeadPlayer;             // 0 = MPH, 1 = KPH
    uint8           m_temperatureUnitsLeadPlayer;       // 0 = Celsius, 1 = Fahrenheit
    uint8           m_speedUnitsSecondaryPlayer;        // 0 = MPH, 1 = KPH
    uint8           m_temperatureUnitsSecondaryPlayer;  // 0 = Celsius, 1 = Fahrenheit
    uint8           m_numSafetyCarPeriods;              // Number of safety cars called during session
    uint8           m_numVirtualSafetyCarPeriods;       // Number of virtual safety cars called
    uint8           m_numRedFlagPeriods;                // Number of red flags called during session

'''

# ------------------ EVENT 2 - LAP DATA ----------------------------------------



'''
    I # uint32 - Last lap time in milliseconds
    I # uint32 - Current time around the lap in milliseconds
    H # uint16 - Sector 1 time in milliseconds
    B # uint8  - Sector 1 whole minute part
    H # uint16 - Sector 2 time in milliseconds
    B # uint8  - Sector 2 whole minute part
    H # uint16 - Time delta to car in front in milliseconds
    H # uint16 - Time delta to race leader in milliseconds
    f # float  - Distance vehicle is around current lap in metres - could be negative if line hasn't been crossed yet
    f # float  - Total distance travelled in session in metres - could be negative if line hasn't been crossed yet
    f # float  - Delta in seconds for safety car
    B # uint8  - Car race position
    B # uint8  - Current lap number
    B # uint8  - 0 = none, 1 = pitting, 2 = in pit area
    B # uint8  - Number of pit stops taken in this race
    B # uint8  - 0 = sector1, 1 = sector2, 2 = sector3
    B # uint8  - Current lap invalid - 0 = valid, 1 = invalid
    B # uint8  - Accumulated time penalties in seconds to be added
    B # uint8  - Accumulated number of warnings issued
    B # uint8  - Accumulated number of corner cutting warnings issued
    B # uint8  - Num drive through pens left to serve
    B # uint8  - Num stop go pens left to serve
    B # uint8  - Grid position the vehicle started the race in
    B # uint8  - Status of driver - 0 = in garage, 1 = flying lap 2 = in lap, 3 = out lap, 4 = on track
    B # uint8  - Result status - 0 = invalid, 1 = inactive, 2 = active 3 = finished, 4 = didnotfinish, 5 = disqualified
                                          // 6 = not classified, 7 = retired
    B # uint8  - Pit lane timing, 0 = inactive, 1 = active
    H # uint16 - If active, the current time spent in the pit lane in ms
    H # uint16 - Time of the actual pit stop in ms
    B # uint8  - Whether the car should serve a penalty at this stop
'''