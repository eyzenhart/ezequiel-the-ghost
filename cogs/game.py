import discord
from discord.ext import commands
from pymongo import MongoClient

class Game(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.cluster = MongoClient("mongodb+srv://eyzenhart:H0ZFBDMfmSQqS3qe@cluster0.ngjuw.mongodb.net/ezequiel?retryWrites=true&w=majority")
        self.collection = self.cluster.ezequiel.friends_of_ezequiel
  

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.client.user:
            return

        user = message.author
        data = self.collection.find_one({"_id": user.id})

        if data["xp"] == 500 + 100 * data["lvl"]:
            self.collection.update_one({"_id": user.id},
            {"$set": {"lvl": data["lvl"] + 1}})
            self.collection.update_one({"_id": user.id},
            {"$set": {"xp": 0}})

            await message.channel.send(f"{user.mention}, поздравляю. Ты стал(-а) сильнее на 1 уровень!")
        else:
            self.collection.update_one({"_id": user.id},
            {"$set": {"xp": data["xp"] + 50}})


    @commands.command(
        name = "баланс", 
        aliases = ["balance", "cash", "money"],
        brief = "Узнайте остаток на счету",
        usage = "balance<@user>"
    )
    async def user_balance(self, ctx, member: discord.Member = None):
        
        if member is None:
            await ctx.send(embed = discord.Embed(
                description = f"Остаток на счету пользователя __{ctx.author}__: {self.collection.find_one({'_id': ctx.author.id})['balance']}"
            ))
        else:
            await ctx.send(embed = discord.Embed(
                description = f"Остаток на счету пользователя __{member}__: {self.collection.find_one({'_id': member.id})['balance']}"
            ))
    

    @commands.command(
        name = "перевод", 
        aliases = ["pay", "give"],
        brief = "Подарите другу ваши э-коины",
        usage = "pay <@user> <amount>"
    )
    async def pay_money(self, ctx, member: discord.Member, amount: int):
        
        ubalance = self.collection.find_one({"_id": ctx.author.id})["balance"]
        mbalance = self.collection.find_one({"_id": member.id})["balance"]

        if amount <= 0:
            await ctx.send(embed = discord.Embed(
                description = f"__{ctx.author}__, не надо так делать, ладно?"
            ))
        else:
            self.collection.update_one({"_id": ctx.author.id},
            {"$set": {"balance": ubalance - amount}})

            self.collection.update_one({"_id": member.id},
            {"$set": {"balance": mbalance + amount}})

            await ctx.message.add_reaction("💸")


def setup(client):
    client.add_cog(Game(client))
    