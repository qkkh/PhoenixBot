import asyncio, os, discord, datetime
from discord.ext import commands, tasks
from discord import app_commands
from flask import Flask
from threading import Thread
from easy_pil import Editor, load_image_async #

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
        super().__init__(command_prefix="!", intents=discord.Intents.all())
    
    async def setup_hook(self):
        await self.tree.sync()
        if not self.auto_refresh_task.is_running():
            self.auto_refresh_task.start()

    # --- نظام الترحيب بالأفاتار الموزون بدقة ---
    async def on_member_join(self, member):
        channel = self.get_channel(WELCOME_ROOM_ID)
        if channel:
            welcome_text = (
                f"_'Have fun in **__PhoenixRising__**_\n"
                f"     _'User: {member.mention}_<a:Via1:1378238620418183188>"
            ) #
            try:
                # تحميل الخلفية الأصلية المرفوعة
                background = Editor("welcome.png")
                avatar_image = await load_image_async(member.display_avatar.url)
                
                # تصغير الحجم ليتناسب مع الدائرة بدقة
                avatar = Editor(avatar_image).resize((150, 150)).circle_image()
                
                # الإحداثيات الموزونة للوسط بالضبط
                background.paste(avatar, (60, 82)) 
                
                file = discord.File(fp=background.image_bytes, filename="welcome_card.png")
                await channel.send(content=welcome_text, file=file)
            except Exception as e:
                print(f"Error drawing image: {e}")
                await channel.send(welcome_text)

    # --- تحديث الإحصائيات التلقائي ---
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

# --- الأوامر الإدارية (Slash Commands) ---

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

@bot.tree.command(name="سجن", description="ميوت مؤقت (تايم أوت)")
@app_commands.checks.has_permissions(moderate_members=True)
async def timeout(interaction: discord.Interaction, العضو: discord.Member, الدقائق: int):
    duration = datetime.timedelta(minutes=الدقائق)
    await العضو.timeout(duration)
    await interaction.response.send_message(f"⏳ تم سجن {العضو.mention} لـ {الدقائق} دقيقة")

@bot.tree.command(name="حظر", description="حظر عضو نهائياً")
@app_commands.checks.has_permissions(ban_members=True)
async def ban(interaction: discord.Interaction, العضو: discord.Member, السبب: str = "غير محدد"):
    await العضو.ban(reason=السبب)
    await interaction.response.send_message(f"🚫 تم حظر {العضو.name}")

@bot.tree.command(name="طرد", description="طرد عضو من السيرفر")
@app_commands.checks.has_permissions(kick_members=True)
async def kick(interaction: discord.Interaction, العضو: discord.Member, السبب: str = "غير محدد"):
    await العضو.kick(reason=السبب)
    await interaction.response.send_message(f"👞 تم طرد {العضو.name}")

@bot.tree.command(name="فك_حظر", description="إلغاء الحظر باستخدام ID")
@app_commands.checks.has_permissions(ban_members=True)
async def unban(interaction: discord.Interaction, ايدي_العضو: str):
    user = await bot.fetch_user(ايدي_العضو)
    await interaction.guild.unban(user)
    await interaction.response.send_message(f"✅ تم فك حظر {user.name}")

@bot.tree.command(name="الحالة", description="تغيير حالة البوت")
async def change_status(interaction: discord.Interaction, النص: str):
    if interaction.user.id == OWNER_ID:
        await bot.change_presence(activity=discord.Game(name=النص))
        await interaction.response.send_message(f"✅ تم تغيير الحالة إلى: {النص}", ephemeral=True)

if __name__ == '__main__':
    keep_alive()
    bot.run(os.getenv('DISCORD_TOKEN'))
