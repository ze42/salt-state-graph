#! /bin/sh

usage()
{
    cat <<EOF >&2
Usage:
  ${0##*/} show_sls.low...

Convert show_sls_low outputs (yaml) to svg documents.

Note: write dot and svg directly next to the .low files.

EOF
    exit 1
}
die()
{
    cat <<EOF >&2
ERROR: $@
EOF
    exit 2
}

binbase=$(dirname "$0")
stategraph="$binbase/salt-state-graph.py"

[ -x "$stategraph" ] || die "${stategraph##*/}: binary not found"


[ $# -lt 1 ] && usage


for low ; do
    [ "${low}" = "${low%.low}" ] && die "$low: file does not end by .low"
    base="${low%.low}"
    dot="${base}.dot"
    svg="${base}.svg"
    "$stategraph" "$low" "$dot" &&
    dot -Tsvg < "$dot" -o "$svg" &&
    echo "ok: $svg" ||
    echo "ERROR: $low"
done
