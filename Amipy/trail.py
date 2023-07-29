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


from kiteconnect import KiteConnect

username = "YY0222"
api_key = "6b0dp5ussukmo67h"
access_token = "ohf3V9Up1JH1Fecxh9rSfFwciQsPVTAi"
kite = KiteConnect(api_key=api_key)
kite.set_access_token(access_token)


modify = kite.modify_order(
                        variety=kite.VARIETY_REGULAR,
                        order_id="230727602962249",
                        price=8.1,
                        trigger_price=8.2)
print(modify)

# order = kite.place_order(variety=kite.VARIETY_REGULAR,
#                          tradingsymbol="IDEA",
#                          exchange=kite.EXCHANGE_NSE,
#                         transaction_type=kite.TRANSACTION_TYPE_BUY,
#                         quantity=1,
#                         order_type=kite.ORDER_TYPE_MARKET,
#                         product=kite.PRODUCT_MIS)
# print(order)

# order_id = kite.place_order(variety=kite.VARIETY_REGULAR,
#                             exchange=kite.EXCHANGE_NSE,
#                             price=7.9,
#                             tradingsymbol="IDEA",
#                             transaction_type=kite.TRANSACTION_TYPE_SELL,
#                             quantity=1,
#                             trigger_price=8.0,
#                             product=kite.PRODUCT_MIS,
#                             order_type=kite.ORDER_TYPE_SL)

# print(order_id)

