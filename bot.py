#!/usr/bin/env python

import asyncio

import discord
import poe_parser


class PoeClient(discord.Client):
    def __init__(self):
        super().__init__()

    async def on_ready(self):
        print("Connected to {}".format(client.guilds))

    async def on_message(self, message):
        if message.content.startswith("!dmg"):
            data = await self.get_character_output(message.content)
            await message.channel.send(data)

    async def get_character_output(self, message):
        parts = message.split(" ")
        c = poe_parser.Character(parts[1], parts[2])
        return c.get_dominant_increase()


if __name__ == "__main__":
    with open("token") as f:
        token = f.read()
    client = PoeClient()
    client.run(token)
