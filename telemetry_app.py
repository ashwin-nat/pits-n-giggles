from telemetry_manager import F12023TelemetryManager
from f1_types import *

port = 20777

class F12023TelemetryApp:

    def __init__(self, port: int) -> None:
        self.m_manager = F12023TelemetryManager(port)

    @staticmethod
    def handleMotion(packet: PacketMotionData) -> None:
        # print('Received motion packet. ' + str(packet))
        return

    @staticmethod
    def handleSessionData(packet: PacketSessionData) -> None:
        print('Received Session Packet. ' + str(packet))
        return

    @staticmethod
    def handleLapData(packet: PacketLapData) -> None:
        # print('Received Lap Data Packet. ' + str(packet))
        return

    @staticmethod
    def handleEvent(packet: PacketEventData) -> None:
        # print('Received Event Packet. ' + str(packet))
        return

    @staticmethod
    def handleParticipants(packet: PacketParticipantsData) -> None:
        # print('Received Participants Packet. ' + str(packet))
        return

    @staticmethod
    def handleCarSetups(packet: PacketCarSetupData) -> None:
        # print('Received Car Setups Packet. ' + str(packet))
        return

    @staticmethod
    def handleCarTelemetry(packet: PacketCarTelemetryData) -> None:
        # print('Received Car Telemetry Packet. ' + str(packet))
        return

    @staticmethod
    def handleCarStatus(packet: PacketCarStatusData) -> None:
        # print('Received Car Status Packet. ' + str(packet))
        return

    @staticmethod
    def handleFinalClassification(packet: PacketFinalClassificationData) -> None:
        # print('Received Final Classification Packet. ' + str(packet))
        return

    @staticmethod
    def handleLobbyInfo(packet: PacketLobbyInfoData) -> None:
        # print('Received Lobby Info Packet. ' + str(packet))
        return

    @staticmethod
    def handleCarDamage(packet: PacketCarDamageData) -> None:
        # print('Received Car Damage Packet. ' + str(packet))
        return

    @staticmethod
    def handleSessionHistory(packet: PacketSessionHistoryData) -> None:
        # print('Received Session History Packet. ' + str(packet))
        return

    @staticmethod
    def handleTyreSets(packet: PacketTyreSetsData) -> None:
        # print('Received Tyre Sets Packet. ' + str(packet))
        return

    @staticmethod
    def handleMotionEx(packet: PacketMotionExData) -> None:
        # print('Received Motion Ex Packet. ' + str(packet))
        return

    def registerCallbacks(self):

        self.m_manager.registerCallback(F1PacketType.MOTION, F12023TelemetryApp.handleMotion)
        self.m_manager.registerCallback(F1PacketType.SESSION, F12023TelemetryApp.handleSessionData)
        self.m_manager.registerCallback(F1PacketType.LAP_DATA, F12023TelemetryApp.handleLapData)
        self.m_manager.registerCallback(F1PacketType.EVENT, F12023TelemetryApp.handleEvent)
        self.m_manager.registerCallback(F1PacketType.PARTICIPANTS, F12023TelemetryApp.handleParticipants)
        self.m_manager.registerCallback(F1PacketType.CAR_SETUPS, F12023TelemetryApp.handleCarSetups)
        self.m_manager.registerCallback(F1PacketType.CAR_TELEMETRY, F12023TelemetryApp.handleCarTelemetry)
        self.m_manager.registerCallback(F1PacketType.CAR_STATUS, F12023TelemetryApp.handleCarStatus)
        self.m_manager.registerCallback(F1PacketType.FINAL_CLASSIFICATION, F12023TelemetryApp.handleFinalClassification)
        self.m_manager.registerCallback(F1PacketType.LOBBY_INFO, F12023TelemetryApp.handleLobbyInfo)
        self.m_manager.registerCallback(F1PacketType.CAR_DAMAGE, F12023TelemetryApp.handleCarDamage)
        self.m_manager.registerCallback(F1PacketType.SESSION_HISTORY, F12023TelemetryApp.handleSessionHistory)
        self.m_manager.registerCallback(F1PacketType.TYRE_SETS, F12023TelemetryApp.handleTyreSets)
        self.m_manager.registerCallback(F1PacketType.MOTION_EX, F12023TelemetryApp.handleMotionEx)

    def run(self):

        self.registerCallbacks()
        self.m_manager.run()

if __name__ == "__main__":
    app = F12023TelemetryApp(port)
    app.run()