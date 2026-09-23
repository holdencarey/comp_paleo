
## Basics of Linux for Data Management
This project is a compilation of useful scripts for a Computational Paleobiology course aimed at data manangement. Scripts start out with understanding the command line and making directories and extend into basic data warngling techniques. These scripts teach the basic logic of C++ coding for data management. 

## Course Context
Computational Paleobiology, The University of Texas at Austin, Fall 2026

## Repository Structure 
Both the repository structure and course are divied into three sections part1_OS, part2_DB, and part3_AL. Each of this directories have subdirectores that store week by week assingments and practice. Please refer to the following weeks to discover what each week entails.
Week 1: Intro to the OS
Week 2: The Posix Shell 
Week 3: Piping
Week 4: Shell Scripting 

## Dependencies 
WSL2 and bash
Important tools: awk, sed, grep, sort

## Usage
Input: Prints the row count, column count, and header field names for the given TSV file
./dataset_info.sh ~/comp_paleo/part1_OS/week03/otb_fossils.tsv

## Output:
=====================================
File:    otb_fossils.tsv
Rows:    1242 (excluding header)
Columns: 30
Header fields:
     1  catalog_number
     2  organism_id
     3  preparations
     4  year
     5  discovered_by
     6  continent
     7  country
     8  state_province
     9  region
    10  subregion
    11  place
    12  locality
    13  earliest_period_or_lowest_system
    14  latest_period_or_highest_system
    15  earliest_epoch_or_lowest_series
    16  latest_epoch_or_highest_series
    17  earliest_age_or_lowest_stage
    18  latest_age_or_highest_stage
    19  formation
    20  member
    21  bed
    22  scientific_name
    23  identification_qualifier
    24  date_identified
    25  verbatim_identification
    26  verbatim_chronometric_age
    27  earliest_chronometric_age
    28  earliest_chronometric_age_reference_system
    29  latest_chronometric_age
    30  latest_chronometric_age_reference_system
=====================================

## Input: Checks that every row in the file has expected number of columns and then reports PASS/FAIL for each check
./validate_tsv.sh ~/comp_paleo/part1_OS/week03/otb_fossils.tsv 30

## Output:
Validating: /home/hjdca/comp_paleo/part1_OS/week03/otb_fossils.tsv
Expected columns: 30
---
PASS: header has 30 columns
INFO: 1242 data rows (plus 1 header)
PASS: all rows have 30 columns
---
RESULT: PASSED (0 errors)

## Data
The dataset used is open access from Origins database: https://paleocore.org/origins/

## Author
Holden Carey 
hc34867@my.utexas.edu
