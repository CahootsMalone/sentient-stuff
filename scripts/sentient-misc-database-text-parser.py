import math
from typing import List, Set, Dict, Tuple, Optional

SHOULD_PRINT = False

LINK_LENGTH = 12 # In the link tables, each link is one four-byte value (position in entry where link starts) followed by four two-byte values (possible destinations).

OUT_PATH_BASE = "C:/Stuff-5/Python/Sentient parsers/database/"

LINK_INVALID = 65535 # If this is a link destination, no link appears at the corresponding security clearance level.

ASCII_NULL = 0
RECORD_SEPARATOR = 30 # With SHIFT_OUT, marks the start of a link.
SHIFT_OUT = 14 # With RECORD_SEPARATOR, marks the start of a link.
START_OF_HEADING = 1 # Marks the end of a link.
LINE_FEED = 10
PRINTABLE_FIRST = 32
PRINTABLE_LAST = 126

used_link_destinations = set()

def generate_link_map(data: bytes) -> Dict[int, List[int]]:
    data_length = len(data)
    link_count = math.ceil(data_length/LINK_LENGTH)

    link_map = {}
    
    for i in range(link_count):
        offset = i * LINK_LENGTH

        # Where the link starts in the associated text.
        location = int.from_bytes(data[offset:offset+4], byteorder='little', signed=False)

        destination_list = []

        # There are four destinations for each link. Which one is used depends on the player's current security clearance.
        # The player's clearance goes up at least twice:
        # - If the player says "sure enough" (the security chief's password) to SUZIE (the AI).
        # - If the senator gives the player command of the station.
        # Perhaps there's a third clearance increase with which I'm not familiar or the fourth level simply isn't used.
        for i in range(4):
            start = offset + 4 + i*2
            end = offset + 6 + i*2
            destination = int.from_bytes(data[start:end], byteorder='little', signed=False)
            
            destination_list.append(destination)

            used_link_destinations.add(destination)

        if SHOULD_PRINT and not all_equal(destination_list):
            print(f"Link with multiple destinations: {str(destination_list)}")

        link_map[location] = destination_list
    
    return link_map

def is_printable(value):
    if (value >= PRINTABLE_FIRST and value <= PRINTABLE_LAST):
        return True
    else:
        return False

def get_title(data):
    title = ""

    for i in range(len(data)):
        value = int.from_bytes(data[i:i+1], byteorder='little', signed=False)

        if is_printable(value):
            title += chr(value)
        elif value == RECORD_SEPARATOR:
            # Part of link indication.
            pass
        elif value == SHIFT_OUT:
            # Part of link indication.
            pass
        elif value == START_OF_HEADING:
            # Part of link indication.
            pass
        else:
            break
    
    return title

def all_equal(list):
    return list.count(list[0]) == len(list)

def generate_page(data, title, link_map, index):

    text = '<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8" /><title>Sentient Database Entry ' + str(index) + ': ' + title + '</title><link rel="stylesheet" href="styles.css"></head><body>\n'
    
    i = 0
    while i < len(data):
        value = int.from_bytes(data[i:i+1], byteorder='little', signed=False)

        if is_printable(value):
            text += chr(value)
        elif value == LINE_FEED:
            text += "<br />\n"
        elif value == RECORD_SEPARATOR:
            # Appears before SHIFT_OUT at the start of links.
            pass
        elif value == SHIFT_OUT: # Start of link.
            link_list = link_map[i]
            
            if all_equal(link_list): # Only one destination for this link regardless of clearance level.
                text += '<a href="' + str(link_list[0]) + '.html">'
                i += 1
                continue

            # Run through data until the end of the link is encountered to get link text.
            link_text = ""
            j = i + 1
            while True:
                value = int.from_bytes(data[j:j+1], byteorder='little', signed=False)

                if value == START_OF_HEADING: # End of link.
                    break
                elif is_printable(value):
                    link_text += chr(value)
                else:
                    print("*** WARNING: non-ASCII character encountered in link text. ***")
                
                j += 1

            text += generate_link_text2(link_text, link_list)
            
            i = j + 1 # Skip past data already processed while getting link text.
            continue
            
        elif value == START_OF_HEADING: # End of link.
            text += '</a>'
        elif value == ASCII_NULL:
            pass
        else:
            print("UNKNOWN VALUE IN TEXT: " + str(value))
        
        i += 1
    
    text += "</body></html>"
    
    out_path = OUT_PATH_BASE + str(index) + ".html"

    with open(out_path, 'w', encoding='utf-8') as out_file:
        out_file.write(text)

# Generate text for links with multiple destinations.
def generate_link_text(link_name, link_list):

    link_text = ""

    added_first_link = False

    for link_index in range(len(link_list)):
        link = link_list[link_index]
        if link != LINK_INVALID:
            if not added_first_link:
                link_text += '<a href="' + str(link) + '.html">' + f"{link_name} L{str(link_index + 1)}" + '</a>'
                added_first_link = True
            else:
                link_text += ' <a href="' + str(link) + '.html">' + f"L{str(link_index + 1)}" + '</a>'
    
    return link_text

