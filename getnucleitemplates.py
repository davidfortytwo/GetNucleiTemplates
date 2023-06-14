#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author: David Espejo (Fortytwo Security)
import os
import subprocess
import requests
from typing import List, Tuple
import shutil
import argparse
from colorama import Fore, Back, Style
from dotenv import load_dotenv, set_key
import getpass
import time

# Get the directory of this script
script_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv()

# Add colorama initializations
print(Style.RESET_ALL)
success_prefix = f"{Fore.GREEN}[+]{Style.RESET_ALL}"
failure_prefix = f"{Fore.RED}[-]{Style.RESET_ALL}"
url_color = Fore.YELLOW
fail_color = Fore.RED
info_color = Fore.CYAN

def read_urls_from_file(filepath: str) -> List[str]:
    """Read URLs from the provided text file, ignoring commented lines."""
    open(filepath, 'a').close()
    with open(filepath, 'r') as f:
        urls = f.readlines()
    return [url.strip() for url in urls if url.strip()]

def get_github_api_key():
    """Gets Github API key from .env file or user input."""
    api_key = os.getenv('GITHUB_API_KEY')
    if not api_key:
        api_key = getpass.getpass(f"{Fore.GREEN}Enter your Github API Key (or press 'Enter' for unauthenticated search): {Style.RESET_ALL}")
        set_key(".env", "GITHUB_API_KEY", api_key)
    return api_key

def is_url_valid(url: str) -> bool:
    """Check if the URL exists and is not a 404."""
    try:
        response = requests.head(url, allow_redirects=True)
        return response.status_code != 404
    except requests.ConnectionError:
        return False

def requires_auth(url: str, api_key: str) -> bool:
    """Check if the URL requires authentication."""
    headers = {'Authorization': f'token {api_key}'}
    response = requests.get(url, headers=headers)
    return response.status_code == 403

def clone_and_validate_repo(url: str, index: int, dir: str) -> Tuple[bool, bool]:
    """Attempt to clone and validate the repository from the given URL."""
    repo_name = url.split('/')[-1]  # Extract repository name
    repo_name = f"{repo_name}_{index}"  # Append index to make it unique
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    validated_dir = os.path.join(dir, "validated")
    not_validated_dir = os.path.join(dir, "not-validated")
    failed_clones_file_path = os.path.join(dir, "failed_clones.txt")

    # Check if the main directory exists, if not - create it
    if not os.path.exists(dir):
        os.makedirs(dir)

    # Create necessary sub-directories if not exist
    for path in [validated_dir, not_validated_dir]:
        if not os.path.exists(path):
            os.makedirs(path)

    if os.path.exists(repo_name):
        print(f"{info_color}Repository {repo_name} already exists. Skipping.{Style.RESET_ALL}")
        return False, True

    try:
        print(f"{success_prefix} Cloning {url_color}{url}{Style.RESET_ALL} into {repo_name}")
        process = subprocess.Popen(
            ['git', 'clone', '--depth', '1', url, repo_name],
            env=dict(os.environ, GIT_TERMINAL_PROMPT='0'),  # Set GIT_TERMINAL_PROMPT=0
            stdout=subprocess.DEVNULL,  # Optional: Suppress stdout
            stderr=subprocess.DEVNULL,  # Optional: Suppress stderr
        )
        process.communicate()  # Wait for process to complete

        if process.returncode != 0:
            raise subprocess.CalledProcessError(process.returncode, 'git')
        else:
            print(f"{Fore.GREEN}[+] Successful cloning {url}{Style.RESET_ALL}")
            with open(os.path.join(validated_dir, "validated.txt"), "a") as validated_file:
                validated_file.write(f"{timestamp} - {url}\n")

        # Validate repository
        print(f"{success_prefix} Validating {url_color}{url}{Style.RESET_ALL} using 'nuclei -validate'")
        validate_process = subprocess.Popen(
            ['nuclei', '-validate', '-t', repo_name],
            stdout=subprocess.DEVNULL,  # Optional: Suppress stdout
            stderr=subprocess.DEVNULL,  # Optional: Suppress stderr
        )
        validate_process.communicate()  # Wait for process to complete

        if validate_process.returncode != 0:
            print(f"{Fore.RED}[-] Failed validation for {url}{Style.RESET_ALL}")
            shutil.move(repo_name, not_validated_dir)
            with open(os.path.join(not_validated_dir, "not-validated.txt"), "a") as not_validated_file:
                not_validated_file.write(f"{timestamp} - {url}\n")
            return False, False
        else:
            print(f"{Fore.GREEN}[+] Successful validation {url}{Style.RESET_ALL}")
            shutil.move(repo_name, validated_dir)
            return True, False

    except subprocess.CalledProcessError as e:
        print(f"{Fore.RED}[-] Failed cloning repo {url}. Reason: {e}{Style.RESET_ALL}")
        if not os.path.isfile(failed_clones_file_path):
            open(failed_clones_file_path, 'w').close()
        with open(failed_clones_file_path, "a") as failed_file:
            failed_file.write(f"{timestamp} - {url}\n")
        return False, False

