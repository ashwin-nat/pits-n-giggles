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

import csv
from collections import defaultdict
from typing import List, Tuple, Dict, Optional
from enum import Enum
from io import StringIO
import json

class OvertakeRecord:
    """
    Represents an overtake record in an F1 race.

    Attributes:
        m_overtaking_driver_name (str): The name of the driver overtaking.
        m_overtaking_driver_lap (int): The lap number when the overtaking occurred.
        m_overtaken_driver_name (str): The name of the driver being overtaken.
        m_overtaken_driver_lap (int): The lap number when the overtaken occurred.
        m_row_id (int): The row ID from the CSV file

    NOTE: The following comparisons based on row ID are supported. ==, <, >, <=, >=
    """

    def __init__(self, overtaking_driver_name: str, overtaking_driver_lap: int,
                overtaken_driver_name: str, overtaken_driver_lap: int, row_id: int) -> None:
        """
        Initialize an OvertakeRecord.

        Args:
            overtaking_driver_name (str): The name of the driver overtaking.
            overtaking_driver_lap (int): The lap number when the overtaking occurred.
            overtaken_driver_name (str): The name of the driver being overtaken.
            overtaken_driver_lap (int): The lap number when the overtaken occurred.
            row_id (int): The row ID from the CSV file
        """

        self.m_overtaking_driver_name: str = overtaking_driver_name
        self.m_overtaking_driver_lap: int = overtaking_driver_lap
        self.m_overtaken_driver_name: str = overtaken_driver_name
        self.m_overtaken_driver_lap: int = overtaken_driver_lap
        self.m_row_id: int = row_id

    def __eq__(self, other) -> bool:
        """
        Compare two OvertakeRecord objects for equality based on row ID.

        Args:
            other (OvertakeRecord): The object to compare.

        Returns:
            bool: True if the objects are equal, False otherwise.
        """
        if not isinstance(other, OvertakeRecord):
            return False

        return (
            self.m_overtaking_driver_name == other.m_overtaking_driver_name
            and self.m_overtaking_driver_lap == other.m_overtaking_driver_lap
            and self.m_overtaken_driver_name == other.m_overtaken_driver_name
            and self.m_overtaken_driver_lap == other.m_overtaken_driver_lap
            and self.m_row_id == other.m_row_id
        )

    def __lt__(self, other) -> bool:
        """
        Compare two OvertakeRecord objects based on m_row_id.

        Args:
            other (OvertakeRecord): The object to compare.

        Returns:
            bool: True if self is less than other, False otherwise.
        """
        return self.m_row_id < other.m_row_id

    def __gt__(self, other) -> bool:
        """
        Compare two OvertakeRecord objects based on m_row_id.

        Args:
            other (OvertakeRecord): The object to compare.

        Returns:
            bool: True if self is less than other, False otherwise.
        """
        return self.m_row_id > other.m_row_id

    def __le__(self, other) -> bool:
        """
        Compare two OvertakeRecord objects based on m_row_id.

        Args:
            other (OvertakeRecord): The object to compare.

        Returns:
            bool: True if self is less than other, False otherwise.
        """
        return self.m_row_id <= other.m_row_id

    def __ge__(self, other) -> bool:
        """
        Compare two OvertakeRecord objects based on m_row_id.

        Args:
            other (OvertakeRecord): The object to compare.

        Returns:
            bool: True if self is less than other, False otherwise.
        """
        return self.m_row_id >= other.m_row_id

    def __str__(self) -> str:

        return (
            "m_overtaking_driver_name=" + self.m_overtaking_driver_name + ", " +
            "m_overtaking_driver_lap=" + str(self.m_overtaking_driver_lap) + ", " +
            "m_overtaken_driver_name=" + self.m_overtaken_driver_name + ", " +
            "m_overtaken_driver_lap=" + str(self.m_overtaken_driver_lap) + ", " +
            "m_row_id=" + str(self.m_row_id)
        )

