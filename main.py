import asyncio, os, discord
from discord.ext import commands, tasks
from discord import app_commands
from flask import Flask
from threading import Thread
import datetime
from easy_pil import Editor, load_image_async, Font #

# --- نظام الاستضافة ---
app = Flask('')
@app.route('/')
def home(): return "Phoenix System Active"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run); t.daemon = True; t.start()

# --- الإعدادات ---
WELCOME_ROOM_ID = 1347630031337160764
CATEGORY_ID = 1497599277793284248 
OWNER_ID = 1341796578742243338

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=discord.Intents.all()) #
    
    async def setup_hook(self):
        await self.tree.sync()
        if not self.auto_refresh_task.is_running():
            self.auto_refresh_task.start()

    # --- نظام الترحيب بالأفاتار المتغير ---
    async def on_member_join(self, member):
        channel = self.get_channel(WELCOME_ROOM_ID)
        if channel:
            # 1. النص المنسق المطلوب
            welcome_text = (
                f"_'Have fun in **__PhoenixRising__**_\n"
                f"     _'User: {member.mention}_<a:Via1:1378238620418183188>"
            )

            try:
                # 2. تحميل الخلفية الأساسية (welcome.png اللي رفعتها)
                background = Editor("welcome.png")
                
                # 3. تحميل صورة العضو (Avatar) وجعلها دائرية
                avatar_image = await load_image_async(member.display_avatar.url)
                avatar = Editor(avatar_image).resize((180, 180)).circle_image()
                
                # 4. وضع الأفاتار في المكان المناسب (الإحداثيات التقريبية حسب صورتك)
                background.paste(avatar, (115, 125)) 
                
                # 5. حفظ الصورة وإرسالها
                file = discord.File(fp=background.image_bytes, filename="welcome_card.png")
                await channel.send(content=welcome_text, file=file) #
            except Exception as e:
                print(f"Error: {e}")
                await channel.send(welcome_text)

    @tasks.loop(minutes=30)
    async def auto_refresh_task(self):
        for guild in self.guilds:
            await self.refresh_stats(guild)

    async def refresh_stats(self, guild):
        category = guild.get_channel(CATEGORY_ID)
        if category:
            for ch in category.voice_channels: 
                try: await ch.delete()
                except: pass
            total = guild.member_count
            online = len([m for m in guild.members if m.status != discord.Status.offline])
            await guild.create_voice_channel(name=f"Members: {total}", category=category)
            await guild.create_voice_channel(name=f"Online: {online}", category=category)

bot = MyBot()

# --- الأوامر الإدارية (قفل، فتح، مسح، سجن) ---
@bot.tree.command(name="مسح", description="مسح الرسائل")
@app_commands.checks.has_permissions(manage_messages=True)
async def clear(interaction: discord.Interaction, العدد: int):
    await interaction.channel.purge(limit=العدد)
    await interaction.response.send_message(f"🧹 تم مسح {العدد} رسالة", ephemeral=True)

@bot.tree.command(name="قفل_القناة", description="قفل الشات")
@app_commands.checks.has_permissions(manage_channels=True)
async def lock(interaction: discord.Interaction):
    await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=False)
    await interaction.response.send_message("🔒 تم قفل القناة")

@bot.tree.command(name="فتح_القناة", description="فتح الشات")
@app_commands.checks.has_permissions(manage_channels=True)
async def unlock(interaction: discord.Interaction):
    await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=True)
    await interaction.response.send_message("🔓 تم فتح القناة")

@bot.tree.command(name="سجن", description="ميوت مؤقت")
@app_commands.checks.has_permissions(moderate_members=True)
async def timeout(interaction: discord.Interaction, العضو: discord.Member, الدقائق: int):
    duration = datetime.timedelta(minutes=الدقائق)
    await العضو.timeout(duration)
    await interaction.response.send_message(f"⏳ تم سجن {العضو.mention} لـ {الدقائق} دقيقة")

if __name__ == '__main__':
    keep_alive()
    bot.run(os.getenv('DISCORD_TOKEN'))
