import os
from pybtex.database import parse_file
from urllib import request

def main():
    script_dir = os.path.dirname(__file__) 
    rel_path = '_bibliography/bib.bib'
    abs_file_path = os.path.join(script_dir, rel_path)

    bib_data = parse_file(abs_file_path)

    for entry_id in bib_data.entries:
        fields = bib_data.entries[entry_id].fields
        if(fields.get("video") != None):
            donwload_thumbnails(fields.get("video"))
        if(fields.get("talk") != None):
            donwload_thumbnails(fields.get("talk"))

def donwload_thumbnails(youtubeUrl):
    youtubeId = youtubeUrl.split('=')[-1].replace('\\', '')
    remote_url = 'https://img.youtube.com/vi/' + youtubeId + '/hqdefault.jpg'

    print(remote_url)

    script_dir = os.path.dirname(__file__) 
    rel_path = 'assets/img/youtube_thumbnails/' + youtubeId + ".jpg"
    abs_file_path = os.path.join(script_dir, rel_path)

    if(os.path.isfile(abs_file_path)):
        print("Skipping " + youtubeId + " as file exists...")
    else:
        request.urlretrieve(remote_url, abs_file_path)


if __name__=="__main__":
    main()