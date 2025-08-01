import asyncio
import base64
import os
import random
import time

import httpx

url = 'http://localhost:8022/api/v1/convert_data/'
ROOT = os.path.dirname(os.path.abspath(__file__))
data_folder = os.path.join(ROOT, 'data')


async def do_test():
    with open(os.path.join(data_folder, '1-page.docx'), 'rb') as f:
        data_1 = {'document': base64.b64encode(f.read()).decode(), 'document_type': 'docx'}

    with open(os.path.join(data_folder, 'testing.xlsx'), 'rb') as f:
        data_2 = {'document': base64.b64encode(f.read()).decode(), 'document_type': 'xlsx'}

    payloads = [data_1, data_2] * 50
    random.shuffle(payloads)
    overall_start = time.perf_counter()

    responses = []
    chunk_size = 25
    async with httpx.AsyncClient(timeout=120) as client:
        for i in range(0, len(payloads), chunk_size):
            print(f'working on {i} : {i + chunk_size}')

            # Start timer for this chunk
            chunk_start = time.perf_counter()
            chunk = payloads[i : i + chunk_size]
            tasks = [client.post(url, json=payload) for payload in chunk]
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
