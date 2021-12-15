from .arxivsearch import ArxivSearch


def setup(bot):
    bot.add_cog(ArxivSearch(bot))
