import os
import sys
import json
#File should look like this, 
"""
[Node.P2P]
StaticNodes = [
  "enode://2b775bc162310dea781618d1ffc25477289460891565043ab899bc83d2ec1b166deea94d713a94611bf1abbbeec1fdf57b07aa2c6c604edda4039deeaf490951@138.197.32.246:30303?discport=30306",
  "enode://2df673c2cfa6a9696dda8cf2878373500ccfac39910f3869d2e61efdf5d51bab8b7a4310caee522db65d578ae0cfc64b87d3cd7470844ee2ae58fa645ac1c817@134.209.41.49:30301?discport=30310"
]
"""
#It will probably be easiest to make the list in the smartmeter.py as a json file and pass that
def make_config_toml_file():
  abs_dir = os.path.dirname(os.path.abspath(__file__))
def main():
  make_config_toml_file()

if __name__ == "__main__":
  main()