# from kiteconnect import KiteConnect
# import datetime

# kite = KiteConnect(api_key="6b0dp5ussukmo67h",access_token="qMh2CuBZJVNNY05HjAbgvSxHkmZM7w4R")

# order = kite.modify_order(
#     variety=kite.VARIETY_REGULAR,
#     order_id="210201000000000",
    

# # )
# import discord
# import os
# from discord.ext import commands
# import asyncio

# client = commands.Bot(command_prefix = '=',intents=discord.Intents.all())

# @client.event
# async def on_ready():
#     await client.tree.sync()
#     print('Bot is ready.')

# async def load():
#     for filename in os.listdir('./cogs'):
#         if filename.endswith('.py'):
#             client.load_extension(f'cogs.{filename[:-3]}')

# class TestMenuButton(discord.ui.View):
#     def __init__(self):
#         super().__init__(timeout=None)

#     @discord.ui.button(label='Test', style=discord.ButtonStyle.blurple)
#     async def test(self, interaction:discord.Interaction, Button:discord.ui.Button):
#         await interaction.channel.send(content='Test')
#     @discord.ui.button(label='Test2', style=discord.ButtonStyle.green)
#     async def test2(self, interaction:discord.Interaction, Button:discord.ui.Button):
#         await interaction.channel.send(content='Test2')
#     @discord.ui.button(label='Test3', style=discord.ButtonStyle.red)
#     async def test3(self, interaction:discord.Interaction, Button:discord.ui.Button):
#         await interaction.channel.send(content='Test3')

# @client.tree.command(name='buttonmenu')
# async def buttonmenu(interaction: discord.Interaction):
#     await interaction.response.send_message(content='Here is the button menu!', view=TestMenuButton())

# async def main():
#     async with client:
#         await client.start('MTEyODk0NjM1ODM2ODM1ODU1MQ.GXdOeu.lR7IU7OB8AqhSySBMde6oQas5P0AUzys1HpF5k')

# asyncio.run(main())

# from pya3 import *
# from pprint import pprint

# alice = Aliceblue(user_id='929016',api_key='NRmFZkHUFYn08WrOT340eRGR5Sh4NdQ3arVBEak3UvgimY91CftfTWvx9QRXYLAtgCFFkrKQ1ax5yTaPKINLYLiLK48YziRLHFv84lf1v8hKWlBjclQhggNXJaj5h67f')
# alice.get_session_id()

# margin = (alice.get_balance())
# print(margin[0]['net'])

from kiteconnect import KiteConnect
from pprint import pprint
username = "YY0222"
api_key = "6b0dp5ussukmo67h"
access_token = "2nfZjbZbw7B1lnFrkKB2G7ya6ezvDEOm"
kite = KiteConnect(api_key=api_key)
kite.set_access_token(access_token)



orders = (kite.orders())


if orders[0]['status'] == 'COMPLETE':
    print(orders['tradingsymbol'])

# margins = (kite.margins(segment="equity"))

# print(margins['available']['live_balance'])





