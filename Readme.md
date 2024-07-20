# TagHTML
1. Install the requirements: `pip install -r requirements.txt`
2. Create a folder for you competition.
3. Run the script:
`python main.py --comp_id <here goes the competition id> --height <height of the nametags> --width <width of the nametags> --update --format <A4/Letter>`
Only use `--update` when you don't already have a current version of the wca database export in the correct location. 
5. Open the html file in chrome and print to pdf. Firefox does weird things with the margins.


You can edit the template pretty much anyway you like, currently changing height/width and format is not yet suppported but i plan to add it. You need to keep the basic sctructure of:
```
<div id="page-example" class="page">
    <div id="front-tag" class="tag left-border top-border">
    </div>
    <div id="back-tag" class="tag left-border top-border">
    </div>
</div>
```

If you want a table with all round 1 assignments you need to mark the template for one row of this table with class "fill-row-template". This template will then be copied and filled with the different event assignments.


