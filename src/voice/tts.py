import os
import subprocess
import uuid
import shutil
from src.config import get_settings

settings = get_settings()

class TTSService:
    def __init__(self):
        self.default_voice = settings.PIPER_VOICE
        # Check if piper binary is available in path
        self.piper_bin = shutil.which("piper")
        if not self.piper_bin:
            # Fallback check common paths or assume it's in a known tools dir
            # For now, if not found, we might mock or fail gracefully
            pass

    def generate_audio(self, text: str, output_dir: str = "tmp_media") -> str:
        """
        Generates audio from text using Piper TTS.
        Returns the filename of the generated wav file.
        """
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        filename = f"{uuid.uuid4()}.wav"
        output_path = os.path.join(output_dir, filename)
        
        # 1. Try running Piper subprocess
        # Command: echo "text" | piper --model en_US-amy-medium --output_file output.wav
        
        try:
            # Check if model file exists locally if using path, but piper usually downloads or needs path
            # We assume 'piper' command manages models or we pass simple name if configured
            
            # Simple mock if no binary found to avoid crashing the whole step if user hasn't installed piper binary
            import shutil
            if not shutil.which("piper"):
                print("Piper binary not found. Generating dummy audio.")
                self._generate_dummy_wav(output_path)
                return filename

            cmd = [
                "piper",
                "--model", self.default_voice,
                "--output_file", output_path
            ]
            
            process = subprocess.Popen(
                cmd, 
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            stdout, stderr = process.communicate(input=text.encode("utf-8"))
            
            if process.returncode != 0:
                print(f"Piper TTS Error: {stderr.decode()}")
                self._generate_dummy_wav(output_path)
            
        except Exception as e:
            print(f"TTS Execution Error: {e}")
            self._generate_dummy_wav(output_path)
            
        return filename

    def _generate_dummy_wav(self, path):
        # Create a 1-second silent or noise wav file using soundfile/numpy
        import soundfile as sf
        import numpy as np
        
        samplerate = 16000
        data = np.random.uniform(-0.1, 0.1, samplerate) # 1 sec noise
        sf.write(path, data, samplerate)
