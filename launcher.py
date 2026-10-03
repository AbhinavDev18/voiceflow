import gc
import fcntl
import os
import signal
import subprocess
import threading
import time

from PySide6.QtCore import QTimer

from core.audio import AudioRecorder
from core.injector import paste_text
from core.transcriber import Transcriber
from ui_overlay import Overlay, create_app


LOCK_PATH = "/tmp/voiceflow.lock"
PID_PATH = "/tmp/voiceflow.pid"
SOCKET_PATH = "/tmp/.ydotool_socket"

STOP_SIGNAL = signal.SIGUSR1


def send_stop_to_running_instance():
    try:
        with open(PID_PATH, "r", encoding="utf-8") as f:
            pid = int(f.read().strip())
    except (FileNotFoundError, ValueError, OSError):
        return False

    try:
        os.kill(pid, STOP_SIGNAL)
        return True
    except ProcessLookupError:
        try:
            os.remove(PID_PATH)
        except FileNotFoundError:
            pass
        return False
    except PermissionError:
        return False


def acquire_single_instance():
    lock_file = open(LOCK_PATH, "w", encoding="utf-8")

    try:
        fcntl.flock(
            lock_file,
            fcntl.LOCK_EX | fcntl.LOCK_NB,
        )
    except BlockingIOError:
        lock_file.close()
        return None

    return lock_file


def write_pid():
    with open(PID_PATH, "w", encoding="utf-8") as f:
        f.write(str(os.getpid()))


def cleanup_pid():
    try:
        os.remove(PID_PATH)
    except FileNotFoundError:
        pass


def start_ydotoold():
    # A stale socket can survive a crashed daemon.
    try:
        os.remove(SOCKET_PATH)
    except FileNotFoundError:
        pass

    process = subprocess.Popen(
        ["ydotoold"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    for _ in range(200):
        if os.path.exists(SOCKET_PATH):
            break

        if process.poll() is not None:
            raise RuntimeError("ydotoold exited unexpectedly.")

        time.sleep(0.01)
    else:
        process.terminate()
        process.wait(timeout=2)
        raise RuntimeError("ydotoold did not create its socket.")

    os.chmod(SOCKET_PATH, 0o666)
    return process


def stop_ydotoold(process):
    if process is None:
        return

    if process.poll() is None:
        process.terminate()

        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()

    try:
        os.remove(SOCKET_PATH)
    except FileNotFoundError:
        pass


def main():
    # This invocation is the STOP command if another instance exists.
    if send_stop_to_running_instance():
        return 0

    lock = acquire_single_instance()

    if lock is None:
        # The first process may still be writing its PID.
        for _ in range(20):
            if send_stop_to_running_instance():
                return 0
            time.sleep(0.025)
        return 0

    write_pid()

    app = create_app()
    recorder = AudioRecorder()
    overlay = None
    ydotool_process = None

    stop_requested = threading.Event()
    finishing = threading.Event()

    def request_stop(signum, frame):
        stop_requested.set()

    signal.signal(STOP_SIGNAL, request_stop)

    try:
        overlay = Overlay(lambda: recorder.level)
        recorder.start()

        print("VoiceFlow listening...")
        print("Press the shortcut again to stop.")

        # Load the model while the user is speaking.
        # This avoids making the user wait for model loading after stop.
        model_ready = threading.Event()
        model_holder = []
        model_error = []

        def load_model():
            try:
                model_holder.append(Transcriber("tiny.en"))
            except Exception as exc:
                model_error.append(exc)
            finally:
                model_ready.set()

        threading.Thread(
            target=load_model,
            daemon=True,
        ).start()

        def check_stop():
            if stop_requested.is_set() and not finishing.is_set():
                finishing.set()
                finish()
            else:
                QTimer.singleShot(20, check_stop)

        def finish():
            nonlocal overlay
            nonlocal ydotool_process

            print("Stopping recording...")

            audio = recorder.stop()

            if overlay is not None:
                overlay.close()
                overlay = None

            if audio.size == 0:
                del audio
                app.quit()
                return

            try:
                # The model should normally be ready by now.
                model_ready.wait()

                if model_error:
                    raise model_error[0]

                transcriber = model_holder[0]

                print("Transcribing...")
                text = transcriber.transcribe(audio)

                # Audio is no longer needed.
                del audio

                print("\nTRANSCRIPTION:")
                print(text)

                if text:
                    print("Injecting text...")

                    # Only create ydotoold for the injection phase.
                    ydotool_process = start_ydotoold()

                    success = paste_text(text)

                    if success:
                        print("Text injected successfully.")
                    else:
                        print("Text injection failed.")

                    # Give the input event a moment to reach the app.
                    time.sleep(0.05)

                del text
                del transcriber
                model_holder.clear()
                gc.collect()

            except Exception as exc:
                print(f"VoiceFlow error: {exc}")

            finally:
                stop_ydotoold(ydotool_process)
                ydotool_process = None
                gc.collect()
                app.quit()

        QTimer.singleShot(20, check_stop)

        return app.exec()

    except Exception as exc:
        print(f"VoiceFlow startup error: {exc}")
        recorder.stop()

        if overlay is not None:
            overlay.close()

        stop_ydotoold(ydotool_process)
        return 1

    finally:
        cleanup_pid()
        try:
            os.remove(SOCKET_PATH)
        except FileNotFoundError:
            pass


if __name__ == "__main__":
    raise SystemExit(main())
