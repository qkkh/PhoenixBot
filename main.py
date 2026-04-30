import asyncio, os, discord, datetime, io
from discord.ext import commands, tasks
from discord import app_commands
from flask import Flask
from threading import Thread
from easy_pil import Editor, load_image_async, Canvas

# كود إبقاء البوت شغال 24 ساعة
app = Flask('')
@app.route('/')
def home(): return "Phoenix Rising System Active"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# إعدادات المعرفات الأصلية
WELCOME_ROOM_ID = 1347630031337160764
CATEGORY_ID = 1497599277793284248 
OWNER_ID = 1341796578742243338

# القنوات المسموح فيها بالنشر التلقائي عبر الصور
ALLOWED_CHANNELS = [
    1378251863098392596,
    1378251900348141589,
    1378251920237395998
]

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=discord.Intents.all())
    
    async def setup_hook(self):
        await self.tree.sync()
        if not self.auto_refresh_task.is_running():
            self.auto_refresh_task.start()

    async def on_member_join(self, member):
        channel = self.get_channel(WELCOME_ROOM_ID)
        if channel:
            welcome_text = (
                f"_'Have fun in **__PhoenixRising__**_\n"
                f"     _'User: {member.mention}_<a:Via1:1378238620418183188>"
            )
            try:
                background = Editor("welcome.png")
                avatar_image = await load_image_async(member.display_avatar.url)
                avatar = Editor(avatar_image).resize((170, 170)).circle_image()
                background.paste(avatar, (52, 72)) 
                file = discord.File(fp=background.image_bytes, filename="welcome_card.png")
                await channel.send(content=welcome_text, file=file)
            except Exception as e:
                print(f"Error drawing image: {e}")
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

    # نظام النشر التلقائي المطور جداً لتفادي أخطاء القراءة
    async def on_message(self, message):
        if message.author.bot: return
        
        if message.channel.id in ALLOWED_CHANNELS:
            if len(message.attachments) == 2 and (message.author.id == OWNER_ID or message.author.guild_permissions.manage_messages):
                if all(message.attachments[i].content_type.startswith('image') for i in range(2)):
                    msg = await message.channel.send("⏳ جاري سحب الصور بدقة...")
                    try:
                        # جلب محتوى الصور كـ Bytes لضمان عدم تلف الملف أثناء القراءة
                        av_bytes = io.BytesIO(await message.attachments[0].read())
                        bn_bytes = io.BytesIO(await message.attachments[1].read())

                        canvas = Editor(Canvas(size=(3188, 2160), color="#000000")) 
                        
                        # البنر (تحميل من Bytes)
                        bn_img = await load_image_async(bn_bytes)
                        bn_res = Editor(bn_img).resize((3188, 1100))
                        canvas.paste(bn_res, (0, 0))
                        
                        # الأفاتار (تحميل من Bytes)
                        av_img = await load_image_async(av_bytes)
                        av_res = Editor(av_img).resize((900, 900)).circle_image()
                        canvas.paste(av_res, (100, 550))
                        
                        # التيمبلت
                        base = Editor("template.png") 
                        canvas.paste(base, (0, 0))
                        
                        file = discord.File(fp=canvas.image_bytes, filename="profile.png")
                        
                        await message.delete() 
                        await msg.delete() 
                        
                        await message.channel.send(file=file, view=CloudDownloadView(message.attachments[0].url, message.attachments[1].url))
                    except Exception as e:
                        await msg.edit(content=f"❌ عذراً، لم أستطع قراءة هذه الصور. تأكد أنها بصيغة PNG أو JPG عادية.\n`{e}`")

        await self.process_commands(message)

bot = MyBot()

# --- بقية الأوامر كما هي دون أي تغيير ---

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

@bot.tree.command(name="الحالة", description="تغيير حالة البوت")
async def change_status(interaction: discord.Interaction, النص: str):
    if interaction.user.id == OWNER_ID:
        await bot.change_presence(activity=discord.Game(name=النص))
        await interaction.response.send_message(f"✅ تم تغيير الحالة إلى: {النص}", ephemeral=True)

class CloudDownloadView(discord.ui.View):
    def __init__(self, av_url, bn_url):
        super().__init__(timeout=None)
        self.av_url = av_url
        self.bn_url = bn_url

    @discord.ui.button(label="", style=discord.ButtonStyle.secondary, emoji="<:download:1286653105878077450>")
    async def download(self, interaction: discord.Interaction, button: discord.ui.Button):
        emb1 = discord.Embed().set_image(url=self.av_url)
        emb2 = discord.Embed().set_image(url=self.bn_url)
        await interaction.response.send_message(embeds=[emb1, emb2], ephemeral=True)

@bot.tree.command(name="نشر", description="نشر بروفايل عبر رابط")
async def post(interaction: discord.Interaction, الافتار: str, البنر: str):
    if interaction.user.id == OWNER_ID or interaction.user.guild_permissions.manage_messages:
        await interaction.response.defer(ephemeral=True)
        try:
            canvas = Editor(Canvas(size=(3188, 2160), color="#000000")) 
            bn_img = await load_image_async(البنر)
            bn_res = Editor(bn_img).resize((3188, 1100))
            canvas.paste(bn_res, (0, 0))
            av_img = await load_image_async(الافتار)
            av_res = Editor(av_img).resize((900, 900)).circle_image()
            canvas.paste(av_res, (100, 550))
            base = Editor("template.png") 
            canvas.paste(base, (0, 0))
            file = discord.File(fp=canvas.image_bytes, filename="profile.png")
            await interaction.channel.send(file=file, view=CloudDownloadView(الافتار, البنر))
            await interaction.followup.send("Done", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"Error: {e}", ephemeral=True)

if __name__ == '__main__':
    keep_alive()
    bot.run(os.getenv('DISCORD_TOKEN'))
