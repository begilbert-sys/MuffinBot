SELECT * FROM stats_guilduser
JOIN stats_user ON stats_guilduser.user_id = stats_user.id
JOIN stats_guild ON stats_guilduser.guild_id = stats_guild.id
--WHERE stats_user.id = ;