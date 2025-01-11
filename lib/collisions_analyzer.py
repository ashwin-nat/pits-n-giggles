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
from typing import List, Tuple, Dict, Optional, Any
from enum import Enum
from io import StringIO
import json

class CollisionRecord:
    """
    Represents an overtake record in an F1 race.

    Attributes:
        m_driver_1_name (str): The name of driver 1.
        m_driver_1_lap (int): The lap number of driver 1 when the collision occurred.
        m_driver_1_index (int): The index of driver 1 in the race.
        m_driver_2_name (str): The name of driver 2.
        m_driver_2_lap (int): The lap number of driver 2 when the collision occurred.
        m_driver_2_index (int): The index of driver 2 in the race.
        m_row_id (int): The row ID from the CSV file

    NOTE: The following comparisons based on row ID are supported. ==, <, >, <=, >=
    """

    @staticmethod
    def fromJSON(record: Dict[str, Any]) -> 'CollisionRecord':
        """
        Create an CollisionRecord object from a JSON object.

        Args:
            record (Dict[str, Any]): The JSON object to create the CollisionRecord from.

        Returns:
            CollisionRecord: The created CollisionRecord object.
        """

        return CollisionRecord(
            driver_1_name=record["driver-1-name"],
            driver_1_lap=record["driver-1-lap"],
            driver_1_index=record["driver-1-index"],
            driver_2_name=record["driver-2-name"],
            driver_2_lap=record["driver-2-lap"],
            driver_2_index=record["driver-2-index"],
            row_id=record["overtake-id"])


    def __init__(self, driver_1_name: str, driver_1_lap: int, driver_1_index: int,
                driver_2_name: str, driver_2_lap: int, driver_2_index: int,
                row_id: Optional[int] = None) -> None:
        """
        Initialize an CollisionRecord.

        Args:
            driver_1_name (str): The name of driver 1.
            driver_1_lap (int): The lap number of driver 1 when the collision occurred.
            driver_1_index (int): The index of driver 1 in the race.
            driver_2_name (str): The name of driver 2.
            driver_2_lap (int): The lap number of driver 2 when the collision occurred.
            driver_2_index (int): The index of driver 2 in the race.
            row_id (int): The row ID from the CSV file (optional, defaults to None)
        """

        self.m_driver_1_name: str   = driver_1_name
        self.m_driver_1_lap: int    = driver_1_lap
        self.m_driver_1_index: int  = driver_1_index
        self.m_driver_2_name: str   = driver_2_name
        self.m_driver_2_lap: int    = driver_2_lap
        self.m_driver_2_index: int  = driver_2_index
        self.m_row_id: int = row_id

    def __eq__(self, other) -> bool:
        """
        Compare two CollisionRecord objects for equality based on row ID.

        Args:
            other (CollisionRecord): The object to compare.

        Returns:
            bool: True if the objects are equal, False otherwise.
        """
        if not isinstance(other, CollisionRecord):
            return False

        if self.m_row_id is not None and other.m_row_id is not None:
            row_id_equal = (self.m_row_id == other.m_row_id)
        else:
            row_id_equal = True

        return (
            self.m_driver_1_name == other.m_driver_1_name
            and self.m_driver_1_index == other.m_driver_1_index
            and self.m_driver_1_lap == other.m_driver_1_lap
            and self.m_driver_2_name == other.m_driver_2_name
            and self.m_driver_2_index == other.m_driver_2_index
            and self.m_driver_2_lap == other.m_driver_2_lap
            and row_id_equal
        )
    def __lt__(self, other: "CollisionRecord") -> bool:
        """
        Compare two CollisionRecord objects based on m_row_id.

        Args:
            other (CollisionRecord): The object to compare.

        Returns:
            bool: True if self is less than other, False otherwise.
        """
        return self.m_row_id < other.m_row_id

    def __gt__(self, other: "CollisionRecord") -> bool:
        """
        Compare two CollisionRecord objects based on m_row_id.

        Args:
            other (CollisionRecord): The object to compare.

        Returns:
            bool: True if self is less than other, False otherwise.
        """
        return self.m_row_id > other.m_row_id

    def __le__(self, other: "CollisionRecord") -> bool:
        """
        Compare two CollisionRecord objects based on m_row_id.

        Args:
            other (CollisionRecord): The object to compare.

        Returns:
            bool: True if self is less than other, False otherwise.
        """
        return self.m_row_id <= other.m_row_id

    def __ge__(self, other: "CollisionRecord") -> bool:
        """
        Compare two CollisionRecord objects based on m_row_id.

        Args:
            other (CollisionRecord): The object to compare.

        Returns:
            bool: True if self is less than other, False otherwise.
        """
        return self.m_row_id >= other.m_row_id

    def __str__(self) -> str:
        """
        Get the string representation of this object.

        Returns:
            str: The string representation of this object.
        """
        return (
            f"m_driver_1_name={self.m_driver_1_name},"
            f"m_driver_1_lap={self.m_driver_1_lap},"
            f"m_driver_1_index={self.m_driver_1_index},"
            f"m_driver_2_name={self.m_driver_2_name}"
            f"m_driver_2_lap={self.m_driver_2_lap},"
            f"m_driver_2_index={self.m_driver_2_index}"
            f"m_row_id={self.m_row_id}"
        )

    def toJSON(self) -> Dict[str, Any]:
        """Get the JSON representation of this object

        Returns:
            Dict[str, Any]: JSON dictionary
        """

        return {
            "driver-1-name": self.m_driver_1_name,
            "driver-1-lap": self.m_driver_1_lap,
            "driver-1-index": self.m_driver_1_index,
            "driver-2-name": self.m_driver_2_name,
            "driver-2-lap": self.m_driver_2_lap,
            "driver-2-index": self.m_driver_2_index,
            "overtake-id" : self.m_row_id
        }

