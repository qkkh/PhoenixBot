import asyncio, os, discord, datetime, io, aiohttp
from discord.ext import commands, tasks
from discord import app_commands
from flask import Flask
from threading import Thread
from easy_pil import Editor, load_image_async, Canvas
from PIL import Image

# نظام البقاء متصلاً
app = Flask('')
@app.route('/')
def home(): return "Phoenix Rising Active"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# الإعدادات الأصلية حقك
WELCOME_ROOM_ID = 1347630031337160764
CATEGORY_ID = 1497599277793284248 
OWNER_ID = 1341796578742243338

# رومات الأرشيف
ARCHIVE_CHANNELS = {
    "شباب": 1378251863098392596,
    "بنات": 1378251900348141589,
    "انمي": 1378251920237395998
}

async def download_image(url):
    headers = {'User-Agent': 'Mozilla/5.0'}
    async with aiohttp.ClientSession(headers=headers) as session:
        try:
            async with session.get(url, timeout=15) as resp:
                if resp.status == 200: return await resp.read()
        except: return None
    return None

# --- زر التحميل (Persistent) ---
class CloudDownloadView(discord.ui.View):
    def __init__(self, av_data=None, bn_data=None):
        super().__init__(timeout=None)
        self.av_data = av_data
        self.bn_data = bn_data

    @discord.ui.button(label="", style=discord.ButtonStyle.secondary, emoji="<:download:1286653105878077450>", custom_id="dl_fixed")
    async def download(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        try:
            files, embeds = [], []
            if self.av_data:
                files.append(discord.File(io.BytesIO(self.av_data), filename="avatar.png"))
                embeds.append(discord.Embed(color=0x2b2d31).set_image(url="attachment://avatar.png"))
            if self.bn_data:
                files.append(discord.File(io.BytesIO(self.bn_data), filename="banner.png"))
                embeds.append(discord.Embed(color=0x2b2d31).set_image(url="attachment://banner.png"))
            await interaction.followup.send(embeds=embeds, files=files, ephemeral=True)
        except: await interaction.followup.send("خطأ بالتحميل", ephemeral=True)

# --- نافذة النشر ---
class PostModal(discord.ui.Modal):
    def __init__(self, cat_name):
        super().__init__(title=f"نشر في {cat_name}")
        self.cat_name = cat_name
    av_url = discord.ui.TextInput(label="رابط الأفتار", required=True)
    bn_url = discord.ui.TextInput(label="رابط البنر", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        av, bn = await download_image(self.av_url.value), await download_image(self.bn_url.value)
        if not av or not bn: return await interaction.followup.send("روابط غلط", ephemeral=True)
        chan = interaction.guild.get_channel(ARCHIVE_CHANNELS.get(self.cat_name))
        try:
            canvas = Editor(Canvas(size=(3188, 2160), color="#000000"))
            canvas.paste(Editor(Image.open(io.BytesIO(bn))).resize((3188, 1100)), (0, 0))
            canvas.paste(Editor(Image.open(io.BytesIO(av))).resize((900, 900)).circle_image(), (100, 550))
            if os.path.exists("template.png"): canvas.paste(Editor("template.png"), (0, 0))
            img_bin = io.BytesIO()
            canvas.image.save(img_bin, "PNG")
            img_bin.seek(0)
            embed = discord.Embed(description=f"بواسطة: {interaction.user.mention}", color=0x2b2d31).set_image(url="attachment://p.png")
            await chan.send(embed=embed, file=discord.File(fp=img_bin, filename="p.png"), view=CloudDownloadView(av, bn))
            await interaction.followup.send("تم النشر", ephemeral=True)
        except: await interaction.followup.send("خطأ برمجـي", ephemeral=True)

# --- داشبرد التحكم الكامل ---
class MasterDashboard(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)

    @discord.ui.select(placeholder="اختر قسم النشر...", custom_id="dash_sel", options=[
        discord.SelectOption(label="شباب", value="شباب", emoji="👦"),
        discord.SelectOption(label="بنات", value="بنات", emoji="👧"),
        discord.SelectOption(label="انمي", value="انمي", emoji="⛩️")
    ])
    async def sel(self, interaction, select):
        if interaction.user.id == OWNER_ID or interaction.user.guild_permissions.manage_messages:
            await interaction.response.send_modal(PostModal(select.values[0]))
        else: await interaction.response.send_message("ما عندك صلاحية", ephemeral=True)

    @discord.ui.button(label="قفل", style=discord.ButtonStyle.danger, custom_id="d_lock")
    async def l(self, interaction, button):
        if interaction.user.guild_permissions.manage_channels:
            await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=False)
            await interaction.response.send_message("قفلنا القناة", ephemeral=True)

    @discord.ui.button(label="فتح", style=discord.ButtonStyle.success, custom_id="d_unlock")
    async def u(self, interaction, button):
        if interaction.user.guild_permissions.manage_channels:
            await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=True)
            await interaction.response.send_message("فتحنا القناة", ephemeral=True)

class MyBot(commands.Bot):
    def __init__(self): super().__init__(command_prefix="!", intents=discord.Intents.all())
    async def setup_hook(self):
        self.add_view(MasterDashboard())
        self.add_view(CloudDownloadView())
        await self.tree.sync()
        if not self.auto_refresh_task.is_running(): self.auto_refresh_task.start()

    async def on_member_join(self, member):
        chan = self.get_channel(WELCOME_ROOM_ID)
        if chan:
            txt = f"_'Have fun in **__PhoenixRising__**_\n     _'User: {member.mention}_<a:Via1:1378238620418183188>"
            try:
                bg = Editor("welcome.png")
                av_b = await download_image(str(member.display_avatar.url))
                if av_b:
                    av = Editor(Image.open(io.BytesIO(av_b))).resize((170, 170)).circle_image()
                    bg.paste(av, (52, 72)) 
                await chan.send(content=txt, file=discord.File(fp=bg.image_bytes, filename="w.png"))
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

# --- أوامرك كما هي بالضبط ---
@bot.tree.command(name="setav")
async def setav(interaction):
    if interaction.user.id == OWNER_ID:
        emb = discord.Embed(title="Phoenix Dashboard", description="تحكم كامل بالسيرفر", color=0x2b2d31)
        await interaction.channel.send(embed=emb, view=MasterDashboard())
        await interaction.response.send_message("تم", ephemeral=True)

@bot.tree.command(name="مسح")
@app_commands.checks.has_permissions(manage_messages=True)
async def clear(interaction, العدد: int):
    await interaction.channel.purge(limit=العدد)
    await interaction.response.send_message(f"مسحت {العدد}", ephemeral=True)

@bot.tree.command(name="قفل_القناة")
@app_commands.checks.has_permissions(manage_channels=True)
async def lock(interaction):
    await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=False)
    await interaction.response.send_message("قُفلت")

@bot.tree.command(name="فتح_القناة")
@app_commands.checks.has_permissions(manage_channels=True)
async def unlock(interaction):
    await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=True)
    await interaction.response.send_message("فُتحت")

@bot.tree.command(name="الحالة")
async def status(interaction, النص: str):
    if interaction.user.id == OWNER_ID:
        await bot.change_presence(activity=discord.Game(name=النص))
        await interaction.response.send_message("تحدثت الحالة", ephemeral=True)

if __name__ == '__main__':
    keep_alive()
    bot.run(os.getenv('DISCORD_TOKEN'))
