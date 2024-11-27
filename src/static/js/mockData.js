const mockTelemetryData = [
  {
    position: 2,
    driver: 'VER',
    delta: '+2.341',
    lastLap: '1:31.234',
    bestLap: '1:30.789',
    tyreInfo: {
      compound: 'Medium',
      age: 12,
      wear: 78,
      prediction: '8 laps'
    },
    ers: 82,
    fuel: 65
  },
  {
    position: 3,
    driver: 'PER',
    delta: '+0.897',
    lastLap: '1:31.456',
    bestLap: '1:30.901',
    tyreInfo: {
      compound: 'Hard',
      age: 15,
      wear: 45,
      prediction: '20 laps'
    },
    ers: 76,
    fuel: 68
  },
  {
    position: 4,
    driver: 'HAM',
    delta: '+0.000',
    lastLap: '1:31.567',
    bestLap: '1:30.674',
    tyreInfo: {
      compound: 'Hard',
      age: 18,
      wear: 65,
      prediction: '15 laps'
    },
    ers: 95,
    fuel: 70,
    isPlayer: true
  },
  {
    position: 5,
    driver: 'LEC',
    delta: '-1.234',
    lastLap: '1:31.789',
    bestLap: '1:30.987',
    tyreInfo: {
      compound: 'Soft',
      age: 5,
      wear: 90,
      prediction: '4 laps'
    },
    ers: 45,
    fuel: 55
  },
  {
    position: 6,
    driver: 'SAI',
    delta: '-2.567',
    lastLap: '1:31.890',
    bestLap: '1:31.123',
    tyreInfo: {
      compound: 'Soft',
      age: 6,
      wear: 85,
      prediction: '5 laps'
    },
    ers: 65,
    fuel: 58
  }
];

const mockWeatherPredictions = [
  { timeOffset: 5, rainProbability: 20, weatherType: 'Light Cloud' },
  { timeOffset: 10, rainProbability: 40, weatherType: 'Light Rain' },
  { timeOffset: 15, rainProbability: 60, weatherType: 'Heavy Rain' }
];