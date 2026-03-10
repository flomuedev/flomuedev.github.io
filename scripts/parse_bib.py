#!/usr/bin/env python3
"""
Parse BibTeX file and generate publications.json for Hugo.
Usage: python scripts/parse_bib.py
"""

import json
import re
import os
import sys


def parse_bibtex(filepath):
    """Parse a BibTeX file and return a list of entry dicts."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    entries = []
    # Match each @type{key, ... } entry
    pattern = re.compile(
        r'@(\w+)\s*\{([^,]+),\s*(.*?)\n\}',
        re.DOTALL
    )

    for match in pattern.finditer(content):
        entry_type = match.group(1).lower()
        cite_key = match.group(2).strip()
        body = match.group(3)

        entry = {
            'type': entry_type,
            'key': cite_key,
        }

        # Parse fields with robust brace matching
        body = body.strip()
        idx = 0
        while idx < len(body):
            # find next '='
            eq_idx = body.find('=', idx)
            if eq_idx == -1:
                break
            
            field_name = body[idx:eq_idx].strip().lower()
            idx = eq_idx + 1
            
            # skip whitespace after '='
            while idx < len(body) and body[idx].isspace():
                idx += 1
                
            if idx >= len(body):
                break
                
            if body[idx] == '{':
                # find matching brace
                start_idx = idx + 1
                brace_count = 1
                curr_idx = start_idx
                while curr_idx < len(body) and brace_count > 0:
                    if body[curr_idx] == '{':
                        brace_count += 1
                    elif body[curr_idx] == '}':
                        brace_count -= 1
                    curr_idx += 1
                
                value = body[start_idx:curr_idx-1]
                idx = curr_idx
            elif body[idx] == '"':
                # quote string
                start_idx = idx + 1
                curr_idx = start_idx
                while curr_idx < len(body) and body[curr_idx] != '"':
                    curr_idx += 1
                value = body[start_idx:curr_idx]
                idx = curr_idx + 1
            else:
                # unquoted value until comma or end
                start_idx = idx
                while idx < len(body) and body[idx] not in (',', '\n'):
                    idx += 1
                value = body[start_idx:idx].strip()
            
            # Read until next comma
            while idx < len(body) and body[idx] != ',':
                idx += 1
            idx += 1 # skip the comma
            
            # Clean up value
            value = clean_latex(value)
            # Remove any trailing commas or newlines that might have snuck in (for unquoted values)
            entry[field_name] = value.strip()
            
        entries.append(entry)

    return entries


def clean_latex(text):
    """Remove common LaTeX formatting from text."""
    # Remove \textbackslash
    text = text.replace('\\textbackslash', '\\')
    # Remove \texttimes
    text = text.replace('\\texttimes', '×')
    # Remove \& -> &
    text = text.replace('\\&', '&')
    # Remove copyright
    text = text.replace('\\copyright{}', '©')
    text = text.replace('\\copyright', '©')
    # Handle accented characters
    replacements = {
        '\\"a': 'ä', '\\"o': 'ö', '\\"u': 'ü',
        '\\"A': 'Ä', '\\"O': 'Ö', '\\"U': 'Ü',
        "\\'a": 'á', "\\'e": 'é', "\\'i": 'í', "\\'o": 'ó', "\\'u": 'ú',
        "\\'A": 'Á', "\\'E": 'É',
        "\\'{a}": 'á', "\\'{e}": 'é', "\\'{i}": 'í', "\\'{o}": 'ó', "\\'{u}": 'ú',
        '\\"{a}': 'ä', '\\"{o}': 'ö', '\\"{u}': 'ü',
        '\\"{A}': 'Ä', '\\"{O}': 'Ö', '\\"{U}': 'Ü',
        '\\ss': 'ß', '\\ss{}': 'ß',
        '\\ae': 'æ', '\\AE': 'Æ',
        '\\o': 'ø', '\\O': 'Ø',
        '\\aa': 'å', '\\AA': 'Å',
        '\\v{c}': 'č', '\\v{s}': 'š', '\\v{z}': 'ž',
        '\\c{c}': 'ç',
        '\\~{n}': 'ñ', '\\~n': 'ñ',
        '\\l': 'ł',
        '\\i': 'ı',
        '\\r{a}': 'å',
    }
    for latex, char in replacements.items():
        text = text.replace(latex, char)

    # Remove remaining {{}} and {} wrappers
    text = re.sub(r'\{\{(.*?)\}\}', r'\1', text)
    text = re.sub(r'\{([^{}]*)\}', r'\1', text)
    # Remove $...$ math mode (simple cases)
    text = re.sub(r'\$([^$]+)\$', r'\1', text)
    # Remove ~ (non-breaking space in LaTeX)
    text = text.replace('~', ' ')
    # Collapse whitespace
    text = re.sub(r'\s+', ' ', text)

    return text


def format_authors(author_str):
    """Format authors string and return both plain text and HTML with Florian Müller highlighted."""
    if not author_str:
        return '', ''

    # Split by ' and '
    authors = re.split(r'\s+and\s+', author_str)
    formatted = []
    formatted_html = []

    for author in authors:
        author = author.strip()
        if not author:
            continue

        # Handle "Last, First" format
        if ',' in author:
            parts = author.split(',', 1)
            name = f"{parts[1].strip()} {parts[0].strip()}"
        else:
            name = author

        formatted.append(name)

        # Highlight Florian Müller / Florian Mueller
        if 'müller' in name.lower() and 'florian' in name.lower():
            formatted_html.append(f'<span class="highlight-author">{name}</span>')
        elif 'mueller' in name.lower() and 'florian' in name.lower():
            formatted_html.append(f'<span class="highlight-author">{name}</span>')
        else:
            formatted_html.append(name)

    return ', '.join(formatted), ', '.join(formatted_html)


def find_file(directory, key, extensions):
    """Find a file matching the key in the directory with given extensions."""
    if not os.path.isdir(directory):
        return None
    for ext in extensions:
        filename = f"{key}{ext}"
        if os.path.isfile(os.path.join(directory, filename)):
            return filename
    return None


def format_bibtex(entry):
    """Reconstruct a clean BibTeX entry string from a parsed entry dict."""
    entry_type = entry.get('type', 'misc')
    key = entry.get('key', 'unknown')

    field_order = [
        'author', 'editor', 'title',
        'booktitle', 'journal', 'year', 'month',
        'volume', 'number', 'pages',
        'publisher', 'address', 'series',
        'doi', 'isbn', 'issn',
        'eprint', 'archiveprefix',
        'keywords', 'abstract',
    ]
    skip = {
        'type', 'key', 'file', 'urldate', 'mendeley-tags', 'note',
        'annotation', 'url', 'video', 'talk', 'code', 'website',
        'shorttitle', 'primaryclass',
    }

    lines = [f'@{entry_type}{{{key},']
    seen = set()
    for field in field_order:
        val = entry.get(field, '').strip()
        if val:
            lines.append(f'  {field} = {{{val}}},')
            seen.add(field)
    # Include any remaining fields not in the ordered list
    for field, val in entry.items():
        if field not in seen and field not in skip and val and val.strip():
            lines.append(f'  {field} = {{{val.strip()}}},')
    lines.append('}')
    return '\n'.join(lines)


def get_venue_short(venue):
    """Infer short conference/journal abbreviation from full venue string."""
    if not venue:
        return ''
    v = venue.lower()

    # Extended Abstracts / Late-Breaking Work must come before plain CHI
    if re.search(r'extended abstract|chi ea|chi conference extended abstract|late.breaking', v):
        return 'CHI EA'

    # CHI
    if re.search(r'chi conference on human factors|chi.*human factors in computing|proceedings of.*chi conference|human factors in computing systems', v):
        return 'CHI'

    # VRST
    if re.search(r'virtual reality software and technology', v):
        return 'VRST'

    # HRI
    if re.search(r'human.robot interaction', v):
        return 'HRI'

    # TVCG
    if re.search(r'transactions on visualization and computer graphics', v):
        return 'TVCG'

    # ISMAR (adjunct before main)
    if re.search(r'mixed and augmented reality.*adjunct|ismar.*adjunct', v):
        return 'ISMAR-Adj'
    if re.search(r'mixed and augmented reality|ismar', v):
        return 'ISMAR'

    # DIS
    if re.search(r'designing interactive systems', v):
        return 'DIS'

    # UIST
    if re.search(r'user interface software and technology', v):
        return 'UIST'

    # INTERACT
    if re.search(r'interact \d{4}|hci.*interact \d{4}|human.computer interaction.*interact', v):
        return 'INTERACT'

    # MobileHCI
    if re.search(r'mobile.*devices and services|mobilehci', v):
        return 'MobileHCI'

    # ISS
    if re.search(r'interactive surfaces and spaces', v):
        return 'ISS'

    # MuC
    if re.search(r'mensch und computer|mensch & computer|muc \'', v):
        return 'MuC'

    # ISWC
    if re.search(r'symposium on wearable computers|international symposium on wearable', v):
        return 'ISWC'

    # SUI
    if re.search(r'spatial user interaction', v):
        return 'SUI'

    # TEI
    if re.search(r'tangible.*embedded.*embodied interaction', v):
        return 'TEI'

    # PETRA
    if re.search(r'pervasive technologies.*assistive|petra \'', v):
        return 'PETRA'

    # UbiComp
    if re.search(r'pervasive and ubiquitous computing|ubicomp', v):
        return 'UbiComp'

    # IMX
    if re.search(r'interactive media experiences', v):
        return 'IMX'

    # IUI
    if re.search(r'intelligent user interfaces', v):
        return 'IUI'

    # EICS
    if re.search(r'engineering interactive computing systems', v):
        return 'EICS'

    # MUM
    if re.search(r'mobile and ubiquitous multimedia', v):
        return 'MUM'

    # IEEE Pervasive Computing (journal)
    if re.search(r'ieee pervasive computing', v):
        return 'IEEE Pervasive'

    # Virtual Reality (journal)
    if venue.strip().lower() == 'virtual reality':
        return 'VR'

    # PACMHCI
    if re.search(r'acm on human.computer interaction|acm hum.*comput.*interact', v):
        return 'PACMHCI'

    # IMWUT
    if re.search(r'interactive, mobile, wearable and ubiquitous|imwut', v):
        return 'IMWUT'

    # EuroiTV
    if re.search(r'european.*interactive tv|euroitv|european conference on interactive tv', v):
        return 'EuroiTV'

    # SmartObjects workshop
    if re.search(r'smart objects|smartobjects', v):
        return 'SmartObjects'

    return ''


def month_to_num(month_str):
    """Convert month string to number for sorting."""
    months = {
        'jan': 1, 'january': 1,
        'feb': 2, 'february': 2,
        'mar': 3, 'march': 3,
        'apr': 4, 'april': 4,
        'may': 5,
        'jun': 6, 'june': 6,
        'jul': 7, 'july': 7,
        'aug': 8, 'august': 8,
        'sep': 9, 'sept': 9, 'september': 9,
        'oct': 10, 'october': 10,
        'nov': 11, 'november': 11,
        'dec': 12, 'december': 12,
    }
    if month_str:
        return months.get(month_str.lower().strip(), 6)
    return 6


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(script_dir)

    bib_path = os.path.join(script_dir, 'bib.bib')
    pdf_dir = os.path.join(project_dir, 'static', 'pdf')
    preview_dir = os.path.join(project_dir, 'static', 'publication_preview')
    output_path = os.path.join(project_dir, 'data', 'publications.json')

    if not os.path.isfile(bib_path):
        print(f"Error: BibTeX file not found at {bib_path}")
        sys.exit(1)

    entries = parse_bibtex(bib_path)
    print(f"Parsed {len(entries)} BibTeX entries")

    publications = []

    for entry in entries:
        year_str = entry.get('year', '')
        try:
            year = int(year_str)
        except (ValueError, TypeError):
            year = 0

        authors_plain, authors_html = format_authors(entry.get('author', ''))

        # Determine venue
        venue = entry.get('booktitle', '') or entry.get('journal', '') or entry.get('publisher', '')

        # Find PDF file
        pdf_file = find_file(pdf_dir, entry['key'], ['.pdf'])

        # Find preview image
        preview_file = find_file(preview_dir, entry['key'], ['.jpg', '.jpeg', '.png', '.gif', '.webp'])

        # Build DOI URL
        doi = entry.get('doi', '')

        # ArXiv
        arxiv = entry.get('eprint', '')
        arxiv_url = f"https://arxiv.org/abs/{arxiv}" if arxiv and entry.get('archiveprefix', '').lower() == 'arxiv' else ''

        pub = {
            'key': entry['key'],
            'type': entry.get('type', 'misc'),
            'title': entry.get('title', ''),
            'authors': authors_plain,
            'authors_html': authors_html,
            'year': year,
            'month': month_to_num(entry.get('month', '')),
            'venue': venue,
            'venue_short': get_venue_short(venue),
            'bibtex': format_bibtex(entry),
            'abstract': entry.get('abstract', ''),
            'doi': doi,
            'pdf': pdf_file,
            'preview': preview_file,
            'video': entry.get('video', ''),
            'talk': entry.get('talk', ''),
            'code': entry.get('code', '') or entry.get('website', ''),
            'arxiv': arxiv_url,
            'keywords': entry.get('keywords', ''),
        }

        publications.append(pub)

    # Sort by year descending, then month descending
    publications.sort(key=lambda p: (p['year'], p['month']), reverse=True)

    # Write JSON
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(publications, f, indent=2, ensure_ascii=False)

    print(f"Generated {len(publications)} publications -> {output_path}")

    # Generate individual markdown pages for each publication
    pub_content_dir = os.path.join(project_dir, 'content', 'publication')
    os.makedirs(pub_content_dir, exist_ok=True)
    
    # Also create the _index.md for the publication section if needed (optional)
    index_md = os.path.join(pub_content_dir, '_index.md')
    if not os.path.exists(index_md):
        with open(index_md, 'w', encoding='utf-8') as f:
            f.write("+++\ntitle = \"Publications\"\ntype = \"publications\"\n+++\n")
            
    for pub in publications:
        md_path = os.path.join(pub_content_dir, f"{pub['key']}.md")
        
        # Format the frontmatter
        year = pub['year'] or 2000
        month = pub['month'] or 1
        date_str = f"{year}-{month:02d}-01T00:00:00Z"
        
        frontmatter = [
            "+++",
            f"title = {json.dumps(pub['title'])}",
            f"date = {json.dumps(date_str)}",
            "type = \"publication\"",
            f"authors = {json.dumps(pub['authors'])}",
            f"authors_html = {json.dumps(pub['authors_html'])}",
            f"venue = {json.dumps(pub['venue'])}",
        ]
        if pub.get('venue_short'):
            frontmatter.append(f"venue_short = {json.dumps(pub['venue_short'])}")
        if pub.get('bibtex'):
            frontmatter.append(f"bibtex = {json.dumps(pub['bibtex'])}")

        # Add optional items
        for field in ['pdf', 'preview', 'video', 'talk', 'code', 'arxiv', 'doi', 'keywords']:
            if pub.get(field):
                if field == 'keywords':
                    kws = [k.strip() for k in pub[field].split(',') if k.strip()]
                    frontmatter.append(f"{field} = {json.dumps(kws)}")
                else:
                    frontmatter.append(f"{field} = {json.dumps(pub[field])}")
                
        frontmatter.append("+++")
        frontmatter.append("\n" + pub.get('abstract', ''))
        
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(frontmatter))

    print(f"Generated {len(publications)} markdown files -> {pub_content_dir}")

    # Stats
    with_pdf = sum(1 for p in publications if p['pdf'])
    with_preview = sum(1 for p in publications if p['preview'])
    years = sorted(set(p['year'] for p in publications if p['year']), reverse=True)
    print(f"  With PDF: {with_pdf}")
    print(f"  With preview: {with_preview}")
    print(f"  Years: {years[0]}–{years[-1]}" if years else "  No years found")


if __name__ == '__main__':
    main()
