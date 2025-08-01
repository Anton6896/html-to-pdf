import asyncio
import os
import random
import time

import httpx

url1 = 'http://localhost:8000/api/convert/'
url2 = 'http://localhost:8000/api/convert/xhtml/'
ROOT = os.path.dirname(os.path.abspath(__file__))
data_folder = os.path.join(ROOT, 'data')


async def do_test():
    with open(os.path.join(data_folder, '1-page.docx'), 'rb') as f:
        data_1 = {'document': f.read(), 'document_type': 'docx', 'url': url1}  # docx -> pdf

    with open(os.path.join(data_folder, 'testing.xlsx'), 'rb') as f:
        data_2 = {'document': f.read(), 'document_type': 'xlsx', 'url': url2}  # xlsx -> html

    payloads = [data_1, data_2] * 50
    random.shuffle(payloads)
    overall_start = time.perf_counter()
    responses = []
    chunk_size = 99

    async with httpx.AsyncClient(timeout=120) as client:
        for i in range(0, len(payloads), chunk_size):
            print(f'working on {i} : {i + chunk_size}')

            chunk_start = time.perf_counter()
            chunk = payloads[i : i + chunk_size]
            tasks = []

            for payload in chunk:
                files = {'file': payload.get('document')}
                url = payload.get('url')
                tasks.append(client.post(url, files=files))

            chunk_responses = await asyncio.gather(*tasks)
            chunk_elapsed = time.perf_counter() - chunk_start
            print(f'Chunk {i // chunk_size + 1} took {chunk_elapsed:.2f} seconds')
            responses.extend(chunk_responses)

    # Report overall duration
    overall_elapsed = time.perf_counter() - overall_start
    print(f'Total elapsed time: {overall_elapsed:.2f} seconds')

    print(f'results {[(x, y.status_code) for x, y in enumerate(responses, 1)]}')


if __name__ == '__main__':
    asyncio.run(do_test())
