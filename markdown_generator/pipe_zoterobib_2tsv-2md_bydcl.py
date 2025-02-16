# 2025/02/16
# ChenluDi
# From zotero export bib and files to _publications/md files and the files in the file directory.

# The file names in the github site should be exact the same as file names in the read-in directory.

import os
import re
import csv

# 0. Read the bib file from zotero: output setting: 

def read_bib_file(bibfile):
    with open(bibfile, 'r', encoding='utf-8') as f:
        return f.read()

def parse_bib_entries(content):
    return re.findall(r'@(article|misc)\s*{(.*?),\s*(.*?)\n}', content, re.DOTALL)


# 1. Get pub_date
# because I cannot get the exact date from the bib file but the date is required by the academicpages, I set the default date as 01.
def extract_pub_date(entries, default_date="01"):
    pub_dates = {}
    month_map = {
        'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04', 'may': '05', 'jun': '06',
        'jul': '07', 'aug': '08', 'sep': '09', 'oct': '10', 'nov': '11', 'dec': '12'
    }
    
    for entry_type, entry_key, entry_content in entries:
        year_match = re.search(r'year\s*=\s*{(\d{4})}', entry_content)
        month_match = re.search(r'month\s*=\s*([a-zA-Z]+)', entry_content)
        
        if year_match:
            year = year_match.group(1)
            month = month_match.group(1) if month_match else '01'  # Default to January if missing
            month = month_map.get(month[:3].lower(), '01')  # Handle variations like "October"
            
            pub_dates[entry_key] = f"{year}-{month}-{default_date}"
    
    return pub_dates


# 2. Get title
# The title can be messy because of font formating. You might need to check it manually.
def extract_title(entries):
    titles = {}
    for entry_type, entry_key, entry_content in entries:
        title_match = re.search(r'title\s*=\s*{(.*?)}', entry_content, re.DOTALL)
        if title_match:
            title = re.sub(r'[{}]', '', title_match.group(1))  # Remove curly braces
            title = re.sub(r'\\[a-zA-Z]+', '', title)  # Remove LaTeX commands
            titles[entry_key] = title
    return titles

def extract_title(entries):
    titles = {}
    for entry_type, entry_key, entry_content in entries:
        title_match = re.search(r'title\s*=\s*{((?:[^{}]|{[^{}]*})*)}', entry_content, re.DOTALL)
        if title_match:
            title = title_match.group(1).replace('{', '').replace('}', '')  # Remove all curly braces
            title = re.sub(r'\\[a-zA-Z]+', '', title)  # Remove LaTeX commands
            titles[entry_key] = title.strip()
    return titles

# 3. Get venue
# If the journal is in biorxiv, zotero won't read the journal name at 2025/02/16. Here you can set the default journal name.
default_journal="biorxiv"
def extract_venue(entries, default_journal="Unknown Journal"):
    venues = {}
    for entry_type, entry_key, entry_content in entries:
        journal_match = re.search(r'journal\s*=\s*{(.*?)}', entry_content, re.DOTALL)
        venues[entry_key] = journal_match.group(1) if journal_match else default_journal
    return venues

# 4. Get excerpt
def extract_authors(entries):
    authors = {}
    for entry_type, entry_key, entry_content in entries:
        author_match = re.search(r'author\s*=\s*{(.*?)}', entry_content, re.DOTALL)
        if author_match:
            authors[entry_key] = author_match.group(1)
    return authors


# 5. Get paper_url
def extract_paper_url(entries):
    paper_urls = {}
    for entry_type, entry_key, entry_content in entries:
        file_match = re.search(r'file\s*=\s*{(.*?)}', entry_content, re.DOTALL)
        if file_match:
            files = file_match.group(1).split(';')
            for file in files:
                if 'application' in file:
                    paper_urls[entry_key] = file.split(':')[0]
                    break
    return paper_urls


def replace_spaces_in_filenames(paper_urls):
    return {key: url.replace(' ', '_') for key, url in paper_urls.items()}

