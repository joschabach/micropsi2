#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Utilities.
"""

__author__ = 'priska'
__date__ = '08.10.14'


def scrape_textures():
    """
    Stand-alone script to scrape block images from minecraft.gamepedia.com with
    BeautifulSoup and saves them to the current directory. Also saves an
    ID-to-blockname mapping to a file called new_structs.

    You can use this script to retrieve the current block icons /textures used
    for visualizing the agent's view; i.e. the icons stored in
    micropsi_server/static/minecraft/block_textures and the mapping used in
    minecraft_struct.js and structs.py.

    Note: even though flat textures would be more aesthetic, the blockish icons
    ensure completeness while still allowing the user to recognize scenes.
    """
    import os
    from io import open as iopen
    import requests
    from bs4 import BeautifulSoup

    url = "http://minecraft.gamepedia.com/Data_values/Block_IDs"
    mapping_file = "new_structs"

    r = requests.get(url)
    if r.status_code == requests.codes.ok:

        html = r.text
        soup = BeautifulSoup(html)
        tds = soup.find_all('td')

        id2name_map = dict()

        ctr = 0
        for td in tds:
            if td.get('height') == "27px":
                # get image url and filename from this <td>, block ID from next <td>
                if td.find('img'):
                    # get name of block type
                    png_name = td.find('img').get('alt')
                    # replace spaces with underscores
                    png_name = png_name.replace(" ", "_")
                    # remove file extension for ID -> name map
                    item = os.path.splitext(png_name)[0]
                    # get URL of block type image
                    image_url = td.find('img').get('src')
                    # get block ID
                    block_id = int(tds[ctr + 1].text)
                    # add pair to map
                    id2name_map[block_id] = item

                    # download image and save it to disk
                    i = requests.get(image_url)
                    if i.status_code == requests.codes.ok:
                        with iopen(png_name, 'wb') as imgf:
                            imgf.write(i.content)
            ctr += 1

        # write ID -> name map to file; done only here to sort them numerically
        with open(mapping_file, 'w') as f:
            for key in sorted(id2name_map.keys()):
                f.write('"%s": "%s",\n' % (key, id2name_map[key]))
