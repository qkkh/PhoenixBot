import asyncio, os, discord
from discord.ext import commands, tasks
from discord import app_commands
from flask import Flask
from threading import Thread

# --- نظام الاستضافة ---
app = Flask('')
@app.route('/')
def home(): return "Phoenix Advanced System Active"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run); t.daemon = True; t.start()

# --- الإعدادات الثابتة ---
PHOENIX_COLOR = 0x00aaff 
CATEGORY_ID = 1497599277793284248 
WELCOME_ROOM_ID = 1347630031337160764
OWNER_ID = 1341796578742243338

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=discord.Intents.all())
    
    async def setup_hook(self):
        # مزامنة الأوامر لتظهر في قائمة السلاش
        await self.tree.sync()
        if not self.auto_refresh_task.is_running():
            self.auto_refresh_task.start()

    async def on_ready(self):
        print(f"Phoenix Slash System is Live and Ready")

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
            bots = len([m for m in guild.members if m.bot])
            await guild.create_voice_channel(name=f"Members: {total}", category=category)
            await guild.create_voice_channel(name=f"Online: {online}", category=category)
            await guild.create_voice_channel(name=f"Bots: {bots}", category=category)

    async def on_member_join(self, member):
        channel = member.guild.get_channel(WELCOME_ROOM_ID)
        if channel:
            embed = discord.Embed(description=f"Welcome , {member.mention} Enjoy your stay in Phoenix Rising", color=PHOENIX_COLOR)
            embed.set_image(url="https://i.postimg.cc/85M8qK2y/welcome.png") #
            await channel.send(content=f"{member.mention}", embed=embed)

bot = MyBot()

# --- حزمة الأوامر الإدارية (Slash Commands) ---

@bot.tree.command(name="حالة_السيرفر", description="تحديث إحصائيات السيرفر (الرومات الصوتية) فوراً")
async def manual_refresh(interaction: discord.Interaction):
    if interaction.user.id != OWNER_ID:
        return await interaction.response.send_message("❌ هذا الأمر للزعيم فقط", ephemeral=True)
    await interaction.response.defer(ephemeral=True)
    await bot.refresh_stats(interaction.guild)
    await interaction.followup.send("Just stay calm - تم تحديث الإحصائيات", ephemeral=True)

@bot.tree.command(name="قفل_القناة", description="قفل الشات ومنع الأعضاء من الكتابة")
@app_commands.checks.has_permissions(manage_channels=True)
async def lock(interaction: discord.Interaction):
    await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=False)
    await interaction.response.send_message("🔒 تم قفل القناة بنجاح")

@bot.tree.command(name="فتح_القناة", description="فتح الشات والسماح للأعضاء بالكتابة")
@app_commands.checks.has_permissions(manage_channels=True)
async def unlock(interaction: discord.Interaction):
    await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=True)
    await interaction.response.send_message("🔓 تم فتح القناة بنجاح")

@bot.tree.command(name="طرد", description="طرد عضو مخالف من السيرفر")
@app_commands.checks.has_permissions(kick_members=True)
async def kick(interaction: discord.Interaction, العضو: discord.Member, السبب: str = "غير محدد"):
    await العضو.kick(reason=السبب)
    await interaction.response.send_message(f"👞 تم طرد {العضو.mention} | السبب: {السبب}")

@bot.tree.command(name="حظر", description="حظر عضو نهائياً من السيرفر")
@app_commands.checks.has_permissions(ban_members=True)
async def ban(interaction: discord.Interaction, العضو: discord.Member, السبب: str = "غير محدد"):
    await العضو.ban(reason=السبب)
    await interaction.response.send_message(f"🚫 تم حظر {العضو.mention} | السبب: {السبب}")

@bot.tree.command(name="مسح", description="تنظيف الشات من عدد معين من الرسائل")
@app_commands.checks.has_permissions(manage_messages=True)
async def clear(interaction: discord.Interaction, العدد: int):
    await interaction.channel.purge(limit=العدد)
    await interaction.response.send_message(f"🧹 تم مسح {العدد} رسالة بنجاح", ephemeral=True)

@bot.tree.command(name="الحالة", description="تغيير النشاط الذي يظهر تحت اسم البوت")
async def change_status(interaction: discord.Interaction, النص: str):
    if interaction.user.id != OWNER_ID:
        return await interaction.response.send_message("❌ لا تملك صلاحية تغيير الحالة", ephemeral=True)
    await bot.change_presence(activity=discord.Game(name=النص))
    await interaction.response.send_message(f"✅ تم تغيير حالة البوت إلى: {النص}", ephemeral=True)

@bot.tree.command(name="سجن", description="إعطاء ميوت (Timeout) لعضو")
@app_commands.checks.has_permissions(moderate_members=True)
async def timeout(interaction: discord.Interaction, العضو: discord.Member, الدقائق: int, السبب: str = "غير محدد"):
    duration = asyncio.tasks.datetime.timedelta(minutes=الدقائق)
    await العضو.timeout(duration, reason=السبب)
    await interaction.response.send_message(f"⏳ تم سجن {العضو.mention} لمدة {الدقائق} دقيقة | السبب: {السبب}")

@bot.tree.command(name="فك_الحظر", description="إزالة الحظر عن عضو (استخدم الـ ID)")
@app_commands.checks.has_permissions(ban_members=True)
async def unban(interaction: discord.Interaction, ايدي_العضو: str):
    user = await bot.fetch_user(int(ايدي_العضو))
    await interaction.guild.unban(user)
    await interaction.response.send_message(f"🔓 تم فك الحظر عن {user.name}")

if __name__ == '__main__':
    keep_alive()
    bot.run(os.getenv('DISCORD_TOKEN'))
