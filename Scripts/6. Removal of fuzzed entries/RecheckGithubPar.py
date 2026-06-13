import asyncio
import aiohttp
import json
import re
import os
from urllib.parse import urlparse
from bs4 import BeautifulSoup

# ---------------------- CONFIG ----------------------
PATH = r"FuzzabilityAnalysisOfDeepBugs\Data\coverage_hits_ordered_under30.json"
github_fuzz_output = r"FuzzabilityAnalysisOfDeepBugs\Data\github_fuzz.json"
github_not_fuzz_output = r"FuzzabilityAnalysisOfDeepBugs\Data\github_notFuzz.json"
# enter github token here if you have one
GITHUB_TOKEN = "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"

FUZZ_KEYWORDS = [


    # 1. Core Fuzzing Terms: Match 'fuzz', 'fuzzer', 'fuzzing' anywhere.
    # We use non-word-boundary matches for flexibility (e.g., matching "libfuzz" or "fuzz_test").
    r"fuzz(er|ing)?", 

    # 2. Project-Specific Fuzzers
    # OSS-Fuzz variations: Capture space, hyphen, or no separator, including misspellings (fuze, fuse).
    r"oss[\s\-]?fuzz(ing)?", r"oss[\s\-]?fuze", r"oss[\s\-]?fuse",
    r"ossfuzz", r"ossfuze", r"ossfuse",
    
    # ClusterFuzz: Capture space or no space.
    r"cluster\s*fuzz",

    # 3. Sanitizers and Tools (No word boundaries for internal use like 'asan_get')
    # Standard Sanitizers
    r"asan", r"ubsan", r"msan", r"tsan", 
    
    # General Sanitizer Terms: Match 'sanitize', 'sanitized', 'sanitizer', 'sanitizers'.
    # This is concise and covers all forms, including prefixes like 'unsanitize'.
    r"sanitize(r|rs|d)?", 
]

FUZZ_REGEX = re.compile("|".join(FUZZ_KEYWORDS), re.IGNORECASE)
MAX_CONCURRENT_REQUESTS = 30

DEFAULT_HEADERS = {
    "User-Agent": "fuzz-detector/1.0"
}

if GITHUB_TOKEN and GITHUB_TOKEN != "...": # Check against placeholder
    DEFAULT_HEADERS["Authorization"] = f"token {GITHUB_TOKEN}"

# HTML selectors for retrieving the commit message from HTML pages
# FIX: Added 'pre' and '.js-details-container' to more reliably grab the full commit message body.
HTML_SELECTORS = [
    ".js-details-container .f4.mb-3", # Targets the main container for commit title and body on GitHub
    "pre.commit-message",           # Often contains the entire raw commit message
    "div.commit-title", 
    "h1.commit-title",
    ".gh-header-title",
    "div.markdown-body",            # Good for capturing rendered markdown
]

# Regex for absolute URLs
GITHUB_LINK_REGEX = re.compile(
    r"(https?://github\.com/[^/]+/[^/]+/(?:issues|pull)/\d+)", 
    re.IGNORECASE
)

# Regex for relative links like #123 or Fixes #123
RELATIVE_ISSUE_REGEX = re.compile(
    r"(?:[Cc]loses|Fixes|Resolves)?\s*#(\d+)",
    re.IGNORECASE
)

# ---------------------- HELPERS ----------------------

def parse_commit_url(commit_url):
    """Extracts owner, repo, and SHA from a GitHub commit URL."""
    try:
        p = urlparse(commit_url)
        parts = [x for x in p.path.split("/") if x]
        if len(parts) >= 4 and parts[2] in ("commit", "commits"):
            return parts[0], parts[1], parts[3]
    except Exception:
        pass
    return None, None, None


