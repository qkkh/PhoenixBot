import asyncio, os, discord, datetime, io, aiohttp
from discord.ext import commands, tasks
from discord import app_commands
from flask import Flask
from threading import Thread
from easy_pil import Editor, Canvas
from PIL import Image

app = Flask('')
@app.route('/')
def home(): return "Phoenix ID Controller Active"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

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

class ChannelControlModal(discord.ui.Modal):
    def __init__(self, action):
        super().__init__(title="التحكم بروم مخصص")
        self.action = action
    
    channel_id = discord.ui.TextInput(
        label="أدخل ID الروم هنا",
        placeholder="مثال 123456789012345678",
        required=True,
        min_length=15
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            target_channel = interaction.guild.get_channel(int(self.channel_id.value))
            if not target_channel:
                return await interaction.response.send_message("لم أتمكن من العثور على هذا الروم" ephemeral=True)
            
            role = interaction.guild.default_role
            if self.action == "lock":
                await target_channel.set_permissions(role, send_messages=False)
                msg = f"تم قفل الروم {target_channel.mention} بنجاح"
            elif self.action == "unlock":
                await target_channel.set_permissions(role, send_messages=True)
                msg = f"تم فتح الروم {target_channel.mention} بنجاح"
            elif self.action == "hide":
                await target_channel.set_permissions(role, view_channel=False)
                msg = f"تم إخفاء الروم {target_channel.name} بنجاح"
            elif self.action == "show":
                await target_channel.set_permissions(role, view_channel=True)
                msg = f"تم إظهار الروم {target_channel.mention} بنجاح"
            
            await interaction.response.send_message(msg, ephemeral=True)
        except ValueError:
            await interaction.response.send_message("يرجى إدخال أرقام فقط" ephemeral=True)

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
        await interaction.followup.send("تم الأرشفة بنجاح", ephemeral=True)

class PhoenixUltraDashboard(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)

    @discord.ui.select(placeholder="نشر وأرشفة", custom_id="u_post", options=[
        discord.SelectOption(label="أرشيف الشباب", value="شباب", emoji="👦"),
        discord.SelectOption(label="أرشيف البنات", value="بنات", emoji="👧"),
        discord.SelectOption(label="أرشيف الانمي", value="انمي", emoji="⛩️")
    ])
    async def post_select(self, interaction, select):
        await interaction.response.send_modal(PostModal(select.values[0]))

    @discord.ui.select(placeholder="تحكم بروم معين عبر الـ ID", custom_id="id_control", options=[
        discord.SelectOption(label="قفل روم بالـ ID", value="lock", emoji="🔒"),
        discord.SelectOption(label="فتح روم بالـ ID", value="unlock", emoji="🔓"),
        discord.SelectOption(label="إخفاء روم بالـ ID", value="hide", emoji="👻"),
        discord.SelectOption(label="إظهار روم بالـ ID", value="show", emoji="👀")
    ])
    async def id_manage(self, interaction, select):
        if not interaction.user.guild_permissions.manage_channels: return
        await interaction.response.send_modal(ChannelControlModal(select.values[0]))

    @discord.ui.button(label="تحديث الإحصائيات", style=discord.ButtonStyle.blurple, emoji="📊", custom_id="u_stats")
    async def refresh_stats(self, interaction, button):
        await bot.auto_refresh_task()
        await interaction.response.send_message("تم تحديث إحصائيات السيرفر", ephemeral=True)

class MyBot(commands.Bot):
    def __init__(self): super().__init__(command_prefix="!", intents=discord.Intents.all())
    async def setup_hook(self):
        self.add_view(PhoenixUltraDashboard())
        await self.tree.sync()
        if not self.auto_refresh_task.is_running(): self.auto_refresh_task.start()

    async def on_member_join(self, member):
        chan = self.get_channel(WELCOME_ROOM_ID)
        if chan:
            txt = f"Have fun in PhoenixRising User {member.mention}"
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

@bot.tree.command(name="dashboard", description="لوحة التحكم")
async def setup(interaction):
    if interaction.user.id == OWNER_ID:
        embed = discord.Embed(title="PHOENIX CONTROL", description="أدخل ID الروم للتحكم", color=0x00aaff)
        embed.set_image(url=DASHBOARD_IMAGE_URL)
        await interaction.channel.send(embed=embed, view=PhoenixUltraDashboard())
        await interaction.response.send_message("تم التشغيل", ephemeral=True)

if __name__ == '__main__':
    keep_alive()
    bot.run(os.getenv('DISCORD_TOKEN'))
