from faster_whisper import WhisperModel


if __name__ == "__main__":
    print("Loading Whisper model...")
    model = WhisperModel(
        "tiny.en",
        device="cpu",
        compute_type="int8",
    )
    print("Whisper loaded.")