# Generate text for links with multiple destinations.
def generate_link_text2(link_name, link_list):

    link_text = ""

    added_first_link = False
    added_text_for_first_link = False

    cur_link_destination = -1
    cur_link_desc = ""

    for link_index in range(len(link_list)):
        link = link_list[link_index]
        if link != LINK_INVALID:
            if not added_first_link:
                cur_link_destination = link
                cur_link_desc += f"{link_name} L{str(link_index + 1)}"
                added_first_link = True
            else:
                if link == cur_link_destination: # Link for this clearance level is the same as the link for the previous level.
                    cur_link_desc += f"/L{str(link_index + 1)}"
                else:
                    if added_text_for_first_link:
                        link_text += ' ' # Space between links.
                    else:
                        added_text_for_first_link = True

                    link_text += '<a href="' + str(cur_link_destination) + '.html">' + cur_link_desc + '</a>'

                    cur_link_destination = link
                    cur_link_desc = f"L{str(link_index + 1)}"
    
    if added_text_for_first_link:
        link_text += ' ' # Space between links.
    else:
        added_text_for_first_link = True

    link_text += '<a href="' + str(cur_link_destination) + '.html">' + cur_link_desc + '</a>'
    
    return link_text

def generate_page_linking_to_unlinked_entries(list_of_unlinked_entries, entry_index_to_title):
    text = '<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8" /><title>Sentient Database Unlinked Entries</title><link rel="stylesheet" href="styles.css"></head><body>\n'

    for entry in list_of_unlinked_entries:
        text += '<a href="' + str(entry) + '.html">' + str(entry) + ': ' + entry_index_to_title[entry] + "</a><br />"
    
    text += "</body></html>"
    
    out_path = OUT_PATH_BASE + "unlinked.html"

    with open(out_path, 'w', encoding='utf-8') as out_file:
        out_file.write(text)

def generate_index_page(block_count, list_of_unlinked_entries, entry_index_to_title):
    text = '<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8" /><title>Sentient Database Index</title><link rel="stylesheet" href="styles.css"></head><body>\n'

    for entry in range(block_count):
        title = entry_index_to_title[entry]

        if entry in list_of_unlinked_entries:
            title += " [unlinked]"

        text += '<a href="' + str(entry) + '.html">' + str(entry) + ': ' + title + "</a><br />"
    
    text += "</body></html>"
    
    out_path = OUT_PATH_BASE + "index.html"

    with open(out_path, 'w', encoding='utf-8') as out_file:
        out_file.write(text)


# Each VSR file contains multiple files.
IN_PATH = "VSRS/MISC.VSR"

FILE_START = 1791304 # SUZIE_HYP (SUZIE database entries) starts at this offset.
FILE_END = 3414396 # TEMP_DB (unknown) starts at this offset.
HEADER_LENGTH = 8 # First eight bytes contain "BIN " (reversed) and four bytes for length.
BLOCK_LENGTH = 2048 # Most blocks in the SUZIE_HYP section are this long or a multiple of this length; the last one is not.

entry_index_to_title = {}

with open(IN_PATH, 'rb') as file:
    data = file.read()

file_length = int.from_bytes(data[FILE_START+4:FILE_START+8], byteorder='little', signed=False)

if SHOULD_PRINT:
    print("File length: " + str(file_length))

cur_block_start = FILE_START + HEADER_LENGTH

block_index = 0

has_skipped_first_block = False # The first block isn't an entry.

while (cur_block_start < FILE_END):

    if SHOULD_PRINT:
        print("Block: " + str(block_index))

    if not has_skipped_first_block:
        cur_block_start += BLOCK_LENGTH
        has_skipped_first_block = True
        continue
    
    start_of_text = int.from_bytes(data[cur_block_start:cur_block_start+4], byteorder='little', signed=False)
    start_of_link_table = int.from_bytes(data[cur_block_start+4:cur_block_start+8], byteorder='little', signed=False)
    link_count = int.from_bytes(data[cur_block_start+8:cur_block_start+12], byteorder='little', signed=False)

    if SHOULD_PRINT:
        print("\tStart of text: " + str(start_of_text))
        print("\tStart of link table: " + str(start_of_link_table))
        print("\tLink count: " + str(link_count))

    length_of_data = start_of_link_table + (LINK_LENGTH * link_count)

    text_data = data[cur_block_start+start_of_text:cur_block_start+start_of_link_table]
    link_table_data = data[cur_block_start+start_of_link_table:cur_block_start+length_of_data]

    title = get_title(text_data)
    entry_index_to_title[block_index] = title

    link_map = generate_link_map(link_table_data)

    if SHOULD_PRINT:
        print(link_map)

    generate_page(text_data, title, link_map, block_index)

    cur_block_start += math.ceil(length_of_data / BLOCK_LENGTH) * BLOCK_LENGTH
    block_index += 1

block_count = block_index

unused_entries = []

for i in range(block_index):
    if i not in used_link_destinations:
        if SHOULD_PRINT:
            print("Page " + str(i) + " is never a link destination.")
        
        unused_entries.append(i)

generate_page_linking_to_unlinked_entries(unused_entries, entry_index_to_title)

generate_index_page(block_count, unused_entries, entry_index_to_title)
