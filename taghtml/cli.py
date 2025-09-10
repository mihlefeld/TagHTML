import typer
import os
from pathlib import Path
from typing import Annotated

app = typer.Typer(add_completion=False, no_args_is_help=True, pretty_exceptions_show_locals=False)

@app.command()
def main(
        comp_id: Annotated[str, typer.Argument(help="Competition ID from the competition link.")], 
        output_path: Annotated[Path, typer.Argument(help="File name of the output html file.")],
        height: Annotated[float, typer.Option("--height", "-h", help="Height of each nametag in cm.")] = 5.4,
        width: Annotated[float, typer.Option("--width", "-w", help="Width of each nametag in cm.")] = 9.0, 
        update: Annotated[bool, typer.Option(help="Set this flag to update the database before generating the nametags.")] = False, 
        template_path: Annotated[Path, typer.Option(help="Path to the html template file.")] = Path("template.html"), 
        experience_emoji_path: Annotated[Path, typer.Option("--experience-emoji-path", "--eep", help="Path to the json file mapping a number of competitions to an emoji.")] = "experience_emoji.json", 
        people_emoji_path: Annotated[Path, typer.Option("--people-emoji-path", "--pep", help="Path to the json file mapping a number of competitions to an emoji.")] = "people_emoji.json", 
        cid_modulo_emoji_path: Annotated[Path, typer.Option("--cid-modulo-emoji-path", "--cep", help="Path to the json file mapping a number of competitions to an emoji.")] = "cid_modulo_emoji.json", 
        format: Annotated[str, typer.Option(help="Page format to use for printing")] = "A4",
        jinja: Annotated[bool, typer.Option(help="Use the jinja rendering engine instead of BS4")] = False,
    ):    
    from taghtml.datahandler import update_data, CompetitorData
    from taghtml.htmlrenderer import BS4Renderer
    from taghtml.jinja_renderer import JinjaRenderer
    if update:
        update_data()
    from rich.progress import Progress
    with Progress() as p:
        cod = p.add_task("Computing data.")
        comp_data = CompetitorData(comp_id)
        p.update(cod, completed=100)
        if jinja: 
            r = JinjaRenderer(width, height, template_path, experience_emoji_path, people_emoji_path, cid_modulo_emoji_path, format)
        else:
            r = BS4Renderer(width, height, template_path, experience_emoji_path, people_emoji_path, cid_modulo_emoji_path, format)
        os.makedirs(output_path.parent, exist_ok=True)
        rth =  p.add_task("Rendering to HTML.")
        r.render(comp_data, output_path, p)
        p.update(rth, completed=100)

if __name__ == "__main__":
    app()