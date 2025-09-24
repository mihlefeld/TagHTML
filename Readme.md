# TagHTML
1. Install taghtml: pip install -e
2. Run the script: `taghtml [OPTIONS] --update COMP_ID` to download the latest wca export and start an interactive server that will re-render the template everytime you reload the page.
Only use `--update` when you don't already have a current version of the wca database export in the correct location. 
3. Visit http://localhost:8000 in chrome to render the current template.

Full help text:
```
 Usage: taghtml [OPTIONS] COMP_ID [OUTPUT_PATH]                                                                                                                                                                                                                                                       

╭─ Arguments ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ *    comp_id          TEXT           Competition ID from the competition link. [default: None] [required]                                                            │
│      output_path      [OUTPUT_PATH]  File name of the output html file. If empty, will try to start an interactive server instead. [default: None]                   │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --height                       -h                 FLOAT  Height of each nametag in cm. [default: 5.5]                                                                │
│ --width                        -w                 FLOAT  Width of each nametag in cm. [default: 8.5]                                                                 │
│ --update                           --no-update           Set this flag to update the database before generating the nametags. [default: no-update]                   │
│ --template                     -t                 PATH   Path to the html template file. [default: templates\basic.jinja]                                            │
│ --experience-emoji-path,--eep                     PATH   Path to the json file mapping a number of competitions to an emoji. [default: experience_emoji.json]        │
│ --people-emoji-path,--pep                         PATH   Path to the json file mapping wca id to an emoji. [default: people_emoji.json]                              │
│ --cid-modulo-emoji-path,--cep                     PATH   Path to the json file mapping the competitor id to an emoji. [default: cid_modulo_emoji.json]               │
│ --papersize                                       TEXT   Paper size as standard format or measurements, some examples: A4, Letter, 20cm 30cm, 4in 5in [default: A4]  │
│ --help                                                   Show this message and exit.                                                                                 │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```


