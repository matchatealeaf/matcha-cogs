import discord
import arxiv
import math
from redbot.core import commands
from redbot.core.utils.menus import menu, DEFAULT_CONTROLS


class ArxivSearch(commands.Cog):
    """Cog that queries arXiv using arxiv API wrapper.

    Functions:
        - _arxiv_results()
            Query arXiv with API wrapper.
            Format results into a list of embeds.

    Commands:
        - arxivsearch [arxiv, arx]
            Get list of embeds from _arxiv_results().
            Use redbot menu utils to browse pages of embeds.
            Return no result message if _arxiv_results() returns empty.
    """

    async def red_delete_data_for_user(self, **kwargs):
        """Nothing to delete"""
        return

    def __init__(self, bot):
        self.bot = bot

    async def _arxiv_results(self, terms: str, N: int):
        """Query arXiv and put in embeds."""

        # Query arxiv with API wrapper
        search = arxiv.Search(
            query=terms,
            max_results=N,
        )

        # No results
        if next(search.results(), None) is None:
            return

        # Replace spaces with + for url link
        terms_url = terms.replace(" ", "+")

        # Get number of results from generator
        results_list = list(search.results())
        num_results = len(results_list)

        # Create list of Discord embeds each with at most 5 results
        ems = [
            discord.Embed(
                title=f"arXiv search results for:\n**{terms}**",
                url=f"https://arxiv.org/search/?query={terms_url}&searchtype=all&source=header",
            )
            for _ in range(math.ceil(num_results / 5))
        ]

        # Loop through each result
        for i, result in enumerate(results_list):

            # Get string of clickable authors
            authors = ""
            extra = 0
            for j, author in enumerate(result.authors):
                # Only show 5 authors
                if j > 4:
                    authors += f" and {len(result.authors) - 5 - extra} others."
                    break
                # Edge cases. Skip ":"
                if author.name == ":":
                    extra += 1
                    continue
                # get rid of "in collaboration with" (first 21 characters)
                if "in collaboration with" in author.name:
                    author.name = author.name[21:]

                author_url = author.name.replace(" ", "+")
                authors += f" | [**{author.name}**](https://arxiv.org/search/?searchtype=author&query={author_url})"

            # Remove first " | "
            authors = authors[3:]

            # Embed values
            abs_url = f"[**Link**]({result.entry_id.replace('http', 'https')})"
            pdf_url = f"[**PDF**]({result.pdf_url.replace('http', 'https')})"
            updated = f"Updated: {str(result.updated)[:10]}"
            submitted = f"Submitted: {str(result.published)[:10]}"

            # Add DOI link if there's DOI
            if result.doi:
                doi_url = f"[**DOI**](https://dx.doi.org/{result.doi})"
                urls = abs_url + " | " + doi_url + " | " + pdf_url
            else:
                urls = abs_url + " | " + pdf_url

            # updated == published/submitted if paper is not updated
            # Also only show published/submitted if they are the same date
            if str(result.updated)[:10] == str(result.published)[:10]:
                pub_or_update = submitted
            else:
                pub_or_update = submitted + " | " + updated

            # Show journal_ref before dates if exists
            if result.journal_ref:
                pub_or_update = result.journal_ref + "\n" + pub_or_update

            # Add embed field for each result
            # Add to next embed after 5 results
            ems[int(i / 5)].add_field(
                name=f"{i+1}) {result.title} [{result.primary_category}]",
                value=authors + "\n" + pub_or_update + "\n" + urls,
                inline=False,
            )

            # Page number and number of results with thanks to arXiv
            ems[int(i / 5)].set_footer(
                text=f"Page {int(i/5)+1}/{math.ceil(num_results/5)} of {num_results} results."
                + "\n"
                + "Thank you to arXiv for use of its open access interoperability."
            )

        return ems

    @commands.command(aliases=["arxiv", "arx"])
    async def arxivsearch(self, ctx, *, terms: str):

        # Show bot is typing
        await ctx.channel.trigger_typing()

        ems = await self._arxiv_results(terms, N=50)
        if ems:
            await menu(ctx, ems, DEFAULT_CONTROLS, timeout=600)
        else:
            await ctx.send(f"No results found for '{terms}'.")

    # Error message of arxivsearch
    @arxivsearch.error
    async def arxivsearch_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Please specify search terms.")
