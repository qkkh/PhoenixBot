import asyncio, os, discord, datetime, io, aiohttp
from discord.ext import commands, tasks
from discord import app_commands
from flask import Flask
from threading import Thread
from easy_pil import Editor, Canvas
from PIL import Image

app = Flask('')
@app.route('/')
def home(): return "Phoenix Admin System Active"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# --- الإعدادات ---
WELCOME_ROOM_ID = 1347630031337160764
CATEGORY_ID = 1497599277793284248 
OWNER_ID = 1341796578742243338
LOGS_ROOM_ID = 1347630031337160764 
ARCHIVE_ROOMS = [1378251863098392596, 1378251900348141589, 1378251920237395998]

async def download_image(url):
    headers = {'User-Agent': 'Mozilla/5.0'}
    async with aiohttp.ClientSession(headers=headers) as session:
        try:
            async with session.get(url, timeout=15) as resp:
                if resp.status == 200: return await resp.read()
        except: return None
    return None

async def send_log(guild, title, description, color=0xff0000):
    log_chan = guild.get_channel(LOGS_ROOM_ID)
    if log_chan:
        embed = discord.Embed(title=title, description=description, color=color, timestamp=datetime.datetime.now())
        await log_chan.send(embed=embed)

class MyBot(commands.Bot):
    def __init__(self): super().__init__(command_prefix="!", intents=discord.Intents.all())
    
    async def setup_hook(self):
        await self.tree.sync()
        if not self.auto_refresh_task.is_running(): self.auto_refresh_task.start()

    # --- نظام الأرشفة التلقائي المحسن ---
    async def on_message(self, message):
        if message.author.bot: return
        if message.channel.id in ARCHIVE_ROOMS and message.attachments:
            if len(message.attachments) >= 2:
                await message.delete()
                # أول صورة هي الأفاتار والثانية هي البنر
                av_url = message.attachments[0].url
                bn_url = message.attachments[1].url
                av_d, bn_d = await download_image(av_url), await download_image(bn_url)
                
                if av_d and bn_d:
                    # إنشاء الخلفية السوداء
                    canvas = Editor(Canvas(size=(3188, 2160), color="#000000"))
                    
                    # وضع البنر في الأعلى
                    banner = Editor(Image.open(io.BytesIO(bn_d))).resize((3188, 1100))
                    canvas.paste(banner, (0, 0))
                    
                    # وضع الأفاتار بشكل دائري
                    avatar = Editor(Image.open(io.BytesIO(av_d))).resize((900, 900)).circle_image()
                    canvas.paste(avatar, (100, 550))
                    
                    # دمج ملف template.png (القالب الشفاف اللي فيه الأيقونات والإطارات)
                    if os.path.exists("template.png"):
                        template = Editor("template.png").resize((3188, 2160))
                        canvas.paste(template, (0, 0))
                    
                    file = discord.File(fp=canvas.image_bytes, filename="archive.png")
                    await message.channel.send(file=file)
                    await send_log(message.guild, "أرشفة تلقائية", f"تمت الأرشفة بنجاح في {message.channel.mention}")

        await self.process_commands(message)

    # --- الترحيب بالرسالة الجديدة ---
    async def on_member_join(self, member):
        chan = self.get_channel(WELCOME_ROOM_ID)
        if chan:
            txt = f"_'Have fun in **__PhoenixRising__**_\n     _'User: {member.mention}_<a:Via1:1378238620418183188>"
            try:
                if os.path.exists("welcome.png"):
                    bg = Editor("welcome.png")
                    av_b = await download_image(str(member.display_avatar.url))
                    if av_b:
                        av = Editor(Image.open(io.BytesIO(av_b))).resize((170, 170)).circle_image()
                        bg.paste(av, (52, 72)) 
                    await chan.send(content=txt, file=discord.File(fp=bg.image_bytes, filename="w.png"))
                else: await chan.send(content=txt)
            except: await chan.send(content=txt)

    @tasks.loop(minutes=30)
    async def auto_refresh_task(self):
        for guild in self.guilds:
            cat = guild.get_channel(CATEGORY_ID)
            if cat:
                for ch in cat.voice_channels: 
                    try: await ch.delete()
                    except: pass
                await guild.create_voice_channel(name=f"Members {guild.member_count}", category=cat)
                on = len([m for m in guild.members if m.status != discord.Status.offline])
                await guild.create_voice_channel(name=f"Online {on}", category=cat)

bot = MyBot()

# --- الـ 20 أمر إداري (سلاش كوماند) ---

@bot.tree.command(name="ban", description="حظر عضو")
@app_commands.checks.has_permissions(ban_members=True)
async def ban(interaction: discord.Interaction, user: discord.Member, reason: str = "لا يوجد"):
    await user.ban(reason=reason)
    await interaction.response.send_message(f"تم حظر {user.name}", ephemeral=True)

@bot.tree.command(name="kick", description="طرد عضو")
@app_commands.checks.has_permissions(kick_members=True)
async def kick(interaction: discord.Interaction, user: discord.Member, reason: str = "لا يوجد"):
    await user.kick(reason=reason)
    await interaction.response.send_message(f"تم طرد {user.name}", ephemeral=True)

@bot.tree.command(name="clear", description="تنظيف الشات")
@app_commands.checks.has_permissions(manage_messages=True)
async def clear(interaction: discord.Interaction, amount: int):
    await interaction.channel.purge(limit=amount)
    await interaction.response.send_message(f"تم مسح {amount} رسالة", ephemeral=True)

