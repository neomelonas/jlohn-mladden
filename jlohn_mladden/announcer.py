import abc
import random
import time

import pyttsx3

from jlohn_mladden.quip import Quip


class Announcer(abc.ABC):

    def __init__(self, config, sound_manager=None):
        self._config = config
        self._sound_manager = sound_manager

        self.main_game = config['calling_for'].lower()
        self.calling_for = self.main_game
        self.last_pbps = []

    def on_update(self):
        def callback(schedule, index):
            if not schedule or index.get(self.calling_for, '') not in schedule:
                return []
            game = schedule[index[self.calling_for]]
            pbp = game.last_update
            if not pbp:
                return []
            self.on_play_by_play(pbp)
            quips = Quip.say_quips(pbp, game)
            for quip in quips:
                if quip in self.last_pbps:
                    continue
                self.last_pbps.append(quip)
                self.enqueue_message(quip)

            self.last_pbps = self.last_pbps[-4:]  # redundancy
            self.speak()

        return callback

    def on_schedule(self, schedule):
        """
        Override with custom logic to process a new schedule update.
        """
        pass

    def on_play_by_play(self, message):
        """
        Override with custom logic to process play by play for calling_game, ie voice switching
        """
        pass

    @abc.abstractmethod
    def enqueue_message(self, message):
        """
        Override with logic to enqueue a message to your output of choice.
        """
        pass

    @abc.abstractmethod
    def speak(self):
        """
        Override to tell your output to flush enqueued messages as appropriate
        """
        pass


class TTSAnnouncer(Announcer):

    def __init__(self, config, sound_manager=None):
        super().__init__(config, sound_manager)
        self.voice = pyttsx3.init(debug=True)
        self.voice.connect('started-utterance', self.sound_effect)

        voice_ids = set([self.voice.getProperty('voice')])
        system_voices = [v.id for v in self.voice.getProperty('voices')]
        for voice in config.get('friends', []):
            if voice in system_voices:
                voice_ids.add(voice)
        self.voice_ids = list(voice_ids)
        self.voice.setProperty('voice', random.choice(self.voice_ids))

    def sound_effect(self, name):
        if self._sound_manager:
            self._sound_manager.cue_sound(name)

    def enqueue_message(self, message):
        self.voice.say(message, message)

    def speak(self):
        self.voice.runAndWait()