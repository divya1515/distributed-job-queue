import csv 
import io

def parse_csv(file_bytes:bytes) -> list[str]:
    text=file_bytes.decode("utf_8")
    reader=csv.reader(io.StringIO(text))
    urls=[]
    for row in reader:
        if not row:
            continue
        url=row[0].strip()
        if url:
            urls.append(url)

    return urls