class CollisionPairKey:

    def __init__(self, driver_1_index: int, driver_1_name: str, driver_2_index: int, driver_2_name: str) -> None:
        """
        Initialize an OvertakeRivalryPair instance with the given driver indices.

        Args:
            driver_1_index (int): The index of the first driver in the pair.
            driver_1_name (str): The name of the first driver in the pair.
            driver_2_index (int): The index of the second driver in the pair.\
            driver_2_name (str): The name of the second driver in the pair.
        """
        self.m_driver_1_index: int = driver_1_index
        self.m_driver_1_name: str = driver_1_name
        self.m_driver_2_index: int = driver_2_index
        self.m_driver_2_name: str = driver_2_name

    def __eq__(self, other: "CollisionPairKey") -> bool:
        """
        Check if two rivalry pairs are equal, considering both orderings of driver names.

        Args:
            other (OvertakeRivalryPair): The other OvertakeRivalryPair instance to compare.

        Returns:
            bool: True if the rivalry pairs are equal, False otherwise.
        """
        return (
            (self.m_driver_1_index == other.m_driver_1_index and self.m_driver_2_index == other.m_driver_2_index) or
            (self.m_driver_1_index == other.m_driver_2_index and self.m_driver_2_index == other.m_driver_1_index)
        )

    def __hash__(self) -> int:
        """
        Generate a hash value for the OvertakeRivalryPair instance.

        Returns:
            int: Hash value.
        """
        # Use a frozenset to ensure order independence
        return hash(frozenset([self.m_driver_1_index, self.m_driver_2_index]))

    def __str__(self) -> str:
        """
        Get a string representation of the OvertakeRivalryPair instance.

        Returns:
            str: A string representation of the OvertakeRivalryPair.
        """
        return f"({str(self.m_driver_1_index)}, {str(self.m_driver_2_index)})"

    def __contains__(self, driver_index: int) -> bool:
        """
        Check if the given driver index is present in the CollisionPairKey.

        Args:
            driver_index (int): The driver index to check

        Returns:
            bool: True if the driver index is present, False otherwise.
        """
        return driver_index in (self.m_driver_1_index, self.m_driver_2_index)

    def getDrivers(self) -> tuple[str, str]:
        """
        Get a tuple of the driver names in this object.

        Returns:
            tuple[str, str]: The first and the second driver's names.
        """
        return (self.m_driver_1_index, self.m_driver_2_index)