def remove_empty_dirs(dir: str) -> None:
    """Remove all empty directories in the given directory."""
    for directory in os.listdir(dir):
        if os.path.isdir(directory) and not os.listdir(directory):
            os.rmdir(directory)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--file", default="nuclei.txt",
                        help="Filename to read the repositories from. Default is 'nuclei.txt'")
    args = parser.parse_args()

    # Path to the file
    filepath = os.path.join(script_dir, args.file)

    # Backup original file before any modifications
    shutil.copy2(filepath, f'{filepath}.bak')

    # Create a directory for the repositories if it doesn't exist
    dir = "nuclei-templates"
    if not os.path.exists(dir):
        os.makedirs(dir)

    # Create validated and not-validated directories
    os.makedirs(os.path.join(dir, "validated"), exist_ok=True)
    os.makedirs(os.path.join(dir, "not-validated"), exist_ok=True)

    # Change the current working directory
    os.chdir(dir)

    attempted_urls = read_urls_from_file('attempted.txt')

    urls = read_urls_from_file(filepath)

    total_attempts, successful_downloads, failed_downloads, invalid_urls = 0, 0, 0, 0

    valid_urls = [url for url in urls if not url.startswith('#')]
    num_repos = len(valid_urls)
    print(f"{Fore.BLUE}Cloning {num_repos} Nuclei templates repositories...{Style.RESET_ALL}")

    api_key = get_github_api_key()

    all_repos_exist = True

    for index, url in enumerate(urls):
        if url.startswith('#') or url in attempted_urls:  # ignore commented lines
            continue

        total_attempts += 1

        if not is_url_valid(url):
            print(f"{failure_prefix} URL not valid: {fail_color}{url}{Style.RESET_ALL}")
            invalid_urls += 1
            with open(filepath, 'r') as f:
                lines = f.readlines()
            with open(filepath, 'w') as f:
                for line in lines:
                    if line.strip() == url:
                        f.write(f"# {url}\n")  # Comment out the invalid url
                    else:
                        f.write(line)
            continue

        if requires_auth(url, api_key):
            print(f"{failure_prefix} URL requires authentication or is a private repository, skipping: {fail_color}{url}{Style.RESET_ALL}")
            continue

        success, exists = clone_and_validate_repo(url, index, ".")

        attempted_urls.append(url)

        if success:
            successful_downloads += 1
        elif not exists:
            all_repos_exist = False
            failed_downloads += 1

    with open('attempted.txt', 'w') as f:
        for url in attempted_urls:
            f.write(url + '\n')

    remove_empty_dirs(dir)

    print(f"\nTotal attempted downloads: {total_attempts}")
    print(f"{success_prefix} Successful downloads: {successful_downloads}")
    print(f"{failure_prefix} Failed downloads: {failed_downloads}")
    print(f"{failure_prefix} Ignored invalid URLs: {invalid_urls}")

    if all_repos_exist and successful_downloads == 0 and failed_downloads == 0:
        print(f"{Fore.GREEN}All repositories from the list are already downloaded!{Style.RESET_ALL}")

if __name__ == "__main__":
    main()
