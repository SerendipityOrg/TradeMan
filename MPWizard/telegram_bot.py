from telethon import TelegramClient

class TelegramBot:
    def __init__(self):
        api_id = 22353756  # This should be an integer
        api_hash = "351041b3c3951a0a116652896d55d9a2"  # This should be a string
        receiver_phone_number = '+919902106162' 
        self.client = TelegramClient(receiver_phone_number, api_id, api_hash)
        self.client.start()

    def send_message(self, message):
        self.client.send_message(entity = 902575766, message=message)

    def wait_for_response(self):
        # Wait for the user's response and return it
        pass


# api_id = 28308447
# api_hash = '63b0228d40d21350751400088775536a'

# # client = TelegramClient(name, api_id, api_hash)

# # username = await client.get_entity('username')
# with TelegramClient('amol', api_id, api_hash) as client:
#     client.loop.run_until_complete(client.send_message('omkarhegde', 'Hello, myself!')
