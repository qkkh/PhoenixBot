import asyncio, os, discord, datetime, io, aiohttp
from discord.ext import commands, tasks
from discord import app_commands
from flask import Flask
from threading import Thread
from easy_pil import Editor, Canvas
from PIL import Image

# تشغيل البوت 24 ساعة
app = Flask('')
@app.route('/')
def home(): return "Phoenix Super Active"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# الإعدادات الأساسية
WELCOME_ROOM_ID = 1347630031337160764
CATEGORY_ID = 1497599277793284248 
OWNER_ID = 1341796578742243338
DASHBOARD_IMAGE_URL = "https://p16-capcut-va.ibyteimg.com/tos-alisg-v-643501-sg/o0fIAfD7fEge8beAA7fInQAEn9EIzlDAnfC2f6~tplv-nh76y3g2ee-f5.webp"

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

# نافذة النشر والأرشفة
class PostModal(discord.ui.Modal):
    def __init__(self, cat):
        super().__init__(title=f"نشر في {cat}")
        self.cat = cat
    av = discord.ui.TextInput(label="رابط الأفتار", required=True)
    bn = discord.ui.TextInput(label="رابط البنر", required=True)

    async def on_submit(self, interaction):
        await interaction.response.defer(ephemeral=True)
        av_d, bn_d = await download_image(self.av.value), await download_image(self.bn.value)
        chan = interaction.guild.get_channel(ARCHIVE_CHANNELS.get(self.cat))
        canvas = Editor(Canvas(size=(3188, 2160), color="#000000"))
        canvas.paste(Editor(Image.open(io.BytesIO(bn_d))).resize((3188, 1100)), (0, 0))
        canvas.paste(Editor(Image.open(io.BytesIO(av_d))).resize((900, 900)).circle_image(), (100, 550))
        if os.path.exists("template.png"): canvas.paste(Editor("template.png"), (0, 0))
        img_bin = io.BytesIO()
        canvas.image.save(img_bin, "PNG")
        img_bin.seek(0)
        await chan.send(file=discord.File(fp=img_bin, filename="p.png"))
        await interaction.followup.send("تم الأرشفة بنجاح" ephemeral=True)

# الداشبرد المتكامل (النسخة العملاقة)
class PhoenixMegaDashboard(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)

    # 1. قائمة النشر والأرشفة
    @discord.ui.select(placeholder="📂 إدارة الأرشيف والنشر", custom_id="m_post", options=[
        discord.SelectOption(label="نشر شباب", value="شباب" emoji="👦"),
        discord.SelectOption(label="نشر بنات", value="بنات" emoji="👧"),
        discord.SelectOption(label="نشر انمي", value="انمي" emoji="⛩️")
    ])
    async def post_select(self, interaction, select):
        await interaction.response.send_modal(PostModal(select.values[0]))

    # 2. قائمة الإشراف العام
    @discord.ui.select(placeholder="🛠️ أدوات الإشراف والتحكم", custom_id="m_mod", options=[
        discord.SelectOption(label="قفل القناة", value="lock" emoji="🔒"),
        discord.SelectOption(label="فتح القناة", value="unlock" emoji="🔓"),
        discord.SelectOption(label="إخفاء القناة", value="hide" emoji="👻"),
        discord.SelectOption(label="إظهار القناة", value="show" emoji="👀"),
        discord.SelectOption(label="قفل السيرفر كامل", value="lock_all" emoji="🚨")
    ])
    async def mod_select(self, interaction, select):
        if not interaction.user.guild_permissions.manage_channels: return
        val = select.values[0]
        role = interaction.guild.default_role
        if val == "lock": await interaction.channel.set_permissions(role, send_messages=False)
        if val == "unlock": await interaction.channel.set_permissions(role, send_messages=True)
        if val == "hide": await interaction.channel.set_permissions(role, view_channel=False)
        if val == "show": await interaction.channel.set_permissions(role, view_channel=True)
        await interaction.response.send_message(f"تم تنفيذ الأمر: {val}" ephemeral=True)

    # 3. قائمة الاختصارات السريعة
    @discord.ui.select(placeholder="⚡ اختصارات سريعة", custom_id="m_quick", options=[
        discord.SelectOption(label="تحديث الإحصائيات فوراً", value="stats" emoji="📊"),
        discord.SelectOption(label="مسح 100 رسالة", value="purge" emoji="🧹"),
        discord.SelectOption(label="معلومات السيرفر", value="info" emoji="💎")
    ])
    async def quick_select(self, interaction, select):
        val = select.values[0]
        if val == "stats":
            await bot.auto_refresh_task()
            await interaction.response.send_message("تم تحديث الرومات" ephemeral=True)
        if val == "purge":
            await interaction.channel.purge(limit=100)
            await interaction.response.send_message("تم التنظيف" ephemeral=True)
        if val == "info":
            emb = discord.Embed(title=interaction.guild.name, description=f"الأعضاء: {interaction.guild.member_count}" color=0x2b2d31)
            await interaction.response.send_message(embed=emb, ephemeral=True)

class MyBot(commands.Bot):
    def __init__(self): super().__init__(command_prefix="!", intents=discord.Intents.all())
    async def setup_hook(self):
        self.add_view(PhoenixMegaDashboard())
        await self.tree.sync()
        if not self.auto_refresh_task.is_running(): self.auto_refresh_task.start()

    # --- (3) الترحيب الذكي - لم يتم لمسه ---
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

    # --- (4) إحصائيات السيرفر - لم يتم لمسه ---
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

@bot.tree.command(name="setup_dashboard" description="إرسال لوحة التحكم العملاقة")
async def setup(interaction):
    if interaction.user.id == OWNER_ID:
        embed = discord.Embed(title="PHOENIX SYSTEM" description="لوحة التحكم الكاملة بالسيرفر" color=0x2b2d31)
        embed.set_image(url=DASHBOARD_IMAGE_URL)
        await interaction.channel.send(embed=embed, view=PhoenixMegaDashboard())
        await interaction.response.send_message("تم التشغيل" ephemeral=True)

if __name__ == '__main__':
    keep_alive()
    bot.run(os.getenv('DISCORD_TOKEN'))