class CollisionAnalyzerMode(Enum):
    """Represents how the CollisionAnalyzer object will be initialized. Used to define whether the input is a file name,
           or the list of csv strings
    """

    INPUT_MODE_FILE_CSV=1
    INPUT_MODE_LIST_CSV=2
    INPUT_MODE_LIST_COLLISION_RECORDS=3
    INPUT_MODE_LIST_COLLISION_RECORDS_JSON=4

class CollisionAnalyzer:

    def __init__(self, input_mode: CollisionAnalyzerMode, input_data: Any):
        """
        Initialize CollisionAnalyzer.

        Args:
            input_mode (CollisionAnalyzerMode): Describes the type of input
            input_data (str): Context varies based on input_mode
                INPUT_MODE_FILE_CSV - This is a JSON file containing all collision records under the key
                INPUT_MODE_LIST_CSV - This is a list of all collisions in csv format
                INPUT_MODE_LIST_COLLISION_RECORDS - This is a list of all OvertakeRecords
                INPUT_MODE_LIST_COLLISION_RECORDS_JSON - This is a list of all OvertakeRecords in JSON format
        """

        self.m_input_mode: CollisionAnalyzerMode = input_mode
        self.m_collision_counts: Dict[Tuple[int,str], int] = defaultdict(int) # Key is (index,name)
        self.m_collision_pair_records: Dict[CollisionPairKey, List[CollisionRecord]] = defaultdict(list)
        self.m_collision_records: List[CollisionRecord] = []
        if input_mode == CollisionAnalyzerMode.INPUT_MODE_FILE_CSV:
            self.__analyzeCsvFile(file_name=input_data)
        elif input_mode == CollisionAnalyzerMode.INPUT_MODE_LIST_CSV:
            self.__analyzeCsvList(csv_list=input_data)
        else:
            self.__analyzeListCollisionRecords(collision_records=input_data)

    def __analyzeListCollisionRecords(self, collision_records: List[CollisionRecord]) -> None:
        """
        Analyze overtaking data from the list of OvertakeRecords.
        """

        for record in collision_records:
            if self.m_input_mode == CollisionAnalyzerMode.INPUT_MODE_LIST_COLLISION_RECORDS_JSON:
                record = CollisionRecord.fromJSON(record)
            self.__processCollisionRecord(record)

    def __analyzeCsvFile(self, file_name) -> None:
        """
        Analyze overtaking data from the CSV file.
        """

        with open(file_name, 'r', encoding='utf-8') as file:
            data = json.load(file)
            # Check if "overtakes" key is present
            overtakes = data.get('collisions', None)
            if not overtakes:
                raise ValueError('"collisions" key is missing in the JSON.')

            # Check if "records" key is present and is a list
            records = overtakes.get('records', None)
            if not records or not isinstance(records, list):
                raise ValueError('"records" key is missing or is not a list in the JSON.')

            # Analyze the input data
            self.__analyze(data['collisions']['records'])

    def __analyzeCsvList(self, csv_list: List[str]) -> None:
        """Parse and analyze the given CSV list into this object

        Args:
            csv_list (List[str]): The list of strings containing csv lines
        """

        csv_data_string = '\n'.join(csv_list)
        csv_data_file = StringIO(csv_data_string)
        self.__analyze(csv_data_file)

    def __processCollisionRecord(self, record: CollisionRecord) -> None:
        """
        Process the given CollisionRecord object.

        Args:
            record (CollisionRecord): The CollisionRecord object to process.
        """

        # Record the collision count for both drivers
        self.m_collision_counts[(record.m_driver_1_index, record.m_driver_1_name)] += 1
        self.m_collision_counts[(record.m_driver_2_index, record.m_driver_2_name)] += 1

        # Use the key type here since it supports bidirectional comparison
        collision_pair_key = CollisionPairKey(
            driver_1_index=record.m_driver_1_index,
            driver_1_name=record.m_driver_1_name,
            driver_2_index=record.m_driver_2_index,
            driver_2_name=record.m_driver_2_name)
        self.m_collision_pair_records[collision_pair_key].append(record)

        # Add to the raw records list
        self.m_collision_records.append(record)

    def __analyze(self, data: List[str]) -> None:
        """
        Analyze collision data from either a file or a list of strings.

        Args:
            data: List of CSV data
        """
        reader = csv.reader(data)
        # next(reader, None)  # Skip header row if present

        row_id = 0
        for row in reader:
            row = [s.strip() for s in row]
            if row in [[''],[]]: # don't process empty lines
                continue
            driver_1_name, driver_1_index, driver_1_lap, driver_2_name, driver_2_index, driver_2_lap = \
                [col.strip() for col in row]
            self.__processCollisionRecord(CollisionRecord(
                driver_1_name=driver_1_name,
                driver_1_lap=int(driver_1_lap),
                driver_1_index=int(driver_1_index),
                driver_2_name=driver_2_name,
                driver_2_lap=int(driver_2_lap),
                driver_2_index=int(driver_2_index),
                row_id=row_id)
            )
            row_id += 1

    def getMostCollisions(self) -> Tuple[List[Tuple[int,str]], int]:
        """
        Get the driver names and number of collisions for the driver with the most collisions.

        Returns:
            Tuple[List[Tuple[int,str]], int]: Tuple containing the driver ID tuple and the number of collisions
                The driver ID tuple is a pair of driver index (int) and driver name (str)
        """

        if not self.m_collision_counts:
            return [], 0

        max_collisions = max(self.m_collision_counts.values())
        most_collision_drivers = [
            (index, name) for (index, name), count in self.m_collision_counts.items() if count == max_collisions
        ]
        return most_collision_drivers, max_collisions

    def getNumCollisions(self) -> int:
        """
        Get the total number of collisions.

        Returns:
            int: The total number of collisions
        """

        return sum(self.m_collision_counts.values())

    def getMostCollidedPairsJSON(self) -> Dict[str, Any]:
        """
        Get the most collided pair of drivers in JSON format.

        Returns:
            Dict[str, Any]: The JSON dictionary containing the most collided pair of drivers.
                Contains the following keys:
                    - "count": The number of collisions
                    - "collision-pairs": A list of pairs of driver IDs and names. Each items contains the following keys
                        - "driver-1-index": The index of the first driver
                        - "driver-1-name": The name of the first driver
                        - "driver-2-index": The index of the second driver
                        - "driver-2-name": The name of the second driver
        """

        if not self.m_collision_counts:
            return {
                "count": 0,
                "collision-pairs": []
            }

        max_collisions_count = max(len(records) for records in self.m_collision_pair_records.values())
        return {
            "count": max_collisions_count,
            "collision-pairs": [
                {
                    "driver-1-index": collision_pair.m_driver_1_index,
                    "driver-1-name": collision_pair.m_driver_1_name,
                    "driver-2-index": collision_pair.m_driver_2_index,
                    "driver-2-name": collision_pair.m_driver_2_name
                }
                for collision_pair, records_list in self.m_collision_pair_records.items()
                if len(records_list) == max_collisions_count
            ]
        }

    def toJSON(self) -> Dict[str, Any]:
        """Get the JSON representation of this object

        Returns:
            Dict[str, Any]: JSON dictionary
        """

        return {
            "most-collided-pairs" : self.getMostCollidedPairsJSON(),
            "collision-pairs": [
                {
                    "driver-1-index": key.m_driver_1_index,
                    "driver-1-name": key.m_driver_1_name,
                    "driver-2-index": key.m_driver_2_index,
                    "driver-2-name": key.m_driver_2_name,
                    "num-collisions": len(list_of_collisions),
                    "collisions": [collision.toJSON() for collision in list_of_collisions],
                }
                for key, list_of_collisions in self.m_collision_pair_records.items()
            ],
            "records" : [record.toJSON() for record in self.m_collision_records],
        }