class OvertakeRivalryKey:

    def __init__(self, driver_1_name: str, driver_2_name: str) -> None:
        """
        Initialize an OvertakeRivalryPair instance with the given driver names.

        Args:
            driver_1_name (str): The name of the first driver.
            driver_2_name (str): The name of the second driver.
        """
        self.m_driver_1_name: str = driver_1_name
        self.m_driver_2_name: str = driver_2_name

    def __eq__(self, other: "OvertakeRivalryKey") -> bool:
        """
        Check if two rivalry pairs are equal, considering both orderings of driver names.

        Args:
            other (OvertakeRivalryPair): The other OvertakeRivalryPair instance to compare.

        Returns:
            bool: True if the rivalry pairs are equal, False otherwise.
        """
        return (
            (self.m_driver_1_name == other.m_driver_1_name and self.m_driver_2_name == other.m_driver_2_name) or
            (self.m_driver_1_name == other.m_driver_2_name and self.m_driver_2_name == other.m_driver_1_name)
        )

    def __hash__(self) -> int:
        """
        Generate a hash value for the OvertakeRivalryPair instance.

        Returns:
            int: Hash value.
        """
        # Use a frozenset to ensure order independence
        return hash(frozenset([self.m_driver_1_name, self.m_driver_2_name]))

    def __str__(self) -> str:
        """
        Get a string representation of the OvertakeRivalryPair instance.

        Returns:
            str: A string representation of the OvertakeRivalryPair.
        """
        return "(" + self.m_driver_1_name + ", " + self.m_driver_2_name + ")"

    def __contains__(self, player_name: str) -> bool:
        """
        Check if the given player name is present in the OvertakeRivalryKey.

        Args:
            player_name (str): The name of the player to check.

        Returns:
            bool: True if the player name is present, False otherwise.
        """
        return player_name in (self.m_driver_1_name, self.m_driver_2_name)

    def getDrivers(self) -> tuple[str, str]:
        """
        Get a tuple of the driver names in this object.

        Returns:
            tuple[str, str]: The first and the second driver's names.
        """
        return (self.m_driver_1_name, self.m_driver_2_name)

class OvertakeAnalyzerMode(Enum):
    """Represents how the OvertakeAnalyzer object will be initialized. Used to define whether the input is a file name,
           or the list of csv strings
    """

    INPUT_MODE_FILE=1,
    INPUT_MODE_LIST=2,

