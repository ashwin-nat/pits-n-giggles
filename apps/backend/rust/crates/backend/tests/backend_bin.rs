use std::io::{BufRead, BufReader};
use std::path::PathBuf;
use std::process::{Command, Stdio};

#[test]
fn backend_binary_reports_pid_and_init_complete() {
    let mut child = Command::new(resolve_backend_binary())
        .args(["--quiet", "--bind-ip", "127.0.0.1", "--telemetry-port", "0"])
        .stdout(Stdio::piped())
        .stderr(Stdio::null())
        .spawn()
        .expect("spawn backend binary");

    let stdout = child.stdout.take().expect("stdout pipe");
    let mut reader = BufReader::new(stdout);

    let mut first_line = String::new();
    reader.read_line(&mut first_line).expect("read pid line");
    assert!(first_line.starts_with("<<PNG_LAUNCHER_CHILD_PID:"));

    let mut second_line = String::new();
    reader
        .read_line(&mut second_line)
        .expect("read init complete line");
    assert_eq!(second_line.trim(), "<<__PNG_SUBSYSTEM_INIT_COMPLETE__>>");

    child.kill().expect("kill child");
    child.wait().expect("wait child");
}

fn resolve_backend_binary() -> PathBuf {
    let cargo_bin = PathBuf::from(env!("CARGO_BIN_EXE_backend"));
    if cargo_bin.is_file() {
        return cargo_bin;
    }

    let test_exe = std::env::current_exe().expect("current test executable");
    let debug_dir = test_exe
        .parent()
        .and_then(|path| path.parent())
        .expect("target debug directory");
    let binary_name = if cfg!(windows) {
        "backend.exe"
    } else {
        "backend"
    };
    let fallback = debug_dir.join(binary_name);
    assert!(
        fallback.is_file(),
        "backend binary not found via cargo env ({}) or fallback ({})",
        cargo_bin.display(),
        fallback.display()
    );
    fallback
}
