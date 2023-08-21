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

from kiteconnect import KiteConnect
from pprint import pprint

# api_key = '6b0dp5ussukmo67h'
# access_token = 'C462xyhTHBs65ghisB4LXiv82A6rhXyx'
# kite = KiteConnect(api_key=api_key)
# kite.set_access_token(access_token)

# history = kite.order_history(order_id=230818600929703)
# # pprint(history)

# #in history, check for the dict where 'status' is 'COMPLETE'

# for i in history:
#     if i['status'] == 'COMPLETE':
#         print(i['average_price'])











