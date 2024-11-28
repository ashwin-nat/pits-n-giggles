import json

input = {
  "air-temperature": 22,
  "circuit": "Austria",
  "current-lap": 1,
  "event-type": "Race",
  "f1-game-year": 24,
  "fastest-lap-overall": 0,
  "is-spectating": 0,
  "pit-speed-limit": 80,
  "race-ended": False,
  "safety-car-status": "NO_SAFETY_CAR",
  "session-time-left": 7168,
  "table-entries": [
    {
      "damage-info": {
        "fl-wing-damage": 0,
        "fr-wing-damage": 0,
        "rear-wing-damage": 0
      },
      "delta-info": {
        "delta": "--- ",
        "delta-to-leader": "0.000 "
      },
      "driver-info": {
        "dnf-status": "",
        "drs": False,
        "index": 16,
        "is-fastest": False,
        "is-player": False,
        "name": "PÉREZ",
        "position": 1,
        "team": "Red Bull Racing",
        "telemetry-setting": "Public"
      },
      "ers-info": {
        "ers-deployed-this-lap": 42.249578125,
        "ers-harvested-by-mguk-this-lap": 13.14564375,
        "ers-mode": "Medium",
        "ers-percent": "42.12%"
      },
      "fuel-info": {
        "curr-fuel-rate": None,
        "fuel-capacity": 110,
        "fuel-in-tank": 10.170424461364746,
        "fuel-mix": "Standard",
        "fuel-remaining-laps": 2.446606159210205,
        "last-lap-fuel-used": None,
        "target-fuel-rate": None
      },
      "lap-info": {
        "best-lap-ms": None,
        "best-lap-ms-player": None,
        "lap-progress": 45.39465108955731,
        "last-lap-ms": 0,
        "last-lap-ms-player": 0,
        "speed-trap-record-kmph": 0
      },
      "tyre-info": {
        "actual-tyre-compound": "C5",
        "current-wear": {
          "average": 0.5929981842637062,
          "desc": "curr tyre wear",
          "front-left-wear": 0.4166416823863983,
          "front-right-wear": 0.1378469467163086,
          "lap-number": None,
          "rear-left-wear": 0.9584136009216309,
          "rear-right-wear": 0.8590905070304871
        },
        "num-pitstops": 0,
        "tyre-age": 0,
        "tyre-life-remaining": 24,
        "visual-tyre-compound": "Soft",
        "wear-prediction": []
      },
      "warns-pens-info": {
        "corner-cutting-warnings": 0,
        "num-dt": 0,
        "num-sg": 0,
        "time-penalties": 0
      }
    },
    {
      "damage-info": {
        "fl-wing-damage": 0,
        "fr-wing-damage": 0,
        "rear-wing-damage": 0
      },
      "delta-info": {
        "delta": "-1.533 ",
        "delta-to-leader": "1.583 "
      },
      "driver-info": {
        "dnf-status": "",
        "drs": False,
        "index": 10,
        "is-fastest": False,
        "is-player": False,
        "name": "NORRIS",
        "position": 2,
        "team": "Mclaren",
        "telemetry-setting": "Public"
      },
      "ers-info": {
        "ers-deployed-this-lap": 33.126040624999995,
        "ers-harvested-by-mguk-this-lap": 15.230796875,
        "ers-mode": "Medium",
        "ers-percent": "64.87%"
      },
      "fuel-info": {
        "curr-fuel-rate": None,
        "fuel-capacity": 110,
        "fuel-in-tank": 10.428911209106445,
        "fuel-mix": "Standard",
        "fuel-remaining-laps": 2.595582962036133,
        "last-lap-fuel-used": None,
        "target-fuel-rate": None
      },
      "lap-info": {
        "best-lap-ms": None,
        "best-lap-ms-player": None,
        "lap-progress": 42.430132747441014,
        "last-lap-ms": 0,
        "last-lap-ms-player": 0,
        "speed-trap-record-kmph": 0
      },
      "tyre-info": {
        "actual-tyre-compound": "C5",
        "current-wear": {
          "average": 0.5188853852450848,
          "desc": "curr tyre wear",
          "front-left-wear": 0.1910427361726761,
          "front-right-wear": 0.14218834042549133,
          "lap-number": None,
          "rear-left-wear": 0.8944181799888611,
          "rear-right-wear": 0.8478922843933105
        },
        "num-pitstops": 0,
        "tyre-age": 0,
        "tyre-life-remaining": 24,
        "visual-tyre-compound": "Soft",
        "wear-prediction": []
      },
      "warns-pens-info": {
        "corner-cutting-warnings": 0,
        "num-dt": 0,
        "num-sg": 0,
        "time-penalties": 0
      }
    },
    {
      "damage-info": {
        "fl-wing-damage": 0,
        "fr-wing-damage": 0,
        "rear-wing-damage": 0
      },
      "delta-info": {
        "delta": "-1.500 ",
        "delta-to-leader": "1.600 "
      },
      "driver-info": {
        "dnf-status": "",
        "drs": False,
        "index": 8,
        "is-fastest": False,
        "is-player": False,
        "name": "SAINZ",
        "position": 3,
        "team": "Ferrari",
        "telemetry-setting": "Public"
      },
      "ers-info": {
        "ers-deployed-this-lap": 40.42021875,
        "ers-harvested-by-mguk-this-lap": 14.801900000000002,
        "ers-mode": "Overtake",
        "ers-percent": "47.08%"
      },
      "fuel-info": {
        "curr-fuel-rate": None,
        "fuel-capacity": 110,
        "fuel-in-tank": 10.144414901733398,
        "fuel-mix": "Standard",
        "fuel-remaining-laps": 2.397447109222412,
        "last-lap-fuel-used": None,
        "target-fuel-rate": None
      },
      "lap-info": {
        "best-lap-ms": None,
        "best-lap-ms-player": None,
        "lap-progress": 42.40824875665047,
        "last-lap-ms": 0,
        "last-lap-ms-player": 0,
        "speed-trap-record-kmph": 0
      },
      "tyre-info": {
        "actual-tyre-compound": "C5",
        "current-wear": {
          "average": 0.5690572932362556,
          "desc": "curr tyre wear",
          "front-left-wear": 0.37912705540657043,
          "front-right-wear": 0.1551613211631775,
          "lap-number": None,
          "rear-left-wear": 0.9105740189552307,
          "rear-right-wear": 0.831366777420044
        },
        "num-pitstops": 0,
        "tyre-age": 0,
        "tyre-life-remaining": 24,
        "visual-tyre-compound": "Soft",
        "wear-prediction": []
      },
      "warns-pens-info": {
        "corner-cutting-warnings": 0,
        "num-dt": 0,
        "num-sg": 0,
        "time-penalties": 0
      }
    },
    {
      "damage-info": {
        "fl-wing-damage": 0,
        "fr-wing-damage": 0,
        "rear-wing-damage": 0
      },
      "delta-info": {
        "delta": "-1.400 ",
        "delta-to-leader": "1.717 "
      },
      "driver-info": {
        "dnf-status": "",
        "drs": False,
        "index": 2,
        "is-fastest": False,
        "is-player": False,
        "name": "PIASTRI",
        "position": 4,
        "team": "Mclaren",
        "telemetry-setting": "Public"
      },
      "ers-info": {
        "ers-deployed-this-lap": 42.669762500000004,
        "ers-harvested-by-mguk-this-lap": 16.4068875,
        "ers-mode": "Overtake",
        "ers-percent": "40.28%"
      },
      "fuel-info": {
        "curr-fuel-rate": None,
        "fuel-capacity": 110,
        "fuel-in-tank": 10.440468788146973,
        "fuel-mix": "Standard",
        "fuel-remaining-laps": 2.600416660308838,
        "last-lap-fuel-used": None,
        "target-fuel-rate": None
      },
      "lap-info": {
        "best-lap-ms": None,
        "best-lap-ms-player": None,
        "lap-progress": 42.20540534007778,
        "last-lap-ms": 0,
        "last-lap-ms-player": 0,
        "speed-trap-record-kmph": 0
      },
      "tyre-info": {
        "actual-tyre-compound": "C5",
        "current-wear": {
          "average": 0.5483175739645958,
          "desc": "curr tyre wear",
          "front-left-wear": 0.2814500033855438,
          "front-right-wear": 0.1874060034751892,
          "lap-number": None,
          "rear-left-wear": 0.8804599046707153,
          "rear-right-wear": 0.8439543843269348
        },
        "num-pitstops": 0,
        "tyre-age": 0,
        "tyre-life-remaining": 24,
        "visual-tyre-compound": "Soft",
        "wear-prediction": []
      },
      "warns-pens-info": {
        "corner-cutting-warnings": 0,
        "num-dt": 0,
        "num-sg": 0,
        "time-penalties": 0
      }
    },
    {
      "damage-info": {
        "fl-wing-damage": 0,
        "fr-wing-damage": 0,
        "rear-wing-damage": 0
      },
      "delta-info": {
        "delta": "-0.950 ",
        "delta-to-leader": "2.167 "
      },
      "driver-info": {
        "dnf-status": "",
        "drs": False,
        "index": 11,
        "is-fastest": False,
        "is-player": False,
        "name": "VERSTAPPEN",
        "position": 5,
        "team": "Red Bull Racing",
        "telemetry-setting": "Public"
      },
      "ers-info": {
        "ers-deployed-this-lap": 35.847978125000004,
        "ers-harvested-by-mguk-this-lap": 14.688014062499999,
        "ers-mode": "Medium",
        "ers-percent": "52.84%"
      },
      "fuel-info": {
        "curr-fuel-rate": None,
        "fuel-capacity": 110,
        "fuel-in-tank": 10.073479652404785,
        "fuel-mix": "Standard",
        "fuel-remaining-laps": 2.3385157585144043,
        "last-lap-fuel-used": None,
        "target-fuel-rate": None
      },
      "lap-info": {
        "best-lap-ms": None,
        "best-lap-ms-player": None,
        "lap-progress": 41.37490647770645,
        "last-lap-ms": 0,
        "last-lap-ms-player": 0,
        "speed-trap-record-kmph": 0
      },
      "tyre-info": {
        "actual-tyre-compound": "C5",
        "current-wear": {
          "average": 0.5808121897280216,
          "desc": "curr tyre wear",
          "front-left-wear": 0.3393697440624237,
          "front-right-wear": 0.1904560774564743,
          "lap-number": None,
          "rear-left-wear": 0.9196615815162659,
          "rear-right-wear": 0.8737613558769226
        },
        "num-pitstops": 0,
        "tyre-age": 0,
        "tyre-life-remaining": 24,
        "visual-tyre-compound": "Soft",
        "wear-prediction": []
      },
      "warns-pens-info": {
        "corner-cutting-warnings": 0,
        "num-dt": 0,
        "num-sg": 0,
        "time-penalties": 0
      }
    },
    {
      "damage-info": {
        "fl-wing-damage": 0,
        "fr-wing-damage": 0,
        "rear-wing-damage": 0
      },
      "delta-info": {
        "delta": "-0.950 ",
        "delta-to-leader": "2.183 "
      },
      "driver-info": {
        "dnf-status": "",
        "drs": False,
        "index": 13,
        "is-fastest": False,
        "is-player": False,
        "name": "LECLERC",
        "position": 6,
        "team": "Ferrari",
        "telemetry-setting": "Public"
      },
      "ers-info": {
        "ers-deployed-this-lap": 37.14101875,
        "ers-harvested-by-mguk-this-lap": 15.956721875,
        "ers-mode": "Overtake",
        "ers-percent": "51.77%"
      },
      "fuel-info": {
        "curr-fuel-rate": None,
        "fuel-capacity": 110,
        "fuel-in-tank": 10.405851364135742,
        "fuel-mix": "Standard",
        "fuel-remaining-laps": 2.5691871643066406,
        "last-lap-fuel-used": None,
        "target-fuel-rate": None
      },
      "lap-info": {
        "best-lap-ms": None,
        "best-lap-ms-player": None,
        "lap-progress": 41.36238883497427,
        "last-lap-ms": 0,
        "last-lap-ms-player": 0,
        "speed-trap-record-kmph": 0
      },
      "tyre-info": {
        "actual-tyre-compound": "C5",
        "current-wear": {
          "average": 0.5381238125264645,
          "desc": "curr tyre wear",
          "front-left-wear": 0.2629411816596985,
          "front-right-wear": 0.16999386250972748,
          "lap-number": None,
          "rear-left-wear": 0.8789037466049194,
          "rear-right-wear": 0.8406564593315125
        },
        "num-pitstops": 0,
        "tyre-age": 0,
        "tyre-life-remaining": 24,
        "visual-tyre-compound": "Soft",
        "wear-prediction": []
      },
      "warns-pens-info": {
        "corner-cutting-warnings": 0,
        "num-dt": 0,
        "num-sg": 0,
        "time-penalties": 0
      }
    },
    {
      "damage-info": {
        "fl-wing-damage": 0,
        "fr-wing-damage": 0,
        "rear-wing-damage": 0
      },
      "delta-info": {
        "delta": "-0.450 ",
        "delta-to-leader": "2.683 "
      },
      "driver-info": {
        "dnf-status": "",
        "drs": False,
        "index": 12,
        "is-fastest": False,
        "is-player": False,
        "name": "ALONSO",
        "position": 7,
        "team": "Aston Martin",
        "telemetry-setting": "Public"
      },
      "ers-info": {
        "ers-deployed-this-lap": 34.438396875,
        "ers-harvested-by-mguk-this-lap": 16.197807812500002,
        "ers-mode": "Medium",
        "ers-percent": "55.18%"
      },
      "fuel-info": {
        "curr-fuel-rate": None,
        "fuel-capacity": 110,
        "fuel-in-tank": 10.15424633026123,
        "fuel-mix": "Standard",
        "fuel-remaining-laps": 2.385509490966797,
        "last-lap-fuel-used": None,
        "target-fuel-rate": None
      },
      "lap-info": {
        "best-lap-ms": None,
        "best-lap-ms-player": None,
        "lap-progress": 40.46159012296148,
        "last-lap-ms": 0,
        "last-lap-ms-player": 0,
        "speed-trap-record-kmph": 0
      },
      "tyre-info": {
        "actual-tyre-compound": "C5",
        "current-wear": {
          "average": 0.5829978063702583,
          "desc": "curr tyre wear",
          "front-left-wear": 0.2759215533733368,
          "front-right-wear": 0.21106034517288208,
          "lap-number": None,
          "rear-left-wear": 0.9210659861564636,
          "rear-right-wear": 0.9239433407783508
        },
        "num-pitstops": 0,
        "tyre-age": 0,
        "tyre-life-remaining": 24,
        "visual-tyre-compound": "Soft",
        "wear-prediction": []
      },
      "warns-pens-info": {
        "corner-cutting-warnings": 0,
        "num-dt": 0,
        "num-sg": 0,
        "time-penalties": 0
      }
    },
    {
      "damage-info": {
        "fl-wing-damage": 0,
        "fr-wing-damage": 0,
        "rear-wing-damage": 0
      },
      "delta-info": {
        "delta": "-0.417 ",
        "delta-to-leader": "2.716 "
      },
      "driver-info": {
        "dnf-status": "",
        "drs": False,
        "index": 6,
        "is-fastest": False,
        "is-player": False,
        "name": "HAMILTON",
        "position": 8,
        "team": "Mercedes",
        "telemetry-setting": "Public"
      },
      "ers-info": {
        "ers-deployed-this-lap": 38.349109375,
        "ers-harvested-by-mguk-this-lap": 16.7211359375,
        "ers-mode": "Overtake",
        "ers-percent": "51.08%"
      },
      "fuel-info": {
        "curr-fuel-rate": None,
        "fuel-capacity": 110,
        "fuel-in-tank": 10.405503273010254,
        "fuel-mix": "Standard",
        "fuel-remaining-laps": 2.5589113235473633,
        "last-lap-fuel-used": None,
        "target-fuel-rate": None
      },
      "lap-info": {
        "best-lap-ms": None,
        "best-lap-ms-player": None,
        "lap-progress": 40.41371924607478,
        "last-lap-ms": 0,
        "last-lap-ms-player": 0,
        "speed-trap-record-kmph": 0
      },
      "tyre-info": {
        "actual-tyre-compound": "C5",
        "current-wear": {
          "average": 0.55454146489501,
          "desc": "curr tyre wear",
          "front-left-wear": 0.2632354497909546,
          "front-right-wear": 0.18432728946208954,
          "lap-number": None,
          "rear-left-wear": 0.896486759185791,
          "rear-right-wear": 0.8741163611412048
        },
        "num-pitstops": 0,
        "tyre-age": 0,
        "tyre-life-remaining": 24,
        "visual-tyre-compound": "Soft",
        "wear-prediction": []
      },
      "warns-pens-info": {
        "corner-cutting-warnings": 0,
        "num-dt": 0,
        "num-sg": 0,
        "time-penalties": 0
      }
    },
    {
      "damage-info": {
        "fl-wing-damage": 0,
        "fr-wing-damage": 0,
        "rear-wing-damage": 0
      },
      "delta-info": {
        "delta": "-0.050 ",
        "delta-to-leader": "3.084 "
      },
      "driver-info": {
        "dnf-status": "",
        "drs": False,
        "index": 3,
        "is-fastest": False,
        "is-player": False,
        "name": "RUSSELL",
        "position": 9,
        "team": "Mercedes",
        "telemetry-setting": "Public"
      },
      "ers-info": {
        "ers-deployed-this-lap": 39.7428,
        "ers-harvested-by-mguk-this-lap": 15.8492609375,
        "ers-mode": "Medium",
        "ers-percent": "48.70%"
      },
      "fuel-info": {
        "curr-fuel-rate": None,
        "fuel-capacity": 110,
        "fuel-in-tank": 9.997783660888672,
        "fuel-mix": "Standard",
        "fuel-remaining-laps": 2.268672466278076,
        "last-lap-fuel-used": None,
        "target-fuel-rate": None
      },
      "lap-info": {
        "best-lap-ms": None,
        "best-lap-ms-player": None,
        "lap-progress": 39.755451626836106,
        "last-lap-ms": 0,
        "last-lap-ms-player": 0,
        "speed-trap-record-kmph": 0
      },
      "tyre-info": {
        "actual-tyre-compound": "C5",
        "current-wear": {
          "average": 0.6376084499061108,
          "desc": "curr tyre wear",
          "front-left-wear": 0.6049375534057617,
          "front-right-wear": 0.2214830368757248,
          "lap-number": None,
          "rear-left-wear": 0.8889539837837219,
          "rear-right-wear": 0.8350592255592346
        },
        "num-pitstops": 0,
        "tyre-age": 0,
        "tyre-life-remaining": 24,
        "visual-tyre-compound": "Soft",
        "wear-prediction": []
      },
      "warns-pens-info": {
        "corner-cutting-warnings": 0,
        "num-dt": 0,
        "num-sg": 0,
        "time-penalties": 0
      }
    },
    {
      "damage-info": {
        "fl-wing-damage": 0,
        "fr-wing-damage": 0,
        "rear-wing-damage": 0
      },
      "delta-info": {
        "delta": "--- ",
        "delta-to-leader": "3.150 "
      },
      "driver-info": {
        "dnf-status": "",
        "drs": False,
        "index": 19,
        "is-fastest": False,
        "is-player": True,
        "name": "RICCIARDO",
        "position": 10,
        "team": "VCARB",
        "telemetry-setting": "Public"
      },
      "ers-info": {
        "ers-deployed-this-lap": 26.6561625,
        "ers-harvested-by-mguk-this-lap": 13.5227359375,
        "ers-mode": "Medium",
        "ers-percent": "77.14%"
      },
      "fuel-info": {
        "curr-fuel-rate": None,
        "fuel-capacity": 110,
        "fuel-in-tank": 9.965755462646484,
        "fuel-mix": "Standard",
        "fuel-remaining-laps": 2.246861457824707,
        "last-lap-fuel-used": None,
        "target-fuel-rate": None
      },
      "lap-info": {
        "best-lap-ms": None,
        "best-lap-ms-player": None,
        "lap-progress": 39.625229174799045,
        "last-lap-ms": 0,
        "last-lap-ms-player": 0,
        "speed-trap-record-kmph": 0
      },
      "tyre-info": {
        "actual-tyre-compound": "C5",
        "current-wear": {
          "average": 0.404990304261446,
          "desc": "curr tyre wear",
          "front-left-wear": 0.1448933333158493,
          "front-right-wear": 0.06746122241020203,
          "lap-number": None,
          "rear-left-wear": 0.7197506427764893,
          "rear-right-wear": 0.6878560185432434
        },
        "num-pitstops": 0,
        "tyre-age": 0,
        "tyre-life-remaining": 24,
        "visual-tyre-compound": "Soft",
        "wear-prediction": []
      },
      "warns-pens-info": {
        "corner-cutting-warnings": 0,
        "num-dt": 0,
        "num-sg": 0,
        "time-penalties": 0
      }
    },
    {
      "damage-info": {
        "fl-wing-damage": 0,
        "fr-wing-damage": 0,
        "rear-wing-damage": 0
      },
      "delta-info": {
        "delta": "+0.600 ",
        "delta-to-leader": "3.750 "
      },
      "driver-info": {
        "dnf-status": "",
        "drs": False,
        "index": 5,
        "is-fastest": False,
        "is-player": False,
        "name": "TSUNODA",
        "position": 11,
        "team": "VCARB",
        "telemetry-setting": "Public"
      },
      "ers-info": {
        "ers-deployed-this-lap": 34.010146875000004,
        "ers-harvested-by-mguk-this-lap": 16.395729687499998,
        "ers-mode": "Medium",
        "ers-percent": "60.62%"
      },
      "fuel-info": {
        "curr-fuel-rate": None,
        "fuel-capacity": 110,
        "fuel-in-tank": 10.148214340209961,
        "fuel-mix": "Standard",
        "fuel-remaining-laps": 2.362452983856201,
        "last-lap-fuel-used": None,
        "target-fuel-rate": None
      },
      "lap-info": {
        "best-lap-ms": None,
        "best-lap-ms-player": None,
        "lap-progress": 38.64713055983258,
        "last-lap-ms": 0,
        "last-lap-ms-player": 0,
        "speed-trap-record-kmph": 0
      },
      "tyre-info": {
        "actual-tyre-compound": "C5",
        "current-wear": {
          "average": 0.5757501721382141,
          "desc": "curr tyre wear",
          "front-left-wear": 0.2892322242259979,
          "front-right-wear": 0.25696733593940735,
          "lap-number": None,
          "rear-left-wear": 0.8608980774879456,
          "rear-right-wear": 0.8959030508995056
        },
        "num-pitstops": 0,
        "tyre-age": 0,
        "tyre-life-remaining": 24,
        "visual-tyre-compound": "Soft",
        "wear-prediction": []
      },
      "warns-pens-info": {
        "corner-cutting-warnings": 0,
        "num-dt": 0,
        "num-sg": 0,
        "time-penalties": 0
      }
    },
    {
      "damage-info": {
        "fl-wing-damage": 0,
        "fr-wing-damage": 0,
        "rear-wing-damage": 0
      },
      "delta-info": {
        "delta": "+0.633 ",
        "delta-to-leader": "3.766 "
      },
      "driver-info": {
        "dnf-status": "",
        "drs": False,
        "index": 7,
        "is-fastest": False,
        "is-player": False,
        "name": "GASLY",
        "position": 12,
        "team": "Alpine",
        "telemetry-setting": "Public"
      },
      "ers-info": {
        "ers-deployed-this-lap": 41.777671875,
        "ers-harvested-by-mguk-this-lap": 17.213090625,
        "ers-mode": "Overtake",
        "ers-percent": "45.24%"
      },
      "fuel-info": {
        "curr-fuel-rate": None,
        "fuel-capacity": 110,
        "fuel-in-tank": 10.351635932922363,
        "fuel-mix": "Standard",
        "fuel-remaining-laps": 2.5036845207214355,
        "last-lap-fuel-used": None,
        "target-fuel-rate": None
      },
      "lap-info": {
        "best-lap-ms": None,
        "best-lap-ms-player": None,
        "lap-progress": 38.61957932136248,
        "last-lap-ms": 0,
        "last-lap-ms-player": 0,
        "speed-trap-record-kmph": 0
      },
      "tyre-info": {
        "actual-tyre-compound": "C5",
        "current-wear": {
          "average": 0.5844462290406227,
          "desc": "curr tyre wear",
          "front-left-wear": 0.27987393736839294,
          "front-right-wear": 0.2503055930137634,
          "lap-number": None,
          "rear-left-wear": 0.8938114047050476,
          "rear-right-wear": 0.9137939810752869
        },
        "num-pitstops": 0,
        "tyre-age": 0,
        "tyre-life-remaining": 24,
        "visual-tyre-compound": "Soft",
        "wear-prediction": []
      },
      "warns-pens-info": {
        "corner-cutting-warnings": 0,
        "num-dt": 0,
        "num-sg": 0,
        "time-penalties": 0
      }
    },
    {
      "damage-info": {
        "fl-wing-damage": 0,
        "fr-wing-damage": 0,
        "rear-wing-damage": 0
      },
      "delta-info": {
        "delta": "+0.950 ",
        "delta-to-leader": "4.067 "
      },
      "driver-info": {
        "dnf-status": "",
        "drs": False,
        "index": 1,
        "is-fastest": False,
        "is-player": False,
        "name": "STROLL",
        "position": 13,
        "team": "Aston Martin",
        "telemetry-setting": "Public"
      },
      "ers-info": {
        "ers-deployed-this-lap": 30.120943750000002,
        "ers-harvested-by-mguk-this-lap": 18.0205375,
        "ers-mode": "Medium",
        "ers-percent": "65.34%"
      },
      "fuel-info": {
        "curr-fuel-rate": None,
        "fuel-capacity": 110,
        "fuel-in-tank": 10.257076263427734,
        "fuel-mix": "Standard",
        "fuel-remaining-laps": 2.432525634765625,
        "last-lap-fuel-used": None,
        "target-fuel-rate": None
      },
      "lap-info": {
        "best-lap-ms": None,
        "best-lap-ms-player": None,
        "lap-progress": 38.11891314444541,
        "last-lap-ms": 0,
        "last-lap-ms-player": 0,
        "speed-trap-record-kmph": 0
      },
      "tyre-info": {
        "actual-tyre-compound": "C5",
        "current-wear": {
          "average": 0.5393365919589996,
          "desc": "curr tyre wear",
          "front-left-wear": 0.22215810418128967,
          "front-right-wear": 0.21369460225105286,
          "lap-number": None,
          "rear-left-wear": 0.8584696054458618,
          "rear-right-wear": 0.8630240559577942
        },
        "num-pitstops": 0,
        "tyre-age": 0,
        "tyre-life-remaining": 24,
        "visual-tyre-compound": "Soft",
        "wear-prediction": []
      },
      "warns-pens-info": {
        "corner-cutting-warnings": 0,
        "num-dt": 0,
        "num-sg": 0,
        "time-penalties": 0
      }
    },
    {
      "damage-info": {
        "fl-wing-damage": 0,
        "fr-wing-damage": 0,
        "rear-wing-damage": 0
      },
      "delta-info": {
        "delta": "+1.450 ",
        "delta-to-leader": "4.567 "
      },
      "driver-info": {
        "dnf-status": "",
        "drs": False,
        "index": 4,
        "is-fastest": False,
        "is-player": False,
        "name": "SARGEANT",
        "position": 14,
        "team": "Williams",
        "telemetry-setting": "Public"
      },
      "ers-info": {
        "ers-deployed-this-lap": 32.11681875,
        "ers-harvested-by-mguk-this-lap": 18.569759375,
        "ers-mode": "Medium",
        "ers-percent": "64.09%"
      },
      "fuel-info": {
        "curr-fuel-rate": None,
        "fuel-capacity": 110,
        "fuel-in-tank": 10.26290512084961,
        "fuel-mix": "Standard",
        "fuel-remaining-laps": 2.4288711547851562,
        "last-lap-fuel-used": None,
        "target-fuel-rate": None
      },
      "lap-info": {
        "best-lap-ms": None,
        "best-lap-ms-player": None,
        "lap-progress": 37.30968552112248,
        "last-lap-ms": 0,
        "last-lap-ms-player": 0,
        "speed-trap-record-kmph": 0
      },
      "tyre-info": {
        "actual-tyre-compound": "C5",
        "current-wear": {
          "average": 0.49672405421733856,
          "desc": "curr tyre wear",
          "front-left-wear": 0.2428901642560959,
          "front-right-wear": 0.2029218226671219,
          "lap-number": None,
          "rear-left-wear": 0.7714787721633911,
          "rear-right-wear": 0.7696054577827454
        },
        "num-pitstops": 0,
        "tyre-age": 0,
        "tyre-life-remaining": 24,
        "visual-tyre-compound": "Soft",
        "wear-prediction": []
      },
      "warns-pens-info": {
        "corner-cutting-warnings": 0,
        "num-dt": 0,
        "num-sg": 0,
        "time-penalties": 0
      }
    },
    {
      "damage-info": {
        "fl-wing-damage": 0,
        "fr-wing-damage": 0,
        "rear-wing-damage": 0
      },
      "delta-info": {
        "delta": "+1.483 ",
        "delta-to-leader": "4.600 "
      },
      "driver-info": {
        "dnf-status": "",
        "drs": False,
        "index": 0,
        "is-fastest": False,
        "is-player": False,
        "name": "BOTTAS",
        "position": 15,
        "team": "Sauber",
        "telemetry-setting": "Public"
      },
      "ers-info": {
        "ers-deployed-this-lap": 35.741665625,
        "ers-harvested-by-mguk-this-lap": 18.148353125,
        "ers-mode": "Overtake",
        "ers-percent": "56.72%"
      },
      "fuel-info": {
        "curr-fuel-rate": None,
        "fuel-capacity": 110,
        "fuel-in-tank": 10.323532104492188,
        "fuel-mix": "Standard",
        "fuel-remaining-laps": 2.470113754272461,
        "last-lap-fuel-used": None,
        "target-fuel-rate": None
      },
      "lap-info": {
        "best-lap-ms": None,
        "best-lap-ms-player": None,
        "lap-progress": 37.2760350026385,
        "last-lap-ms": 0,
        "last-lap-ms-player": 0,
        "speed-trap-record-kmph": 0
      },
      "tyre-info": {
        "actual-tyre-compound": "C5",
        "current-wear": {
          "average": 0.5762875750660896,
          "desc": "curr tyre wear",
          "front-left-wear": 0.26056957244873047,
          "front-right-wear": 0.22088971734046936,
          "lap-number": None,
          "rear-left-wear": 0.9101491570472717,
          "rear-right-wear": 0.913541853427887
        },
        "num-pitstops": 0,
        "tyre-age": 0,
        "tyre-life-remaining": 24,
        "visual-tyre-compound": "Soft",
        "wear-prediction": []
      },
      "warns-pens-info": {
        "corner-cutting-warnings": 0,
        "num-dt": 0,
        "num-sg": 0,
        "time-penalties": 0
      }
    },
    {
      "damage-info": {
        "fl-wing-damage": 0,
        "fr-wing-damage": 0,
        "rear-wing-damage": 0
      },
      "delta-info": {
        "delta": "+1.900 ",
        "delta-to-leader": "5.017 "
      },
      "driver-info": {
        "dnf-status": "",
        "drs": False,
        "index": 15,
        "is-fastest": False,
        "is-player": False,
        "name": "ZHOU",
        "position": 16,
        "team": "Sauber",
        "telemetry-setting": "Public"
      },
      "ers-info": {
        "ers-deployed-this-lap": 28.296599999999998,
        "ers-harvested-by-mguk-this-lap": 18.4086390625,
        "ers-mode": "Overtake",
        "ers-percent": "69.60%"
      },
      "fuel-info": {
        "curr-fuel-rate": None,
        "fuel-capacity": 110,
        "fuel-in-tank": 10.541647911071777,
        "fuel-mix": "Standard",
        "fuel-remaining-laps": 2.6169047355651855,
        "last-lap-fuel-used": None,
        "target-fuel-rate": None
      },
      "lap-info": {
        "best-lap-ms": None,
        "best-lap-ms-player": None,
        "lap-progress": 36.6520334773667,
        "last-lap-ms": 0,
        "last-lap-ms-player": 0,
        "speed-trap-record-kmph": 0
      },
      "tyre-info": {
        "actual-tyre-compound": "C5",
        "current-wear": {
          "average": 0.5334571301937103,
          "desc": "curr tyre wear",
          "front-left-wear": 0.2321610003709793,
          "front-right-wear": 0.2047671526670456,
          "lap-number": None,
          "rear-left-wear": 0.8468801975250244,
          "rear-right-wear": 0.850020170211792
        },
        "num-pitstops": 0,
        "tyre-age": 0,
        "tyre-life-remaining": 24,
        "visual-tyre-compound": "Soft",
        "wear-prediction": []
      },
      "warns-pens-info": {
        "corner-cutting-warnings": 0,
        "num-dt": 0,
        "num-sg": 0,
        "time-penalties": 0
      }
    },
    {
      "damage-info": {
        "fl-wing-damage": 0,
        "fr-wing-damage": 0,
        "rear-wing-damage": 0
      },
      "delta-info": {
        "delta": "+2.367 ",
        "delta-to-leader": "5.467 "
      },
      "driver-info": {
        "dnf-status": "",
        "drs": False,
        "index": 9,
        "is-fastest": False,
        "is-player": False,
        "name": "OCON",
        "position": 17,
        "team": "Alpine",
        "telemetry-setting": "Public"
      },
      "ers-info": {
        "ers-deployed-this-lap": 33.69668125,
        "ers-harvested-by-mguk-this-lap": 19.5597140625,
        "ers-mode": "Medium",
        "ers-percent": "60.93%"
      },
      "fuel-info": {
        "curr-fuel-rate": None,
        "fuel-capacity": 110,
        "fuel-in-tank": 10.415420532226562,
        "fuel-mix": "Standard",
        "fuel-remaining-laps": 2.522357940673828,
        "last-lap-fuel-used": None,
        "target-fuel-rate": None
      },
      "lap-info": {
        "best-lap-ms": None,
        "best-lap-ms-player": None,
        "lap-progress": 36.0012290049228,
        "last-lap-ms": 0,
        "last-lap-ms-player": 0,
        "speed-trap-record-kmph": 0
      },
      "tyre-info": {
        "actual-tyre-compound": "C5",
        "current-wear": {
          "average": 0.5028573051095009,
          "desc": "curr tyre wear",
          "front-left-wear": 0.2007823884487152,
          "front-right-wear": 0.17751997709274292,
          "lap-number": None,
          "rear-left-wear": 0.808875560760498,
          "rear-right-wear": 0.8242512941360474
        },
        "num-pitstops": 0,
        "tyre-age": 0,
        "tyre-life-remaining": 24,
        "visual-tyre-compound": "Soft",
        "wear-prediction": []
      },
      "warns-pens-info": {
        "corner-cutting-warnings": 0,
        "num-dt": 0,
        "num-sg": 0,
        "time-penalties": 0
      }
    },
    {
      "damage-info": {
        "fl-wing-damage": 0,
        "fr-wing-damage": 0,
        "rear-wing-damage": 0
      },
      "delta-info": {
        "delta": "+2.400 ",
        "delta-to-leader": "5.517 "
      },
      "driver-info": {
        "dnf-status": "",
        "drs": False,
        "index": 14,
        "is-fastest": False,
        "is-player": False,
        "name": "MAGNUSSEN",
        "position": 18,
        "team": "Haas",
        "telemetry-setting": "Public"
      },
      "ers-info": {
        "ers-deployed-this-lap": 31.307546874999996,
        "ers-harvested-by-mguk-this-lap": 19.2971609375,
        "ers-mode": "Overtake",
        "ers-percent": "64.53%"
      },
      "fuel-info": {
        "curr-fuel-rate": None,
        "fuel-capacity": 110,
        "fuel-in-tank": 10.042997360229492,
        "fuel-mix": "Standard",
        "fuel-remaining-laps": 2.263357639312744,
        "last-lap-fuel-used": None,
        "target-fuel-rate": None
      },
      "lap-info": {
        "best-lap-ms": None,
        "best-lap-ms-player": None,
        "lap-progress": 35.91945064914411,
        "last-lap-ms": 0,
        "last-lap-ms-player": 0,
        "speed-trap-record-kmph": 0
      },
      "tyre-info": {
        "actual-tyre-compound": "C5",
        "current-wear": {
          "average": 0.5022204220294952,
          "desc": "curr tyre wear",
          "front-left-wear": 0.2064748853445053,
          "front-right-wear": 0.1799568086862564,
          "lap-number": None,
          "rear-left-wear": 0.7962761521339417,
          "rear-right-wear": 0.8261738419532776
        },
        "num-pitstops": 0,
        "tyre-age": 0,
        "tyre-life-remaining": 24,
        "visual-tyre-compound": "Soft",
        "wear-prediction": []
      },
      "warns-pens-info": {
        "corner-cutting-warnings": 0,
        "num-dt": 0,
        "num-sg": 0,
        "time-penalties": 0
      }
    },
    {
      "damage-info": {
        "fl-wing-damage": 0,
        "fr-wing-damage": 0,
        "rear-wing-damage": 0
      },
      "delta-info": {
        "delta": "+2.867 ",
        "delta-to-leader": "5.950 "
      },
      "driver-info": {
        "dnf-status": "",
        "drs": False,
        "index": 17,
        "is-fastest": False,
        "is-player": False,
        "name": "ALBON",
        "position": 19,
        "team": "Williams",
        "telemetry-setting": "Public"
      },
      "ers-info": {
        "ers-deployed-this-lap": 27.914753125000004,
        "ers-harvested-by-mguk-this-lap": 18.98154375,
        "ers-mode": "Overtake",
        "ers-percent": "70.03%"
      },
      "fuel-info": {
        "curr-fuel-rate": None,
        "fuel-capacity": 110,
        "fuel-in-tank": 10.237702369689941,
        "fuel-mix": "Standard",
        "fuel-remaining-laps": 2.393583297729492,
        "last-lap-fuel-used": None,
        "target-fuel-rate": None
      },
      "lap-info": {
        "best-lap-ms": None,
        "best-lap-ms-player": None,
        "lap-progress": 35.396812945473336,
        "last-lap-ms": 0,
        "last-lap-ms-player": 0,
        "speed-trap-record-kmph": 0
      },
      "tyre-info": {
        "actual-tyre-compound": "C5",
        "current-wear": {
          "average": 0.43659239262342453,
          "desc": "curr tyre wear",
          "front-left-wear": 0.2029174268245697,
          "front-right-wear": 0.15886878967285156,
          "lap-number": None,
          "rear-left-wear": 0.685707688331604,
          "rear-right-wear": 0.6988756656646729
        },
        "num-pitstops": 0,
        "tyre-age": 0,
        "tyre-life-remaining": 24,
        "visual-tyre-compound": "Soft",
        "wear-prediction": []
      },
      "warns-pens-info": {
        "corner-cutting-warnings": 0,
        "num-dt": 0,
        "num-sg": 0,
        "time-penalties": 0
      }
    },
    {
      "damage-info": {
        "fl-wing-damage": 0,
        "fr-wing-damage": 0,
        "rear-wing-damage": 0
      },
      "delta-info": {
        "delta": "+2.867 ",
        "delta-to-leader": "6.000 "
      },
      "driver-info": {
        "dnf-status": "",
        "drs": False,
        "index": 18,
        "is-fastest": False,
        "is-player": False,
        "name": "HULKENBERG",
        "position": 20,
        "team": "Haas",
        "telemetry-setting": "Public"
      },
      "ers-info": {
        "ers-deployed-this-lap": 26.504178125,
        "ers-harvested-by-mguk-this-lap": 19.1699953125,
        "ers-mode": "Overtake",
        "ers-percent": "73.86%"
      },
      "fuel-info": {
        "curr-fuel-rate": None,
        "fuel-capacity": 110,
        "fuel-in-tank": 10.109335899353027,
        "fuel-mix": "Standard",
        "fuel-remaining-laps": 2.3038086891174316,
        "last-lap-fuel-used": None,
        "target-fuel-rate": None
      },
      "lap-info": {
        "best-lap-ms": None,
        "best-lap-ms-player": None,
        "lap-progress": 35.332341296734036,
        "last-lap-ms": 0,
        "last-lap-ms-player": 0,
        "speed-trap-record-kmph": 0
      },
      "tyre-info": {
        "actual-tyre-compound": "C5",
        "current-wear": {
          "average": 0.4533884860575199,
          "desc": "curr tyre wear",
          "front-left-wear": 0.17736969888210297,
          "front-right-wear": 0.14363649487495422,
          "lap-number": None,
          "rear-left-wear": 0.7327645421028137,
          "rear-right-wear": 0.7597832083702087
        },
        "num-pitstops": 0,
        "tyre-age": 0,
        "tyre-life-remaining": 24,
        "visual-tyre-compound": "Soft",
        "wear-prediction": []
      },
      "warns-pens-info": {
        "corner-cutting-warnings": 0,
        "num-dt": 0,
        "num-sg": 0,
        "time-penalties": 0
      }
    }
  ],
  "total-laps": 5,
  "track-temperature": 32,
  "weather-forecast-samples": [
    {
      "rain-probability": "18",
      "time-offset": "0",
      "weather": "Overcast"
    },
    {
      "rain-probability": "18",
      "time-offset": "5",
      "weather": "Overcast"
    },
    {
      "rain-probability": "18",
      "time-offset": "10",
      "weather": "Overcast"
    }
  ]
}

output = input["table-entries"][7:12]
print(json.dumps(output, indent=4))
print(len(output))