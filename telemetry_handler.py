"""
MIT License

Copyright (c) 2024 Ashwin Natarajan

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

from telemetry_manager import F12023TelemetryManager
from f1_types import *
from packet_cap import F1PacketCapture
from overtake_analyzer import OvertakeAnalyzer, OvertakeAnalyzerMode
import telemetry_data as TelData
from threading import Lock
from enum import Enum
from typing import Optional, List, Tuple, Dict
from datetime import datetime
import os
import logging

class PacketCaptureMode(Enum):
    """Enum representing packet capture modes."""
    DISABLED = 'disabled'
    ENABLED = 'enabled'
    ENABLED_WITH_AUTOSAVE = 'enabled-with-autosave'

g_packet_capture_table = F1PacketCapture()
g_packet_capture_table_lock = Lock()
g_pkt_cap_mode = PacketCaptureMode.DISABLED
g_num_active_cars = 0
g_overtakes_history = []
g_overtakes_table_lock = Lock()
g_autosave_overtakes = False
g_directory_mapping = {}

class PktSaveStatus(Enum):
    """Enum representing packet save status."""
    SUCCESS = 0
    DISABLED = 1
    TABLE_EMPTY = 2
    OS_ERROR = 3
    OTHER = 4

    def __str__(self):
        return self.name

class GetOvertakesStatus(Enum):

    RACE_COMPLETED = 0
    RACE_ONGOING = 1
    NO_DATA = 2

    def __str__(self):
        return self.name

def initOvertakesAutosave(autosave_enabled: bool = False):
    global g_autosave_overtakes
    global g_overtakes_history
    global g_overtakes_table_lock
    g_autosave_overtakes = autosave_enabled
    g_overtakes_history = []
    g_overtakes_table_lock = Lock()

def initDirectories():

    def ensureDirectoryExists(directory: str) -> None:
        """
        Ensure that the specified directory exists. If it doesn't, create it along with any missing parent directories.

        Parameters:
        - directory (str): The path of the directory to be checked or created.

        Returns:
        - None
        """
        if not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
            logging.info(f"Directory '{directory}' created.")

    global g_directory_mapping
    ts_prefix = getTimestampStr()
    g_directory_mapping['overtakes'] = "data/" + ts_prefix + "/overtakes/"
    g_directory_mapping['race-info'] = "data/" + ts_prefix + "/race-info/"
    g_directory_mapping['packet-captures'] = "data/" + ts_prefix + "/packet-captures/"

    for directory in g_directory_mapping.values():
        ensureDirectoryExists(directory)


def initPktCap(packet_capture_mode: PacketCaptureMode):
    """
    Initialize packet capture.

    Parameters:
    - packet_capture_mode (PacketCaptureMode): The mode for packet capture.

    Returns:
    None
    """

    # global g_packet_capture_table
    # global g_packet_capture_table_lock
    global g_pkt_cap_mode
    # g_packet_capture_table = F1PacketCapture()
    # g_packet_capture_table_lock = Lock()
    g_pkt_cap_mode = packet_capture_mode

def addRawPacket(packet: List[bytes]):
    """
    Add raw packet to the packet capture table.

    Parameters:
    - packet (List[bytes]): The raw packet data.

    Returns:
    None
    """
    global g_packet_capture_table
    global g_packet_capture_table_lock
    with g_packet_capture_table_lock:
        g_packet_capture_table.add(packet)

def getTimestampStr() -> str:
    return datetime.now().strftime("%Y_%m_%d_%H_%M_%S")

def dumpPktCapToFile(file_name: Optional[str] = None, clear_db: bool = False, reason: str = '') -> Tuple[PktSaveStatus, str, int, int]:
    """
    Dump packet capture data to a file.

    Parameters:
    - file_name (Optional[str]): The name of the file to save. Default is None.
    - clear_db (bool): Whether to clear the packet capture database. Default is False.
    - reason (str): Reason for dumping the packet capture data.

    Returns:
    Tuple[PktSaveStatus, str, int, int]: A tuple representing the save status, file name, number of packets, and number of bytes.
    """
    global g_pkt_cap_mode

    if g_pkt_cap_mode == PacketCaptureMode.DISABLED:
        return PktSaveStatus.DISABLED, None, 0, 0

    global g_packet_capture_table
    global g_packet_capture_table_lock

    with g_packet_capture_table_lock:
        try:
            file_name, num_packets, num_bytes = g_packet_capture_table.dumpToFile(file_name)
            if clear_db:
                g_packet_capture_table.clear()
            if (file_name is not None) and (num_bytes > 0) and (num_packets > 0):
                print(
                    f"Dumped raw telemetry data. "
                    f"File Name: {file_name}, "
                    f"Number of Packets: {num_packets}, "
                    f"Number of Bytes: {num_bytes}, "
                    f"Clear DB: {str(clear_db)}, ",
                    f"Reason: {reason}"
                )
                return PktSaveStatus.SUCCESS, file_name, num_packets, num_bytes
            else:
                return PktSaveStatus.TABLE_EMPTY, None, 0, 0

        except Exception as e:
            # Log the exception
            print(f"An error occurred while dumping telemetry data: {e}")

            # Return the appropriate status
            return PktSaveStatus.OS_ERROR, None, 0, 0

def getOvertakeJSON() -> Tuple[GetOvertakesStatus, Dict]:
    """Get the JSON value containing key overtake information

    Returns:
        Tuple[GetOvertakesStatus, Dict]: Status, JSON value (may be empty)
    """
    _, _, _, _, _, _, _, _, final_classification_received = TelData.getGlobals()
    global g_overtakes_history
    global g_overtakes_table_lock
    with g_overtakes_table_lock:
        player_name = TelData.getPlayerName()
        if not final_classification_received:
            if len(g_overtakes_history) == 0:
                return GetOvertakesStatus.NO_DATA, {}
            else:
                return GetOvertakesStatus.RACE_ONGOING, OvertakeAnalyzer(
                    input_mode=OvertakeAnalyzerMode.INPUT_MODE_LIST,
                    input=g_overtakes_history).toJSON(
                        driver_name=player_name,
                        is_case_sensitive=True)
        else:
            return GetOvertakesStatus.RACE_COMPLETED, OvertakeAnalyzer(
                input_mode=OvertakeAnalyzerMode.INPUT_MODE_LIST,
                input=g_overtakes_history).toJSON(
                    driver_name=player_name,
                    is_case_sensitive=True)


def printOvertakeData(file_name: str=None):
    """Print the overtake data

    Args:
        file_name (str): Name of the csv file with the overtake data. If None, directly gets the data from the list
    """

    player_name = TelData.getPlayerName()
    if file_name:
        overtake_analyzer = OvertakeAnalyzer(
            input_mode=OvertakeAnalyzerMode.INPUT_MODE_FILE,
            input=file_name)
    else:
        global g_overtakes_history
        global g_overtakes_table_lock
        with g_overtakes_table_lock:
            overtake_analyzer = OvertakeAnalyzer(
                input_mode=OvertakeAnalyzerMode.INPUT_MODE_LIST,
                input=g_overtakes_history)
    print(overtake_analyzer.getFormattedString(driver_name=player_name, is_case_sensitive=True))

class F12023TelemetryHandler:
    """
    Handles incoming F1 2023 telemetry data. Handles the various types of incoming packets

    Attributes:
    - m_manager (F12023TelemetryManager): The telemetry manager instance.
    - m_raw_packet_capture (PacketCaptureMode): The raw packet capture mode.
    """

    def __init__(self, port: int, raw_packet_capture: PacketCaptureMode = PacketCaptureMode.DISABLED,
                 replay_server: bool = False) -> None:
        """
        Initialize F12023TelemetryHandler.

        Parameters:
        - port (int): The port number for telemetry.
        - raw_packet_capture (PacketCaptureMode): The mode for raw packet capture. Default is PacketCaptureMode.DISABLED.

        Returns:
        None
        """
        self.m_manager = F12023TelemetryManager(port, replay_server)
        self.m_raw_packet_capture = raw_packet_capture

    def run(self):
        """
        Run the telemetry handler.

        Returns:
        None
        """
        self.registerCallbacks()
        self.m_manager.run()

    def registerCallbacks(self) -> None:
        """
        Register callback functions for different types of telemetry packets.

        Returns:
        None
        """

        # self.m_manager.registerCallback(F1PacketType.MOTION, F12023TelemetryHandler.handleMotion)
        self.m_manager.registerCallback(F1PacketType.SESSION, F12023TelemetryHandler.handleSessionData)
        self.m_manager.registerCallback(F1PacketType.LAP_DATA, F12023TelemetryHandler.handleLapData)
        self.m_manager.registerCallback(F1PacketType.EVENT, F12023TelemetryHandler.handleEvent)
        self.m_manager.registerCallback(F1PacketType.PARTICIPANTS, F12023TelemetryHandler.handleParticipants)
        # self.m_manager.registerCallback(F1PacketType.CAR_SETUPS, F12023TelemetryHandler.handleCarSetups)
        self.m_manager.registerCallback(F1PacketType.CAR_TELEMETRY, F12023TelemetryHandler.handleCarTelemetry)
        self.m_manager.registerCallback(F1PacketType.CAR_STATUS, F12023TelemetryHandler.handleCarStatus)
        self.m_manager.registerCallback(F1PacketType.FINAL_CLASSIFICATION, F12023TelemetryHandler.handleFinalClassification)
        # self.m_manager.registerCallback(F1PacketType.LOBBY_INFO, F12023TelemetryHandler.handleLobbyInfo)
        self.m_manager.registerCallback(F1PacketType.CAR_DAMAGE, F12023TelemetryHandler.handleCarDamage)
        self.m_manager.registerCallback(F1PacketType.SESSION_HISTORY, F12023TelemetryHandler.handleSessionHistory)
        self.m_manager.registerCallback(F1PacketType.TYRE_SETS, F12023TelemetryHandler.handleTyreSets)
        # self.m_manager.registerCallback(F1PacketType.MOTION_EX, F12023TelemetryHandler.handleMotionEx)

        if self.m_raw_packet_capture != PacketCaptureMode.DISABLED:
            self.m_manager.registerRawPacketCallback(F12023TelemetryHandler.handleRawPacket)

    @staticmethod
    def handleRawPacket(packet: List[bytes]) -> None:
        """
        Handle raw telemetry packet.

        Parameters:
        - packet (List[bytes]): The raw telemetry packet.

        Returns:
        None
        """
        addRawPacket(packet)

    @staticmethod
    def handleMotion(packet: PacketMotionData) -> None:
        """
        Handle motion telemetry packet.

        Parameters:
        - packet (PacketMotionData): The motion telemetry packet.

        Returns:
        None
        """
        return

    @staticmethod
    def handleSessionData(packet: PacketSessionData) -> None:
        """
        Handle session data telemetry packet.

        Parameters:
        - packet (PacketSessionData): The session data telemetry packet.

        Returns:
        None
        """
        TelData.set_globals(
            circuit=str(packet.m_trackId),
            track_temp=packet.m_trackTemperature,
            event_type=str(packet.m_sessionType),
            total_laps=packet.m_totalLaps,
            safety_car_status=packet.m_safetyCarStatus,
            is_spectating=bool(packet.m_isSpectating),
            spectator_car_index=packet.m_spectatorCarIndex,
            weather_forecast_samples=packet.m_weatherForecastSamples,
            pit_speed_limit=packet.m_pitSpeedLimit)

        return

    @staticmethod
    def handleLapData(packet: PacketLapData) -> None:
        """
        Handle lap data telemetry packet.

        Parameters:
        - packet (PacketLapData): The lap data telemetry packet.

        Returns:
        None
        """
        # print('Received Lap Data Packet. ' + str(packet))
        # should_recompute_fastest_lap = False
        # global g_num_active_cars
        # num_active_cars = 0

        # # loop through each of the car's lap data
        # for index, lap_data in enumerate(packet.m_LapData):
        #     # not handling invalid laps as of now
        #     if lap_data.m_resultStatus == ResultStatus.INVALID:
        #         continue
        #     num_active_cars += 1
        #     data = TelData.DataPerDriver()
        #     data.m_position = lap_data.m_carPosition
        #     data.m_last_lap = F12023TelemetryHandler.millisecondsToMinutesSeconds(lap_data.m_lastLapTimeInMS) \
        #         if (lap_data.m_lastLapTimeInMS > 0) else "---"
        #     data.m_delta = lap_data.m_deltaToCarInFrontInMS
        #     data.m_delta_to_leader = lap_data.m_deltaToRaceLeaderInMS
        #     data.m_penalties = F12023TelemetryHandler.getPenaltyString(lap_data.m_penalties,
        #                         lap_data.m_numUnservedDriveThroughPens, lap_data.m_numUnservedStopGoPens)
        #     data.m_current_lap = lap_data.m_currentLapNum
        #     data.m_is_pitting = True if lap_data.m_pitStatus in \
        #             [LapData.PitStatus.PITTING, LapData.PitStatus.IN_PIT_AREA] else False
        #     data.m_num_pitstops = lap_data.m_numPitStops
        #     result_str_map = {
        #         ResultStatus.DID_NOT_FINISH : "DNF",
        #         ResultStatus.DISQUALIFIED : "DSQ",
        #         ResultStatus.RETIRED : "DNF"
        #     }
        #     data.m_dnf_status_code = result_str_map.get(lap_data.m_resultStatus, "")
        #     should_recompute_fastest_lap |= TelData.set_driver_data(index, data)

        # if should_recompute_fastest_lap:
        #     TelData.recompute_fastest_lap()
        # if g_num_active_cars != num_active_cars:
        #     g_num_active_cars = num_active_cars
        #     TelData.set_num_cars(num_active_cars)
        TelData.processLapDataUpdate(packet)

    @staticmethod
    def handleEvent(packet: PacketEventData) -> None:
        """Handle the Event packet

        Args:
            packet (PacketEventData): The parsed object containing the event data packet's contents
        """
        global g_overtakes_table_lock
        global g_overtakes_history
        global g_num_active_cars
        if packet.m_eventStringCode == PacketEventData.EventPacketType.BUTTON_STATUS:
            # explicitly handle this bullshit first because this just adds unnecessary load
            return
        elif packet.m_eventStringCode == PacketEventData.EventPacketType.FASTEST_LAP:
            # data = TelData.DataPerDriver()
            # data.m_best_lap = F12023TelemetryHandler.floatSecondsToMinutesSecondsMilliseconds(packet.mEventDetails.lapTime)
            # TelData.set_driver_data(packet.mEventDetails.vehicleIdx, data, is_fastest=True)
            TelData.processFastestLapUpdate(packet)
        elif packet.m_eventStringCode == PacketEventData.EventPacketType.SESSION_STARTED:
            g_num_active_cars = 0
            TelData.processSessionStarted()
            # Clear the list regardless of event type
            with g_overtakes_table_lock:
                g_overtakes_history.clear()
            print("Received SESSION_STARTED")
        elif packet.m_eventStringCode == PacketEventData.EventPacketType.RETIREMENT:
            # data = TelData.DataPerDriver()
            # data.m_dnf_status_code = True
            # TelData.set_driver_data(packet.mEventDetails.vehicleIdx, data)
            TelData.processRetirementEvent(packet)
        elif packet.m_eventStringCode == PacketEventData.EventPacketType.OVERTAKE:
            overtake_csv_str = TelData.getOvertakeString(packet.mEventDetails.overtakingVehicleIdx,
                                                        packet.mEventDetails.beingOvertakenVehicleIdx)
            if overtake_csv_str:
                with g_overtakes_table_lock:
                    # Experimental input sanitizer
                    if len(g_overtakes_history) > 0 and g_overtakes_history[-1] == overtake_csv_str:
                        print("not adding repeated overtake string " + overtake_csv_str)
                    else:
                        g_overtakes_history.append(overtake_csv_str)
        # elif packet.m_eventStringCode == PacketEventData.EventPacketType.SPEED_TRAP_TRIGGERED:
        #     name = TelData.getDriverNameByIndex(packet.mEventDetails.vehicleIdx)
        #     if name:
        #         print("Speed trap triggered for " + name + " Speed = " + str(packet.mEventDetails.speed))
        return

    @staticmethod
    def handleParticipants(packet: PacketParticipantsData) -> None:
        # print('Received Participants Packet. ' + str(packet))
        # for index, participant in enumerate(packet.m_participants):
        #     data = TelData.DataPerDriver()
        #     data.m_name = participant.m_name
        #     data.m_team = str(participant.m_teamId)
        #     data.m_is_player = True if (index == packet.m_header.m_playerCarIndex) else False
        #     data.m_telemetry_restrictions = participant.m_yourTelemetry
        #     TelData.set_driver_data(index, data)
        TelData.processParticipantsUpdate(packet)
        return

    @staticmethod
    def handleCarSetups(packet: PacketCarSetupData) -> None:
        # print('Received Car Setups Packet. ' + str(packet))
        return

    @staticmethod
    def handleCarTelemetry(packet: PacketCarTelemetryData) -> None:
        # print('Received Car Telemetry Packet. ' + str(packet))
        # for index, car_telemetry_data in enumerate(packet.m_carTelemetryData):
        #     driver_data = TelData.DataPerDriver()
        #     driver_data.m_drs_activated = bool(car_telemetry_data.m_drs)
        #     driver_data.m_tyre_inner_temp = \
        #             sum(car_telemetry_data.m_tyresInnerTemperature)/len(car_telemetry_data.m_tyresInnerTemperature)
        #     driver_data.m_tyre_surface_temp = \
        #             sum(car_telemetry_data.m_tyresSurfaceTemperature)/len(car_telemetry_data.m_tyresSurfaceTemperature)
        #     TelData.set_driver_data(index, driver_data)
        TelData.processCarTelemetryUpdate(packet)
        return

    @staticmethod
    def handleCarStatus(packet: PacketCarStatusData) -> None:

        # for index, car_status_data in enumerate(packet.m_carStatusData):
        #     data = TelData.DataPerDriver()
        #     data.m_ers_perc = (car_status_data.m_ersStoreEnergy/CarStatusData.max_ers_store_energy) * 100.0
        #     data.m_tyre_age = car_status_data.m_tyresAgeLaps
        #     data.m_tyre_compound_type = str(car_status_data.m_actualTyreCompound) + ' - ' + \
        #         str(car_status_data.m_visualTyreCompound)
        #     data.m_drs_allowed = bool(car_status_data.m_drsAllowed)
        #     data.m_drs_distance = bool(car_status_data.m_drsActivationDistance)

        #     TelData.set_driver_data(index, data)
        TelData.processCarStatusUpdate(packet)
        return

    @staticmethod
    def handleFinalClassification(packet: PacketFinalClassificationData) -> None:
        print('Received Final Classification Packet. ')
        TelData.processFinalClassificationUpdate(packet)

        # Perform the auto save stuff only for races
        _, _, event_type_str, _, _, _, _, _, _ = TelData.getGlobals()
        global g_overtakes_table_lock
        global g_directory_mapping
        if event_type_str in [str(SessionType.RACE), str(SessionType.RACE_2), str(SessionType.RACE_3)]:

            # Capture the packets if required
            global g_pkt_cap_mode
            if g_pkt_cap_mode == PacketCaptureMode.ENABLED_WITH_AUTOSAVE:
                event_str = TelData.getEventInfoStr()
                if event_str:
                    global g_directory_mapping
                    file_name = 'capture_' + event_str + '_' + datetime.now().strftime("%Y_%m_%d_%H_%M_%S") + '.bin'
                    file_name = g_directory_mapping["packet-captures"] + file_name
                    dumpPktCapToFile(file_name=file_name,reason='Final Classification')

            # Compute and display overtake stats
            event_str = TelData.getEventInfoStr()
            if event_str:
                global g_autosave_overtakes
                file_name=None
                if g_autosave_overtakes:
                    file_name = 'overtakes_history_' + event_str +  datetime.now().strftime("%Y_%m_%d_%H_%M_%S") + '.csv'
                    file_name = g_directory_mapping['overtakes'] + file_name
                    with open(file_name, 'w', encoding='utf-8') as file:
                        # Iterate through the list and write each string to the file
                        for line in g_overtakes_history:
                            file.write(line + '\n')  # Add a newline character after each line
                        print("Recorded overtakes to file " + file_name + ". Number of overtakes was " +
                            str(len(g_overtakes_history)))
                    # Analyze the overtake data and dump the output
                printOvertakeData(file_name)
        return

    @staticmethod
    def handleLobbyInfo(packet: PacketLobbyInfoData) -> None:
        # print('Received Lobby Info Packet. ' + str(packet))
        return

    @staticmethod
    def handleCarDamage(packet: PacketCarDamageData) -> None:
        # print('Received Car Damage Packet. ' + str(packet))
        # for index, car_damage in enumerate(packet.m_carDamageData):
        #     data = TelData.DataPerDriver()
        #     data.m_tyre_wear = sum(car_damage.m_tyresWear)/len(car_damage.m_tyresWear)
        #     TelData.set_driver_data(index, data)
        TelData.processCarDamageUpdate(packet)
        return

    @staticmethod
    def handleSessionHistory(packet: PacketSessionHistoryData) -> None:
        # print('Received Session History Packet. ' + str(packet))
        # Update the best time for this car
        # driver_data = TelData.DataPerDriver()
        # if (packet.m_bestLapTimeLapNum > 0) and (packet.m_bestLapTimeLapNum <= packet.m_numLaps):
        #     driver_data.m_best_lap = F12023TelemetryHandler.millisecondsToMinutesSeconds(
        #         packet.m_lapHistoryData[packet.m_bestLapTimeLapNum-1].m_lapTimeInMS)
        #     if (TelData.set_driver_data(packet.m_carIdx, driver_data)) is True:
        #         TelData.recompute_fastest_lap()
        TelData.processSessionHistoryUpdate(packet)
        return

    @staticmethod
    def handleTyreSets(packet: PacketTyreSetsData) -> None:
        # print('Received Tyre Sets Packet. ' + str(packet))

        # data = TelData.DataPerDriver()
        # data.m_tyre_life_remaining_laps = packet.m_tyreSetData[packet.m_fittedIdx].m_lifeSpan
        # TelData.set_driver_data(packet.m_carIdx, data)
        TelData.processTyreSetsUpdate(packet)
        return

    @staticmethod
    def handleMotionEx(packet: PacketMotionExData) -> None:
        # print('Received Motion Ex Packet. ' + str(packet))
        return

    @staticmethod
    def millisecondsToMinutesSeconds(milliseconds):
        if not isinstance(milliseconds, int):
            raise ValueError("Input must be an integer representing milliseconds")

        if milliseconds < 0:
            raise ValueError("Input must be a non-negative integer")

        total_seconds, milliseconds = divmod(milliseconds, 1000)
        minutes, seconds = divmod(total_seconds, 60)

        return f"{minutes:02}:{seconds:02}.{milliseconds:03}"

    @staticmethod
    def floatSecondsToMinutesSecondsMilliseconds(seconds):
        if not isinstance(seconds, float):
            raise ValueError("Input must be a float representing seconds")

        if seconds < 0:
            raise ValueError("Input must be a non-negative float")

        total_milliseconds = int(seconds * 1000)
        minutes, seconds = divmod(total_milliseconds // 1000, 60)
        milliseconds = total_milliseconds % 1000

        return f"{minutes:02}:{seconds:02}.{milliseconds:03}"

    @staticmethod
    def getPenaltyString(penalties_sec, num_dt, num_stop_go):
        if penalties_sec == 0 and num_dt == 0 and num_stop_go == 0:
            return ""
        penalty_string = "("
        started_filling = False
        if penalties_sec > 0:
            penalty_string += "+" + str(penalties_sec) + " sec"
            started_filling = True
        if num_dt > 0:
            if started_filling:
                penalty_string += " + "
            penalty_string += str(num_dt) + "DT"
            started_filling = True
        if num_stop_go:
            if started_filling:
                penalty_string += " + "
            penalty_string += str(num_stop_go) + "SG"
        penalty_string += ")"
        return penalty_string
