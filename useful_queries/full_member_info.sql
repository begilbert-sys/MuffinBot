SELECT * FROM stats_member
JOIN stats_user ON stats_member.user_id = stats_user.id
JOIN stats_guild ON stats_member.guild_id = stats_guild.id
--WHERE stats_user.id = ;