# 6. Get slide_url
# Extract slides url based on its file name. The file name must start with "slides" or end with "slides.[?]"
# This can be applied to extract other type of files based on the keyword in the file name.
def extract_file_by_keyword(entries, file_category):
    extracted_files = {}
    for entry_type, entry_key, entry_content in entries:
        file_match = re.search(r'file\s*=\s*{(.*?)}', entry_content, re.DOTALL)
        if file_match:
            files = file_match.group(1).split(';')
            matching_files = [file.split(':')[0] for file in files if re.search(rf'{file_category}.*|.*{file_category}\.[^:]+$', file.split(':')[0])]
            
            if len(matching_files) > 1:
                print(f"Warning: Multiple {file_category} files found for {entry_key}: {matching_files}")
            elif matching_files:
                extracted_files[entry_key] = matching_files[0]
    return extracted_files

# 7. Get poster_url
# extract_file_by_keyword(entries, "poster")

# 8. Get video_url
def extract_full_file_path(entries, file_category):
    file_paths = {}
    for entry_type, entry_key, entry_content in entries:
        file_match = re.search(r'file\s*=\s*{(.*?)}', entry_content, re.DOTALL)
        if file_match:
            files = file_match.group(1).split(';')
            matching_files = [file.split(':')[1] for file in files if re.search(rf'{file_category}.*|.*{file_category}\.[^:]+$', file.split(':')[0])]
            
            if len(matching_files) > 1:
                print(f"Warning: Multiple {file_category} files found for {entry_key}: {matching_files}")
            elif matching_files:
                file_paths[entry_key] = matching_files[0]
    return file_paths

def get_video_url(entries):
    video_paths = extract_full_file_path(entries, "video")
    video_urls = {}
    for key, path in video_paths.items():
        try:
            with open(path, 'r', encoding='utf-8') as f:
                video_urls[key] = f.readline().strip()
        except FileNotFoundError:
            print(f"Warning: Video file not found for {key}: {path}")
    return video_urls


# Write the TSV file

def write_tsv(entries, output_file):
    if not entries:
        print("Warning: No entries found. Check if the input file is correctly parsed.")
        return
    
    try:
        pub_dates = extract_pub_date(entries)
        titles = extract_title(entries)
        venues = extract_venue(entries)
        excerpts = extract_authors(entries)
        paper_urls =replace_spaces_in_filenames(extract_paper_url(entries))
        slide_urls = extract_file_by_keyword(entries, "slides")
        poster_urls = extract_file_by_keyword(entries, "poster")
        video_urls = get_video_url(entries)
    except NameError as e:
        print(f"Error: Missing function definition - {e}")
        return
    
    # print("Debug: Extracted data samples:")
    # print("Pub Dates:", pub_dates)
    # print("Titles:", titles)
    # print("Venues:", venues)
    # print("Excerpts:", excerpts)
    # print("Paper URLs:", paper_urls)
    # print("Slide URLs:", slide_urls)
    # print("Poster URLs:", poster_urls)
    # print("Video URLs:", video_urls)
        
    with open(output_file, 'w', newline='', encoding='utf-8') as tsvfile:
        fieldnames = ["pub_date", "title", "venue", "excerpt", "paper_url", "slideurl", "posterurl", "videourl"]
        writer = csv.DictWriter(tsvfile, fieldnames=fieldnames, delimiter='\t')
        writer.writeheader()
        
        for entry_type, entry_key, entry_content in entries:
            writer.writerow({
                "pub_date": pub_dates.get(entry_key, ""),
                "title": titles.get(entry_key, ""),
                "venue": venues.get(entry_key, ""),
                "excerpt": excerpts.get(entry_key, ""),
                "paper_url": paper_urls.get(entry_key, ""),
                "slideurl": slide_urls.get(entry_key, ""),
                "posterurl": poster_urls.get(entry_key, ""),
                "videourl": video_urls.get(entry_key, "")
            })
    
    print(f"TSV file successfully written to {output_file}")