class OvertakeAnalyzer:
    """
    Class to analyze overtaking data from an F1 race.

    Attributes:
        m_file_name (str): The name of the CSV file containing overtaking data.
        m_overtaking_counts (Dict[str, int]): Dictionary to store the count of overtakes by each driver.
        m_being_overtaken_counts (Dict[str, int]): Dictionary to store the count of being overtaken by each driver.
        m_m_rivalry_records (Dict[OvertakeRivalryPair, List[OvertakeRecord]]):
                Dictionary to store the records of overtaking rivalry pairs.

    Methods:
        getMostOvertakes() -> Tuple[str, int]: Get the driver with the most overtakes and the count.
        getMostOvertaken() -> Tuple[str, int]: Get the driver who has been overtaken the most and the count.
        getMostHeatedRivalry() -> Tuple[Tuple[str, str], int, List[str]]:
            Get the most heated overtaking rivalry, its count, and details of each overtake involved.
        formatOvertakesInvolved(overtakes: List[str]) -> List[str]:
            Format overtakes details for display.
        toJSON() -> Dict. Returns a JSON dictionary containing the results of the above methods (except)
    """

    def __init__(self, input_mode: OvertakeAnalyzerMode, input: str):
        """
        Initialize OvertakeAnalyzer.

        Args:
            input_mode (OvertakeAnalyzerMode): Describes the type of input
            input (str): Context varies based on input_mode
                INPUT_MODE_LIST - This is a list of all overtakes in csv format
                INPUT_MODE_FILE - This is a JSON file containing all overtake records under the key
        """

        self.m_input_mode: OvertakeAnalyzerMode = input_mode
        self.m_overtaking_counts: Dict[str, int] = defaultdict(int)
        self.m_being_overtaken_counts: Dict[str, int] = defaultdict(int)
        self.m_rivalry_records: Dict[OvertakeRivalryKey, List[OvertakeRecord]] = defaultdict(list)
        if input_mode == OvertakeAnalyzerMode.INPUT_MODE_FILE:
            self.__analyzeFile(file_name=input)
        else:
            self.__analyzeCsvList(csv_list=input)

    def __analyzeFile(self, file_name) -> None:
        """
        Analyze overtaking data from the CSV file.
        """

        with open(file_name, 'r', encoding='utf-8') as file:
            data = json.load(file)
            # Check if "overtakes" key is present
            overtakes = data.get('overtakes', None)
            if not overtakes:
                raise ValueError('"overtakes" key is missing in the JSON.')

            # Check if "records" key is present and is a list
            records = overtakes.get('records', None)
            if not records or not isinstance(records, list):
                raise ValueError('"records" key is missing or is not a list in the JSON.')

            self.__analyze(data['overtakes']['records'], is_file=False)

    def __analyzeCsvList(self, csv_list: List[str]) -> None:
        """Parse and analyze the given CSV list into this object

        Args:
            csv_list (List[str]): The list of strings containing csv lines
        """

        csv_data_string = '\n'.join(csv_list)
        csv_data_file = StringIO(csv_data_string)
        self.__analyze(csv_data_file, is_file=False)

    def __analyze(self, data, is_file: bool) -> None:
        """
        Analyze overtaking data from either a file or a list of strings.

        Args:
            data: Either a file object or a string containing CSV data.
            is_file (bool): True if data is a file object, False if it's a string.
        """
        reader = csv.reader(data)
        # next(reader, None)  # Skip header row if present

        row_id = 0
        for row in reader:
            row = [s.strip() for s in row]
            if row in [[''],[]]: # don't process empty lines
                continue
            lap_overtaking, driver_overtaking, lap_being_overtaken, driver_being_overtaken = map(str.strip, row)

            lap_overtaking = int(lap_overtaking)
            lap_being_overtaken = int(lap_being_overtaken)

            # Record overtakes in both directions
            self.m_overtaking_counts[driver_overtaking] += 1
            self.m_being_overtaken_counts[driver_being_overtaken] += 1

            # Use the key type here since it supports bidirectional comparison
            rivalry_key = OvertakeRivalryKey(
                driver_1_name=driver_overtaking,
                driver_2_name=driver_being_overtaken)

            # Append the overtake into the rivalry table
            self.m_rivalry_records[rivalry_key].append(OvertakeRecord(
                    overtaking_driver_name=driver_overtaking,
                    overtaken_driver_lap=lap_overtaking,
                    overtaken_driver_name=driver_being_overtaken,
                    overtaking_driver_lap=lap_being_overtaken,
                    row_id=row_id))
            row_id += 1

    def getMostOvertakes(self) -> Tuple[List[str], int]:
        """
        Get the driver(s) with the most overtakes and their count.

        Returns:
            List[str]: List of driver names with the most overtakes.
            int: The number of overtakes
        """
        if not self.m_overtaking_counts:
            return [], 0

        max_overtakes = max(self.m_overtaking_counts.values())
        most_overtakes_drivers = [driver for driver, count in self.m_overtaking_counts.items() if count == max_overtakes]
        return most_overtakes_drivers, max_overtakes

    def getMostOvertaken(self) -> Tuple[List[str], int]:
        """
        Get the driver(s) who has been overtaken the most and their count.

        Returns:
            List[str]: List of driver names who have been overtaken the most.
            int: The number of overtakes
        """
        if not self.m_being_overtaken_counts:
            return [], 0

        max_overtaken = max(self.m_being_overtaken_counts.values())
        most_overtaken_drivers = [driver for driver, count in self.m_being_overtaken_counts.items() if count == max_overtaken]
        return most_overtaken_drivers, max_overtaken

    def getTotalNumberOfOvertakes(self) -> int:
        """Get the total number of overtakes occured in this race

        Returns:
            int: The overtakes count
        """
        # return sum(self.overtaking_counts.values()) // 2  # Each overtake is counted twice (for both drivers)
        return sum(self.m_overtaking_counts.values())

    def getMostHeatedRivalries(self,
                        driver_name: Optional[str] = None,
                        is_case_sensitive: Optional[bool] = True) -> Dict[OvertakeRivalryKey, List[OvertakeRecord]]:
        """
        Get the most heated overtaking rivalries and details of each overtake involved.

        Args:
            driver_name (str, optional): The driver's name to check involvement in most heated rivalries.
            is_case_sensitive (bool, optional): Whether the player name search must be case sensitive

        Returns:
            Dict[OvertakeRivalryPair, List[OvertakeRecord]]:
                A dictionary containing rivalries as keys and details of each overtake involved as values.
                Returns empty dictionary if the specified driver_name is invalid.
        """
        if not self.m_rivalry_records:
            return {}

        # Find the maximum length of overtaking rivalry records
        max_rivalry_len = max(len(rivalry_data) for rivalry_data in self.m_rivalry_records.values())

        # Create a dictionary of overtaking rivalry pairs and their records for the most heated rivalries
        rivalry_dict = {
            key: data
            for key, data in self.m_rivalry_records.items()
            if len(data) == max_rivalry_len
        }

        # If a specific driver is provided and not found in the most heated rivalries, filter to include the driver
        if driver_name is not None and driver_name not in rivalry_dict:
            str_compare = (lambda a, b: a == b) if is_case_sensitive else (lambda a, b: a.lower() == b.lower())
            filtered_rivalries = {
                key: data
                for key, data in self.m_rivalry_records.items()
                if any(
                    str_compare(overtake.m_overtaking_driver_name, driver_name)
                    or str_compare(overtake.m_overtaken_driver_name, driver_name)
                    for overtake in data
                )
            }

            # Check if there are any filtered rivalries
            if not filtered_rivalries:
                return {}

            # Find the maximum length of overtaking rivalry records among the filtered rivalries
            max_filtered_rivalry_len = max(len(rivalry_data) for rivalry_data in filtered_rivalries.values())

            # Filter further to include only the rivalries with the maximum number of elements
            filtered_rivalries = {
                key: data
                for key, data in filtered_rivalries.items()
                if len(data) == max_filtered_rivalry_len
            }

            return filtered_rivalries

        return rivalry_dict

    def toJSON(self,
            driver_name: Optional[str] = None,
            is_case_sensitive: Optional[bool] = False) -> Dict[str, dict]:
        """
        Generate a JSON dictionary containing information about the most overtakes,
        the most overtaken driver, and the most heated rivalry.

        Args:
            driver_name(str) - Name of the player if player specific info is required
            is_case_sensitive(bool) - Whether the player name search must be case sensitive

        Returns:
            Dict[str, dict]: JSON dictionary.
        """

        if not driver_name:
            most_overtakes_drivers, overtakes_count = self.getMostOvertakes()
            most_overtaken_driver, overtaken_count = self.getMostOvertaken()
            most_heated_rivalries = self.getMostHeatedRivalries()

            return {
                "number-of-overtakes": self.getTotalNumberOfOvertakes(),
                "most-overtakes": {"drivers": most_overtakes_drivers, "count": overtakes_count},
                "most-overtaken": {"drivers": most_overtaken_driver, "count": overtaken_count},
                "most-heated-rivalries": [
                    {
                        # Extracting data from rivalry_key
                        "driver1": rivalry_key.m_driver_1_name,
                        "driver2": rivalry_key.m_driver_2_name,
                        "overtakes": [
                            {
                                # Extracting data from each record in rivalry_data
                                "overtaking-driver-name": record.m_overtaking_driver_name,
                                "overtaking-driver-lap": record.m_overtaking_driver_lap,
                                "overtaken-driver-name": record.m_overtaken_driver_name,
                                "overtaken-driver-lap": record.m_overtaken_driver_lap,
                            }
                            for record in rivalry_data
                        ],
                    }
                    for rivalry_key, rivalry_data in most_heated_rivalries.items()
                ],
            }

        else:
            if driver_name not in self.m_overtaking_counts or driver_name not in self.m_being_overtaken_counts:
                return {}
            final_dict = {}
            final_dict["player-name"] = driver_name
            final_dict["number-of-overtakes"] = self.m_overtaking_counts[driver_name]
            final_dict["number-of-times-overtaken"] = self.m_being_overtaken_counts[driver_name]
            player_most_heated_rivalries = self.getMostHeatedRivalries(
                driver_name=driver_name,
                is_case_sensitive=is_case_sensitive)

            if player_most_heated_rivalries:
                final_dict["player-most-heated-rivalries"] = [
                    {
                        # Extracting data from rivalry_key
                        "driver1": rivalry_key.m_driver_1_name,
                        "driver2": rivalry_key.m_driver_2_name,
                        "overtakes": [
                            {
                                # Extracting data from each record in rivalry_data
                                "overtaking-driver-name": record.m_overtaking_driver_name,
                                "overtaking-driver-lap": record.m_overtaking_driver_lap,
                                "overtaken-driver-name": record.m_overtaken_driver_name,
                                "overtaken-driver-lap": record.m_overtaken_driver_lap,
                            }
                            for record in rivalry_data
                        ],
                    }
                    for rivalry_key, rivalry_data in player_most_heated_rivalries.items()
                ]
            else:
                final_dict["most-heated-rivalries"] = {}

            # final_dict["player-name"] = driver_name
            # final_dict["is-player-in-most-heated-rivalries"] = any(driver_name in key for key in most_heated_rivalries)
            # if not final_dict["is-player-in-most-heated-rivalries"]:
            #     # Get the dict including the player name
            #     player_most_heated_rivalries = self.getMostHeatedRivalries(
            #         driver_name=driver_name,
            #         is_case_sensitive=is_case_sensitive)
            #     if player_most_heated_rivalries:
            #         final_dict["player-most-heated-rivalries"] = [
            #             {
            #                 # Extracting data from rivalry_key
            #                 "driver1": rivalry_key.m_driver_1_name,
            #                 "driver2": rivalry_key.m_driver_2_name,
            #                 "overtakes": [
            #                     {
            #                         # Extracting data from each record in rivalry_data
            #                         "overtaking-driver-name": record.m_overtaking_driver_name,
            #                         "overtaking-driver-lap": record.m_overtaking_driver_lap,
            #                         "overtaken-driver-name": record.m_overtaken_driver_name,
            #                         "overtaken-driver-lap": record.m_overtaken_driver_lap,
            #                     }
            #                     for record in rivalry_data
            #                 ],
            #             }
            #             for rivalry_key, rivalry_data in player_most_heated_rivalries.items()
            #         ]
            #     else:
            #         final_dict["player-most-heated-rivalries"] = []

        return final_dict

    def formatOvertakesInvolved(self, overtakes: List[OvertakeRecord]) -> List[str]:
        """
        Format overtakes details for display.

        Args:
            overtakes (List[OvertakeRecord]): List of OvertakeRecord instances.

        Returns:
            List[str]: Formatted overtakes details.
        """
        formatted_overtakes = []
        for overtake in overtakes:
            lap_overtaking = overtake.m_overtaking_driver_lap
            driver_overtaking = overtake.m_overtaking_driver_name
            lap_being_overtaken = overtake.m_overtaken_driver_lap
            driver_being_overtaken = overtake.m_overtaken_driver_name

            if lap_overtaking == lap_being_overtaken:
                formatted_overtake = (
                    f"{driver_overtaking} overtook {driver_being_overtaken} "
                    f"in lap {lap_overtaking}"
                )
            else:
                formatted_overtake = (
                    f"{driver_overtaking} overtook {driver_being_overtaken} "
                    f"in lap {lap_overtaking} (lap {lap_being_overtaken} of {driver_being_overtaken})"
                )
            formatted_overtakes.append(formatted_overtake)
        return formatted_overtakes

    def getFormattedString(self,
            driver_name: Optional[str] = None,
            is_case_sensitive: Optional[bool] = True) -> str:
        """Returns a formatted string containing the overtakes info. Contains the following
                - Most overtakes
                - Most overtaken
                - Most heated rivalries
                - Specified driver's most heated rivalries

        Args:
            driver_name (str): Name of the specific driver whose overtake data is required. Defaults to None.
            is_case_sensitive (bool): Whether the name search must be case sensitive. Defaults to True.

        Returns:
            str: Formatted string representing the overtakes info.
        """

        final_str = ''
        total_overtakes = self.getTotalNumberOfOvertakes()
        most_overtakes_drivers, overtakes_count = self.getMostOvertakes()
        most_overtaken_drivers, overtaken_count = self.getMostOvertaken()

        final_str += ("=== Overtake Analysis ===\n" )
        final_str += (f"There were {total_overtakes} overtakes in this race!\n")
        final_str += (f"Driver(s) with the most overtakes: {most_overtakes_drivers} (Count: {overtakes_count})\n")
        final_str += (f"Driver(s) who has been overtaken the most: {most_overtaken_drivers} (Count: {overtaken_count})\n")

        final_str += ("Here are the most heated rivalries from the race\n")
        most_heated_rivalries = self.getMostHeatedRivalries()
        player_found = False
        for rivalry_key, rivalry_record in most_heated_rivalries.items():
            status, riv_str = self._getMostHeatedRivalryStr(rivalry_key, rivalry_record, driver_name, is_case_sensitive)
            final_str += riv_str
            player_found |= status

        if driver_name and not player_found:
            most_heated_rivalries_involving_player = self.getMostHeatedRivalries(driver_name, is_case_sensitive)
            final_str += ("These were your most heated rivalries\n")
            if not most_heated_rivalries_involving_player:
                final_str += ("Invalid player name. Not found in input data set\n")
            else:
                for rivalry_key, rivalry_record in most_heated_rivalries_involving_player.items():
                    _, riv_str = self._getMostHeatedRivalryStr(rivalry_key, rivalry_record, \
                        driver_name, is_case_sensitive)
                    final_str += riv_str

        return final_str

    def _getMostHeatedRivalryStr(self,
            rivalry_key: OvertakeRivalryKey,
            rivalry_record: List[OvertakeRecord],
            player_name: Optional[str] = None,
            is_case_sensitive: Optional[bool] = True) -> Tuple[bool, str]:

        """
        Returns details of the most heated rivalry in a formatted string.

        Args:
            rivalry_key (OvertakeRivalryPair): The rivalry key.
            rivalry_record (List[OvertakeRecord]): The list of overtaking records for the rivalry.
            player_name (str, optional): The name of the player to focus on.
            is_case_sensitive (bool, optional): Whether the player name check is case-sensitive. Default is True.

        Returns:
            bool: True if the player is involved in the rivalry, False otherwise.
            str: The formatted string
        """

        final_str = ''
        final_str += (f"    Most heated rivalry: {rivalry_key}, Count: {len(rivalry_record)}\n")
        final_str += ("    Overtakes involved:\n")
        formatted_overtakes = self.formatOvertakesInvolved(rivalry_record)
        for overtake in formatted_overtakes:
            final_str += ('        ' + overtake + '\n')
        final_str += ("\n")

        # Check if the player is involved in the rivalry
        if player_name:
            if is_case_sensitive:
                player_involved = player_name in rivalry_key.getDrivers()
            else:
                player_involved = player_name.lower() in [driver.lower() for driver in rivalry_key.getDrivers()]
            return player_involved, final_str

        return False, final_str

if __name__ == "__main__":
    import sys
    import argparse

    # Parse the command line args
    parser = argparse.ArgumentParser(description="Send captured F1 packets over TCP")
    parser.add_argument("--file-name", help="Name of the capture file")
    parser.add_argument("--driver-name", type=str, help="Name of the driver whose specific info is required")

    args = parser.parse_args()

    overtake_analyzer = OvertakeAnalyzer(OvertakeAnalyzerMode.INPUT_MODE_FILE, args.file_name)
    print(overtake_analyzer.getFormattedString(driver_name=args.driver_name))
