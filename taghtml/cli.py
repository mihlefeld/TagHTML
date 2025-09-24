import typer
import os
import shutil
from pathlib import Path
from typing import Annotated

app = typer.Typer(add_completion=False, no_args_is_help=True, pretty_exceptions_show_locals=False)

def init_directory():
    package_dir = Path(__file__).parent
    graphics = list((package_dir / "graphics").rglob("*"))
    styles = list((package_dir / "styles").rglob("*"))
    jsons = list((package_dir / "jsons").glob("*"))
    templates = list((package_dir / "templates").glob("*"))
    base_files = graphics + styles + jsons + templates
    confirmed = False
    for file in base_files:
        if file.is_dir():
            continue
        rel = file.relative_to(package_dir)
        if rel.is_file():
            continue
        elif not confirmed:
            value = input("Some files are missing from your directory, do you want to copy them? This will also create folders if necessary. (y/n)")
            if value.lower().strip() != "y":
                print("Exiting")
                exit(1)
            confirmed = True
        # print(f"copy {file.absolute().as_posix()} {rel.absolute().as_posix()}")
        rel.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(file, rel)

@app.command()
def main(
        comp_id: Annotated[str, typer.Argument(help="Competition ID from the competition link.")], 
        output_path: Annotated[Path | None, typer.Argument(help="File name of the output html file. If empty, will try to start an interactive server instead.")] = None,
        height: Annotated[float, typer.Option("--height", "-h", help="Height of each nametag in cm.")] = 5.5,
        width: Annotated[float, typer.Option("--width", "-w", help="Width of each nametag in cm.")] = 8.5, 
        update: Annotated[bool, typer.Option(help="Set this flag to update the database before generating the nametags.")] = False, 
        template_path: Annotated[Path, typer.Option("--template", "-t", help="Path to the html template file.")] = Path("templates/basic.jinja"), 
        experience_emoji_path: Annotated[Path, typer.Option("--experience-emoji-path", "--eep", help="Path to the json file mapping a number of competitions to an emoji.")] = "jsons/experience_emoji.json", 
        people_emoji_path: Annotated[Path, typer.Option("--people-emoji-path", "--pep", help="Path to the json file mapping wca id to an emoji.")] = "jsons/people_emoji.json", 
        cid_modulo_emoji_path: Annotated[Path, typer.Option("--cid-modulo-emoji-path", "--cep", help="Path to the json file mapping the competitor id to an emoji.")] = "jsons/cid_modulo_emoji.json", 
        papersize: Annotated[str, typer.Option(help="Paper size as standard format or measurements, some examples: A4, Letter, 20cm 30cm, 4in 5in")] = "A4",
    ):    
    from taghtml.datahandler import update_data, CompetitorData
    from taghtml.jinjarenderer import JinjaRenderer
    init_directory()
    if update:
        update_data()
    from rich.progress import Progress
    with Progress() as p:
        cod = p.add_task("Computing data.")
        comp_data = CompetitorData(comp_id)
        p.update(cod, completed=100)
        r = JinjaRenderer(width, height, template_path, experience_emoji_path, people_emoji_path, cid_modulo_emoji_path, papersize)
        if output_path:
            rth =  p.add_task("Rendering to HTML.")
            os.makedirs(output_path.parent, exist_ok=True)
            r.render_file(comp_data, output_path)
            p.update(rth, completed=100)
        else:
            r.setup(comp_data)
    if not output_path:
        import fastapi
        from fastapi.staticfiles import StaticFiles
        server = fastapi.FastAPI()
        @server.get("/")
        def render(tag_width: float | None = None, tag_height: float | None = None):
            return fastapi.responses.HTMLResponse(r.render(tag_width, tag_height))
        import uvicorn
        server.mount("/styles", StaticFiles(directory="styles", html=True), name="styles")
        server.mount("/graphics", StaticFiles(directory="graphics", html=True), name="graphics")
        uvicorn.run(server, )


if __name__ == "__main__":
    app()