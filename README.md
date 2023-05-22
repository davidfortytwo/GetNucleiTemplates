# Description

This set of Python scripts helps to automate the process of gathering and organizing various GitHub repositories which contain Nuclei templates. The first script, getnucleitemplates.py, clones repositories from a list in a text file, checks for validity of the URLs, handles any issues with gists or duplicates, and organizes the clones in a directory. The second script, searchmore.py, uses the GitHub API to search for additional repositories containing Nuclei templates, prompts the user if they wish to clone the discovered repositories, and adds them to the list.

Nuclei is a project that allows you to customize scanning for specific vulnerabilities, and these templates are the definitions of those specific vulnerabilities. This script helps in automating the process of getting those templates.

# Installation

# Prerequisites

* Python 3.6 or newer: You can download it from the official Python website.
* GitPython package: You can install it via pip with the following command in your terminal:

  pip install GitPython

* Git: This script uses git commands to clone repositories. If you haven't installed git yet, you can download it from the official Git website.

# Usage

* Update the nuclei.txt file with the list of repositories you want to clone.
* Run the getnucleitemplates.py script to clone the repositories. It will clone the repositories into a new nuclei_templates directory, ignore commented lines, and comment out any invalid URLs.

  python3 getnucleitemplates.py

* You will see a summary of the attempted downloads, successful downloads, failed downloads, ignored gists, and ignored invalid URLs. Any failed or invalid repository URLs will be commented out in nuclei.txt.
* To find more repositories, run the searchmore.py script. This will search GitHub for repositories containing the string "nuclei-templates". It will handle pagination to ensure all possible repositories are found, and respect GitHub's rate limits.

  python3 searchmore.py

You will be presented with a summary of the found repositories. If you choose to download the found repositories, they will be added to the nuclei.txt file and getnucleitemplates.py will be executed to clone them.

Please note that using the GitHub API may require a personal access token if you need to make a large number of requests. Refer to the GitHub API documentation for more information.

# Notes

The scripts will treat GitHub Gist links as invalid URLs and ignore them.

The scripts check for the existence of repositories before attempting to clone them to avoid errors.

For the searchmore.py script, the search terms are currently hard-coded. If you want to search for different terms, you will need to modify the script.
