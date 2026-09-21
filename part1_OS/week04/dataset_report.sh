#!/usr/bin/env bash
# dataset_report.sh
# Generate a summary report of all TSV files in a directory.
# Usage: ./dataset_report.sh <directory>
#
# Author: Holden Carey
# Date: 9/15/2026

# ── Argument handling ────────────────────────────────────────────────────────

if [ $# -ne 1 ]; then
    echo "Usage: $0 <directory>"
    exit 1
fi

DIRPATH="$1"

if [ ! -d "$DIRPATH" ]; then
    echo "Error: not a directory: $DIRPATH"
    exit 1
fi

# ── Initialise counters and log file ─────────────────────────────────────────

TOTAL_FILES=0
TOTAL_ROWS=0
SMALL_FILES=0
OVERALL_RESULT="PASS"
SMALL_LOG="small_files.log"
 
> "$SMALL_LOG"

echo "Dataset Report"
echo "Directory: $DIRPATH"
echo "Generated: $(date +"%Y-%m-%d %H:%M:%S")"
echo "============================================================"
echo ""

# ── Main loop: process each TSV file ─────────────────────────────────────────

for FILEPATH in "$DIRPATH"/*.tsv; do
    [ -e "$FILEPATH" ] || continue

    FILENAME=$(basename "$FILEPATH")
    ROWS=$(tail -n +2 "$FILEPATH" | wc -l | tr -d ' ')
    COLS=$(head -1 "$FILEPATH" | tr '\t' '\n' | wc -l | tr -d ' ')
    FIELDS=$(head -1 "$FILEPATH" | cut -f1-3 | tr '\t' '|' | sed 's/|/ | /g')

    
    BAD_ROWS=$(awk -F'\t' -v cols="$COLS" 'NF != cols {print NR}' "$FILEPATH" | wc -l | tr -d ' ')
    if [ "$BAD_ROWS" -eq 0 ]; then
        VALIDATION="PASS"
    else
        VALIDATION="FAIL"
        OVERALL_RESULT="FAIL"
    fi

    echo "File: $FILENAME"
    echo "  Rows:    $ROWS"
    echo "  Columns: $COLS"
    echo "  Fields:  $FIELDS"
    echo "  Validation: $VALIDATION"
    echo ""

    TOTAL_FILES=$((TOTAL_FILES + 1))
    TOTAL_ROWS=$((TOTAL_ROWS + ROWS))

    if [ "$ROWS" -lt 100 ]; then
        SMALL_FILES=$((SMALL_FILES + 1))
        echo "$FILENAME: $ROWS rows" >> "$SMALL_LOG"
    fi
done

# ── Summary ───────────────────────────────────────────────────────────────────

echo "============================================================"
echo "Summary"
echo "  Files processed: $TOTAL_FILES"
echo "  Total rows:      $TOTAL_ROWS"
echo "  Small files:     $SMALL_FILES"
echo "  Overall result:  $OVERALL_RESULT"

if [ "$OVERALL_RESULT" = "PASS" ]; then
    exit 0
else
    exit 1
fi