# 

# write markdonw file as below from TSV file: 
# 1. if the key value is empty, don't write it as a row in the markdown file
# 2. name it based on pubdate and first three words of the title, replace space with "_"
# ---
# title: "Genes derived from ancient polyploidy have higher genetic diversity and are associated with domestication in Brassica rapa"
# collection: publications
# permalink: /publication/2021-10-12-paper-title-number-1
# date: 2021-10-12
# venue: 'eLife'
# paperurl: 'http://chenludi.github.io/files/2021_Di_elife.pdf'
# slidesurl: 'http://chenludi.github.io/files/SMBE_20210528_ChenluDi_noaudio_0528.pdf'
# videourl: 'https://youtu.be/nK1KgorccI4'
# ---
def write_markdown_from_tsv(tsv_file, output_dir):
    with open(tsv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            if not any(row.values()):  # Skip empty rows
                continue
            
            pub_date = row.get("pub_date", "").strip()
            title = row.get("title", "").strip()
            venue = row.get("venue", "").strip()
            excerpt = row.get("excerpt", "").strip()
            paper_url = row.get("paper_url", "").strip()
            slide_url = row.get("slideurl", "").strip()
            poster_url = row.get("posterurl", "").strip()
            video_url = row.get("videourl", "").strip()
            
            if not pub_date or not title:
                continue  # Skip if pub_date or title is missing
            
            title_slug = "_".join(title.split()[:3]).replace(" ", "_").replace("/", "_")
            filename = f"{pub_date}-{title_slug}.md"
            filepath = f"{output_dir}/{filename}"
            
            with open(filepath, 'w', encoding='utf-8') as md_file:
                md_file.write("---\n")
                md_file.write(f"title: \"{title}\"\n")
                md_file.write("collection: publications\n")
                md_file.write(f"permalink: /publication/{filename.replace('.md', '')}\n")
                if excerpt:
                    md_file.write(f"excerpt: '{excerpt}'\n")
                md_file.write(f"date: {pub_date}\n")
                if venue:
                    md_file.write(f"venue: '{venue}'\n")
                if paper_url:
                    md_file.write(f"paperurl: '{paper_url}'\n")
                if slide_url:
                    md_file.write(f"slidesurl: '{slide_url}'\n")
                if video_url:
                    md_file.write(f"videourl: '{video_url}'\n")
                if poster_url:
                    md_file.write(f"posterurl: '{poster_url}'\n")
                md_file.write("---\n")
    print(f"Markdown files successfully written to {output_dir}")


dir_root="/Users/test/c6googledrive/Chenlu Di/mywebsite/biball"
os.chdir(dir_root)

bibfile="/Users/test/c6googledrive/Chenlu Di/mywebsite/biball/biball.bib"
output_file="/Users/test/c6googledrive/Chenlu Di/mywebsite/biball/biball.tsv"
content = read_bib_file(bibfile)
entries = parse_bib_entries(content)
write_tsv(entries, output_file)

write_markdown_from_tsv(output_file, dir_root)

# Optional step:
# move files in all the subdirectories to the root directory/file and rename it by replcacing space with "_"
import shutil

def move_files_to_root(directory):
    for root, _, files in os.walk(directory):
        for file in files:
            source = os.path.join(root, file)
            new_filename = file.replace(" ", "_")
            destination = os.path.join(directory, new_filename)
            if source != destination:
                shutil.move(source, destination)
    print(f"All files moved to root directory with renamed files: {directory}")

def copy_files_to_root(directory):
    for root, _, files in os.walk(directory):
        for file in files:
            source = os.path.join(root, file)
            new_filename = file.replace(" ", "_")
            destination = os.path.join(directory, new_filename)
            if source != destination and not os.path.exists(destination):
                shutil.copy2(source, destination)
    print(f"All files copied to root directory with renamed files: {directory}")


file_direcotry=dir_root+'/files'

copy_files_to_root(file_direcotry)

