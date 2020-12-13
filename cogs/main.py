import discord
from discord.ext import commands
import asyncio
import functools
import itertools
import math
import random

import youtube_dl
from async_timeout import timeout


youtube_dl.utils.bug_reports_message = lambda: ""

class VoiceError(Exception):
    pass

class YTDLError(Exception):
    pass

class YTDLSource(discord.PCMVolumeTransformer):
    YTDL_OPTIONS = {
        "format": "bestaudio/best",
        "extractaudio": True,
        "audioformat": "mp3",
        "outtmpl": "%(extractor)s-%(id)s-%(title)s.%(ext)s",
        "restrictfilenames": True,
        "noplaylist": True,
        "nocheckcertificate": True,
        "ignoreerrors": False,
        "logtostderr": False,
        "quiet": True,
        "no_warnings": True,
        "default_search": "auto",
        "source_address": "0.0.0.0",
    }

    FFMPEG_OPTIONS = {
        "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
        "options": "-vn",
    }

    ytdl = youtube_dl.YoutubeDL(YTDL_OPTIONS)

    def __init__(self, ctx: commands.Context, source: discord.FFmpegPCMAudio, *, data: dict, volume: float = 0.5):
        super().__init__(source, volume)

        self.requester = ctx.author
        self.channel = ctx.channel
        self.data = data

        self.title = data.get("title")
        self.thumbnail = data.get("thumbnail")
        self.description = data.get("description")
        self.url = data.get("webpage_url")
        self.stream_url = data.get("url")

    def __str__(self):
        return "**{0.title}**".format(self)

    @classmethod
    async def create_source(cls, ctx: commands.Context, search: str, *, loop: asyncio.BaseEventLoop = None):
        loop = loop or asyncio.get_event_loop()

        partial = functools.partial(cls.ytdl.extract_info, search, download=False, process=False)
        data = await loop.run_in_executor(None, partial)

        if data is None:
            raise YTDLError("Не могу найти ничего похожего на `{}`".format(search))

        if "entries" not in data:
            process_info = data
        else:
            process_info = None
            for entry in data["entries"]:
                if entry:
                    process_info = entry
                    break

            if process_info is None:
                raise YTDLError("Не могу найти ничего похожего на `{}`".format(search))

        webpage_url = process_info["webpage_url"]
        partial = functools.partial(cls.ytdl.extract_info, webpage_url, download=False)
        processed_info = await loop.run_in_executor(None, partial)

        if processed_info is None:
            raise YTDLError("Невозможно получить `{}`".format(webpage_url))

        if "entries" not in processed_info:
            info = processed_info
        else:
            info = None
            while info is None:
                try:
                    info = processed_info["entries"].pop(0)
                except IndexError:
                    raise YTDLError("Не могу найти ничего похожего на `{}`".format(webpage_url))

        return cls(ctx, discord.FFmpegPCMAudio(info["url"], **cls.FFMPEG_OPTIONS), data=info)


class Song:
    __slots__ = ("source", "requester")

    def __init__(self, source: YTDLSource):
        self.source = source
        self.requester = source.requester

    def create_embed(self):
        embed = (discord.Embed(title="Cейчас играет",
                               description="```css\n{0.source.title}\n```".format(self),
                               color=discord.Color.blurple())
                 .add_field(name="Поставил(-а)", value=self.requester.mention)
                 .add_field(name="URL", value="[Ссылка]({0.source.url})".format(self))
                 .set_thumbnail(url=self.source.thumbnail))

        return embed


class SongQueue(asyncio.Queue):
    def __getitem__(self, item):
        if isinstance(item, slice):
            return list(itertools.islice(self._queue, item.start, item.stop, item.step))
        else:
            return self._queue[item]

    def __iter__(self):
        return iter(self._queue)

    def __len__(self):
        return self.qsize()

    def clear(self):
        self._queue.clear()

    def remove(self, index: int):
        del self._queue[index]


class VoiceState:
    def __init__(self, bot: commands.Bot, ctx: commands.Context):
        self.bot = bot
        self._ctx = ctx

        self.current = None
        self.voice = None
        self.next = asyncio.Event()
        self.songs = SongQueue()

        self._loop = False
        self._volume = 0.5
        self.skip_votes = set()

        self.audio_player = bot.loop.create_task(self.audio_player_task())

    def __del__(self):
        self.audio_player.cancel()

    @property
    def loop(self):
        return self._loop

    @loop.setter
    def loop(self, value: bool):
        self._loop = value

    @property
    def volume(self):
        return self._volume

    @volume.setter
    def volume(self, value: float):
        self._volume = value

    @property
    def is_playing(self):
        return self.voice and self.current

    async def audio_player_task(self):
        while True:
            self.next.clear()

            if not self.loop:

                try:
                    async with timeout(180): 
                        self.current = await self.songs.get()
                except asyncio.TimeoutError:
                    self.bot.loop.create_task(self.stop())
                    return

            self.current.source.volume = self._volume
            self.voice.play(self.current.source, after=self.play_next_song)
            await self.current.source.channel.send(embed=self.current.create_embed())

            await self.next.wait()

    def play_next_song(self, error=None):
        if error:
            raise VoiceError(str(error))

        self.next.set()

    def skip(self):
        self.skip_votes.clear()

        if self.is_playing:
            self.voice.stop()

    async def stop(self):
        self.songs.clear()

        if self.voice:
            await self.voice.disconnect()
            self.voice = None


