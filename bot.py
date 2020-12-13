import discord
from discord.ext import commands
import os
from pymongo import MongoClient

TOKEN = os.environ["TOKEN"]
MONG0 = "mongodb+srv://eyzenhart:H0ZFBDMfmSQqS3qe@cluster0.ngjuw.mongodb.net/ezequiel?retryWrites=true&w=majority"
PREFIX = ("?", "!")
INTENTS = discord.Intents().all()

client = commands.Bot(command_prefix = PREFIX, intents = INTENTS)  
cluster = MongoClient(MONG0)
friends_collection = cluster.ezequiel.friends_of_ezequiel


@client.event
async def on_ready():
    print("Bot connected...")

    for guild in client.guilds:
        for member in guild.members:
            post = {
                "_id": member.id,
                "balance": 300,
                "xp": 0,
                "lvl": 1
            }

            if friends_collection.count_documents({"_id": member.id}) == 0:
                friends_collection.insert_one(post)
            
            friends_collection.update_one({"_id": member.id}, {"$set": {"server": guild.id}})


@client.event
async def on_member_join(member):
    post = {
        "_id": member.id,
        "balance": 300,
        "xp": 0,
        "lvl": 1
    }

    if friends_collection.count_documents({"_id": member.id}) == 0:
        friends_collection.insert_one(post)
    
    friends_collection.update_one({"_id": member.id}, {"$set": {"server": member.guild.id}})
    

@client.event
async def on_command_error(ctx, error):
    print(error)

    if isinstance(error, commands.UserInputError):
        await ctx.send(embed = discord.Embed(
            description = f"Правильное использованиие команды: `{ctx.prefix}{ctx.command.name}` ({ctx.command.brief}): `{ctx.prefix}{ctx.command.usage}`"
        ))


@client.command(
    brief = "Загрузка кога (creator only)",
    usage = "load <cog>"
)
@commands.is_owner()
async def load(ctx, extension):
    client.load_extension(f"cogs.{extension}")
    await ctx.send("Cogs are loaded")


@client.command(
    brief = "Отгрузка кога (creator only)",
    usage = "unload <cog>"
)
@commands.is_owner()
async def unload(ctx, extension):
    client.unload_extension(f"cogs.{extension}")
    await ctx.send("Cogs are unloaded")


@client.command(
    brief = "Перезагрузка кога (creator only)",
    usage = "reload <cog>"

)
@commands.is_owner()
async def reload(ctx, extension):
    client.unload_extension(f"cogs.{extension}")
    client.load_extension(f"cogs.{extension}")
    await ctx.send("Cogs are reloaded")


client.load_extension("cogs.main")
client.load_extension("cogs.game")
client.load_extension("cogs.social")


client.run(TOKEN)