@bot.tree.command(name="mute", description="إسكات مؤقت")
@app_commands.checks.has_permissions(moderate_members=True)
async def mute(interaction: discord.Interaction, user: discord.Member, minutes: int):
    await user.timeout(datetime.timedelta(minutes=minutes))
    await interaction.response.send_message(f"تم إسكات {user.name} لـ {minutes} دقيقة", ephemeral=True)

@bot.tree.command(name="unmute", description="فك الإسكات")
@app_commands.checks.has_permissions(moderate_members=True)
async def unmute(interaction: discord.Interaction, user: discord.Member):
    await user.timeout(None)
    await interaction.response.send_message(f"تم فك الإسكات عن {user.name}", ephemeral=True)

@bot.tree.command(name="lock", description="قفل الروم")
@app_commands.checks.has_permissions(manage_channels=True)
async def lock(interaction: discord.Interaction):
    await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=False)
    await interaction.response.send_message("تم قفل الروم")

@bot.tree.command(name="unlock", description="فتح الروم")
@app_commands.checks.has_permissions(manage_channels=True)
async def unlock(interaction: discord.Interaction):
    await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=True)
    await interaction.response.send_message("تم فتح الروم")

@bot.tree.command(name="hide", description="إخفاء الروم")
@app_commands.checks.has_permissions(manage_channels=True)
async def hide(interaction: discord.Interaction):
    await interaction.channel.set_permissions(interaction.guild.default_role, view_channel=False)
    await interaction.response.send_message("تم إخفاء الروم", ephemeral=True)

@bot.tree.command(name="show", description="إظهار الروم")
@app_commands.checks.has_permissions(manage_channels=True)
async def show(interaction: discord.Interaction):
    await interaction.channel.set_permissions(interaction.guild.default_role, view_channel=True)
    await interaction.response.send_message("تم إظهار الروم", ephemeral=True)

@bot.tree.command(name="slowmode", description="وضع البطء")
@app_commands.checks.has_permissions(manage_channels=True)
async def slowmode(interaction: discord.Interaction, seconds: int):
    await interaction.channel.edit(slowmode_delay=seconds)
    await interaction.response.send_message(f"تم تفعيل وضع البطء {seconds} ثانية", ephemeral=True)

@bot.tree.command(name="warn", description="تحذير عضو")
@app_commands.checks.has_permissions(manage_messages=True)
async def warn(interaction: discord.Interaction, user: discord.Member, reason: str):
    await interaction.response.send_message(f"تم تحذير {user.mention} | السبب: {reason}")

@bot.tree.command(name="nick", description="تغيير اللقب")
@app_commands.checks.has_permissions(manage_nicknames=True)
async def nick(interaction: discord.Interaction, user: discord.Member, name: str):
    await user.edit(nick=name)
    await interaction.response.send_message(f"تم تغيير لقب {user.name}", ephemeral=True)

@bot.tree.command(name="role_add", description="إضافة رتبة")
@app_commands.checks.has_permissions(manage_roles=True)
async def role_add(interaction: discord.Interaction, user: discord.Member, role: discord.Role):
    await user.add_roles(role)
    await interaction.response.send_message(f"تم إضافة رتبة {role.name}", ephemeral=True)

@bot.tree.command(name="role_remove", description="سحب رتبة")
@app_commands.checks.has_permissions(manage_roles=True)
async def role_remove(interaction: discord.Interaction, user: discord.Member, role: discord.Role):
    await user.remove_roles(role)
    await interaction.response.send_message(f"تم سحب رتبة {role.name}", ephemeral=True)

@bot.tree.command(name="id_lock", description="قفل روم بالـ ID")
@app_commands.checks.has_permissions(manage_channels=True)
async def id_lock(interaction: discord.Interaction, channel_id: str):
    chan = interaction.guild.get_channel(int(channel_id))
    await chan.set_permissions(interaction.guild.default_role, send_messages=False)
    await interaction.response.send_message(f"تم قفل {chan.name}", ephemeral=True)

@bot.tree.command(name="id_unlock", description="فتح روم بالـ ID")
@app_commands.checks.has_permissions(manage_channels=True)
async def id_unlock(interaction: discord.Interaction, channel_id: str):
    chan = interaction.guild.get_channel(int(channel_id))
    await chan.set_permissions(interaction.guild.default_role, send_messages=True)
    await interaction.response.send_message(f"تم فتح {chan.name}", ephemeral=True)

@bot.tree.command(name="set_name", description="اسم الروم")
@app_commands.checks.has_permissions(manage_channels=True)
async def set_name(interaction: discord.Interaction, name: str):
    await interaction.channel.edit(name=name)
    await interaction.response.send_message(f"تم تغيير الاسم إلى {name}", ephemeral=True)

@bot.tree.command(name="user_info", description="بيانات عضو")
async def user_info(interaction: discord.Interaction, user: discord.Member):
    embed = discord.Embed(title=f"معلومات {user.name}", color=0x00aaff)
    embed.add_field(name="ID", value=user.id)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="ping", description="سرعة الاتصال")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f"بينج البوت: {round(bot.latency * 1000)}ms")

@bot.tree.command(name="bot_status", description="حالة النظام")
async def bot_status(interaction: discord.Interaction):
    await interaction.response.send_message("نظام Phoenix يعمل بكامل طاقته")

if __name__ == '__main__':
    keep_alive()
    bot.run(os.getenv('DISCORD_TOKEN'))
