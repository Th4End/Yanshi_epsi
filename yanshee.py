"""
yanshee.py — Bibliothèque Python pour contrôler le robot Yanshee depuis un PC
Utilise l'API REST Apollo (port 9090) via Wi-Fi
"""

import requests

class Yanshee:
    def __init__(self, ip: str, port: int = 9090, timeout: int = 10):
        self.base = f"http://{ip}:{port}/v1"
        self.timeout = timeout

    def _handle_response(self, response):
        """Gère la réponse et évite les erreurs sur les corps vides."""
        response.raise_for_status()
        if response.text:
            return response.json()
        return {"status": "success"}

    def _get(self, path, params=None):
        r = requests.get(f"{self.base}{path}", params=params, timeout=self.timeout)
        return self._handle_response(r)

    def _post(self, path, data=None):
        r = requests.post(f"{self.base}{path}", json=data, timeout=self.timeout)
        return self._handle_response(r)

    def _put(self, path, data=None):
        r = requests.put(f"{self.base}{path}", json=data, timeout=self.timeout)
        return self._handle_response(r)

    def _delete(self, path, params=None):
        r = requests.delete(f"{self.base}{path}", params=params, timeout=self.timeout)
        return self._handle_response(r)

    # ─── SYSTÈME ────────────────────────────────────────────────────────────────

    def get_battery(self) -> dict:
        return self._get("/devices/battery").get("data", {})

    def get_volume(self) -> int:
        return self._get("/devices/volume").get("data", {}).get("volume", 0)

    def set_volume(self, volume: int):
        return self._put("/devices/volume", {"volume": volume})

    def get_version(self, type: str = "SN") -> dict:
        return self._get("/devices/versions", params={"type": type})
    
    def get_languages(self) -> str:
        res = self._get("/devices/languages")
        return res.get("data", {}).get("language", "unknown")
    
    def set_language(self, language: str):
        return self._put("/devices/languages", {"language": language})
    
    def get_voices(self) -> list:
        res = self._get("/voice/asr")
        return res.get("data", {}).get("voices", "unknown")

    # ─── MOUVEMENTS ─────────────────────────────────────────────────────────────

    def list_motions(self) -> list:
        return self._get("/motions/list").get("data", {}).get("motions", [])

    def play_motion(self, name: str, repeat: int = 1):
        return self._post("/motions", {"name": name, "repeat": repeat})

    def stop_motion(self):
        return self._delete("/motions")

    # ─── SERVOS ─────────────────────────────────────────────────────────────────

    def set_servos(self, angles: dict, speed: int = 5):
        return self._put("/servos/angles", {"angles": angles, "speed": speed})

    # ─── VOIX (CORRIGÉ) ────────────────────────────────────────────────────────

    def say(self, text: str, language: str = "fr-FR"):
        """
        Fait parler le robot (Text-To-Speech).
        CORRECTION : Le robot exige le champ 'tts' et non 'text'.
        """
        payload = {
            "tts": str(text),
            "language": language
        }
        return self._put("/voice/tts", payload)

    def listen(self, timeout: int = 5) -> str:
        """
        Lance la reconnaissance vocale (ASR).
        CORRECTIF : Le swagger indique 'put' pour /voice/asr
        """
        result = self._put("/voice/asr", {"timeout": timeout})
        return result.get("data", {}).get("text", "")

    # ─── CAPTEURS ───────────────────────────────────────────────────────────────

    def get_ultrasonic(self) -> float:
        data = self._get("/sensors/ultrasonic")
        return data.get("data", {}).get("distance", 0.0)

    # ─── VISION ─────────────────────────────────────────────────────────────────

    def take_photo(self, filename: str = "photo.jpg") -> dict:
        return self._post("/visions/photos", {"name": filename})
    
    def get_vision(self) -> list:
        return self._get("/visions").get("data", {})
    def start_camera(self, resolution: str = "640x480"):
        """Active le flux vidéo MJPEG sur le port 8000."""
        return self._post("/visions/streams", {"resolution": resolution})
    def get_face_tracking(self):
        """Récupère les données de détection de visage du robot."""
        return self._get("/visions", params={"option": "face"})