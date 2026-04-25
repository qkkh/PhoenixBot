import asyncio, os, re, discord, requests
from discord.ext import commands, tasks
from flask import Flask
from threading import Thread

# --- نظام الاستضافة للبقاء حياً 24 ساعة ---
app = Flask('')
@app.route('/')
def home(): return "Phoenix Panel is Active"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run); t.daemon = True; t.start()

# --- إعداداتك الخاصة ---
OWNER_ID = 1341796578742243338 
PHOENIX_COLOR = 0x00aaff 

# --- إعدادات قنوات الإحصائيات (ضع الـ ID حق القناة الصوتية هنا) ---
# ستقوم هذه الميزة بتحديث اسم القناة ليعرض عدد الأعضاء تلقائياً
STATS_CHANNEL_ID = 123456789012345678 

# --- واجهات التفاعل (نوافذ إدخال البيانات) ---

class YTPostModal(discord.ui.Modal, title='نشر فيديو يوتيوب 🎬'):
    link = discord.ui.TextInput(label="رابط الفيديو", placeholder="ضع رابط المقطع هنا...", required=True)
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        try:
            r = requests.get(self.link.value).text
            ch_name = re.search(r'"author":"(.*?)"', r).group(1)
        except: ch_name = "قناتنا"
        
        # روم اليوتيوب الأساسي في سيرفرك
        channel = interaction.guild.get_channel(924316521050820609) 
        if channel:
            msg = f"**انتباه يا أبطال الفينيق! المبدع {ch_name} نزل مقطع جديد ورهيب، شاهدوا المقطع الآن:**"
            await channel.send(content=f"@everyone\n{msg}\n{self.link.value}")
            await interaction.followup.send("✅ تم النشر بنجاح يا زعيم!", ephemeral=True)

class AnnounceModal(discord.ui.Modal, title='إرسال إعلان عام 📢'):
    text = discord.ui.TextInput(label="محتوى الإعلان", style=discord.TextStyle.paragraph, placeholder="اكتب رسالتك هنا...", required=True)
    async def on_submit(self, interaction: discord.Interaction):
        embed = discord.Embed(title="📢 تنبيه من Phoenix Rising", description=self.text.value, color=PHOENIX_COLOR)
        embed.set_footer(text="نظام الإشعارات الذكي")
        await interaction.channel.send(content="@everyone", embed=embed)
        await interaction.response.send_message("✅ تم إرسال الإعلان للجميع.", ephemeral=True)

# --- لوحة التحكم (الأزرار فقط) ---

class PhoenixDashboard(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot
    
    @discord.ui.button(label="نشر يوتيوب", style=discord.ButtonStyle.primary, emoji="🎥")
    async def yt_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != OWNER_ID: return
        await interaction.response.send_modal(YTPostModal())

    @discord.ui.button(label="إرسال إعلان", style=discord.ButtonStyle.success, emoji="📢")
    async def ann_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != OWNER_ID: return
        await interaction.response.send_modal(AnnounceModal())

    @discord.ui.button(label="قفل الروم", style=discord.ButtonStyle.danger, emoji="🔒")
    async def lock_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != OWNER_ID: return
        await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=False)
        await interaction.response.send_message("🔒 تم قفل الروم بنجاح.", ephemeral=True)

    @discord.ui.button(label="فتح الروم", style=discord.ButtonStyle.secondary, emoji="🔓")
    async def unlock_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != OWNER_ID: return
        await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=True)
        await interaction.response.send_message("🔓 تم فتح الروم للجميع.", ephemeral=True)

# --- البوت الأساسي ---

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=discord.Intents.all())
    
    async def on_ready(self):
        await self.tree.sync()
        self.update_stats.start() # بدء تحديث عدد الأعضاء في القناة الصوتية
        print(f"Phoenix Advanced Panel is Online")

    # مهمة لتحديث اسم القناة الصوتية بعدد الأعضاء كل 5 دقائق
    @tasks.loop(minutes=5)
    async def update_stats(self):
        channel = self.get_channel(STATS_CHANNEL_ID)
        if channel:
            try:
                await channel.edit(name=f"📊 الأعضاء: {channel.guild.member_count}")
            except Exception as e:
                print(f"Error updating stats channel: {e}")

bot = MyBot()

@bot.command(name="79")
async def panel(ctx):
    if ctx.author.id == OWNER_ID:
        emb = discord.Embed(
            title="🎮 مركز عمليات PHOENIX RISING", 
            description="مرحباً بك يا زعيم الفينيق. هذه هي لوحة التحكم الخاصة بك، مصممة لتنفيذ أوامرك بضغطة زر واحدة.", 
            color=PHOENIX_COLOR
        )
        emb.set_thumbnail(url=bot.user.display_avatar.url)
        await ctx.send(embed=emb, view=PhoenixDashboard(bot))

if __name__ == '__main__':
    keep_alive()
    bot.run(os.getenv('DISCORD_TOKEN'))