def extract_github_links(message, owner, repo):
    """
    Extracts absolute URLs and relative issue/PR numbers, converting 
    relative references to absolute Issue/PR URLs.
    """
    if not message or not owner or not repo:
        return []

    found_links = set()
    
    # 1. Find absolute URLs
    absolute_urls = GITHUB_LINK_REGEX.findall(message)
    for url in absolute_urls:
        found_links.add(url)
        
    # 2. Find relative issue numbers and convert to ONLY Issue/PR URLs
    issue_numbers = RELATIVE_ISSUE_REGEX.findall(message)
    for number in issue_numbers:
        issue_url = f"https://github.com/{owner}/{repo}/issues/{number}"
        found_links.add(issue_url)
        
    return list(found_links)


async def fetch_commit_message_api(session, owner, repo, sha):
    """Fetches the commit message using the GitHub API."""
    if not (owner and repo and sha):
        return None

    url = f"https://api.github.com/repos/{owner}/{repo}/commits/{sha}"

    try:
        async with session.get(url, headers=DEFAULT_HEADERS, timeout=15) as resp:
            if resp.status == 200:
                j = await resp.json()
                # The commit message in the API response includes both summary and body
                return j.get("commit", {}).get("message", "") or None
            elif resp.status == 403:
                print(f"⚠️ Warning: API access forbidden (403) for commit {owner}/{repo}@{sha}. Falling back to HTML.")
                return None
            else:
                return None
    except:
        return None

    return None


async def fetch_commit_message_html(session, commit_url):
    """
    Fetches the commit message by scraping the commit HTML page.
    Uses aggressive selectors to ensure the full message (summary + body) is retrieved.
    """
    try:
        async with session.get(commit_url, headers=DEFAULT_HEADERS, timeout=15) as resp:
            if resp.status != 200:
                return None
            text = await resp.text()
    except:
        return None

    soup = BeautifulSoup(text, "html.parser")

    for sel in HTML_SELECTORS:
        el = soup.select_one(sel)
        if el:
            # Use get_text to merge the title and body into one string for regex
            msg = el.get_text(" ", strip=True) 
            if msg:
                return msg

    # Fallback: search whole page for fuzzing keywords
    page_text = soup.get_text(" ", strip=True)
    if FUZZ_REGEX.search(page_text):
        return page_text

    return None


async def fetch_and_check_linked_content(session, link_url):
    """Aggressively targets specific text containers on GitHub Issue/PR pages for reliable scraping."""
    try:
        async with session.get(link_url, headers=DEFAULT_HEADERS, timeout=15) as resp:
            if resp.status != 200:
                if resp.status == 403:
                    print(f"⚠️ Warning: Linked content access forbidden (403) for {link_url}. Skipping.")
                return False
            text = await resp.text()
    except Exception:
        return False
    
    soup = BeautifulSoup(text, "html.parser")
    
    # Aggressive selectors for relevant text on GitHub Issue/PR pages
    text_selectors = [
        "h1.gh-header-title",                  
        ".markdown-body",                      
        ".js-comment-container .markdown-body",
    ]
    
    combined_text = ""
    for sel in text_selectors:
        elements = soup.select(sel)
        for el in elements:
            combined_text += el.get_text(" ", strip=True) + " "

    return bool(FUZZ_REGEX.search(combined_text))


def commit_mentions_fuzzing(message):
    """Checks if a string message contains any fuzzing keywords."""
    if not message:
        return False
    return bool(FUZZ_REGEX.search(message))


# ---------------------- CORE ----------------------

async def process_commit(session, entry_source, file_entry, sem):
    """Fetches and classifies a single commit, returning the updated file_entry and classification."""
    # Create a copy to modify and return, keeping the original data structure intact for the queue
    updated_file_entry = file_entry.copy() 
    commit_url = updated_file_entry.get("commit_url")
    
    if not commit_url:
        updated_file_entry["commit_message"] = "Error: Missing commit URL"
        return updated_file_entry, False

    owner, repo, sha = parse_commit_url(commit_url) 
    
    if not (owner and repo and sha):
        updated_file_entry["commit_message"] = "Error: Could not parse commit URL"
        return updated_file_entry, False
        
    async with sem:
        # --- 1. Primary Check: Commit Message ---
        msg = await fetch_commit_message_api(session, owner, repo, sha)
        if not msg:
            # This HTML fetch is critical for retrieving the message body (e.g., Fixes #...)
            msg = await fetch_commit_message_html(session, commit_url)

        is_fuzz = commit_mentions_fuzzing(msg)
        
        # --- 2. Secondary Check: Linked Issues/PRs ---
        if not is_fuzz and msg:
            linked_urls = extract_github_links(msg, owner, repo) 
            
            if linked_urls:
                # Concurrently check all linked resources
                link_tasks = [fetch_and_check_linked_content(session, url) for url in linked_urls]
                linked_results = await asyncio.gather(*link_tasks)
                
                if any(linked_results):
                    is_fuzz = True 
                    msg = (msg or "") + "\n[INDIRECT HIT: Fuzzing keyword found in linked Issue/PR]"
        
        # Add the commit message to the updated file entry dictionary (retains all original metadata)
        updated_file_entry["commit_message"] = msg or ""

        return updated_file_entry, is_fuzz


