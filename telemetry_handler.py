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

from telemetry_manager import F12023TelemetryManager
from f1_types import *
import telemetry_data as TelData

num_active_cars = 0

class F12023TelemetryHandler:

    def __init__(self, port: int) -> None:
        self.m_manager = F12023TelemetryManager(port)

    @staticmethod
    def handleMotion(packet: PacketMotionData) -> None:
        # print('Received motion packet. ' + str(packet))
        return

    @staticmethod
    def handleSessionData(packet: PacketSessionData) -> None:

        TelData.set_globals(
            circuit=getTrackName(packet.m_trackId),
            track_temp=packet.m_trackTemperature,
            event_type=getSessionTypeName(packet.m_sessionType),
            total_laps=packet.m_totalLaps,
            safety_car_status=packet.m_safetyCarStatus,
            is_spectating=bool(packet.m_isSpectating),
            spectator_car_index=packet.m_spectatorCarIndex,
            weather_forecast_samples=packet.m_weatherForecastSamples)


        return

    @staticmethod
    def handleLapData(packet: PacketLapData) -> None:
        # print('Received Lap Data Packet. ' + str(packet))
        should_recompute_fastest_lap = False
        for index, lap_data in enumerate(packet.m_LapData):
            data = TelData.DataPerDriver()
            data.m_position = lap_data.m_carPosition
            data.m_last_lap = F12023TelemetryHandler.millisecondsToMinutesSeconds(lap_data.m_lastLapTimeInMS) \
                if (lap_data.m_lastLapTimeInMS > 0) else "---"
            data.m_delta = lap_data.m_deltaToCarInFrontInMS
            # data.m_delta = ("{:.3f}".format(lap_data.m_deltaToRaceLeaderInMS / 1000))
            data.m_penalties = F12023TelemetryHandler.getPenaltyString(lap_data.m_penalties,
                                lap_data.m_numUnservedDriveThroughPens, lap_data.m_numUnservedStopGoPens)
            data.m_current_lap = lap_data.m_currentLapNum
            data.m_is_pitting = True if lap_data.m_pitStatus in [1,2] else False
            data.m_num_pitstops = lap_data.m_numPitStops

            should_recompute_fastest_lap |= TelData.set_driver_data(index, data)

        if should_recompute_fastest_lap:
            TelData.recompute_fastest_lap()

        return

    @staticmethod
    def handleEvent(packet: PacketEventData) -> None:
        if packet.m_eventStringCode == EventPacketType.FASTEST_LAP:
            data = TelData.DataPerDriver()
            data.m_best_lap = F12023TelemetryHandler.floatSecondsToMinutesSecondsMilliseconds(packet.mEventDetails.lapTime)
            TelData.set_driver_data(packet.mEventDetails.vehicleIdx, data, is_fastest=True)
        elif packet.m_eventStringCode == EventPacketType.SESSION_STARTED:
            global num_active_cars
            num_active_cars = 0
            TelData.clear_all_driver_data()
            print("Received SESSION_STARTED")
        return

    @staticmethod
    def handleParticipants(packet: PacketParticipantsData) -> None:
        # print('Received Participants Packet. ' + str(packet))
        for index, participant in enumerate(packet.m_participants):
            data = TelData.DataPerDriver()
            data.m_name = participant.m_name
            data.m_team = getTeamName(participant.m_teamId)
            data.m_is_player = True if (index == packet.m_header.m_playerCarIndex) else False
            TelData.set_driver_data(index, data)
        global num_active_cars
        if num_active_cars != packet.m_numActiveCars:
            num_active_cars = packet.m_numActiveCars
            TelData.set_num_cars(num_active_cars)
        return

    @staticmethod
    def handleCarSetups(packet: PacketCarSetupData) -> None:
        # print('Received Car Setups Packet. ' + str(packet))
        return

    @staticmethod
    def handleCarTelemetry(packet: PacketCarTelemetryData) -> None:
        # print('Received Car Telemetry Packet. ' + str(packet))
        for index, car_telemetry_data in enumerate(packet.m_carTelemetryData):
            driver_data = TelData.DataPerDriver()
            driver_data.m_drs_activated = bool(car_telemetry_data.m_drs)
            TelData.set_driver_data(index, driver_data)
        return

    @staticmethod
    def handleCarStatus(packet: PacketCarStatusData) -> None:

        for index, car_status_data in enumerate(packet.m_carStatusData):
            data = TelData.DataPerDriver()
            data.m_ers_perc = (car_status_data.m_ersStoreEnergy / CarStatusData.max_ers_store_energy) * 100.0
            data.m_tyre_age = car_status_data.m_tyresAgeLaps
            # TODO: remove below
            # act_cmp_name = getActualTyreCompoundName(car_status_data.m_actualTyreCompound)
            # if act_cmp_name is None:
            #     act_cmp_name = "---"
            # vis_cmp_name = getVisualTyreCompoundName(car_status_data.m_visualTyreCompound)
            # if vis_cmp_name is None:
            #     vis_cmp_name = "---"
            # data.m_tyre_compound_type = act_cmp_name + ' - ' + vis_cmp_name
            data.m_tyre_compound_type = str(car_status_data.m_actualTyreCompound) + ' - ' + \
                str(car_status_data.m_visualTyreCompound)
            data.m_drs_allowed = bool(car_status_data.m_drsAllowed)
            data.m_drs_distance = bool(car_status_data.m_drsActivationDistance)

            TelData.set_driver_data(index, data)
        return

    @staticmethod
    def handleFinalClassification(packet: PacketFinalClassificationData) -> None:
        print('Received Final Classification Packet. ')
        return

    @staticmethod
    def handleLobbyInfo(packet: PacketLobbyInfoData) -> None:
        # print('Received Lobby Info Packet. ' + str(packet))
        return

    @staticmethod
    def handleCarDamage(packet: PacketCarDamageData) -> None:
        # print('Received Car Damage Packet. ' + str(packet))
        for index, car_damage in enumerate(packet.m_carDamageData):
            data = TelData.DataPerDriver()
            data.m_tyre_wear = sum(car_damage.m_tyresWear)/len(car_damage.m_tyresWear)
            TelData.set_driver_data(index, data)

        return

    @staticmethod
    def handleSessionHistory(packet: PacketSessionHistoryData) -> None:
        # print('Received Session History Packet. ' + str(packet))
        # Update the best time for this car
        driver_data = TelData.DataPerDriver()
        if (packet.m_bestLapTimeLapNum > 0) and (packet.m_bestLapTimeLapNum <= packet.m_numLaps):
            driver_data.m_best_lap = F12023TelemetryHandler.millisecondsToMinutesSeconds(
                packet.m_lapHistoryData[packet.m_bestLapTimeLapNum-1].m_lapTimeInMS)
            if (TelData.set_driver_data(packet.m_carIdx, driver_data)) is True:
                TelData.recompute_fastest_lap()

        return

    @staticmethod
    def handleTyreSets(packet: PacketTyreSetsData) -> None:
        # print('Received Tyre Sets Packet. ' + str(packet))
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

    def registerCallbacks(self):

        self.m_manager.registerCallback(F1PacketType.MOTION, F12023TelemetryHandler.handleMotion)
        self.m_manager.registerCallback(F1PacketType.SESSION, F12023TelemetryHandler.handleSessionData)
        self.m_manager.registerCallback(F1PacketType.LAP_DATA, F12023TelemetryHandler.handleLapData)
        self.m_manager.registerCallback(F1PacketType.EVENT, F12023TelemetryHandler.handleEvent)
        self.m_manager.registerCallback(F1PacketType.PARTICIPANTS, F12023TelemetryHandler.handleParticipants)
        self.m_manager.registerCallback(F1PacketType.CAR_SETUPS, F12023TelemetryHandler.handleCarSetups)
        self.m_manager.registerCallback(F1PacketType.CAR_TELEMETRY, F12023TelemetryHandler.handleCarTelemetry)
        self.m_manager.registerCallback(F1PacketType.CAR_STATUS, F12023TelemetryHandler.handleCarStatus)
        self.m_manager.registerCallback(F1PacketType.FINAL_CLASSIFICATION, F12023TelemetryHandler.handleFinalClassification)
        self.m_manager.registerCallback(F1PacketType.LOBBY_INFO, F12023TelemetryHandler.handleLobbyInfo)
        self.m_manager.registerCallback(F1PacketType.CAR_DAMAGE, F12023TelemetryHandler.handleCarDamage)
        self.m_manager.registerCallback(F1PacketType.SESSION_HISTORY, F12023TelemetryHandler.handleSessionHistory)
        self.m_manager.registerCallback(F1PacketType.TYRE_SETS, F12023TelemetryHandler.handleTyreSets)
        self.m_manager.registerCallback(F1PacketType.MOTION_EX, F12023TelemetryHandler.handleMotionEx)

    def run(self):

        self.registerCallbacks()
        self.m_manager.run()

# if __name__ == "__main__":
#     app = F12023TelemetryHandler(20777)
#     app.run()