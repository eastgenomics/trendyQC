# commands

These scripts are used to handle the import of MultiQC reports into the database.

## _check.py

The aim of this script is to check things. So far only one function is present is to check if a model object is present in the database

## _dnanexus_utils.py

Collection of functions that have something to do with DNAnexus.

## _multiqc.py

Script containing the MultiQC report object and everything needed to setup the data in a way to be imported.

## _notifications.py

Script containing functions for the notifications via Slack

## _parsing.py

Script to parse things (only parsing the assay config)

## _report.py

Script to handle the setup and import of MultiQC reports.

## _tool.py

Script containing the tool class object.

## _utils.py

Script containing functions that didn't fit in other scripts or are general purpose

## add_projects.py

This script is the entrypoint for importing data.
