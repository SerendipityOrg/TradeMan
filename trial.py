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

# from kiteconnect import KiteConnect
# from pprint import pprint

# api_key = '6b0dp5ussukmo67h'
# api_secret = 'eln2qrqob5neowjuedmbv0f0hzq6lhby'
# kite = KiteConnect(api_key=api_key)
# # print(kite.login_url())
# data = kite.generate_session('dVSA80jTIZy8wQ4t90Sz2sDmELz9w2fL', api_secret=api_secret)
# print(data)
# print(kite.set_access_token(data["access_token"]))


#update ChromeDriver


# from pya3 import *

# alice = Aliceblue("929016",'NRmFZkHUFYn08WrOT340eRGR5Sh4NdQ3arVBEak3UvgimY91CftfTWvx9QRXYLAtgCFFkrKQ1ax5yTaPKINLYLiLK48YziRLHFv84lf1v8hKWlBjclQhggNXJaj5h67f')
# alice.get_session_id()

# order_id = alice.place_order(transaction_type = TransactionType.Buy,
#                     instrument =alice.get_instrument_for_fno(exch="NFO",symbol='BANKNIFTY', expiry_date="2023-09-13", is_fut=False,strike=44500, is_CE=False),
#                     quantity = 15,
#                     order_type = OrderType.Market,
#                     product_type = ProductType.Intraday,
#                     price=0.0,
#                     trigger_price = 0.0)

                             
# order_id_value = order_id.get('NOrdNo')
# print(order_id_value)
# avg_prc_data = alice.get_order_history(order_id_value)
# avg_prc = avg_prc_data.get('AvgPrice')

# print(avg_prc)


# output flowchart code.


from kiteconnect import KiteConnect
from pprint import pprint
kite = KiteConnect(api_key='6b0dp5ussukmo67h')
kite.set_access_token('8eNVAA7XVfuRJJcHG1Oqm15eYYHs7nxS')

order_history = kite.order_history(order_id='230911500362923')
pprint(order_history)