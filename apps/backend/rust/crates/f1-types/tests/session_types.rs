use f1_types::{SessionType23, SessionType24};

#[test]
fn session_type_23_classification_matches_python_tests() {
    for session in [
        SessionType23::PRACTICE_1,
        SessionType23::PRACTICE_2,
        SessionType23::PRACTICE_3,
        SessionType23::SHORT_PRACTICE,
    ] {
        assert!(session.is_fp_type_session());
        assert!(!session.is_race_type_session());
    }

    for session in [
        SessionType23::QUALIFYING_1,
        SessionType23::QUALIFYING_2,
        SessionType23::QUALIFYING_3,
        SessionType23::SHORT_QUALIFYING,
        SessionType23::ONE_SHOT_QUALIFYING,
    ] {
        assert!(session.is_quali_type_session());
    }

    for session in [
        SessionType23::RACE,
        SessionType23::RACE_2,
        SessionType23::RACE_3,
    ] {
        assert!(session.is_race_type_session());
    }

    assert!(SessionType23::TIME_TRIAL.is_time_trial_type_session());
    assert_eq!(
        SessionType23::ONE_SHOT_QUALIFYING.to_string(),
        "One Shot Qualifying"
    );
    assert_eq!(SessionType23::try_from(13), Ok(SessionType23::TIME_TRIAL));
    assert!(SessionType23::try_from(99).is_err());
}

#[test]
fn session_type_24_classification_matches_python_tests() {
    for session in [
        SessionType24::PRACTICE_1,
        SessionType24::PRACTICE_2,
        SessionType24::PRACTICE_3,
        SessionType24::SHORT_PRACTICE,
    ] {
        assert!(session.is_fp_type_session());
        assert!(!session.is_quali_type_session());
    }

    for session in [
        SessionType24::QUALIFYING_1,
        SessionType24::QUALIFYING_2,
        SessionType24::QUALIFYING_3,
        SessionType24::SHORT_QUALIFYING,
        SessionType24::ONE_SHOT_QUALIFYING,
        SessionType24::SPRINT_SHOOTOUT_1,
        SessionType24::SPRINT_SHOOTOUT_2,
        SessionType24::SPRINT_SHOOTOUT_3,
        SessionType24::SHORT_SPRINT_SHOOTOUT,
        SessionType24::ONE_SHOT_SPRINT_SHOOTOUT,
    ] {
        assert!(session.is_quali_type_session());
    }

    for session in [
        SessionType24::RACE,
        SessionType24::RACE_2,
        SessionType24::RACE_3,
    ] {
        assert!(session.is_race_type_session());
    }

    assert!(SessionType24::TIME_TRIAL.is_time_trial_type_session());
    assert_eq!(
        SessionType24::ONE_SHOT_SPRINT_SHOOTOUT.to_string(),
        "One Shot Sprint Shootout"
    );
    assert_eq!(SessionType24::try_from(18), Ok(SessionType24::TIME_TRIAL));
    assert!(SessionType24::try_from(99).is_err());
}