class Music(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.voice_states = {}

    def get_voice_state(self, ctx: commands.Context):
        state = self.voice_states.get(ctx.guild.id)
        if not state:
            state = VoiceState(self.bot, ctx)
            self.voice_states[ctx.guild.id] = state

        return state

    def cog_unload(self):
        for state in self.voice_states.values():
            self.bot.loop.create_task(state.stop())

    def cog_check(self, ctx: commands.Context):
        if not ctx.guild:
            raise commands.NoPrivateMessage("Нельзя использовать в этом канале")

        return True

    async def cog_before_invoke(self, ctx: commands.Context):
        ctx.voice_state = self.get_voice_state(ctx)

    async def cog_command_error(self, ctx: commands.Context, error: commands.CommandError):
        await ctx.send("Ошибка: {}".format(str(error)))

    @commands.command(name = "присоединиться", aliases = ["join"], 
                      brief = "Пригласите бота в ваш канал", invoke_without_subcommand=True)
    async def _join(self, ctx: commands.Context):

        destination = ctx.author.voice.channel
        if ctx.voice_state.voice:
            await ctx.voice_state.voice.move_to(destination)
            return

        ctx.voice_state.voice = await destination.connect()


    @commands.command(name="выйти", aliases=["leave"], brief = "Попросите бота покинуть ваш канал")
    async def _leave(self, ctx: commands.Context):

        if not ctx.voice_state.voice:
            return await ctx.send("Вы не подключены к аудио-каналу!")

        await ctx.voice_state.stop()
        del self.voice_states[ctx.guild.id]


    @commands.command(name="играет", aliases=["now"], brief = "Узнайте, какая песня сейчас играет")
    async def _now(self, ctx: commands.Context):

        await ctx.send(embed=ctx.voice_state.current.create_embed())

    @commands.command(name="пауза", aliases = ["pause"], brief = "Приостановите воспроизведение музыки")
    async def _pause(self, ctx: commands.Context):

        server = ctx.message.guild
        voice_channel = server.voice_client
        voice_channel.pause()

    @commands.command(name="продолжить", aliases = ["resume"], brief = "Продолжайте воспроизведение музыки")
    async def _resume(self, ctx: commands.Context):

        server = ctx.message.guild
        voice_channel = server.voice_client
        voice_channel.resume()

    @commands.command(name="пропустить", aliases = ["skip"], brief = "Пропустите трек")
    async def _skip(self, ctx: commands.Context):

        if not ctx.voice_state.is_playing:
            return await ctx.send("Сейчас ничего не играет!")

        voter = ctx.message.author
        if voter == ctx.voice_state.current.requester:
            ctx.voice_state.skip()

    @commands.command(name="очередь", aliases = ["queue"], brief = "Просмотрите вашу очередь")
    async def _queue(self, ctx: commands.Context, *, page: int = 1):

        if len(ctx.voice_state.songs) == 0:
            return await ctx.send("Очередь пуста.")

        items_per_page = 10
        pages = math.ceil(len(ctx.voice_state.songs) / items_per_page)

        start = (page - 1) * items_per_page
        end = start + items_per_page

        queue = ""
        for i, song in enumerate(ctx.voice_state.songs[start:end], start=start):
            queue += "`{0}.` [**{1.source.title}**]({1.source.url})\n".format(i + 1, song)

        embed = (discord.Embed(description="**{} Следующие треки:**\n\n{}".format(len(ctx.voice_state.songs), queue))
                 .set_footer(text="Страница {}/{}".format(page, pages)))
        await ctx.send(embed=embed)


    @commands.command(name = "убрать", aliases = ["remove"], brief = "Удалите трек из очереди")
    async def _remove(self, ctx: commands.Context, index: int):

        if len(ctx.voice_state.songs) == 0:
            return await ctx.send("Очередь и так пуста.")

        ctx.voice_state.songs.remove(index - 1)

    @commands.command(name = "проиграть", aliases = ["play"], brief = "Начните слушать музыку")
    async def _play(self, ctx: commands.Context, *, search: str):

        if not ctx.voice_state.voice:
            await ctx.invoke(self._join)

        async with ctx.typing():
            try:
                source = await YTDLSource.create_source(ctx, search, loop=self.bot.loop)
            except YTDLError as e:
                await ctx.send("Произошла ошибка во время запроса: {}".format(str(e)))
            else:
                song = Song(source)

                await ctx.voice_state.songs.put(song)
                await ctx.send("В очередь добавлен {}".format(str(source)))

    @_join.before_invoke
    @_play.before_invoke
    async def ensure_voice_state(self, ctx: commands.Context):
        if not ctx.author.voice or not ctx.author.voice.channel:
            raise commands.CommandError("Вы не подключены к аудио-каналу")

        if ctx.voice_client:
            if ctx.voice_client.channel != ctx.author.voice.channel:
                raise commands.CommandError("Бот уже подключен к аудио-каналу")


def setup(client):
    client.add_cog(Music(client))