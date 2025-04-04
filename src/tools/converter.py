import asyncio
import os

import imageio
from docx2pdf import convert as docx2pdf_convert
from pdf2docx import Converter

from src.utils.async_copy_file import async_copy_file


class FileConverter:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.base, self.extension = os.path.splitext(file_path)
        self.extension = self.extension.lower()

    async def get_available_formats(self):
        """
        Асинхронно определяет, в какие форматы возможно конвертировать данный файл.
        Возвращаются допустимые расширения для видео, изображений и документов.
        """
        video_formats = ['.mp4', '.avi', '.mkv', '.mov']
        image_formats = ['.jpg', '.jpeg', '.png', '.gif']
        document_formats = ['.doc', '.docx', '.pdf']
        if self.extension in video_formats:
            video_formats.remove(self.extension)
            return video_formats
        elif self.extension in image_formats:
            image_formats.remove(self.extension)
            return image_formats
        elif self.extension in document_formats:
            if self.extension in ['.doc', '.docx']:
                formats = ['.docx', '.pdf']
                formats.remove(self.extension)
                return formats
            elif self.extension == '.pdf':
                formats = ['.pdf', '.docx']
                formats.remove(self.extension)
                return formats
        return []

    async def convert_to_format(self, target_format: str, output_file: str = None):
        """
        Асинхронно конвертирует исходный файл в указанный формат.
        """
        target_format = target_format.lower()
        available = await self.get_available_formats()
        if target_format not in available:
            raise ValueError(f"Конвертация в формат {target_format} не поддерживается для файла {self.file_path}.")

        if output_file is None:
            output_file = self.base + target_format

        if self.extension == target_format:
            return self.file_path

        video_formats = ['.mp4', '.avi', '.mkv', '.mov']
        if self.extension in video_formats:
            await asyncio.to_thread(self._convert_video, output_file)
            return output_file

        image_formats = ['.jpg', '.jpeg', '.png', '.gif']
        if self.extension in image_formats:
            await asyncio.to_thread(self._convert_image, output_file)
            return output_file

        document_formats = ['.doc', '.docx', '.pdf']
        if self.extension in document_formats:
            if self.extension in ['.doc', '.docx'] and target_format == '.pdf':
                await asyncio.to_thread(docx2pdf_convert, self.file_path, output_file)
                return output_file
            elif self.extension == '.pdf' and target_format == '.docx':
                await asyncio.to_thread(self._convert_pdf_to_docx, output_file)
                return output_file
            else:
                await async_copy_file(self.file_path, output_file)
                return output_file

        raise ValueError("Неизвестный тип файла для конвертации.")

    def _convert_video(self, output_file: str):
        reader = imageio.get_reader(self.file_path)
        meta_data = reader.get_meta_data()
        fps = meta_data.get('fps', 25)
        writer = imageio.get_writer(output_file, fps=fps)
        try:
            for frame in reader:
                writer.append_data(frame)
        finally:
            writer.close()
            reader.close()

    def _convert_image(self, output_file: str):
        img = imageio.imread(self.file_path)
        imageio.imwrite(output_file, img)

    def _convert_pdf_to_docx(self, output_file: str):
        cv = Converter(self.file_path)
        try:
            cv.convert(output_file, start=0, end=None)
        finally:
            cv.close()
