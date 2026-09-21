#!/usr/bin/env bash
# batch_inspect.sh
# Inspect all TSV files in a directory and report basic stats.
# Usage: ./batch_inspect.sh <directory>

if [ $# -ne 1 ]; then
    echo "Usage: $0 <directory>"
    exit 1
fi

DIRPATH="$1"

if [ ! -d "$DIRPATH" ]; then
    echo "Error: not a directory: $DIRPATH"
    exit 1
fi

# Count how many TSV files we found
TSV_COUNT=$(ls "$DIRPATH"/*.tsv 2>/dev/null | wc -l | tr -d ' ')

if [ "$TSV_COUNT" -eq 0 ]; then
    echo "No TSV files found in: $DIRPATH"
    exit 0
fi

echo "Found $TSV_COUNT TSV file(s) in: $DIRPATH"
echo ""
printf "%-35s  %8s  %8s\n" "Filename" "Rows" "Columns"
printf "%-35s  %8s  %8s\n" "--------" "----" "-------"

for FILEPATH in "$DIRPATH"/*.tsv; do
    FILENAME=$(basename "$FILEPATH")
    ROWS=$(tail -n +2 "$FILEPATH" | wc -l | tr -d ' ')
    COLS=$(head -1 "$FILEPATH" | tr '\t' '\n' | wc -l | tr -d ' ')
    printf "%-35s  %8d  %8d\n" "$FILENAME" "$ROWS" "$COLS"
done

