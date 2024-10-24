from discord.ext.commands import Bot

class TalkingBot(Bot):
    def __init__(self,command_prefix,intents):
        self.music_queue = []
        super().__init__(command_prefix=command_prefix,intents=intents)
    
    def clear_music_queue(self):
        self.music_queue = [self.music_queue[0]]

    def pass_to_next_music(self):
        self.music_queue = self.music_queue[1:]

    def get_next_music(self):
        next_music= self.music_queue[0]
        return next_music

    def music_queue_is_empty(self):
        return len(self.music_queue) == 0

    def add_music_to_queue(self,music_url):
        self.music_queue.append(music_url)