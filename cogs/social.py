import discord
from discord.ext import commands
from pymongo import MongoClient

MONG0 = "mongodb+srv://eyzenhart:H0ZFBDMfmSQqS3qe@cluster0.ngjuw.mongodb.net/ezequiel?retryWrites=true&w=majority"
cluster = MongoClient(MONG0)
friends_collection = cluster.ezequiel.friends_of_ezequiel

class Social(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_member_join(self, member):
        channel = discord.utils.get(member.guild.channels, name='general')
        await channel.send(f"Ура, {member.mention} теперь с нами! Чувствуй(-те) себя как дома, советую начать с команды '!help'")
    

    @commands.command(
        name = "стереть", 
        aliases = ["clear", "delete", "del"],
        brief = "Удалите сообщения (admin)",
        usage = "clear number"
    )
    @commands.has_permissions(administrator = True)
    async def clear(self, ctx, amount = 100):
        await ctx.channel.purge(limit = amount)


    @commands.command(
        name = "забанить",
        aliases = ["ban", "kick"],
        brief = "Выгоните и забаньте пользователя (admin)",
        usage = "ban <@user>"
    )
    @commands.has_permissions(administrator = True)
    async def ban(self, ctx, member: discord.Member, *, reason = None):
        await ctx.channel.purge(limit = 1)

        await member.ban(reason = reason)
        await ctx.send(f"{member.mention} был забанен")


    @commands.command(
        name = "автор",
        aliases = ["author", "creator"],
        brief = "Кто сделал этого бота?",
    )
    async def creator(self, ctx):
        await ctx.send("Я создан студенткой РТУ МИРЭА, Дубосарской Таисией, как курсовой проект по дисциплине 'Технологии программирования в среде Python'. 2020 год.")


    @commands.command(
        name = "топ",
        aliases = ["top", "leaders"],
        brief = "Откройте доску лидеров",
    )
    async def leaders(self, ctx):
        embed = discord.Embed(title = "Top 10")
        counter = 0

        for user in friends_collection.find({"server": ctx.guild.id}).sort("lvl", -1).limit(10):
            counter += 1
            embed.add_field(
                name = f"#{counter} {self.client.get_user(user['_id'])}",
                value = f"Level: {user['lvl']}",
                inline = False
            )

        await ctx.send(embed = embed)


def setup(client):
    client.add_cog(Social(client))
