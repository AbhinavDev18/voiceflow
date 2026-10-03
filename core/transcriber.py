from faster_whisper import WhisperModel


class Transcriber:
    def __init__(self, model_name="tiny.en"):
        self.model = WhisperModel(
            model_name,
            device="cpu",
            compute_type="int8",
        )

    def transcribe(self, audio, sample_rate=16000):
        segments, _ = self.model.transcribe(
            audio,
            language="en",
            vad_filter=True,
            beam_size=1,
        )

        return " ".join(
            segment.text.strip()
            for segment in segments
        ).strip()
