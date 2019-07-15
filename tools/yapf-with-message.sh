#!/bin/bash

yapf_args=( "$@" )

function fail_yapf () {
    # lots of space to make it obvious
    set +x
    echo ""
    echo ""
    echo "=========================================="
    echo ""
    echo "  To correct formatting, run: tox -e fmt"
    echo ""
    echo "=========================================="
    echo ""
    echo ""
    return 1
}

function run_yapf () {
    yapf -dr "${yapf_args[@]}" || fail_yapf
}

run_yapf

