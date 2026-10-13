# ----------------------------------------------------
# ADMIN COMMAND 4B: /club-member-remove (Admin Only)
# ----------------------------------------------------
class ClubRemoveSelect(discord.ui.Select):
    def __init__(self, club_key, members_dict):
        self.club_key = club_key
        options = []
        
        # Build dropdown options for members in this specific club
        for r_name in list(members_dict.keys())[:25]:  # Discord limit: max 25 items per select menu
            disc_tag = members_dict[r_name].get("discord", "N/A")
            options.append(
                discord.SelectOption(
                    label=r_name,
                    description=f"Discord: @{disc_tag}",
                    value=r_name
                )
            )

        if not options:
            options = [discord.SelectOption(label="No members in this club", value="none")]

        super().__init__(
            placeholder=f"Select member to remove from {club_key}...",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        selected_member = self.values[0]
        
        if selected_member == "none":
            await interaction.response.send_message("❌ No valid member selected.", ephemeral=True)
            return

        # Fetch live data to avoid concurrency issues
        current_data = load_data()
        club_members = current_data["clubs"][self.club_key]["members"]

        if selected_member in club_members:
            del current_data["clubs"][self.club_key]["members"][selected_member]
            save_data(current_data)

            # Update local memory
            global clan_data
            clan_data = current_data

            embed = discord.Embed(
                title="🗑️ Member Removed",
                description=f"Successfully removed **{selected_member}** from **{clan_data['clubs'][self.club_key]['title']}**.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message("❌ Member was not found or already removed.", ephemeral=True)


class ClubRemoveView(discord.ui.View):
    def __init__(self, club_key, members_dict):
        super().__init__(timeout=60)
        self.add_item(ClubRemoveSelect(club_key, members_dict))


@bot.tree.command(name="club-member-remove", description="Select a club first, then choose a member to remove from it.")
@app_commands.checks.has_permissions(administrator=True)  # 🔒 ADMIN ONLY
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
        await interaction.response.send_message(
            f"⚠️ There are currently no members in **{clan_data['clubs'][club_key]['title']}** to remove.",
            ephemeral=True
        )
        return

    embed = discord.Embed(
        title=f"🔻 Remove Member from {clan_data['clubs'][club_key]['title']}",
        description="Select the member you want to remove from the dropdown menu below:",
        color=discord.Color.dark_red()
    )
    await interaction.response.send_message(embed=embed, view=ClubRemoveView(club_key, members), ephemeral=True)
