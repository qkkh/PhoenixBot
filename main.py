import asyncio, os, discord, datetime, io, aiohttp
from discord.ext import commands, tasks
from discord import app_commands
from flask import Flask
from threading import Thread
from easy_pil import Editor, load_image_async, Canvas
from PIL import Image

# --- نظام البقاء متصلاً Keep Alive ---
app = Flask('')
@app.route('/')
def home(): return "Phoenix Rising Active"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# --- الإعدادات الثابتة ---
WELCOME_ROOM_ID = 1347630031337160764
CATEGORY_ID = 1497599277793284248 
OWNER_ID = 1341796578742243338

# --- دالة تحميل الصور ---
async def download_image(url):
    headers = {'User-Agent': 'Mozilla/5.0'}
    async with aiohttp.ClientSession(headers=headers) as session:
        try:
            async with session.get(url, timeout=15) as resp:
                if resp.status == 200:
                    return await resp.read()
        except:
            return None
    return None

# --- واجهة أزرار التحميل (تم إصلاحها لمنع الـ failed) ---
class CloudDownloadView(discord.ui.View):
    def __init__(self, av_data, bn_data):
        super().__init__(timeout=None)
        self.av_data = av_data
        self.bn_data = bn_data

    @discord.ui.button(label="", style=discord.ButtonStyle.secondary, emoji="<:download:1286653105878077450>")
    async def download(self, interaction: discord.Interaction, button: discord.ui.Button):
        # ضروري جداً هنا لمنع ظهور الـ failed في الأزرار
        await interaction.response.defer(ephemeral=True)
        
        try:
            files = []
            embeds = []
            
            # معالجة الصور وإرسالها
            if self.av_data:
                av_file = discord.File(io.BytesIO(self.av_data), filename="avatar.png")
                files.append(av_file)
                embeds.append(discord.Embed(color=0x2b2d31).set_image(url="attachment://avatar.png"))
            
            if self.bn_data:
                bn_file = discord.File(io.BytesIO(self.bn_data), filename="banner.png")
                files.append(bn_file)
                embeds.append(discord.Embed(color=0x2b2d31).set_image(url="attachment://banner.png"))
            
            if files:
                await interaction.followup.send(embeds=embeds, files=files, ephemeral=True)
            else:
                await interaction.followup.send("لم يتم العثور على بيانات الصور", ephemeral=True)
        except Exception as e:
            # لو حصل أي تأخير في الشبكة
            try: await interaction.followup.send("حدث خطأ أثناء تحميل الصور، حاول مرة أخرى", ephemeral=True)
            except: pass

# --- كلاس البوت الأساسي ---
class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=discord.Intents.all())
    
    async def setup_hook(self):
        await self.tree.sync()
        if not self.auto_refresh_task.is_running():
            self.auto_refresh_task.start()

    # نظام الترحيب التلقائي
    async def on_member_join(self, member):
        channel = self.get_channel(WELCOME_ROOM_ID)
        if channel:
            welcome_text = (
                f"_'Have fun in **__PhoenixRising__**_\n"
                f"     _'User: {member.mention}_<a:Via1:1378238620418183188>"
            )
            try:
                background = Editor("welcome.png")
                av_bytes = await download_image(str(member.display_avatar.url))
                if av_bytes:
                    avatar = Editor(Image.open(io.BytesIO(av_bytes))).resize((170, 170)).circle_image()
                    background.paste(avatar, (52, 72)) 
                file = discord.File(fp=background.image_bytes, filename="welcome_card.png")
                await channel.send(content=welcome_text, file=file)
            except:
                await channel.send(content=welcome_text)

    # نظام تحديث الإحصائيات (كل 30 دقيقة)
    @tasks.loop(minutes=30)
    async def auto_refresh_task(self):
        for guild in self.guilds:
            category = guild.get_channel(CATEGORY_ID)
            if category:
                for ch in category.voice_channels: 
                    try: await ch.delete()
                    except: pass
                total = guild.member_count
                online = len([m for m in guild.members if m.status != discord.Status.offline])
                await guild.create_voice_channel(name=f"Members {total}", category=category)
                await guild.create_voice_channel(name=f"Online {online}", category=category)

bot = MyBot()

# --- الأوامر التفاعلية Slash Commands ---

@bot.tree.command(name="نشر", description="نشر بروفايل")
async def post(interaction: discord.Interaction, الافتار: str, البنر: str):
    if interaction.user.id == OWNER_ID or interaction.user.guild_permissions.manage_messages:
        try:
            # تحميل البيانات
            av_data = await download_image(الافتار)
            bn_data = await download_image(البنر)
            
            if not av_data or not bn_data:
                return await interaction.response.send_message("تأكد من روابط الصور", ephemeral=True)

            av_pil = Image.open(io.BytesIO(av_data))
            bn_pil = Image.open(io.BytesIO(bn_data))
            
            # إنشاء التصميم
            canvas = Editor(Canvas(size=(3188, 2160), color="#000000")) 
            canvas.paste(Editor(bn_pil).resize((3188, 1100)), (0, 0))
            canvas.paste(Editor(av_pil).resize((900, 900)).circle_image(), (100, 550))
            canvas.paste(Editor("template.png"), (0, 0))
            
            image_binary = io.BytesIO()
            canvas.image.save(image_binary, "PNG", optimize=True)
            image_binary.seek(0)
            
            file = discord.File(fp=image_binary, filename="profile.png")
            embed = discord.Embed(color=0x2b2d31)
            embed.set_image(url="attachment://profile.png")
            
            # إرسال النتيجة
            await interaction.channel.send(embed=embed, file=file, view=CloudDownloadView(av_data, bn_data))
            await interaction.response.send_message("تم النشر بنجاح", ephemeral=True)
        except Exception as e:
            if not interaction.response.is_done():
                await interaction.response.send_message("حدث خطأ حاول مرة اخرى", ephemeral=True)

@bot.tree.command(name="مسح")
@app_commands.checks.has_permissions(manage_messages=True)
async def clear(interaction: discord.Interaction, العدد: int):
    await interaction.channel.purge(limit=العدد)
    await interaction.response.send_message(f"تم propaganda {العدد}", ephemeral=True)

@bot.tree.command(name="قفل_القناة")
@app_commands.checks.has_permissions(manage_channels=True)
async def lock(interaction: discord.Interaction):
    await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=False)
    await interaction.response.send_message("تم قفل القناة")

@bot.tree.command(name="فتح_القناة")
@app_commands.checks.has_permissions(manage_channels=True)
async def unlock(interaction: discord.Interaction):
    await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=True)
    await interaction.response.send_message("تم فتح القناة")

@bot.tree.command(name="الحالة")
async def change_status(interaction: discord.Interaction, النص: str):
    if interaction.user.id == OWNER_ID:
        await bot.change_presence(activity=discord.Game(name=النص))
        await interaction.response.send_message("تم تغيير الحالة", ephemeral=True)

# --- التشغيل ---
if __name__ == '__main__':
    keep_alive()
    bot.run(os.getenv('DISCORD_TOKEN'))
