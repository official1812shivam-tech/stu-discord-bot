import os
import json
import discord
from discord import app_commands
from discord.ext import commands
from flask import Flask
from threading import Thread

# ----------------------------------------------------
# 1. FLASK WEB SERVER (24/7 Hosting Keep Alive)
# ----------------------------------------------------
app = Flask('')

@app.route('/')
def home():
    return "STU Clan Bot is 24/7 Active!"

def run_web():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run_web)
    t.start()

# ----------------------------------------------------
# 2. DATA STORAGE MANAGEMENT (JSON file)
# ----------------------------------------------------
DATA_FILE = "clan_data.json"

DEFAULT_DATA = {
    "clubs": {
        "ROOK": {"title": "亗 ROOK", "president": "STU_HANEESH", "points": 0, "members": {}},
        "SMILERS": {"title": "ツ SMILERS", "president": "STU_SHADOW", "points": 0, "members": {}},
        "SHIN": {"title": "么 SHIN", "president": "STU_Criminal", "points": 0, "members": {}},
        "WIND": {"title": "彡 WIND", "president": "STU_YASIN", "points": 0, "members": {}}
    }
}

def load_data():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_DATA, f, indent=4)
        return DEFAULT_DATA
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
        # Ensure backwards compatibility for points field
        for key, default_club in DEFAULT_DATA["clubs"].items():
            if key not in data["clubs"]:
                data["clubs"][key] = default_club
            elif "points" not in data["clubs"][key]:
                data["clubs"][key]["points"] = 0
        return data

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

clan_data = load_data()

# ----------------------------------------------------
# 3. DISCORD BOT SETUP & ERROR HANDLING
# ----------------------------------------------------
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

class STUBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        await self.tree.sync()
        print("Slash commands synced globally.")

    async def on_ready(self):
        print(f"Logged in as {self.user} (ID: {self.user.id})")

bot = STUBot()

# Embed Theme Colors
COLOR_MAIN = discord.Color.from_rgb(46, 204, 113)
COLOR_HEADER = discord.Color.from_rgb(155, 89, 182)

