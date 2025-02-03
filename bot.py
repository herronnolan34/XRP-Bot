import discord
from discord.ext import commands, tasks
import aiohttp
import asyncio
from datetime import datetime
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)

# Bot configuration
TOKEN = os.getenv('DISCORD_TOKEN')
CHANNEL_ID = int(os.getenv('CHANNEL_ID', 0))  # Convert to int
UPDATE_INTERVAL = 300  # 5 minutes in seconds

# Initialize bot with intents
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

async def fetch_xrp_price():
    """Fetch XRP price from CoinGecko API"""
    async with aiohttp.ClientSession() as session:
        async with session.get('https://api.coingecko.com/api/v3/simple/price?ids=ripple&vs_currencies=usd,eur&include_24hr_change=true') as response:
            if response.status == 200:
                data = await response.json()
                return {
                    'usd': data['ripple']['usd'],
                    'eur': data['ripple']['eur'],
                    'usd_24h_change': data['ripple']['usd_24h_change']
                }
            return None

@tasks.loop(seconds=UPDATE_INTERVAL)
async def price_update():
    """Regular price update task"""
    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        try:
            price_data = await fetch_xrp_price()
            if price_data:
                embed = discord.Embed(
                    title="XRP Price Update",
                    color=0x00ff00 if price_data['usd_24h_change'] >= 0 else 0xff0000,
                    timestamp=datetime.utcnow()
                )
                embed.add_field(
                    name="USD",
                    value=f"${price_data['usd']:.4f}",
                    inline=True
                )
                embed.add_field(
                    name="EUR",
                    value=f"€{price_data['eur']:.4f}",
                    inline=True
                )
                embed.add_field(
                    name="24h Change",
                    value=f"{price_data['usd_24h_change']:.2f}%",
                    inline=True
                )
                
                await channel.send(embed=embed)
                logging.info(f"Price update sent. XRP: ${price_data['usd']:.4f}")
        except Exception as e:
            logging.error(f"Error updating price: {e}")

@bot.event
async def on_ready():
    """Bot initialization"""
    logging.info(f'Bot is ready: {bot.user.name}')
    price_update.start()

@bot.command()
async def price(ctx):
    """Manual price check command"""
    try:
        price_data = await fetch_xrp_price()
        if price_data:
            embed = discord.Embed(
                title="XRP Price Check",
                color=0x00ff00 if price_data['usd_24h_change'] >= 0 else 0xff0000,
                timestamp=datetime.utcnow()
            )
            embed.add_field(
                name="USD",
                value=f"${price_data['usd']:.4f}",
                inline=True
            )
            embed.add_field(
                name="EUR",
                value=f"€{price_data['eur']:.4f}",
                inline=True
            )
            embed.add_field(
                name="24h Change",
                value=f"{price_data['usd_24h_change']:.2f}%",
                inline=True
            )
            
            await ctx.send(embed=embed)
            logging.info(f"Manual price check requested by {ctx.author}")
    except Exception as e:
        logging.error(f"Error in price command: {e}")
        await ctx.send(f"Error fetching price: {e}")

if __name__ == "__main__":
    if not TOKEN:
        logging.error("No token provided")
        exit(1)
    if CHANNEL_ID == 0:
        logging.error("No channel ID provided")
        exit(1)
    bot.run(TOKEN)
