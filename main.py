import asyncio, os, discord
from discord.ext import commands, tasks
from discord import app_commands
from flask import Flask
from threading import Thread
import datetime

# --- نظام الاستضافة (لضمان عمل البوت 24 ساعة) ---
app = Flask('')
@app.route('/')
def home(): return "Phoenix Rising System Active"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run); t.daemon = True; t.start()

# --- الإعدادات الثابتة ---
WELCOME_ROOM_ID = 1347630031337160764
CATEGORY_ID = 1497599277793284248 
OWNER_ID = 1341796578742243338

class MyBot(commands.Bot):
    def __init__(self):
        # تفعيل الـ Intents لضمان الترحيب التلقائي
        super().__init__(command_prefix="!", intents=discord.Intents.all())
    
    async def setup_hook(self):
        # مزامنة أوامر السلاش (/)
        await self.tree.sync()
        if not self.auto_refresh_task.is_running():
            self.auto_refresh_task.start()

    async def on_ready(self):
        print(f"Logged in as {self.user.name}")

    # --- 1. نظام الترحيب التلقائي (نص منسق + صورة الملف المحلي) ---
    async def on_member_join(self, member):
        channel = self.get_channel(WELCOME_ROOM_ID)
        if channel:
            # النص المنسق المطلوب بالضبط
            welcome_text = (
                f"_'Have fun in **__PhoenixRising__**_\n"
                f"     _'User: {member.mention}_<a:Via1:1378238620418183188>"
            )
            
            # إرسال صورة welcome.png من المجلد الرئيسي
            try:
                file = discord.File("welcome.png", filename="welcome.png")
                await channel.send(content=welcome_text, file=file) #
            except Exception as e:
                print(f"خطأ في تحميل الصورة: {e}")
                await channel.send(welcome_text)

    # --- 2. نظام الإحصائيات التلقائي ---
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

# --- 3. الأوامر الإدارية (بالعربي) ---

@bot.tree.command(name="حالة_السيرفر", description="تحديث الإحصائيات فوراً")
async def manual_refresh(interaction: discord.Interaction):
    if interaction.user.id != OWNER_ID: return
    await interaction.response.defer(ephemeral=True)
    await bot.refresh_stats(interaction.guild)
    await interaction.followup.send("Just stay calm - تم التحديث", ephemeral=True)

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

@bot.tree.command(name="سجن", description="ميوت مؤقت للعضو")
@app_commands.checks.has_permissions(moderate_members=True)
async def timeout(interaction: discord.Interaction, العضو: discord.Member, الدقائق: int):
    duration = datetime.timedelta(minutes=الدقائق)
    await العضو.timeout(duration)
    await interaction.response.send_message(f"⏳ تم سجن {العضو.mention} لمدة {الدقائق} دقيقة")

if __name__ == '__main__':
    keep_alive()
    bot.run(os.getenv('DISCORD_TOKEN'))
