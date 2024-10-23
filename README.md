# Image-Visualizer
a pygame program written with assistance of claude.ai

This program let's you add images by dragging them onto the interface, then connecting images together by dragging them onto one another. Connections can be broken by dragging previously connected images onto one another. The current example is using pokemon. 

Things to Fix:
- Connection breaking seems to be one sided, so if one direction doesn't break it currently we have to try the other direction. 

Things to Implement:
- File and system Menus
- Graph Paper like Grid?
- Dark Mode
- Thicker Connection Lines and/or animation of the lines pulsing
- move images into folders based on connections
- rename images
- add corresponding text file for image, edit text file, show text as tooltip
    - click on image and keep it selected, while selected show tooltip
- auto loading
- multiple instances to be saved and loaded
- larger canvas area, can click and drag to see it or use arrow keys or wasd keys
- grouping, like a circular area that surrounds groups of images? ability to name groups, folder things go into is named for the group
- many to many connections?
- redirect to missing images inside of folders and sub folders, scan for them
- category by color ring, official, unofficial, mega etc, have a color key too
- I need an equivalent connection type alongside the hierarchical, maybe direction arrows?
- arrow icon indicating if something is offscreen in that direction, click said icon to be taken to it
- ways to sort and view only certain ones, may require a different kind of anchoring system
- color coded lines to show different types of connections, be able to assign them, have a key and by clicking on the key only show those and hide the rest. for pokemon this may look like "evolution, trade with, alternate form, rival", while with something else like superhero characters it could be "parent, lover, sibling, rival, killed, friend, teammate"
