from tqdm import tqdm
from src import config


class Downloader:
    def __init__(self, tracker):
        pass

    def download_all_pdfs(self, documents_metadata, folder):
        status_l = []
        for doc in tqdm(documents_metadata):
            try:
                status = self.download_pdf()
            except:
                status = 404
            status_l.append(status)
            time.sleep(10)
        return status_l

    def download_pdf(self, document_metadata, folder):
        headers = config.HEADERS
        download_url = document_metadata.download_url
        filename = folder / f'{document_metadata.title.replace("/", "_")}.pdf'
        response = requests.get(download_url, headers=headers)

        if response.status_code == 200:
            # Save the PDF content to a local file
            with open(filename, "wb") as pdf_file:
                pdf_file.write(response.content)
            logger.info(f"Downloaded: {download_url}")
        else:
            logger.info(
                f"Failed to download file: {document_metadata.title} with url: {download_url}. Status Code: {response.status_code}"
            )
        return response.status_code
