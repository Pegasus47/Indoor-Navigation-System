# Indoor Navigation System

##### This project aims to make a robust navigation system which produces navigation paths given dxf files or floor plans. 
---
### Installation guide
- To install this on your system
  
`git clone https://github.com/Pegasus47/Indoor-Navigation-System.git`

- Change into this directory
  
`cd Indoor-Navigation-System`

- Source your python env, preferably with venv
  
`source venv/bin/activate`

- and run the demo with
  
`python3 main.py d_block_demo.dxf`

- if you want to run it with your custom file please make sure to run it with
  
`python3 main.py <your_file_name>.dxf`

---
### File structure 
1. *constants.py*: list of relavent constants used throughout the project
2. *dxf_viewer.py*: main game loop with handles the rendering of the `.dxf` files
3. *nav_engine.py*: modular component which makes the graph in the form of nodes and an adjecency list (will be expanded to also use algorithms for path finding)
4. *main.py*: responsible for importing all the modular components and running the programs  



