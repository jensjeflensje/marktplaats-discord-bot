import discord
from discord.ext.commands import Bot
from discord.ext import commands
import asyncio
import time
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from discord import NotFound
from config import marktplaats_channel_id, server_name, prefix, help_text

client = discord.Client()

basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(basedir, "data.sqlite")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

class Items(db.Model):
    __tablename__ = "items"

    id = db.Column(db.Integer, primary_key=True)
    itemname = db.Column(db.Text)
    author = db.Column(db.Text)
    price = db.Column(db.Text)
    messageid = db.Column(db.Text)
    deleted = db.Column(db.Text)

    def __init__(self, id, itemname, author, price, messageid, deleted):
        self.id = id
        self.itemname = itemname
        self.author = author
        self.price = price
        self.messageid = messageid
        self.deleted = deleted
    def __repr__(self):
        return  "{}§{}§{}§{}§{}§{}".format(self.id, self.itemname, self.author, self.price, self.messageid, self.deleted)

@client.event
@asyncio.coroutine
async def on_ready():
    print("Bot is ready!")

@client.event
@asyncio.coroutine
async def on_message(message):
        if message.content.split(" ")[0] == prefix + "help":
            embed = discord.Embed(title=server_name + " Marktplaats Help", description=help_text, colour=0xff8040)
            embed.add_field(name="!plaatsadvertentie", value="Hiermee kan je een advertentie plaatsen! \nZo gebruik je het commando: \n{p}plaatsadvertentie <prijs (getal)> <naam advertentie>".format(p=prefix))
            embed.add_field(name="!bied", value="Hiermee kan je op advertenties bieden! \nZo gebruik je het commando: \n{p}bied <id van de advertentie (tussen de ()) <geld dat je wilt bieden (getal)>".format(p=prefix))
            embed.add_field(name="!verkocht", value="Hiermee kan je een advertentie op de verkocht status zetten! \nZo gebruik je het commando: \n{p}verkocht <id van de advertentie (tussen de ())".format(p=prefix))
            embed.set_footer(text=server_name + " Marktplaats discord bot")
            await client.send_message(message.channel, embed=embed)
        if message.content.split(" ")[0] == prefix + "plaatsadvertentie":
            try:
                if message.content.split(" ")[1] != None:
                    if message.content.split(" ")[2] != None:
                        itemname =  " ".join(message.content.split(" ")[2:])
                        if Items.query.all() != []:
                            itemid = str(int(str(Items.query.all()[-1]).split("§")[0]) + 1)
                        else:
                            itemid = "1"
                        price = int(message.content.split(" ")[1])
                        embed = discord.Embed(title="Te verkopen (" + itemid + "):", description="Het item '" + itemname + "' wordt verkocht!", colour=0xff8040)
                        embed.add_field(name="Hoogste bod", value=message.content.split(" ")[1] + " (start bod)")
                        embed.set_footer(text=message.author)
                        await client.send_message(client.get_channel(marktplaats_channel_id), ":beginner: **{name}** :beginner:".format(name=server_name))
                        await client.send_message(message.channel, "Jouw advertentie is geplaatst!")
                        messagefrombot = await client.send_message(client.get_channel(marktplaats_channel_id), embed=embed)
                        item = Items(int(itemid), itemname, str(message.author), message.content.split(" ")[1], str(messagefrombot.id), False)
                        db.session.add(item)
                        db.session.commit()
                    else:
                        message = await client.send_message(message.channel, "Oeps, het lijkt er op dat er iets fout is gegaan bij het opgeven van dit commando!")
                else:
                    message = await client.send_message(message.channel, "Oeps, het lijkt er op dat er iets fout is gegaan bij het opgeven van dit commando!")
            except Exception as e:
                message = await client.send_message(message.channel, "Oeps, het lijkt er op dat er iets fout is gegaan bij het opgeven van dit commando!")
        elif message.content.split(" ")[0] == prefix + "bied":
            try:
                if message.content.split(" ")[1]:
                    item = Items.query.filter_by(id=message.content.split(" ")[1]).first()
                    print(message.content.split(" ")[2])
                    print(item.price)
                    if int(item.deleted) != 1:
                        if int(message.content.split(" ")[2]) > int(item.price):
                            messageid = item.messageid
                            embed = discord.Embed(title="Te verkopen ( " + str(item.id) + " )", description="Het item '" + item.itemname + "' wordt verkocht!", colour=0xff8040)
                            embed.add_field(name="Hoogste bod", value=message.content.split(" ")[2])
                            embed.set_footer(text=item.author)
                            channel = client.get_channel(marktplaats_channel_id)
                            messageforedit = await client.get_message(channel, messageid)
                            await client.edit_message(messageforedit, embed=embed)
                            await client.send_message(channel.server.get_member_named(item.author), "Er is een bod van " + message.content.split(" ")[2]  + " op jouw '" + item.itemname + "' geplaatst door " + str(message.author) + "!")
                            await client.send_message(message.channel, "Jouw bod van " + message.content.split(" ")[2]  + " is geplaatst!")
                            item.price = message.content.split(" ")[2]
                            db.session.commit()
                        else:
                            await client.send_message(message.channel, "Oeps, het lijkt er op dat jouw bod niet groter is dan een bod dat er al staat. Dit moet wel zo zijn!")
                    else:
                        await client.send_message(message.channel, "Oeps, het lijkt er op dat deze advertentie al is verwijderd!")
                else:
                    await client.send_message(message.channel, "Oeps, het lijkt er op dat er iets fout is gegaan bij het opgeven van dit commando!")
            except Exception as e:
                await client.send_message(message.channel, "Oeps, het lijkt er op dat er iets fout is gegaan bij het opgeven van dit commando!")
        elif message.content.split(" ")[0] == prefix + "verkocht":
            try:
                if message.content.split(" ")[1]:
                    item = Items.query.filter_by(id=message.content.split(" ")[1]).first()
                    if str(message.author) == item.author:
                        messageid = item.messageid
                        embed = discord.Embed(title="Verkocht! ( " + str(item.id) + " )", description="Het item '" + item.itemname + "' is verkocht!", colour=0xf44141)
                        embed.add_field(name="Hoogste bod", value=item.price)
                        embed.set_footer(text=item.author)
                        channel = client.get_channel(marktplaats_channel_id)
                        messageforedit = await client.get_message(channel, messageid)
                        await client.edit_message(messageforedit, embed=embed)
                        await client.send_message(message.channel, "Je hebt jouw advertentie met het id " + message.content.split(" ")[1]  + " verwijderd!")
                        item.deleted = True
                        db.session.commit()
                    else:
                        await client.send_message(message.channel, "Oeps, het lijkt er op dat jij niet de eigenaar van deze advertentie bent. Daarom kan jij hem ook niet verwijderen!")
                else:
                    await client.send_message(message.channel, "Oeps, het lijkt er op dat er iets fout is gegaan bij het opgeven van dit commando!")
            except Exception as e:
                await client.send_message(message.channel, "Oeps, het lijkt er op dat er iets fout is gegaan bij het opgeven van dit commando!")

if __name__ == "__main__":
    client.run("NDk1Mjc1MDEyMDk4NjIxNDQw.DwpBGw.0n74VZt8F7-A7HjOIcsw9aiI5uw")