The templating engine is based on [jinja](https://jinja.palletsprojects.com/en/stable/) and leaves a lot of freedom but the very basic structure of using pages and tag divs should probably stay the same.
The "flex direction row-reverse" is only important for 2 sided printing. If you know your printer needs something else, you can change it.
```
{% for page in pages %}
<div class="page">
    {% for competitor in page %}
    <div class="tag">
        do anything here
    </div>
    {% endfor %}
</div>
<div class="page" style="flex-direction: row-reverse;">
    {% for competitor in page %}
    <div class="tag">
        do anything here
    </div>
    {% endfor %}
</div>
{% endfor %}
```


The data available to you in your jinja template looks a bit like this following example, though in a real use-case scenario it would contain multiple pages and all assignments.
```python
{
    "comp_name": "Competition Name 2025",
    "comp_id": "CompetitionName2025",
    "pages": [ # the data for each competitor organized in pages
        [ # the number of competitors per page depends on the width and height you provided when starting taghtml, you can change the values without restarting by adding new width/height into the url: localhost:8000/?tag_width=9&tag_heigt=6 for example
            {
                "name": "Some One",
                "native_name": "",
                "wca_id": "2025SOME99",
                "iso2": "DE",
                "iso2flag": "🇩🇪",
                "firstname": "Some",
                "lastname": "One",
                "assignments": [
                    Assignment( # can be accessed lik a normal dictionary in Jinja
                        event="666",
                        round=1,
                        group=5,
                        role="competitor", # this is the role the competitor has for this specific assignment
                        start_time=datetime.datetime(2025, 9, 26, 11, 30), # this is the start time of the overall event
                        end_time=datetime.datetime(2025, 9, 26, 12, 40), # and the end time
                        group_start_time=datetime.datetime(2025, 9, 26, 12, 5), # this is the start time of the specific group
                        group_end_time=datetime.datetime(2025, 9, 26, 12, 40), # and the end time
                        room_name="stage-2", # this is the wca site room name but .lower() and spaces replaced by "-" so you can use it as a css class name
                    ),
                    Assignment(
                        event="777",
                        round=1,
                        group=3,
                        role="competitor",
                        start_time=datetime.datetime(2025, 9, 26, 10, 10),
                        end_time=datetime.datetime(2025, 9, 26, 11, 30),
                        group_start_time=datetime.datetime(2025, 9, 26, 10, 10),
                        group_end_time=datetime.datetime(2025, 9, 26, 10, 50),
                        room_name="stage-3",
                    ),
                ],
                "event_assignments": {
                    "666": {
                        "r1": [
                            Assignment(
                                event="666",
                                round=1,
                                group=5,
                                role="competitor",
                                start_time=datetime.datetime(2025, 9, 26, 11, 30),
                                end_time=datetime.datetime(2025, 9, 26, 12, 40),
                                group_start_time=datetime.datetime(2025, 9, 26, 12, 5),
                                group_end_time=datetime.datetime(2025, 9, 26, 12, 40),
                                room_name="stage-2",
                            )
                        ]
                    },
                    "777": {
                        "r1": [
                            Assignment(
                                event="777",
                                round=1,
                                group=3,
                                role="competitor",
                                start_time=datetime.datetime(2025, 9, 26, 10, 10),
                                end_time=datetime.datetime(2025, 9, 26, 11, 30),
                                group_start_time=datetime.datetime(2025, 9, 26, 10, 10),
                                group_end_time=datetime.datetime(2025, 9, 26, 10, 50),
                                room_name="stage-3",
                            )
                        ]
                    },
                },
                "event_comp_r1_assignments": {
                    "666": Assignment( 
                        event="666",
                        round=1,
                        group=5,
                        role="competitor",
                        start_time=datetime.datetime(2025, 9, 26, 11, 30),
                        end_time=datetime.datetime(2025, 9, 26, 12, 40),
                        group_start_time=datetime.datetime(2025, 9, 26, 12, 5),
                        group_end_time=datetime.datetime(2025, 9, 26, 12, 40),
                        room_name="stage-2",
                    ),
                    "777": Assignment(
                        event="777",
                        round=1,
                        group=3,
                        role="competitor",
                        start_time=datetime.datetime(2025, 9, 26, 10, 10),
                        end_time=datetime.datetime(2025, 9, 26, 11, 30),
                        group_start_time=datetime.datetime(2025, 9, 26, 10, 10),
                        group_end_time=datetime.datetime(2025, 9, 26, 10, 50),
                        room_name="stage-3",
                    ),
                },
                "event_help_r1_assignments": {
                    "333oh": [
                        Assignment(
                            event="333oh",
                            round=1,
                            group=1,
                            role="runner",
                            start_time=datetime.datetime(2025, 9, 26, 17, 20),
                            end_time=datetime.datetime(2025, 9, 26, 18, 40),
                            group_start_time=datetime.datetime(2025, 9, 26, 17, 20),
                            group_end_time=datetime.datetime(2025, 9, 26, 17, 46, 40),
                            room_name="stage-1",
                        )
                    ],
                    "clock": [
                        Assignment(
                            event="clock",
                            round=1,
                            group=3,
                            role="runner",
                            start_time=datetime.datetime(2025, 9, 26, 16, 15),
                            end_time=datetime.datetime(2025, 9, 26, 17, 20),
                            group_start_time=datetime.datetime(2025, 9, 26, 16, 15),
                            group_end_time=datetime.datetime(2025, 9, 26, 16, 47, 30),
                            room_name="stage-3",
                        )
                    ],
                },
                "cid_emoji": "🐆",
                "pep_emoji": "",
                "exp_emoji": "🦚",
                "id": 42,
                "country": "Germany",
                "num_competitions": 156,
                "roles": [], # this will contain delegate or organizer roles (i think)
                "qr": "data:image/svg+xml;b...", # you can use this qr code in an image tag as src, for now it will always lead to the overview for the competitor on competitiongroups.
            },
            ...
        ],
        ...
    ],
    "wca_events": ["333", "222", "444", "555", "666", "777", "333bf", "333fm", "333oh", "clock", "minx", "pyram", "skewb", "sq1", "444bf", "555bf", "333mbf"], # all wca events in wca event order
    "event_times": { # full schedule with every round for every event
        ("333", 1): ( # key is event, round
            datetime.datetime(2025, 9, 27, 9, 0), # first entry is start time
            datetime.datetime(2025, 9, 27, 11, 0), # second entry is end time
        ), 
    },
    "event_r1_times": OrderedDict( # only round one start times in wca event order
        {
            "333": ( # since it's only round 1, we don't need the round as key
                datetime.datetime(2025, 9, 27, 9, 0),
                datetime.datetime(2025, 9, 27, 11, 0),
            ), 
        }
    ),
    "tag_width": 8.5,
    "tag_height": 5.5,
    "page_width": 21.0,
    "page_height": 29.7,
}
```