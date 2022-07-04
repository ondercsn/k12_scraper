import os
import sys

from multiprocessing.pool import Pool
from src.k12_scraper import K12Scraper

if __name__ == "__main__":
    uname_arg = None
    passw_arg = None

    if len(sys.argv) > 1 :
        uname_arg = sys.argv[1]
        passw_arg = sys.argv[2]

    download_dir = "/downloads"
    username = uname_arg if uname_arg is not None else os.getenv("USERNAME")
    password = passw_arg if passw_arg is not None else os.getenv("PASSWORD")
    app = passw_arg if passw_arg is not None else os.getenv("APP")

    k12 = K12Scraper(app=app, username=username, password=password, target_dir=download_dir)

    messages = k12.fetch_messages()
    if messages:
        attachments = k12.fetch_attachments(messages)
        pool = Pool(os.cpu_count())
        results = pool.map(k12.download_file, attachments)
        pool.close()
        pool.join()
