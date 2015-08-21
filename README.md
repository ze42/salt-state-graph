This scripts help visualise state dependencies within salt states.

# Main usage

Use a `show_lowstate`, or `show_low_sls` to get an idea what salt would do, and
visualise dependencies about all those states.

```bash
# Generate a .low file
# Either for a full lowstate
salt --out=yaml --out-file=<minion>.low <minion> state.show_lowstate
# Or a given sls
salt --out=yaml --out-file=<minion>.low <minion> state.show_low_sls generic.ssh

# Retrieve the file, and convert it to svg
# Note: will also generate a .dot file next to your svg
./low2svg.sh <minion>.low <minion>.svg
```

You might also want to use `salt-state-check-graph.py` to check dependencies,
but that will need some more wrapping to get a nice output, and get it
documented properly.


# Legend

Color

  * Blue - require
  * Red - watch

Style

  * Plain - normal dependencies
  * Dashed - reverse dependencies (Using `_in` in the source)

# Requirements

  * Package `python-pydot` -- library to generate and manipulate `dot` graphs.
  * Package `graphviz` -- binaries to generate the `svg` from the `dot` files.

# low2svg.sh

Main script to convert your .low file into an image.

```text
Usage:
  low2svg.sh show_sls.low...

Convert show_sls_low outputs (yaml) to svg documents.

Note: write dot and svg directly next to the .low files.
```

The input file can be generated with either the global command
`state.show_lowstate` or for a specific sls with `state.show_low_sls`.
Input file must be `yaml`, it can be generated with
`--out=yaml --out-file=<filename>.low`.
