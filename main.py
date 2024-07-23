import click
from pathlib import Path
from taghtml.datahandler import update_data, CompetitorData
from taghtml.htmlrenderer import BS4Renderer

@click.command()
@click.option("--comp_id", help="Competition ID from the competition link.")
@click.option("--height", help="Height of each nametag", default=5.4)
@click.option("--width", help="Width of each nametag", default=9.0)
@click.option("--update/--no_update", help="Set this flag if the daabase needs to be updated.", default=False)
@click.option("--template_path", help="Path to the html template that should be used.", default='template.html')
@click.option("--exp_emoji_path", help="Path to the json file that encodes which emoji to use for different number of competitions.", default="experience_emoji.json")
@click.option("--format", help="Page format to use for printing.", default="A4")
def main(comp_id, height, width, update, template_path, exp_emoji_path, format):
    if update:
        update_data()
    comp_data = CompetitorData(comp_id)
    r = BS4Renderer(width, height, template_path, exp_emoji_path, format)
    r.render(comp_data, "name_tags.html")

if __name__ == "__main__":
    main()