# Global Error Handler for Missing Permissions
@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.MissingPermissions):
        embed = discord.Embed(
            title="🚫 Access Denied",
            description="You do not have the required **Administrator** permissions to use this command!",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
    else:
        print(f"Command Error: {error}")

# ----------------------------------------------------
# PUBLIC COMMAND 1: /club-leaderboard (Everyone can run)
# ----------------------------------------------------
@bot.tree.command(name="club-leaderboard", description="Shows the club leaderboard ranked by points.")
async def club_leaderboard(interaction: discord.Interaction):
    club_scores = []
    for key, club in clan_data["clubs"].items():
        club_scores.append({
            "title": club["title"],
            "president": club["president"],
            "points": club["points"],
            "count": len(club["members"])
        })

    # Sort descending by total points
    club_scores.sort(key=lambda x: x["points"], reverse=True)

    embed = discord.Embed(
        title="🏆 **STU CLAN — CLUB LEADERBOARD** 🏆",
        description="Leaderboard updates automatically based on club points.",
        color=COLOR_HEADER
    )

    medals = ["🥇", "🥈", "🥉", "4️⃣"]
    for idx, club in enumerate(club_scores):
        rank = medals[idx] if idx < len(medals) else f"#{idx+1}"
        embed.add_field(
            name=f"{rank} {club['title']}",
            value=f"**President:** `{club['president']}`\n**Points:** `{club['points']} PTS`\n**Members:** `{club['count']}`",
            inline=False
        )

    await interaction.response.send_message(embed=embed)

# ----------------------------------------------------
# PUBLIC COMMAND 2: /club [name] (Everyone can run)
# ----------------------------------------------------
@bot.tree.command(name="club", description="View details and members of a specific club.")
@app_commands.choices(name=[
    app_commands.Choice(name="亗 ROOK", value="ROOK"),
    app_commands.Choice(name="ツ SMILERS", value="SMILERS"),
    app_commands.Choice(name="么 SHIN", value="SHIN"),
    app_commands.Choice(name="彡 WIND", value="WIND")
])
async def club(interaction: discord.Interaction, name: app_commands.Choice[str]):
    club_key = name.value
    club_info = clan_data["clubs"][club_key]

    embed = discord.Embed(
        title=f"🛡️ {club_info['title']}",
        description=f"👑 **President:** `{club_info['president']}`\n💎 **Club Points:** `{club_info['points']} PTS`",
        color=COLOR_MAIN
    )

    members = club_info["members"]
    if not members:
        embed.add_field(name="👥 Members", value="*No members added yet.*", inline=False)
    else:
        member_text = ""
        for i, (r_name, info) in enumerate(members.items(), 1):
            member_text += f"`{i}.` **{r_name}** (@{info['discord']})\n"
        embed.add_field(name="👥 Members List", value=member_text, inline=False)

    await interaction.response.send_message(embed=embed)

# ----------------------------------------------------
# ADMIN COMMAND 3: /club-point (Admin Only)
# ----------------------------------------------------
@bot.tree.command(name="club-point", description="Select a club and add or deduct its points.")
@app_commands.checks.has_permissions(administrator=True) # 🔒 ADMIN ONLY
@app_commands.choices(
    club=[
        app_commands.Choice(name="亗 ROOK", value="ROOK"),
        app_commands.Choice(name="ツ SMILERS", value="SMILERS"),
        app_commands.Choice(name="么 SHIN", value="SHIN"),
        app_commands.Choice(name="彡 WIND", value="WIND")
    ],
    action=[
        app_commands.Choice(name="➕ Add Points", value="add"),
        app_commands.Choice(name="➖ Deduct Points", value="deduct")
    ]
)
async def club_point(interaction: discord.Interaction, club: app_commands.Choice[str], action: app_commands.Choice[str], amount: int):
    club_key = club.value
    club_info = clan_data["clubs"][club_key]
    
    curr_pts = club_info["points"]
    if action.value == "add":
        new_pts = curr_pts + amount
        action_text = f"Added {amount} pts to"
    else:
        new_pts = curr_pts - amount
        action_text = f"Deducted {amount} pts from"

    club_info["points"] = new_pts
    save_data(clan_data)

    embed = discord.Embed(
        title="✨ Club Points Updated",
        description=f"Successfully {action_text} **{club_info['title']}**.",
        color=discord.Color.gold()
    )
    embed.add_field(name="New Club Points", value=f"`{new_pts} PTS`", inline=False)
    await interaction.response.send_message(embed=embed)

# ----------------------------------------------------
# ADMIN COMMAND 4A: /club-member-add (Admin Only)
# ----------------------------------------------------
@bot.tree.command(name="club-member-add", description="Add a new member to a club.")
@app_commands.checks.has_permissions(administrator=True) # 🔒 ADMIN ONLY
@app_commands.choices(club=[
    app_commands.Choice(name="亗 ROOK", value="ROOK"),
    app_commands.Choice(name="ツ SMILERS", value="SMILERS"),
    app_commands.Choice(name="么 SHIN", value="SHIN"),
    app_commands.Choice(name="彡 WIND", value="WIND")
])
async def club_member_add(interaction: discord.Interaction, club: app_commands.Choice[str], roblox_name: str, discord_name: str):
    club_key = club.value
    clan_data["clubs"][club_key]["members"][roblox_name] = {
        "discord": discord_name.replace("@", "")
    }
    save_data(clan_data)

    embed = discord.Embed(
        title="✅ Member Added",
        description=f"Added **{roblox_name}** to **{clan_data['clubs'][club_key]['title']}**.",
        color=discord.Color.green()
    )
    embed.add_field(name="Discord User", value=f"`{discord_name}`", inline=True)
    await interaction.response.send_message(embed=embed)

# ----------------------------------------------------
# ADMIN COMMAND 4B: /club-member-remove (Admin Only)
# ----------------------------------------------------
class ClubRemoveSelect(discord.ui.Select):
    def __init__(self, club_key, members_dict):
        self.club_key = club_key
        options = [
            discord.SelectOption(label=r_name, value=r_name)
            for r_name in members_dict.keys()
        ]
        if not options:
            options = [discord.SelectOption(label="No members in this club", value="none")]
        super().__init__(placeholder=f"Select member to remove from {club_key}...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == "none":
            await interaction.response.send_message("No members to remove.", ephemeral=True)
            return

        r_name = self.values[0]
        if r_name in clan_data["clubs"][self.club_key]["members"]:
            del clan_data["clubs"][self.club_key]["members"][r_name]
            save_data(clan_data)

            embed = discord.Embed(
                title="🗑️ Member Removed",
                description=f"Successfully removed **{r_name}** from **{clan_data['clubs'][self.club_key]['title']}**.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message("Member not found.", ephemeral=True)

class ClubRemoveView(discord.ui.View):
    def __init__(self, club_key, members_dict):
        super().__init__(timeout=60)
        self.add_item(ClubRemoveSelect(club_key, members_dict))

@bot.tree.command(name="club-member-remove", description="Select a club first, then view and remove members from it.")
@app_commands.checks.has_permissions(administrator=True) # 🔒 ADMIN ONLY
@app_commands.choices(club=[
    app_commands.Choice(name="亗 ROOK", value="ROOK"),
    app_commands.Choice(name="ツ SMILERS", value="SMILERS"),
    app_commands.Choice(name="么 SHIN", value="SHIN"),
    app_commands.Choice(name="彡 WIND", value="WIND")
])
async def club_member_remove(interaction: discord.Interaction, club: app_commands.Choice[str]):
    club_key = club.value
    members = clan_data["clubs"][club_key]["members"]
    
    if not members:
        await interaction.response.send_message(f"⚠️ There are no members in **{clan_data['clubs'][club_key]['title']}** to remove.", ephemeral=True)
        return

    embed = discord.Embed(
        title=f"🔻 Remove Member from {clan_data['clubs'][club_key]['title']}",
        description="Choose a member from the dropdown menu below to remove them.",
        color=discord.Color.dark_red()
    )
    await interaction.response.send_message(embed=embed, view=ClubRemoveView(club_key, members), ephemeral=True)

# ----------------------------------------------------
# RUN BOT
# ----------------------------------------------------
if __name__ == "__main__":
    keep_alive()
    TOKEN = os.getenv("DISCORD_TOKEN")
    if TOKEN:
        bot.run(TOKEN)
    else:
        print("Error: DISCORD_TOKEN is missing!")
