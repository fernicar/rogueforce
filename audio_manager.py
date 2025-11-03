import pygame
from asset_manager import asset_manager
from config import DEBUG, AUDIO_ENABLED, SFX_VOLUME, MUSIC_VOLUME, MASTER_VOLUME

class AudioManager:
    """Manages sound effects and music playback"""
    
    def __init__(self):
        self.enabled = AUDIO_ENABLED
        self.sfx_volume = SFX_VOLUME * MASTER_VOLUME
        self.music_volume = MUSIC_VOLUME * MASTER_VOLUME
        
        if self.enabled:
            try:
                pygame.mixer.set_num_channels(16)
            except Exception as e:
                if DEBUG:
                    print(f"DEBUG: Audio initialization failed: {e}")
                self.enabled = False
    
    def play_sound(self, filename, volume_modifier=1.0):
        """Play a sound effect"""
        if not self.enabled:
            return
        
        sound = asset_manager.load_sound(filename)
        if sound:
            try:
                sound.set_volume(self.sfx_volume * volume_modifier)
                sound.play()
            except Exception as e:
                if DEBUG:
                    print(f"DEBUG: Error playing sound {filename}: {e}")
    
    def play_music(self, filename, loop=-1):
        """Play background music"""
        if not self.enabled:
            return
        
        if asset_manager.load_music(filename):
            try:
                pygame.mixer.music.set_volume(self.music_volume)
                pygame.mixer.music.play(loop)
            except Exception as e:
                if DEBUG:
                    print(f"DEBUG: Error playing music {filename}: {e}")
    
    def stop_music(self):
        """Stop background music"""
        if self.enabled:
            pygame.mixer.music.stop()

# Global audio manager
audio_manager = AudioManager()