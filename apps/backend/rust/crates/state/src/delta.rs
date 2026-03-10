#[derive(Clone, Debug, PartialEq, Eq)]
pub struct DeltaResult {
    pub delta_ms: i32,
    pub best_lap_num: u8,
    pub best_time_ms_at_distance: u32,
}

#[derive(Clone, Debug, PartialEq)]
struct LapPoint {
    lap_num: u8,
    distance_m: f32,
    time_ms: u32,
}

#[derive(Clone, Debug, Default, PartialEq)]
pub struct LapDeltaManager {
    laps: std::collections::BTreeMap<u8, Vec<LapPoint>>,
    best_lap_num: Option<u8>,
    last_recorded_point: Option<LapPoint>,
}

impl LapDeltaManager {
    pub fn record_data_point(&mut self, lap_num: u8, curr_distance: f32, curr_time_ms: u32) {
        let points = self.laps.entry(lap_num).or_default();

        if points.is_empty() {
            let point = LapPoint {
                lap_num,
                distance_m: curr_distance,
                time_ms: curr_time_ms,
            };
            points.push(point.clone());
            self.last_recorded_point = Some(point);
            return;
        }

        if curr_distance
            > points
                .last()
                .map(|point| point.distance_m)
                .unwrap_or(f32::MIN)
        {
            let point = LapPoint {
                lap_num,
                distance_m: curr_distance,
                time_ms: curr_time_ms,
            };
            points.push(point.clone());
            self.last_recorded_point = Some(point);
            return;
        }

        let drop_idx = points.partition_point(|point| point.distance_m < curr_distance);
        points.truncate(drop_idx);
        let point = LapPoint {
            lap_num,
            distance_m: curr_distance,
            time_ms: curr_time_ms,
        };
        points.push(point.clone());
        self.last_recorded_point = Some(point);
    }

    pub fn set_best_lap(&mut self, lap_num: u8) {
        self.best_lap_num = Some(lap_num);
    }

    pub fn get_delta(&self) -> Option<DeltaResult> {
        let best_lap_num = self.best_lap_num?;
        let curr = self.last_recorded_point.as_ref()?;
        let best_time_ms_at_distance =
            self.interpolated_time_for_distance(best_lap_num, curr.distance_m)?;
        Some(DeltaResult {
            delta_ms: curr.time_ms as i32 - best_time_ms_at_distance as i32,
            best_lap_num,
            best_time_ms_at_distance,
        })
    }

    pub fn handle_flashback(&mut self, lap_num: u8, curr_distance: f32) {
        self.laps
            .retain(|stored_lap_num, _| *stored_lap_num <= lap_num);

        let points = self.laps.entry(lap_num).or_default();
        let truncate_idx = points.partition_point(|point| point.distance_m < curr_distance);
        points.truncate(truncate_idx);

        let point = LapPoint {
            lap_num,
            distance_m: curr_distance,
            time_ms: 0,
        };
        points.push(point.clone());
        self.last_recorded_point = Some(point);
    }

    fn interpolated_time_for_distance(&self, lap_num: u8, distance_m: f32) -> Option<u32> {
        let points = self.laps.get(&lap_num)?;
        if points.is_empty() {
            return None;
        }
        if distance_m < points.first()?.distance_m || distance_m > points.last()?.distance_m {
            return None;
        }

        let idx = points.partition_point(|point| point.distance_m < distance_m);
        if idx < points.len() && points[idx].distance_m == distance_m {
            return Some(points[idx].time_ms);
        }
        if idx == 0 || idx >= points.len() {
            return None;
        }

        let lo = &points[idx - 1];
        let hi = &points[idx];
        if hi.distance_m == lo.distance_m {
            return Some(lo.time_ms);
        }

        let ratio = (distance_m - lo.distance_m) / (hi.distance_m - lo.distance_m);
        let interpolated = lo.time_ms as f32 + ratio * (hi.time_ms as f32 - lo.time_ms as f32);
        Some(interpolated as u32)
    }
}

#[cfg(test)]
mod tests {
    use super::LapDeltaManager;

    #[test]
    fn basic_recording_and_forward_only() {
        let mut mgr = LapDeltaManager::default();
        mgr.record_data_point(1, 10.0, 1000);
        mgr.record_data_point(1, 20.0, 2000);
        assert_eq!(mgr.laps.get(&1).map(|points| points.len()), Some(2));
    }

    #[test]
    fn backwards_movement_rewrites() {
        let mut mgr = LapDeltaManager::default();
        mgr.record_data_point(1, 50.0, 3000);
        mgr.record_data_point(1, 49.0, 3100);
        mgr.record_data_point(1, 70.0, 3500);

        let points = mgr.laps.get(&1).expect("lap 1");
        assert_eq!(points.len(), 2);
        assert_eq!(points[0].distance_m, 49.0);
        assert_eq!(points[1].distance_m, 70.0);
    }

    #[test]
    fn delta_interpolation() {
        let mut mgr = LapDeltaManager::default();
        mgr.record_data_point(1, 10.0, 1000);
        mgr.record_data_point(1, 20.0, 2000);
        mgr.set_best_lap(1);
        mgr.record_data_point(2, 15.0, 1700);

        let delta = mgr.get_delta().expect("delta");
        assert_eq!(delta.best_time_ms_at_distance, 1500);
        assert_eq!(delta.delta_ms, 200);
    }

    #[test]
    fn flashback_to_previous_lap() {
        let mut mgr = LapDeltaManager::default();
        mgr.record_data_point(1, 10.0, 1000);
        mgr.record_data_point(1, 50.0, 3000);
        mgr.record_data_point(2, 10.0, 1200);
        mgr.record_data_point(2, 60.0, 4000);

        mgr.handle_flashback(1, 20.0);

        assert!(!mgr.laps.contains_key(&2));
        let lap1 = mgr.laps.get(&1).expect("lap 1");
        assert_eq!(lap1.len(), 2);
        assert_eq!(lap1[1].distance_m, 20.0);
        assert_eq!(lap1[1].time_ms, 0);
    }
}
