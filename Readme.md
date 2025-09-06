# TagHTML
1. Install taghtml: pip install -e
2. Run the script:
`taghtml <here goes the competition id> <name of the output html file> --height <height of the nametags> --width <width of the nametags> --update --format <A4/Letter>`
Only use `--update` when you don't already have a current version of the wca database export in the correct location. 
3. Open the html file in chrome and print to pdf. Firefox does weird things with the margins.

Full help text:
```
Usage: taghtml [OPTIONS] COMP_ID OUTPUT_PATH                                                                                                                                                                                                                                                       

╭─ Arguments ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ *    comp_id          TEXT  Competition ID from the competition link. [default: None] [required]                                                                │
│ *    output_path      PATH  File name of the output html file. [default: None] [required]                                                                       │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --height                       -h                 FLOAT  Height of each nametag in cm. [default: 5.4]                                                           │
│ --width                        -w                 FLOAT  Width of each nametag in cm. [default: 9.0]                                                            │
│ --update                           --no-update           Set this flag to update the database before generating the nametags. [default: no-update]              │
│ --template-path                                   PATH   Path to the html template file. [default: template.html]                                               │
│ --experience-emoji-path,--emp                     PATH   Path to the json file mapping a number of competitions to an emoji. [default: experience_emoji.json]   │
│ --people-emoji-path,--emp                         PATH   Path to the json file mapping a number of competitions to an emoji. [default: people_emoji.json]       │
│ --cid-modulo-emoji-path,--emp                     PATH   Path to the json file mapping a number of competitions to an emoji. [default: cid_modulo_emoji.json]   │
│ --format                                          TEXT   Page format to use for printing [default: A4]                                                          │
│ --help                                                   Show this message and exit.                                                                            │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```


You can edit the template pretty much anyway you like. You need to keep the basic sctructure of:
```
<div id="page-example" class="page">
    <div id="front-tag" class="tag left-border top-border">
    </div>
    <div id="back-tag" class="tag left-border top-border">
    </div>
</div>
```

If you want a table with all round 1 assignments you need to mark the template for one row of this table with class "fill-row-template". This template will then be copied and filled with the different event assignments.