async def find_fuzzing_bugs_async(dataset_path, fuzz_out, notfuzz_out):
    """Main asynchronous function to process and reconstruct the nested dataset."""
    try:
        with open(dataset_path, "r", encoding="utf8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: Dataset file not found at {dataset_path}")
        return

    sem = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
    
    # List to track the original file entry and its parent source index
    processing_queue = []

    # 1. Prepare tasks and map original file entries
    for i, entry in enumerate(data):
        for file_entry in entry.get("files", []):
            processing_queue.append({'parent_index': i, 'file_entry': file_entry})

    # The tasks must be created and run inside the ClientSession
    async with aiohttp.ClientSession() as session:
        # Prepare the tasks list *inside* the session context
        tasks = [
            process_commit(session, item['file_entry'].get('source'), item['file_entry'], sem) 
            for item in processing_queue
        ]

        print(f"Starting to process {len(tasks)} file entries with {MAX_CONCURRENT_REQUESTS} concurrent requests...")
        results = await asyncio.gather(*tasks)

    # 2. Reconstruct the JSON structure
    
    # Deep copy the original data structure to modify it
    final_fuzz_data = [d.copy() for d in data]
    final_not_fuzz_data = [d.copy() for d in data]
    
    # Clear the files list in the copies to be repopulated
    for d in final_fuzz_data: d['files'] = []
    for d in final_not_fuzz_data: d['files'] = []

    
    # 3. Distribute results back into the reconstructed structures
    for idx, (updated_file_entry, is_fuzz) in enumerate(results):
        parent_index = processing_queue[idx]['parent_index']
        
        # Append the fully updated file entry (containing all original and new fields)
        if is_fuzz:
            final_fuzz_data[parent_index]['files'].append(updated_file_entry)
        else:
            final_not_fuzz_data[parent_index]['files'].append(updated_file_entry)


    # 4. Final Cleanup: Remove parent entries that have no files remaining
    final_fuzz_data = [d for d in final_fuzz_data if d['files']]
    final_not_fuzz_data = [d for d in final_not_fuzz_data if d['files']]


    # 5. Write output files

    with open(fuzz_out, "w", encoding="utf8") as f:
        json.dump(final_fuzz_data, f, indent=2, ensure_ascii=False)

    with open(notfuzz_out, "w", encoding="utf8") as f:
        json.dump(final_not_fuzz_data, f, indent=2, ensure_ascii=False)

    print("-" * 50)
    print(f"✅ Processing complete.")
    print(f"➡️ Total file entries processed: {len(results)}")
    print(f"➡️ Fuzz-related entries saved: {sum(len(d['files']) for d in final_fuzz_data)}")
    print(f"➡️ Non-Fuzz entries saved: {sum(len(d['files']) for d in final_not_fuzz_data)}")
    print(f"➡️ Output written to {fuzz_out} and {notfuzz_out} with nested structure and complete metadata.")


def run(dataset_path):
    """Initiates the asynchronous operation."""
    # Necessary for Windows compatibility
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy()) 
    
    asyncio.run(
        find_fuzzing_bugs_async(
            dataset_path,
            github_fuzz_output,
            github_not_fuzz_output
        )
    )


# ---------------------- RUN ----------------------
run(PATH)